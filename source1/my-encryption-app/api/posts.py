"""
This python file contains the API endpoints for posts. It allows users to create, retrieve, like, and comment on posts.
The API endpoints interact with a Redis database to store and retrieve post data. The Redis database is hosted on Upstash.
"""

from http.server import BaseHTTPRequestHandler
import logging
from flask import Blueprint, Request, Response, app, request, jsonify
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

# Redis configurations
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_PASSWORD")
HEADERS = {"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"}

# Safe request helper function
# Safe request helper function
def safe_request(method, endpoint_path, headers=None, data=None):
    base_url = UPSTASH_REDIS_URL
    full_url = urljoin(base_url, endpoint_path)
    parsed_url = urlparse(full_url)

    # Allowed paths for Redis operations
    allowed_paths = ["/hset/", "/hget/", "/hincrby/", "/del/", "/keys/", "/hgetall/", "/pipeline", "/ttl/"]  # Added /ttl/
    if not any(parsed_url.path.startswith(path) for path in allowed_paths):
        raise ValueError(f"Security Exception: Unsafe URL path detected: {parsed_url.path}")

    # Serialize data if provided
    if data is not None:
        data = json.dumps(data)

    # Make the request
    if method == "get":
        return requests.get(full_url, headers=HEADERS)
    elif method == "post":
        return requests.post(full_url, headers=HEADERS, data=data)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")


# Route to handle posts (create and retrieve)
@posts_bp.route("", methods=["POST", "GET"])
def handle_posts():
    if request.method == "POST":
        # Create a new post
        data = request.json
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        author = data.get("author", "Anonymous").strip()
        ttl = int(data.get("ttl", 90 * 24 * 60 * 60))  # Default to 90 days in seconds

        post_id = generate_id()
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
        }

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

        response = safe_request("post", "/pipeline", headers=HEADERS, data=redis_pipeline)
        if response.status_code == 200:
            return jsonify({
                "message": "Post created successfully",
                "post_id": post_id,
                "expires_in_days": ttl // (24 * 3600)
            }), 201
        return jsonify({"error": "Failed to create post"}), 500

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
    key = f"post:{post_id}"
    response = safe_request("post", f"/hincrby/{key}/likes/1", headers=HEADERS)
    if response.status_code == 200:
        return jsonify({"message": "Post liked successfully"}), 200
    return jsonify({"error": "Failed to like post"}), 500

# Route to delete a post
@posts_bp.route("/<post_id>", methods=["DELETE"])
def delete_post(post_id):
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
    key = f"post:{post_id}"
    response = safe_request("get", f"/hget/{key}/comments", headers=HEADERS)

    if response.status_code == 200:
        comments = json.loads(response.json().get("result", "[]"))
        return jsonify(comments), 200

    return jsonify({"error": "Failed to retrieve comments"}), 500

# Route to add a comment to a post
@posts_bp.route("/<post_id>/comment", methods=["POST"])
def add_comment(post_id):
    try:
        data = request.json
        content = data.get("content", "").strip()
        author = data.get("author", "Anonymous").strip()

        if not content or not author:
            return jsonify({"error": "Author and content are required"}), 400

        key = f"post:{post_id}"
        response = safe_request("get", f"/hget/{key}/comments", headers=HEADERS)

        if response.status_code != 200:
            return jsonify({"error": "Failed to retrieve comments"}), 500

        comments = json.loads(response.json().get("result", "[]"))
        if not isinstance(comments, list):
            comments = []

        new_comment = {
            "content": content,
            "author": author,
            "author_id": generate_id(),
            "timestamp": datetime.utcnow().isoformat(),
        }
        comments.append(new_comment)

        response = safe_request(
            "post",
            f"/hset/{key}/comments",
            headers=HEADERS,
            data={"comments": json.dumps(comments)},
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to add comment"}), 500

        return jsonify({"message": "Comment added successfully", "comments": comments}), 200

    except Exception as e:
        logging.error(f"Error in add_comment: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Route to delete a comment from a post
@posts_bp.route("/<post_id>/comment/<comment_id>", methods=["DELETE"])
def delete_comment(post_id, comment_id):
    key = f"post:{post_id}"
    response = safe_request("get", f"/hget/{key}/comments", headers=HEADERS)

    if response.status_code != 200:
        return jsonify({"error": "Failed to retrieve comments"}), 500

    comments = json.loads(response.json().get("result", "[]"))
    if not isinstance(comments, list):
        comments = []

    for comment in comments:
        if comment.get("author_id") == comment_id:
            comments.remove(comment)
            break

    response = safe_request(
        "post",
        f"/hset/{key}/comments",
        headers=HEADERS,
        data={"comments": json.dumps(comments)},
    )

    if response.status_code != 200:
        return jsonify({"error": "Failed to delete comment"}), 500

    return jsonify({"message": "Comment deleted successfully", "comments": comments}), 200


# A class to handle HTTP requests in a Vercel-compatible manner
class handler(BaseHTTPRequestHandler):
    def handle_request(self):
        try:
            # Build the environment for the request
            env = {
                "REQUEST_METHOD": self.command,
                "PATH_INFO": self.path,
                "SERVER_PROTOCOL": self.request_version,
                "CONTENT_LENGTH": self.headers.get('Content-Length'),
                "CONTENT_TYPE": self.headers.get('Content-Type'),
            }
            
            # Read the request body if it exists
            body = self.rfile.read(int(env["CONTENT_LENGTH"]) if env["CONTENT_LENGTH"] else 0)
            
            # Create a Werkzeug request object
            req = Request.from_values(
                path=self.path,
                environ=env,
                input_stream=body,
            )
            
            # Let Flask handle the request
            response = Response.force_type(app.full_dispatch_request(), req)
            
            # Send the response
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.get_data())
        except Exception as e:
            logging.error(f"Error handling request: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Internal Server Error")

    # Map HTTP methods to `handle_request` to prevent recursion
    def do_GET(self): self.handle_request()
    def do_POST(self): self.handle_request()
    def do_PUT(self): self.handle_request()
    def do_PATCH(self): self.handle_request()
    def do_DELETE(self): self.handle_request()
    def do_OPTIONS(self): self.handle_request()

    # Logging helpers for debugging
    def log_message(self, format, *args):
        logging.debug("%s - - [%s] %s\n" % 
                      (self.address_string(), 
                       self.log_date_time_string(), 
                       format % args))

    def log_error(self, format, *args):
        logging.error("%s - - [%s] %s\n" % 
                      (self.address_string(), 
                       self.log_date_time_string(), 
                       format % args))

    def log_date_time_string(self):
        return datetime.now().isoformat()
