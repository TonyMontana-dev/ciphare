from flask import Flask, Blueprint, request, jsonify
from api.registry import EncryptionRegistry
from api.utils import generate_id
from api.mongodb_client import mongodb_client
from api.storage_service import storage_service
import base64
import os
import logging
from datetime import datetime, timedelta
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Request, Response
from http.server import BaseHTTPRequestHandler

# Flask Blueprint for encoding
encode_bp = Blueprint("encode", __name__, url_prefix="/api/encode")

# Initialize Flask app
app = Flask(__name__)

@encode_bp.route("", methods=["POST", "OPTIONS"])
@encode_bp.route("/", methods=["POST", "OPTIONS"])
def encode():
    if request.method == "OPTIONS":
        # Handle preflight request
        response = jsonify({"message": "OK"})
        response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response

    try:
        # Parse request data
        data = request.json
        logging.debug(f"Request received for encoding: {data}")

        # Extract encryption details
        algorithm_name = data.get("algorithm", "AES256")
        password = data.get("password")
        file_data = data.get("file_data")  # Already in Base64 format

        if not file_data:
            logging.error("No file data provided")
            return jsonify({"error": "No file data provided"}), 400

        try:
            # Decode Base64 string to bytes for encryption
            file_data_bytes = base64.b64decode(file_data)
        except Exception as e:
            logging.error(f"Invalid Base64 input: {e}")
            return jsonify({"error": "Invalid Base64 file_data"}), 400

        # Validate algorithm
        algorithm = EncryptionRegistry.get(algorithm_name)
        if algorithm is None:
            logging.error(f"Algorithm not found: {algorithm_name}")
            return jsonify({"error": "Unsupported encryption algorithm"}), 400

        # Encrypt file data
        encrypted_data, encryption_metadata = algorithm.encrypt(file_data_bytes, password)

        # Validate and enforce TTL bounds
        ttl_seconds = data.get("ttl", 60)  # Default to 60 seconds if not provided
        if ttl_seconds < 60:
            ttl_seconds = 60  # Minimum TTL is 1 minute
        elif ttl_seconds > 90 * 86400:
            ttl_seconds = 90 * 86400  # Maximum TTL is 90 days

        # Generate unique file ID
        file_id = generate_id()

        # Store encrypted data in MongoDB
        metadata = {
            "file_id": file_id,
            "encrypted_data": base64.b64encode(encrypted_data).decode("utf-8"),  # Convert back to Base64 for storage
            "tag": base64.b64encode(encryption_metadata["tag"]).decode("utf-8"),
            "reads": data.get("reads", 1),
            "ttl": ttl_seconds,
            "file_name": data.get("file_name", "unknown"),
            "file_type": data.get("file_type", "application/octet-stream"),
            "iv": base64.b64encode(encryption_metadata["iv"]).decode("utf-8"),
            "salt": base64.b64encode(encryption_metadata["salt"]).decode("utf-8"),
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=ttl_seconds),
            "algorithm": algorithm_name
        }

        # Store metadata in MongoDB
        if not mongodb_client.store_file_metadata(file_id, metadata):
            return jsonify({"error": "Failed to store file metadata"}), 500

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
