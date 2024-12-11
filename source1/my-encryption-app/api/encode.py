from flask import Flask, Blueprint, request, jsonify
from api.registry import EncryptionRegistry
from api.utils import generate_id
import base64
import requests
import os
import logging
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Request, Response
from http.server import BaseHTTPRequestHandler

# Flask Blueprint for encoding
encode_bp = Blueprint("encode", __name__, url_prefix="/api/encode/")

# Load Redis configurations
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
UPSTASH_REDIS_PASSWORD = os.getenv("UPSTASH_REDIS_PASSWORD")
HEADERS = {"Authorization": f"Bearer {UPSTASH_REDIS_PASSWORD}"}

# Initialize Flask app
app = Flask(__name__)

@encode_bp.route("", methods=["POST"])
def encode():
    try:
        # Parse request data
        data = request.json
        logging.debug(f"Request received for encoding: {data}")

        # Extract encryption details
        algorithm_name = data.get("algorithm", "AES256")
        password = data.get("password")
        try:
            file_data = base64.b64decode(data.get("file_data"))
        except Exception as e:
            logging.error(f"Invalid Base64 input: {e}")
            return jsonify({"error": "Invalid Base64 file_data"}), 400

        # Validate algorithm
        algorithm = EncryptionRegistry.get(algorithm_name)
        if algorithm is None:
            logging.error(f"Algorithm not found: {algorithm_name}")
            return jsonify({"error": "Unsupported encryption algorithm"}), 400

        # Encrypt file data
        encrypted_data, encryption_metadata = algorithm.encrypt(file_data, password)

        # Validate and enforce TTL bounds
        ttl_seconds = data.get("ttl", 60)  # Default to 60 seconds if not provided

        # Debug received TTL for accuracy
        logging.debug(f"Received TTL in seconds: {ttl_seconds}")

        if ttl_seconds < 60:
            ttl_seconds = 60  # Minimum TTL is 1 minute
        elif ttl_seconds > 90 * 86400:
            ttl_seconds = 90 * 86400  # Maximum TTL is 90 days

        # Log the validated TTL
        logging.debug(f"Final validated TTL (in seconds): {ttl_seconds}")

        # Add metadata for Redis
        metadata = {
            "encrypted_data": base64.b64encode(encrypted_data).decode("utf-8"),
            "tag": base64.b64encode(encryption_metadata["tag"]).decode("utf-8"),
            "reads": str(data.get("reads", 1)),  # Store as string
            "ttl": ttl_seconds,  # Store as integer
            "file_name": str(data.get("file_name", "unknown")),
            "file_type": str(data.get("file_type", "application/octet-stream")),
            "iv": base64.b64encode(encryption_metadata["iv"]).decode("utf-8"),
            "salt": base64.b64encode(encryption_metadata["salt"]).decode("utf-8"),
        }

        # Log metadata for debugging
        logging.debug(f"Metadata for Redis: {metadata}")

        # Generate unique file ID and prepare Redis commands
        file_id = generate_id()
        key = f"cipher_share:{file_id}"
        redis_pipeline = []
        for k, v in metadata.items():
            redis_pipeline.append(["hset", key, k, str(v) if k != "ttl" else v])  # Convert all but TTL to string
        # Debug the TTL being sent to Redis
        logging.debug(f"Setting TTL for key {key}: {ttl_seconds} seconds")
        redis_pipeline.append(["expire", key, ttl_seconds])  # TTL as integer for Redis

        # Log Redis pipeline for debugging
        logging.debug(f"Redis pipeline: {redis_pipeline}")

        # Store encrypted data in Redis
        response = requests.post(f"{UPSTASH_REDIS_URL}/pipeline", headers=HEADERS, json=redis_pipeline)
        logging.debug(f"Redis response: {response.status_code}, {response.text}")
        if response.status_code != 200:
            return jsonify({"error": "Failed to store encrypted data"}), 500

        # Generate and return shareable link
        domain = os.getenv("DOMAIN", "https://ciphare.vercel.app")
        return jsonify({"file_id": file_id, "share_link": f"{domain}/decode/{file_id}"}), 201
    except Exception as e:
        logging.error(f"Error during encoding: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Define a BaseHTTPRequestHandler for Vercel compatibility
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        env = {
            "REQUEST_METHOD": self.command,
            "PATH_INFO": self.path,
            "SERVER_PROTOCOL": self.request_version,
            "CONTENT_LENGTH": self.headers.get('Content-Length'),
            "CONTENT_TYPE": self.headers.get('Content-Type'),
        }
        body = self.rfile.read(int(env['CONTENT_LENGTH']) if env['CONTENT_LENGTH'] else 0)
        req = Request.from_values(
            path=self.path,
            environ=env,
            input_stream=body,
        )
        response = Response.force_type(app.full_dispatch_request(), req)
        self.send_response(response.status_code)
        for key, value in response.headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(response.get_data())
