"""
This python file contains the API endpoints for posts. It allows users to create, retrieve, like, and comment on posts.
The API endpoints are as follows:
1. POST /api/v1/posts - Create a new post
2. GET /api/v1/posts - Retrieve all posts
3. POST /api/v1/posts/<post_id>/like - Like a post
4. POST /api/v1/posts/<post_id>/comment - Add a comment to a post
5. DELETE /api/v1/posts/<post_id> - Delete a post
6. DELETE /api/v1/posts/<post_id>/comment/<comment_index> - Delete a comment from a post

The API endpoints interact with a Redis database to store and retrieve post data. The Redis database is hosted on Upstash. 
This file also contains helper functions to safely make requests to the Redis database to avoid SSRF vulnerabilities. 

"""


from flask import Blueprint, request, jsonify
from datetime import datetime
import json
from utils import generate_id
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import os
import requests

posts_bp = Blueprint("posts", __name__, url_prefix="/api/v1/posts")  # Create a Blueprint for posts API

# Load environment variables from .env file
load_dotenv() 

# Retrieve UPSTASH_REDIS_URL
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")  
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_PASSWORD")  
headers = {"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"}  


# Safe request helper function to avoid SSRF vulnerabilities
def safe_request(method, endpoint_path, headers=None, data=None):
    base_url = UPSTASH_REDIS_URL  # Base URL for the Redis database
    full_url = urljoin(base_url, endpoint_path)  # Construct the full URL
    parsed_url = urlparse(full_url)

    # Check if the path is in allowed paths to avoid SSRF vulnerabilities 
    if not any(parsed_url.path.startswith(path) for path in ["/hset/", "/hget/", "/hincrby/", "/del/", "/smembers/", "/expire/", "/keys/", "/hgetall/", "/pipeline"]):
        raise ValueError(f"Security Exception: Unsafe URL path detected: {parsed_url.path}")

    # Serialize data to JSON if provided 
    if data is not None:
        data = json.dumps(data)

    # Make the request
    if method == "get":
        return requests.get(full_url, headers=headers)  # SSRF detected here
    elif method == "post":
        return requests.post(full_url, headers=headers, data=data)  # SSRF detected here
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

# Route to create a new post
@posts_bp.route("", methods=["POST", "GET"])
def handle_posts():
    # Check if the request method is POST to create a new post or GET to retrieve all posts
    if request.method == "POST":
        data = request.json
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        author = data.get("author", "Anonymous").strip() 
        ttl = int(data.get("ttl", 90 * 24 * 60 * 60))  # Default to 3 months in seconds

        post_id = generate_id() # Generate a unique post ID
        key = f"post:{post_id}" # Define the key for Redis

        # Create a dictionary to store the post data 
        post_data = {
            "title": title,
            "content": content,
            "author": author,
            "likes": 0,
            "created_at": datetime.utcnow().isoformat(),
            "comments": []
        }

        # Pipeline to store the post data in Redis with an expiration time (TTL) 
        redis_pipeline = [
            ["hset", key, "title", title],
            ["hset", key, "content", content],
            ["hset", key, "author", author],
            ["hset", key, "likes", 0],
            ["hset", key, "created_at", post_data["created_at"]],
            ["hset", key, "comments", json.dumps([])],
            ["expire", key, ttl]
        ]

        # Make a safe request to store the post data in Redis using a pipeline to ensure atomicity
        try:
            response = safe_request("post", "/pipeline", headers=headers, data=redis_pipeline)
            if response.status_code == 200:
                return jsonify({"message": "Post created successfully", "post_id": post_id}), 201
        except ValueError as e:
            print(f"Security Exception: {e}")
            return jsonify({"error": "Failed to store post due to security constraints"}), 400
        
    # If the request method is GET, retrieve all posts
    elif request.method == "GET":
        try:
            response = safe_request("get", "/keys/post:*", headers=headers)
            if response.status_code != 200:
                return jsonify({"error": "Failed to retrieve posts"}), 500

            keys = response.json().get("result", [])
            posts = []

            for key in keys:
                post_data_response = safe_request("get", f"/hgetall/{key}", headers=headers)
                if post_data_response.status_code == 200:
                    raw_post_data = post_data_response.json().get("result", [])
                    if raw_post_data:
                        post_data = dict(zip(raw_post_data[::2], raw_post_data[1::2]))
                        post_data["_id"] = key.split(":")[1]
                        post_data["likes"] = int(post_data.get("likes", 0))
                        post_data["comments"] = json.loads(post_data.get("comments", "[]"))
                        post_data["created_at"] = post_data.get("created_at", "")
                        posts.append(post_data)

            posts = sorted(posts, key=lambda x: x["likes"], reverse=True)
            return jsonify(posts), 200
        except ValueError as e:
            print(f"Security Exception: {e}")
            return jsonify({"error": "Failed to retrieve posts due to security constraints"}), 400
        
