"""
This python file contains the API endpoints for posts. It allows users to create, retrieve, like, and comment on posts.
The API endpoints interact with a Redis database to store and retrieve post data. The Redis database is hosted on Upstash.
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
from api.utils import generate_id
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import os
import requests

# Create a Blueprint for posts API
posts_bp = Blueprint("posts", __name__, url_prefix="/api/posts")

# Load environment variables
load_dotenv()

# Redis configurations (optional - only needed for community posts feature)
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_PASSWORD")

# Make Redis optional - posts feature will fail gracefully if not configured
if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
    logging.warning("Redis not configured - community posts feature will be unavailable")
    UPSTASH_REDIS_URL = None
    UPSTASH_REDIS_TOKEN = None
    HEADERS = None
else:
    HEADERS = {"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"}

# Safe request helper function
def safe_request(method, endpoint_path, headers=None, data=None):
    if not UPSTASH_REDIS_URL:
        raise ValueError("Redis not configured. Community posts feature requires UPSTASH_REDIS_URL and UPSTASH_REDIS_PASSWORD.")
    
    base_url = UPSTASH_REDIS_URL
    full_url = urljoin(base_url, endpoint_path)
    parsed_url = urlparse(full_url)

    # Allowed paths for Redis operations
    allowed_paths = ["/hset/", "/hget/", "/hincrby/", "/del/", "/keys/", "/hgetall/", "/pipeline", "/ttl/", "/expire/"]  # Added /expire/ for TTL preservation
    if not any(parsed_url.path.startswith(path) for path in allowed_paths):
        raise ValueError(f"Security Exception: Unsafe URL path detected: {parsed_url.path}")

    # Serialize data if provided
    if data is not None:
        data = json.dumps(data)

    # Make the request with timeout for security
    timeout = 10  # 10 second timeout
    if not HEADERS:
        raise ValueError("Redis not configured. Community posts feature requires Redis credentials.")
    
    if method == "get":
        return requests.get(full_url, headers=HEADERS, timeout=timeout)
    elif method == "post":
        return requests.post(full_url, headers=HEADERS, data=data, timeout=timeout)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")


# Route to handle posts (create and retrieve)
@posts_bp.route("", methods=["POST", "GET"])
def handle_posts():
    if not UPSTASH_REDIS_URL or not HEADERS:
        return jsonify({"error": "Community posts feature requires Redis configuration. Set UPSTASH_REDIS_URL and UPSTASH_REDIS_PASSWORD."}), 503
    if request.method == "POST":
        # Create a new post
        data = request.json
        if not data:
            return jsonify({"error": "Request body is required"}), 400
            
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        author = data.get("author", "Anonymous").strip()
        ttl = data.get("ttl")
        
        # Validate required fields
        if not title:
            return jsonify({"error": "Title is required"}), 400
        if not content:
            return jsonify({"error": "Content is required"}), 400
        
        # Validate TTL
        if ttl is None:
            return jsonify({"error": "TTL is required"}), 400
        
        try:
            ttl = int(ttl)
        except (ValueError, TypeError):
            return jsonify({"error": "TTL must be a valid number"}), 400
        
        # Validate TTL range (1-90 days in seconds)
        min_ttl_seconds = 1 * 24 * 60 * 60  # 1 day
        max_ttl_seconds = 90 * 24 * 60 * 60  # 90 days
        
        if ttl < min_ttl_seconds or ttl > max_ttl_seconds:
            return jsonify({"error": "TTL must be between 1 and 90 days"}), 400

        post_id = generate_id() # Generate a unique post ID
        key = f"post:{post_id}"
        created_at = datetime.utcnow()
        post_data = {
            "title": title,
            "content": content,
            "author": author,
            "author_id": generate_id(),
            "likes": 0,
            "created_at": created_at.isoformat(),
            "comments": json.dumps([]),  # Initialize with empty comments
        } # Post data to store in Redis

        # Redis pipeline for atomic operations
        redis_pipeline = [
            ["hset", key, "title", title],
            ["hset", key, "content", content],
            ["hset", key, "author", author],
            ["hset", key, "author_id", post_data["author_id"]],
            ["hset", key, "likes", 0],
            ["hset", key, "created_at", post_data["created_at"]],
            ["hset", key, "comments", post_data["comments"]],
            ["expire", key, ttl]
        ]

        # Make a request to Redis to create the post
        response = safe_request("post", "/pipeline", headers=HEADERS, data=redis_pipeline)
        if response.status_code == 200: 
            return jsonify({ 
                "message": "Post created successfully", 
                "post_id": post_id, 
                "expires_in_days": ttl // (24 * 3600) 
            }), 201
        return jsonify({"error": "Failed to create post"}), 500 
    
    # Retrieve all posts if the request method is GET
    elif request.method == "GET": 
        # Retrieve all posts
        response = safe_request("get", "/keys/post:*", headers=HEADERS)
        if response.status_code != 200:
            return jsonify({"error": "Failed to retrieve posts"}), 500 

        keys = response.json().get("result", [])
        posts = []

        for key in keys:
            post_response = safe_request("get", f"/hgetall/{key}", headers=HEADERS)
            if post_response.status_code == 200:
                raw_post_data = post_response.json().get("result", [])
                post_data = dict(zip(raw_post_data[::2], raw_post_data[1::2]))
                post_data["_id"] = key.split(":")[1]
                post_data["likes"] = int(post_data.get("likes", 0))
                post_data["comments"] = json.loads(post_data.get("comments", "[]"))
                if "created_at" in post_data:
                    post_data["created_at"] = datetime.fromisoformat(post_data["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    post_data["created_at"] = "Unknown"


                # Calculate expiration
                ttl_response = safe_request("get", f"/ttl/{key}", headers=HEADERS)
                if ttl_response.status_code == 200:
                    ttl_seconds = ttl_response.json().get("result", 0)
                    post_data["expires_in"] = max(ttl_seconds // (24 * 3600), 0)  # Convert TTL to days
                posts.append(post_data)

        return jsonify(sorted(posts, key=lambda x: x["likes"], reverse=True)), 200

# Route to like a post
@posts_bp.route("/<post_id>/like", methods=["POST"])
def like_post(post_id):
    if not UPSTASH_REDIS_URL or not HEADERS:
        return jsonify({"error": "Community posts feature requires Redis configuration."}), 503
    key = f"post:{post_id}"
    
    # Get current TTL before liking to preserve expiration
    ttl_response = safe_request("get", f"/ttl/{key}", headers=HEADERS)
    current_ttl = -1
    if ttl_response.status_code == 200:
        current_ttl = ttl_response.json().get("result", -1)
    
    # Increment likes
    response = safe_request("post", f"/hincrby/{key}/likes/1", headers=HEADERS)
    if response.status_code == 200:
        # Restore TTL if it was valid (preserve expiration time)
        if current_ttl > 0:
            # Use EXPIRE to restore the original TTL
            expire_response = safe_request("post", f"/expire/{key}/{current_ttl}", headers=HEADERS)
            if expire_response.status_code != 200:
                logging.warning(f"Failed to restore TTL for post {post_id} after like")
        return jsonify({"message": "Post liked successfully"}), 200
    return jsonify({"error": "Failed to like post"}), 500

# Route to delete a post
@posts_bp.route("/<post_id>", methods=["DELETE"])
def delete_post(post_id):
    if not UPSTASH_REDIS_URL or not HEADERS:
        return jsonify({"error": "Community posts feature requires Redis configuration."}), 503
    key = f"post:{post_id}"  # Define the key for Redis
    logging.debug(f"Attempting to delete Redis key: {key}")
    
    # Verify if the post exists before attempting to delete
    response = safe_request("get", f"/keys/{key}", headers=HEADERS)
    if response.status_code != 200 or not response.json().get("result", []):
        logging.error(f"Post not found or already deleted: {key}")
        return jsonify({"error": "Post not found or already deleted"}), 404
    
    # Proceed with deletion
    response = safe_request("post", f"/del/{key}", headers=HEADERS)  # Delete the post from Redis
    if response.status_code == 200:
        logging.debug(f"Post deleted successfully: {key}")
        return jsonify({"message": "Post deleted successfully"}), 200
    else:
        logging.error(f"Failed to delete post. Redis Error: {response.status_code}, {response.text}")
        return jsonify({"error": "Failed to delete post"}), 500

# Route to retrieve comments for a post
@posts_bp.route("/<post_id>/comments", methods=["GET"])
def get_comments(post_id):
    if not UPSTASH_REDIS_URL or not HEADERS:
        return jsonify({"error": "Community posts feature requires Redis configuration."}), 503
    key = f"post:{post_id}"
    response = safe_request("get", f"/hget/{key}/comments", headers=HEADERS)

    if response.status_code == 200:
        # Handle None result from Redis
        result = response.json().get("result")
        if result is None:
            comments = []
        else:
            try:
                comments = json.loads(result) if isinstance(result, str) else result
            except (json.JSONDecodeError, TypeError):
                comments = []
        if not isinstance(comments, list):
            comments = []
        return jsonify(comments), 200

    return jsonify({"error": "Failed to retrieve comments"}), 500

# Route to add a comment to a post
@posts_bp.route("/<post_id>/comment", methods=["POST"])
def add_comment(post_id):
    if not UPSTASH_REDIS_URL or not HEADERS:
        return jsonify({"error": "Community posts feature requires Redis configuration."}), 503
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body is required"}), 400
            
        content = data.get("content", "").strip()
        author = data.get("author", "Anonymous").strip()
        ttl = data.get("ttl")

        if not content:
            return jsonify({"error": "Comment content is required"}), 400
        
        # Validate TTL
        if ttl is None:
            return jsonify({"error": "TTL is required for comments"}), 400
        
        try:
            ttl = int(ttl)
        except (ValueError, TypeError):
            return jsonify({"error": "TTL must be a valid number"}), 400
        
        # Validate TTL range (1-90 days in seconds)
        min_ttl_seconds = 1 * 24 * 60 * 60  # 1 day
        max_ttl_seconds = 90 * 24 * 60 * 60  # 90 days
        
        if ttl < min_ttl_seconds or ttl > max_ttl_seconds:
            return jsonify({"error": "TTL must be between 1 and 90 days"}), 400

        key = f"post:{post_id}"
        
        # Verify post exists
        post_check = safe_request("get", f"/hgetall/{key}", headers=HEADERS)
        if post_check.status_code != 200:
            return jsonify({"error": "Post not found"}), 404
        
        # Get existing comments
        response = safe_request("get", f"/hget/{key}/comments", headers=HEADERS)
        if response.status_code != 200:
            return jsonify({"error": "Failed to retrieve comments"}), 500

        # Handle None result from Redis
        result = response.json().get("result")
        if result is None:
            comments = []
        else:
            try:
                comments = json.loads(result) if isinstance(result, str) else result
            except (json.JSONDecodeError, TypeError):
                comments = []
        
        if not isinstance(comments, list):
            comments = []

        # Calculate expiration date for the comment
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        expires_in_days = ttl // (24 * 60 * 60)
        
        new_comment = {
            "content": content,
            "author": author,
            "author_id": generate_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "expires_in": expires_in_days,
        }
        comments.append(new_comment)

        # Update comments in Redis using hset
        # Upstash REST API format: POST /hset/{key}/{field} with value in request body
        comments_json = json.dumps(comments)
        response = safe_request(
            "post",
            f"/hset/{key}/comments",
            headers=HEADERS,
            data=comments_json,
        )

        if response.status_code != 200:
            logging.error(f"Failed to update comments in Redis: {response.status_code}, {response.text}")
            return jsonify({"error": "Failed to add comment"}), 500

        return jsonify({"message": "Comment added successfully", "comments": comments}), 200

    except ValueError as e:
        logging.error(f"Validation error in add_comment: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.error(f"Error in add_comment: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to add comment: {str(e)}"}), 500

# Route to delete a comment from a post
@posts_bp.route("/<post_id>/comment/<comment_id>", methods=["DELETE"])
def delete_comment(post_id, comment_id):
    if not UPSTASH_REDIS_URL or not HEADERS:
        return jsonify({"error": "Community posts feature requires Redis configuration."}), 503
    key = f"post:{post_id}"
    response = safe_request("get", f"/hget/{key}/comments", headers=HEADERS)

    if response.status_code != 200:
        return jsonify({"error": "Failed to retrieve comments"}), 500

    # Handle None result from Redis
    result = response.json().get("result")
    if result is None:
        comments = []
    else:
        try:
            comments = json.loads(result) if isinstance(result, str) else result
        except (json.JSONDecodeError, TypeError):
            comments = []
    if not isinstance(comments, list):
        comments = []

    for comment in comments:
        if comment.get("author_id") == comment_id:
            comments.remove(comment)
            break

    # Update comments in Redis
    comments_json = json.dumps(comments)
    response = safe_request(
        "post",
        f"/hset/{key}/comments",
        headers=HEADERS,
        data=comments_json,
    )

    if response.status_code != 200:
        return jsonify({"error": "Failed to delete comment"}), 500

    return jsonify({"message": "Comment deleted successfully", "comments": comments}), 200


# Note: Vercel serverless function handler is in api/posts/index.py
