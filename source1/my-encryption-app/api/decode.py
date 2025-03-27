from flask import Flask, Blueprint, request, jsonify
from api.registry import EncryptionRegistry
from api.mongodb_client import mongodb_client
from api.storage_service import storage_service
import base64
import os
import logging
from datetime import datetime
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Request, Response
from http.server import BaseHTTPRequestHandler

# Flask Blueprint for decoding
decode_bp = Blueprint("decode", __name__, url_prefix="/api/decode")

# Initialize Flask app
app = Flask(__name__)

@decode_bp.route("", methods=["OPTIONS"])
@decode_bp.route("/", methods=["OPTIONS"])
def handle_options():
    # Handle preflight request
    response = jsonify({"message": "OK"})
    response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    return response

@decode_bp.route("/<file_id>", methods=["POST", "OPTIONS"])
def decode(file_id):
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
        password = data.get("password")

        # Get file metadata from MongoDB
        metadata = mongodb_client.get_file_metadata(file_id)
        if not metadata:
            return jsonify({"error": "File not found or expired"}), 404

        # Check if file has expired
        if datetime.utcnow() > metadata["expires_at"]:
            return jsonify({"error": "File has expired"}), 410

        # Check if max reads reached
        if metadata["reads"] <= 0:
            return jsonify({"error": "Maximum reads reached"}), 403

        # Get encryption algorithm
        algorithm = EncryptionRegistry.get(metadata["algorithm"])
        if algorithm is None:
            return jsonify({"error": "Unsupported encryption algorithm"}), 400

        # Decrypt the data
        try:
            encrypted_data = base64.b64decode(metadata["encrypted_data"])
            decrypted_data = algorithm.decrypt(
                encrypted_data,
                password,
                {
                    "iv": base64.b64decode(metadata["iv"]),
                    "tag": base64.b64decode(metadata["tag"]),
                    "salt": base64.b64decode(metadata["salt"])
                }
            )
        except Exception as e:
            logging.error(f"Decryption error: {str(e)}")
            return jsonify({"error": "Invalid password or corrupted data"}), 400

        # Update read count
        if not mongodb_client.update_file_reads(file_id):
            logging.error("Failed to update read count")

        # Return decrypted data
        return jsonify({
            "file_data": base64.b64encode(decrypted_data).decode("utf-8"),
            "file_name": metadata["file_name"],
            "file_type": metadata["file_type"],
            "remaining_reads": metadata["reads"] - 1
        }), 200

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
