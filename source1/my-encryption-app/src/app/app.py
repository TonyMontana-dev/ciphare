"""
This file is responsible for handling the encryption and decryption of data using AES-256 encryption with a randomly generated salt. 

It defines two Flask routes: one for storing and encrypting data, and another for retrieving and decrypting data. 
The encryption process involves generating a unique file ID, encrypting the file data using AES-256 encryption, and storing the encrypted data in the Redis cache.
The decryption process involves retrieving the encrypted data from the Redis cache using the file ID, decrypting it using the password, and returning the decrypted data to the user.
The file also includes functions for deriving an encryption key using Scrypt, encrypting and decrypting data using AES-256, and generating shareable links for the decrypted data.
The Flask app is configured to run on port 5000 with CORS enabled for all origins.

"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import base64
import os
import requests
from dotenv import load_dotenv
from utils import generate_id, generate_salt
from typing import Tuple
from pages.api.v1.posts import posts_bp


# Load environment variables
load_dotenv()
app = Flask(__name__)  # Create Flask app
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Set to 16MB or any size of choice

# Enable CORS for all routes and methods on /api/* paths only (for security)
CORS(app, resources={r"/api/*": {"origins": "*"}}, methods=["GET", "POST", "DELETE"])

# Register Blueprints
app.register_blueprint(posts_bp)

# Configuring Redis
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_PASSWORD")
# Set the authorization header for Upstash Redis
headers = {"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"}

# Constants for encryption
ENCRYPTION_KEY_LENGTH = 32  # For AES-256
DOMAIN = os.getenv("DOMAIN", "https://ciphare.vercel.app/")  # For generating shareable links

# Derive encryption key using Scrypt
def derive_key(password: str, salt: bytes) -> bytes:
    # Scrypt parameters: n=2^14, r=8, p=1 for 256-bit key length (32 bytes) with default backend (OpenSSL)
    kdf = Scrypt(salt=salt, length=ENCRYPTION_KEY_LENGTH, n=2**14, r=8, p=1, backend=default_backend())
    return kdf.derive(password.encode())

# AES-256 encryption function with GCM mode for authenticated encryption with associated data (AEAD) 
# using a randomly generated IV and tag for authentication and integrity protection
def encrypt_aes256(data: bytes, password: str, salt: bytes) -> Tuple[bytes, bytes, bytes]:
    key = derive_key(password, salt)
    iv = os.urandom(12)  # 12-byte IV for GCM mode
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(data) + encryptor.finalize()
    return encrypted_data, iv, encryptor.tag

# AES-256 decryption function with GCM mode for authenticated decryption with associated data (AEAD) using the provided tag and IV
def decrypt_aes256(encrypted_data: bytes, password: str, salt: bytes, iv: bytes, tag: bytes) -> bytes:
    key = derive_key(password, salt)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted_data) + decryptor.finalize()

# Store and encrypt data
@app.route("/api/v1/encode", methods=["POST"])
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

# Retrieve and decrypt data
@app.route("/api/v1/decode", methods=["POST"])
def decode_data():
    try:
        data = request.json
        file_id = data.get("file_id")
        password = data.get("password")

        # Check for required parameters
        if not file_id or not password:
            return jsonify({"error": "File ID and password are required"}), 400

        # Generate Redis key
        key = f"cipher_share:{file_id}"
        
        # Retrieve all fields from Redis
        response = requests.get(f"{UPSTASH_REDIS_URL}/hgetall/{key}", headers=headers)  # SSRF detected here
        print(f"Raw Redis response for key {key}: {response.json()}")

        if response.status_code != 200:
            return jsonify({"error": "File not found or expired"}), 404

        # Convert flat list to dictionary
        raw_result = response.json().get("result", [])
        result = dict(zip(raw_result[::2], raw_result[1::2]))  # Convert alternating list to a dictionary

        try:
            encrypted_data = base64.urlsafe_b64decode(result["encrypted_data"])
            iv = base64.urlsafe_b64decode(result["iv"])
            tag = base64.urlsafe_b64decode(result["tag"])
            salt = base64.urlsafe_b64decode(result["salt"])
            remaining_reads = int(result["reads"])
            file_name = result["file_name"]
            file_type = result["file_type"]
        except KeyError as e:
            print(f"Missing data in Redis response: {e}")
            return jsonify({"error": "Missing encrypted data, possibly expired"}), 404

        # Update reads or delete if exhausted
        if remaining_reads > 1:
            requests.post(f"{UPSTASH_REDIS_URL}/hincrby/{key}/reads/-1", headers=headers)  # SSRF detected here
        elif remaining_reads == 1:
            requests.post(f"{UPSTASH_REDIS_URL}/del/{key}", headers=headers)  # SSRF detected here

        # Decrypt the data
        try:
            decrypted_data = decrypt_aes256(encrypted_data, password, salt, iv, tag)
        except Exception as e:
            print(f"Decryption error: {e}")
            return jsonify({"error": "Decryption failed. Incorrect password or data corrupted."}), 400

        # Encode decrypted data as Base64 for transfer
        decrypted_base64 = base64.b64encode(decrypted_data).decode()

        # Return decrypted data, file name, file type, and updated remaining reads
        return jsonify({
            "decrypted_data": decrypted_base64,
            "file_name": file_name,
            "file_type": file_type,
            "remaining_reads": max(remaining_reads - 1, 0)
        })

    except Exception as e:
        print(f"Decode Error: {e}")
        return jsonify({"error": "An error occurred during decoding"}), 500

# Root route to prevent 404 errors
@app.route("/")
def root():
    return jsonify({"message": "Welcome to the Encryption API. Use /api/v1/encode or /api/v1/decode."}), 200

# Health checker route
@app.route("/api/healthchecker", methods=["GET"])
def healthchecker():
    return {"status": "success", "message": "Integrate Flask Framework with Next.js"}

if __name__ == "__main__":
    # Run using the environment-provided PORT or default to 5000
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
