from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
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
CORS(app)  # Enable CORS for the app

@encode_bp.route("", methods=["POST"])
def encode():
    try:
        # Parse request data
        data = request.json
        logging.debug(f"Request received for encoding: {data}")
        
        # Extract encryption details
        algorithm_name = data.get("algorithm", "AES256")
        password = data.get("password")
        file_data = base64.b64decode(data.get("file_data"))

        # Validate algorithm
        algorithm = EncryptionRegistry.get(algorithm_name)
        if algorithm is None:
            raise ValueError(f"Algorithm {algorithm_name} not found in registry.")

        # Encrypt file data
        encrypted_data, metadata = algorithm.encrypt(file_data, password)

        # Add metadata for Redis
        metadata["encrypted_data"] = base64.b64encode(encrypted_data).decode()
        metadata["reads"] = int(data.get("reads", 1))
        metadata["ttl"] = int(data.get("ttl", 86400))
        metadata["file_name"] = data.get("file_name", "unknown")
        metadata["file_type"] = data.get("file_type", "application/octet-stream")

        # Ensure all metadata values are JSON serializable
        for key, value in metadata.items():
            if isinstance(value, bytes):
                metadata[key] = base64.b64encode(value).decode()

        # Generate unique file ID and prepare Redis commands
        file_id = generate_id()
        key = f"cipher_share:{file_id}"
        redis_pipeline = [[f"hset", key, k, v] for k, v in metadata.items()]
        redis_pipeline.append(["expire", key, metadata["ttl"]])

        # Store encrypted data in Redis
        response = requests.post(f"{UPSTASH_REDIS_URL}/pipeline", headers=HEADERS, json=redis_pipeline)
        logging.debug(f"Redis response: {response.text}")

        # Handle Redis errors
        if response.status_code != 200:
            return jsonify({"error": "Failed to store encrypted data"}), 500

        # Generate and return shareable link
        domain = os.getenv("DOMAIN", "https://ciphare.vercel.app")
        return jsonify({"file_id": file_id, "share_link": f"{domain}/decode/{file_id}"})
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
