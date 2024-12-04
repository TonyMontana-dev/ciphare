from flask import Blueprint, request, jsonify
from api.registry import EncryptionRegistry
from api.utils import generate_id
import base64
import requests
import os
import logging

encode_bp = Blueprint("encode", __name__, url_prefix="/api/encode/")

# Load Redis configurations
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
UPSTASH_REDIS_PASSWORD = os.getenv("UPSTASH_REDIS_PASSWORD")
HEADERS = {"Authorization": f"Bearer {UPSTASH_REDIS_PASSWORD}"}


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



# BACKUP CODE FOR REFERENCE
"""
# Store and encrypt data
@app.route("/api/encode", methods=["POST"])
def encode_data():
    try:
        data = request.json  
        password = data.get("password")  # Password for encryption
        file_data = data.get("file_data")  # Base64 encoded file data
        file_name = data.get("file_name")  # Original file name
        file_type = data.get("file_type")  # Original MIME type
        reads = int(data.get("reads", 1))  # Default to 1 read
        ttl = int(data.get("ttl", 86400))  # Default to 1 day
        
        if not password or not file_data or not file_name or not file_type:
            return jsonify({"error": "Password, file data, file name, and file type are required"}), 400

        file_data_bytes = base64.b64decode(file_data)  # Decode Base64 data
        salt = generate_salt()  # Generate random salt for encryption
        encrypted_data, iv, tag = encrypt_aes256(file_data_bytes, password, salt)  # Encrypt the data
        file_id = generate_id()  # Generate unique file ID
        key = f"cipher_share:{file_id}"  # Redis key for storing the encrypted data

        # Encoded payload for Redis storage and shareable link generation
        encoded_data = {
            "encrypted_data": base64.urlsafe_b64encode(encrypted_data).decode(),
            "iv": base64.urlsafe_b64encode(iv).decode(),
            "tag": base64.urlsafe_b64encode(tag).decode(),
            "salt": base64.urlsafe_b64encode(salt).decode(),
            "reads": reads,
            "file_name": file_name,
            "file_type": file_type
        }

        # Pipeline commands as list of lists for Redis storage and expiration with TTL in seconds
        redis_pipeline = [
            ["hset", key, "encrypted_data", encoded_data["encrypted_data"]],
            ["hset", key, "iv", encoded_data["iv"]],
            ["hset", key, "tag", encoded_data["tag"]],
            ["hset", key, "salt", encoded_data["salt"]],
            ["hset", key, "reads", encoded_data["reads"]],
            ["hset", key, "file_name", file_name],
            ["hset", key, "file_type", file_type],
            ["expire", key, ttl]
        ]

        # Send pipeline request to Upstash Redis for atomicity and expiration of data with TTL
        redis_response = requests.post(
            f"{UPSTASH_REDIS_URL}/pipeline",
            headers=headers,
            json=redis_pipeline
        )

        if redis_response.status_code != 200:
            print(f"Redis Error: {redis_response.status_code}, {redis_response.text}")
            return jsonify({"error": "Failed to store encrypted data in Redis"}), 500

        # Generate shareable link
        share_link = f"{DOMAIN}/decode/{file_id}"

        return jsonify({"file_id": file_id, "ttl": ttl, "reads": reads, "share_link": share_link}), 201

    except Exception as e:
        print(f"Encode Error: {e}")
        return jsonify({"error": "An error occurred during encoding"}), 500
"""