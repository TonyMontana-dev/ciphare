"""
This file is responsible for loading the encrypted data from the Redis cache, decrypting it, and returning it to the user.

The load_data function is a Flask route that accepts a POST request with a JSON payload containing the file_id and password. 
It retrieves the encrypted data from the Redis cache using the file_id as the key, decrypts it using the password, and returns the decrypted data to the user. 
It also decrements the remaining_reads counter in the Redis cache, or deletes the entry if the counter reaches zero.
The load_bp Blueprint is registered in the app.py file to define the route for this functionality.

"""

from flask import Blueprint, request, jsonify
from api.utils import decrypt_aes256
import base64
import os
import redis

# Create a Redis client
redis_client = redis.from_url(os.getenv("UPSTASH_REDIS_URL"), password=os.getenv("UPSTASH_REDIS_PASSWORD"))
# Create a Blueprint for the load functionality
load_bp = Blueprint("load", __name__)

# Define the route for loading the encrypted data from the Redis cache and decrypting it 
@load_bp.route("/api/load", methods=["POST"])
def load_data():
    data = request.json  # Get the JSON payload from the request
    file_id = data["file_id"]  # Extract the file_id and password from the payload
    password = data["password"]  # Extract the file_id and password from the payload

    # Retrieve encrypted data from Redis cache
    key = f"cipher_share:{file_id}"
    # Get the encrypted data, iv, tag, salt, and remaining_reads from the Redis cache
    result = redis_client.hgetall(key)
    if not result:
        return jsonify({"error": "File not found or expired"}), 404

    # Decrypt data
    encrypted_data = base64.urlsafe_b64decode(result[b"encrypted_data"])  # Decode the base64 encoded data
    iv = base64.urlsafe_b64decode(result[b"iv"])  # Decode the base64 encoded iv
    tag = base64.urlsafe_b64decode(result[b"tag"])  # Decode the base64 encoded tag
    salt = base64.urlsafe_b64decode(result[b"salt"])  # Decode the base64 encoded salt
    remaining_reads = int(result[b"reads"])  # Get the remaining_reads count

    # Decrement reads or delete if exhausted
    if remaining_reads > 0:
        redis_client.hincrby(key, "reads", -1)  # Decrement the remaining_reads count
    elif remaining_reads == 1:
        redis_client.delete(key)  # Delete the entry if the remaining_reads count is zero

    try:
        decrypted_data = decrypt_aes256(encrypted_data, password, salt, iv, tag).decode()  # Decrypt the data using the password and other parameters from Redis
    except Exception:
        return jsonify({"error": "Decryption failed"}), 400

    return jsonify({"decrypted_data": decrypted_data, "remaining_reads": max(remaining_reads - 1, 0)})  # Return the decrypted data and updated remaining_reads count