# Route to like a post
@posts_bp.route("/<post_id>/like", methods=["POST"])
def like_post(post_id):
    key = f"post:{post_id}"  # Define the key for Redis
    try:
        response = safe_request("post", f"/hincrby/{key}/likes/1", headers=headers)  # Increment the likes count by 1 in Redis
        if response.status_code == 200:
            return jsonify({"message": "Post liked successfully"}), 200
    except ValueError as e:
        print(f"Security Exception: {e}")
        return jsonify({"error": "Failed to like post due to security constraints"}), 400

# Route to add a comment to a post
@posts_bp.route("/<post_id>/comment", methods=["POST"])
def add_comment(post_id):
    try:
        # Retrieve and sanitize input data
        data = request.json
        content = data.get("content", "").strip()  # Get the content of the comment
        author = data.get("author", "Anonymous").strip()  # Get the author of the comment

        if not content or not author:
            return jsonify({"error": "Author and content are required"}), 400

        # Define the key for Redis
        key = f"post:{post_id}"

        # Retrieve existing comments and ensure they are in list format
        response = safe_request("get", f"/hget/{key}/comments", headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve comments. Redis Error: {response.status_code}, {response.text}")
            return jsonify({"error": "Failed to retrieve comments"}), 500

        # Parse the existing comments or default to an empty list
        existing_comments = response.json().get("result", "[]")
        comments = json.loads(existing_comments)
        if not isinstance(comments, list):
            print(f"Unexpected data type for comments: {type(comments)}")
            comments = []  # Reset to empty list if not a list

        # Add the new comment
        new_comment = {"content": content, "author": author, "timestamp": datetime.utcnow().isoformat()}
        comments.append(new_comment)

        # Store updated comments back in Redis
        response = safe_request(
            "post",
            f"/hset/{key}/comments",
            headers=headers,
            data={"comments": json.dumps(comments)}  # Serialize comments to JSON string for storage in Redis hash field
        )

        if response.status_code == 200:
            return jsonify({"message": "Comment added successfully"}), 200
        else:
            print(f"Failed to add comment. Redis Error: {response.status_code}, {response.text}")
            return jsonify({"error": "Failed to add comment"}), 500

    except Exception as e:
        print(f"Error in adding comment: {e}")
        return jsonify({"error": "An error occurred while adding the comment"}), 500

# Route to delete a post
@posts_bp.route("/<post_id>", methods=["DELETE"])
def delete_post(post_id):
    key = f"post:{post_id}"  # Define the key for Redis
    response = safe_request("post", f"/del/{key}", headers=headers)  # Delete the post from Redis
    
    if response and response.status_code == 200:
        return jsonify({"message": "Post deleted successfully"}), 200
    else:
        print(f"Failed to delete post. Redis Error: {response.status_code}, {response.text}")
        return jsonify({"error": "Failed to delete post"}), 500
    
# Route to delete a comment from a post
@posts_bp.route("/<post_id>/comment/<int:comment_index>", methods=["DELETE"])
def delete_comment(post_id, comment_index):
    try:
        key = f"post:{post_id}"  # Define the key for Redis

        # Retrieve the existing comments
        response = safe_request("get", f"/hget/{key}/comments", headers=headers)  # Get the comments from Redis hash field

        if response.status_code != 200:
            print(f"Failed to retrieve comments. Redis Error: {response.status_code}, {response.text}")
            return jsonify({"error": "Failed to retrieve comments"}), 500

        # Parse comments and remove the specified comment
        comments = json.loads(response.json().get("result", "[]"))
        if 0 <= comment_index < len(comments):
            deleted_comment = comments.pop(comment_index)
            print(f"Deleted comment: {deleted_comment}")

            # Update the comments in Redis
            response = safe_request(
                "post",
                f"/hset/{key}/comments",
                headers=headers,
                data={"comments": json.dumps(comments)}
            )

            if response.status_code == 200:
                return jsonify({"message": "Comment deleted successfully"}), 200
            else:
                print(f"Failed to delete comment. Redis Error: {response.status_code}, {response.text}")
                return jsonify({"error": "Failed to delete comment"}), 500
        else:
            return jsonify({"error": "Comment index out of range"}), 404

    except Exception as e:
        print(f"Error in deleting comment: {e}")
        return jsonify({"error": "An error occurred while deleting the comment"}), 500
