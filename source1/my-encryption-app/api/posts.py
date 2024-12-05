"""
This python file contains the API endpoints for posts. It allows users to create, retrieve, like, and comment on posts.
The API endpoints are as follows:
1. POST /api/posts - Create a new post
2. GET /api/posts - Retrieve all posts
3. POST /api/posts/<post_id>/like - Like a post
4. POST /api/posts/<post_id>/comment - Add a comment to a post
5. DELETE /api/posts/<post_id> - Delete a post
6. DELETE /api/posts/<post_id>/comment/<comment_index> - Delete a comment from a post

The API endpoints interact with a Redis database to store and retrieve post data. The Redis database is hosted on Upstash. 
This file also contains helper functions to safely make requests to the Redis database to avoid SSRF vulnerabilities. 

"""


from flask import Flask, Blueprint, request, jsonify
from datetime import datetime
import json
from api.utils import generate_id
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
import os
import requests
from http.server import BaseHTTPRequestHandler
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Request, Response

posts_bp = Blueprint("posts", __name__, url_prefix="/api/posts")  # Create a Blueprint for posts API

# Load environment variables from .env file
load_dotenv() 

# Retrieve UPSTASH_REDIS_URL
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")  
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_PASSWORD")  
HEADERS = {"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"}

# Initialize Flask app
app = Flask(__name__)

# Safe request helper function to avoid SSRF vulnerabilities
# Helper function for safe Redis requests
def safe_request(method, endpoint_path, headers=None, data=None):
    base_url = UPSTASH_REDIS_URL
    full_url = urljoin(base_url, endpoint_path)
    parsed_url = urlparse(full_url)

    # Allowed paths to avoid SSRF vulnerabilities
    allowed_paths = ["/hset/", "/hget/", "/hincrby/", "/del/", "/smembers/", "/expire/", "/keys/", "/hgetall/", "/pipeline"]
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

@posts_bp.route("", methods=["POST", "GET"])
def handle_posts():
    # Check if the request method is POST to create a new post or GET to retrieve all posts
    if request.method == "POST":
        # Logic for creating a new post
        data = request.json
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        author = data.get("author", "Anonymous").strip()
        ttl = int(data.get("ttl", 90 * 24 * 60 * 60))  # Default to 3 months in seconds

        post_id = generate_id()
        key = f"post:{post_id}"
        post_data = {
            "title": title,
            "content": content,
            "author": author,
            "likes": 0,
            "created_at": datetime.utcnow().isoformat(),
            "comments": []
        }

        redis_pipeline = [
            ["hset", key, "title", title],
            ["hset", key, "content", content],
            ["hset", key, "author", author],
            ["hset", key, "likes", 0],
            ["hset", key, "created_at", post_data["created_at"]],
            ["hset", key, "comments", json.dumps([])],
            ["expire", key, ttl]
        ]

        response = safe_request("post", "/pipeline", headers=HEADERS, data=redis_pipeline)
        if response.status_code == 200:
            return jsonify({"message": "Post created successfully", "post_id": post_id}), 201
        return jsonify({"error": "Failed to create post"}), 500

    elif request.method == "GET":
        # Logic for retrieving all posts
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
                posts.append(post_data)

        return jsonify(sorted(posts, key=lambda x: x["likes"], reverse=True)), 200


@posts_bp.route("/<post_id>/like", methods=["POST"])
def like_post(post_id):
    key = f"post:{post_id}"
    response = safe_request("post", f"/hincrby/{key}/likes/1", headers=HEADERS)
    if response.status_code == 200:
        return jsonify({"message": "Post liked successfully"}), 200
    return jsonify({"error": "Failed to like post"}), 500

# Route to add a comment to a post
@posts_bp.route("/<post_id>/comment", methods=["POST"])
def add_comment(post_id):
    try:
        data = request.json
        content = data.get("content", "").strip()
        author = data.get("author", "Anonymous").strip()
        ttl = data.get("ttl", 90 * 24 * 60 * 60)  # Default to 90 days in seconds

        if not content or not author:
            return jsonify({"error": "Author and content are required"}), 400

        key = f"post:{post_id}"
        response = safe_request("get", f"/hget/{key}/comments", headers=HEADERS)

        if response.status_code != 200:
            return jsonify({"error": "Failed to retrieve comments"}), 500

        # Ensure comments are parsed as a list
        existing_comments = response.json().get("result", "[]")
        try:
            comments = json.loads(existing_comments)
            if not isinstance(comments, list):
                raise ValueError("Comments is not a list")
        except Exception:
            comments = []  # Reset to an empty list if parsing fails

        # Generate a unique ID for the comment's author
        author_id = generate_id()

        # Add the new comment
        new_comment = {
            "content": content,
            "author": author,
            "author_id": author_id,
            "timestamp": datetime.utcnow().isoformat(),
            "ttl": ttl,
        }
        comments.append(new_comment)

        # Update comments in Redis
        response = safe_request(
            "post", f"/hset/{key}/comments", headers=HEADERS, data={"comments": json.dumps(comments)}
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to add comment"}), 500

        # Fetch the updated post data
        post_response = safe_request("get", f"/hgetall/{key}", headers=HEADERS)
        if post_response.status_code != 200:
            return jsonify({"error": "Failed to retrieve updated post"}), 500

        raw_post_data = post_response.json().get("result", [])
        post_data = dict(zip(raw_post_data[::2], raw_post_data[1::2]))
        post_data["_id"] = key.split(":")[1]
        post_data["likes"] = int(post_data.get("likes", 0))
        post_data["comments"] = json.loads(post_data.get("comments", "[]"))
        post_data["created_at"] = post_data.get("created_at", "")

        return jsonify(post_data), 200  # Return the updated post

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to delete a post
@posts_bp.route("/<post_id>", methods=["DELETE"])
def delete_post(post_id):
    key = f"post:{post_id}"  # Define the key for Redis
    response = safe_request("post", f"/del/{key}", headers=HEADERS)  # Delete the post from Redis
    
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
        response = safe_request("get", f"/hget/{key}/comments", headers=HEADERS)  # Get the comments from Redis hash field

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
                headers=HEADERS,
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
    
# Define a handler for Vercel
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