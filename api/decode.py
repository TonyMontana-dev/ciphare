from flask import Blueprint, request, jsonify
from api.registry import EncryptionRegistry
from api.storage import Storage
import base64
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask Blueprint for decoding
decode_bp = Blueprint("decode", __name__, url_prefix="/api/decode")

# Initialize storage
try:
    storage = Storage()
except Exception as e:
    logger.error(f"Failed to initialize storage: {e}")
    storage = None

# Helper function
def add_padding(base64_string):
    """Ensure Base64 string has proper padding."""
    return base64_string.rstrip("=").ljust(len(base64_string) + (-len(base64_string) % 4), "=")

@decode_bp.route("", methods=["POST"])
@decode_bp.route("/", methods=["POST"])
def decode():
    try:
        if not storage:
            return jsonify({"error": "Storage service unavailable"}), 500
        
        # Parse request data
        data = request.json
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        logger.debug("Request received for decoding")

        # Extract decryption details
        file_id = data.get("file_id")
        password = data.get("password")
        algorithm_name = data.get("algorithm", "AES256")

        # Validate inputs
        if not file_id or not password:
            return jsonify({"error": "File ID and password are required"}), 400

        # Validate file_id format (basic sanitization)
        if len(file_id) > 100 or not isinstance(file_id, str):
            return jsonify({"error": "Invalid file ID format"}), 400
        
        # Clean and normalize file_id (remove any whitespace, URL decode if needed)
        file_id = file_id.strip()
        logger.info(f"Looking up file_id: '{file_id}' (length: {len(file_id)})")
        
        # Get metadata from MongoDB
        metadata_doc = storage.get_metadata(file_id)
        if not metadata_doc:
            logger.warning(f"File not found: {file_id}")
            return jsonify({"error": "File not found or expired"}), 404
        
        logger.info(f"Found metadata for file_id: {file_id}, reads remaining: {metadata_doc.get('reads', 0)}")

        # Check reads count
        if metadata_doc.get('reads', 0) <= 0:
            logger.info(f"File {file_id} has no reads remaining")
            storage.delete_file(file_id)
            return jsonify({"error": "File has been deleted after reaching maximum reads"}), 404

        # Get encrypted file from R2
        encrypted_data = storage.get_file(file_id)
        if not encrypted_data:
            return jsonify({"error": "Encrypted file not found"}), 404

        logger.info(f"Retrieved encrypted file: {len(encrypted_data)} bytes")

        # Prepare metadata for decryption
        try:
            metadata = {
                "iv": base64.b64decode(add_padding(metadata_doc['iv'])),
                "salt": base64.b64decode(add_padding(metadata_doc['salt'])),
                "tag": base64.b64decode(add_padding(metadata_doc['tag'])),
            }
        except Exception as e:
            logger.error(f"Error decoding metadata: {str(e)}")
            return jsonify({"error": "Invalid metadata format"}), 400

        # Validate tag length
        if len(metadata["tag"]) != 16:
            return jsonify({"error": "Invalid authentication tag"}), 400

        # Validate algorithm
        try:
            algorithm = EncryptionRegistry.get(algorithm_name)
        except ValueError:
            return jsonify({"error": f"Algorithm {algorithm_name} not supported"}), 400

        # Decrypt file data
        try:
            logger.info("Starting decryption...")
            decrypted_data = algorithm.decrypt(encrypted_data, password, metadata)
            logger.info(f"Decryption successful, size: {len(decrypted_data)} bytes")
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            return jsonify({"error": "Decryption failed. Invalid password or corrupted data."}), 400

        # Decrement reads count
        remaining_reads = storage.decrement_reads(file_id)
        if remaining_reads is None:
            remaining_reads = 0

        # Return decrypted file data and metadata
        return jsonify({
            "decrypted_data": base64.b64encode(decrypted_data).decode(),
            "file_name": metadata_doc.get("file_name", "unknown"),
            "file_type": metadata_doc.get("file_type", "application/octet-stream"),
            "remaining_reads": max(remaining_reads, 0)
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error during decoding: {error_msg}", exc_info=True)
        # Return more specific error messages for common issues
        if "MONGODB_URI" in error_msg or "MongoDB" in error_msg:
            return jsonify({"error": "Database connection failed. Please check MongoDB configuration."}), 500
        elif "R2" in error_msg or "boto3" in error_msg or "S3" in error_msg:
            return jsonify({"error": "File storage connection failed. Please check R2 configuration."}), 500
        else:
            return jsonify({"error": f"Decryption failed: {error_msg}"}), 500

# Note: Vercel serverless function handler is in api/decode/index.py
