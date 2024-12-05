from flask import Flask, Blueprint, request, jsonify
from api.registry import EncryptionRegistry
import base64
import requests
import os
import logging
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Request, Response
from http.server import BaseHTTPRequestHandler

# Flask Blueprint for decoding
decode_bp = Blueprint("decode", __name__, url_prefix="/api/decode")

# Load Redis configurations
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
UPSTASH_REDIS_PASSWORD = os.getenv("UPSTASH_REDIS_PASSWORD")
HEADERS = {"Authorization": f"Bearer {UPSTASH_REDIS_PASSWORD}"}

# Initialize Flask app
app = Flask(__name__)

# Helper functions
def is_valid_base64(s: str) -> bool:
    """Check if a string is valid Base64."""
    try:
        base64.b64decode(s, validate=True)
        return True
    except Exception:
        return False

def add_padding(base64_string):
    """Ensure Base64 string has proper padding."""
    return base64_string + "=" * (-len(base64_string) % 4)

@decode_bp.route("", methods=["POST"])
def decode():
    try:
        # Parse request data
        data = request.json
        logging.debug(f"Request received for decoding: {data}")

        # Extract decryption details
        file_id = data.get("file_id")
        password = data.get("password")
        algorithm_name = data.get("algorithm", "AES256")

        # Validate inputs
        if not file_id or not password:
            return jsonify({"error": "File ID and password are required"}), 400

        # Fetch metadata from Redis
        key = f"cipher_share:{file_id}"
        response = requests.get(f"{UPSTASH_REDIS_URL}/hgetall/{key}", headers=HEADERS)
        logging.debug(f"Redis response for key {key}: {response.text}")

        if response.status_code != 200 or not response.json().get("result"):
            return jsonify({"error": "File not found or expired"}), 404

        raw_result = response.json()["result"]
        metadata = {}

        # Process metadata
        for i in range(0, len(raw_result), 2):
            k, v = raw_result[i], raw_result[i + 1]
            if k in ["file_name", "file_type"]:
                metadata[k] = v  # Skip decoding for plain strings
            elif k in ["ttl", "reads"]:
                metadata[k] = int(v)  # Parse as integers
            else:
                if not is_valid_base64(v):
                    logging.error(f"Invalid Base64 string for key {k}: {v}")
                    return jsonify({"error": f"Invalid Base64 string for key {k}"}), 400
                metadata[k] = base64.b64decode(add_padding(v))

        encrypted_data = metadata.pop("encrypted_data")

        # Validate algorithm
        algorithm = EncryptionRegistry.get(algorithm_name)
        if not algorithm:
            return jsonify({"error": f"Algorithm {algorithm_name} not supported"}), 400

        # Decrypt file data
        decrypted_data = algorithm.decrypt(encrypted_data, password, metadata)

        # Update `reads` or delete if exhausted
        remaining_reads = metadata["reads"] - 1
        if remaining_reads > 0:
            requests.post(
                f"{UPSTASH_REDIS_URL}/hincrby/{key}/reads/-1",
                headers=HEADERS
            )
        else:
            requests.post(
                f"{UPSTASH_REDIS_URL}/del/{key}",
                headers=HEADERS
            )

        # Return decrypted file data and metadata
        return jsonify({
            "decrypted_data": base64.b64encode(decrypted_data).decode(),
            "file_name": metadata.get("file_name", "unknown"),
            "file_type": metadata.get("file_type", "application/octet-stream"),
            "remaining_reads": remaining_reads
        })
    except Exception as e:
        logging.error(f"Error during decoding: {str(e)}")
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
