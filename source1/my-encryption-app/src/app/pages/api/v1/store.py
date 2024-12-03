""""
This file is responsible for storing the encrypted data in the Redis cache and returning a shareable link to the user. 

The store_data function is a Flask route that accepts a POST request with a JSON payload containing the file data, password, reads, and TTL (time-to-live). 
It encrypts the file data using AES-256 encryption with a randomly generated salt, stores the encrypted data in the Redis cache, and returns a shareable link to the user. 
The shareable link contains the file ID, TTL, reads, and the domain name.

"""


from flask import Blueprint, request, jsonify
from ....utils import encrypt_aes256, generate_salt, generate_id
import base64
import os
import redis

# Create a Redis client
redis_client = redis.from_url(os.getenv("UPSTASH_REDIS_URL"), password=os.getenv("UPSTASH_REDIS_PASSWORD"))
# Create a Blueprint for the store functionality
store_bp = Blueprint("store", __name__)

# Define the route for storing the encrypted data in the Redis cache
@store_bp.route("/api/v1/store", methods=["POST"])
def store_data():
    data = request.json # Get the JSON payload from the request
    password = data["password"] # Extract the password from the JSON payload
    file_data = data["file_data"].encode() # Get the file data from the JSON payload
    reads = int(data.get("reads", 1)) # Remaining reads
    ttl = int(data.get("ttl", 86400))  # TTL in seconds

    # Encrypt and prepare data for storage
    salt = generate_salt()
    encrypted_data, iv, tag = encrypt_aes256(file_data, password, salt) # Encrypt the file data using AES-256 encryption
    file_id = generate_id() # Generate a unique file ID
    key = f"cipher_share:{file_id}" # Redis key for storing the encrypted data

    # Store encrypted data in Redis cache with TTL and remaining reads count using the function hset (hash set) to store multiple fields in a single key
    redis_client.hset(key, mapping={
        "encrypted_data": base64.urlsafe_b64encode(encrypted_data).decode(),
        "iv": base64.urlsafe_b64encode(iv).decode(),
        "tag": base64.urlsafe_b64encode(tag).decode(),
        "salt": base64.urlsafe_b64encode(salt).decode(),
        "reads": reads
    })
    if ttl > 0:
        redis_client.expire(key, ttl)  # Set the TTL for the key if greater than zero

    # Shareable link structure
    domain = os.getenv("DOMAIN", "http://localhost:5000") # For local testing
    share_link = f"{domain}/api/v1/decrypt/{file_id}"

    return jsonify({"file_id": file_id, "ttl": ttl, "reads": reads, "share_link": share_link}), 201
