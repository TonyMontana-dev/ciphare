from flask import Blueprint, request, jsonify
from api.registry import EncryptionRegistry
from api.utils import generate_id
from api.storage import Storage
import base64
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask Blueprint for encoding
encode_bp = Blueprint("encode", __name__, url_prefix="/api/encode")

# Initialize storage
try:
    storage = Storage()
    logger.info("Storage initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize storage: {e}", exc_info=True)
    storage = None

@encode_bp.route("", methods=["POST"])
@encode_bp.route("/", methods=["POST"])
def encode():
    try:
        if not storage:
            error_msg = "Storage service unavailable. Please check MongoDB and R2 configuration."
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 500
        
        # Parse request data
        data = request.json
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        logger.debug("Request received for encoding")

        # Extract encryption details
        algorithm_name = data.get("algorithm", "AES256")
        password = data.get("password")
        
        if not password:
            return jsonify({"error": "Password is required"}), 400

        # Validate and decode file data
        file_data_b64 = data.get("file_data")
        if not file_data_b64:
            return jsonify({"error": "file_data is required"}), 400

        try:
            file_data = base64.b64decode(file_data_b64)
        except Exception as e:
            logger.error(f"Invalid Base64 input: {e}")
            return jsonify({"error": "Invalid Base64 file_data"}), 400

        # Validate file size (500MB max)
        MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
        if len(file_data) > MAX_FILE_SIZE:
            return jsonify({"error": f"File size exceeds 500MB limit. File size: {len(file_data) / (1024*1024):.2f}MB"}), 400

        # Validate algorithm
        try:
            algorithm = EncryptionRegistry.get(algorithm_name)
        except ValueError as e:
            logger.error(f"Algorithm not found: {algorithm_name}")
            return jsonify({"error": "Unsupported encryption algorithm"}), 400

        # Encrypt file data
        logger.info(f"Encrypting file, size: {len(file_data)} bytes")
        encrypted_data, encryption_metadata = algorithm.encrypt(file_data, password)
        logger.info(f"Encryption complete, encrypted size: {len(encrypted_data)} bytes")

        # Validate and enforce TTL bounds
        ttl_seconds = data.get("ttl", 60)  # Default to 60 seconds if not provided

        if ttl_seconds < 60:
            ttl_seconds = 60  # Minimum TTL is 1 minute
        elif ttl_seconds > 90 * 86400:
            ttl_seconds = 90 * 86400  # Maximum TTL is 90 days

        # Validate reads
        reads = data.get("reads", 1)
        if reads < 1:
            reads = 1
        elif reads > 100:
            reads = 100  # Maximum reads limit

        # Prepare metadata for storage
        metadata = {
            "file_name": str(data.get("file_name", "unknown"))[:255],
            "file_type": str(data.get("file_type", "application/octet-stream"))[:100],
            "iv": base64.b64encode(encryption_metadata["iv"]).decode("utf-8"),
            "salt": base64.b64encode(encryption_metadata["salt"]).decode("utf-8"),
            "tag": base64.b64encode(encryption_metadata["tag"]).decode("utf-8"),
            "reads": reads,
            "ttl_seconds": ttl_seconds,
        }

        # Generate unique file ID
        file_id = generate_id()
        logger.info(f"Generated file_id: {file_id}")

        # Store encrypted file in R2 and metadata in MongoDB
        storage.store_file(file_id, encrypted_data, metadata)
        logger.info(f"File stored successfully: {file_id}")

        # Generate and return shareable link
        domain = os.getenv("DOMAIN", "https://ciphare.vercel.app")
        # Use query parameter format to match decode page extraction logic
        share_link = f"{domain}/decode?id={file_id}"
        return jsonify({
            "file_id": file_id,
            "share_link": share_link
        }), 201
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error during encoding: {error_msg}", exc_info=True)
        # Return more specific error messages for common issues
        if "MONGODB_URI" in error_msg or "MongoDB" in error_msg:
            return jsonify({"error": "Database connection failed. Please check MongoDB configuration."}), 500
        elif "R2" in error_msg or "boto3" in error_msg or "S3" in error_msg:
            return jsonify({"error": "File storage connection failed. Please check R2 configuration."}), 500
        else:
            return jsonify({"error": f"Encryption failed: {error_msg}"}), 500

# Note: Vercel serverless function handler is in api/encode/index.py
