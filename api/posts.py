"""
This python file contains the API endpoints for posts. It allows users to create, retrieve, like, and comment on posts.
The API endpoints interact with MongoDB to store and retrieve post data.
"""

from http.server import BaseHTTPRequestHandler
import logging
from flask import Blueprint, Request, Response, app, request, jsonify
from datetime import datetime, timedelta
import json
from api.utils import generate_id
from api.mongodb_client import get_db
from bson import ObjectId

# Create a Blueprint for posts API
posts_bp = Blueprint("posts", __name__, url_prefix="/api/posts")

# Get MongoDB database
db = get_db()

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

        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        post_data = {
            "title": title,
            "content": content,
            "author": author,
            "author_id": generate_id(),
            "likes": 0,
            "dislikes": 0,
            "created_at": datetime.utcnow(),
            "comments": [],
            "ttl": ttl,
            "expires_at": expires_at
        }

        try:
            # Drop the post_id index if it exists
            try:
                db.posts.drop_index("post_id_1")
            except:
                pass  # Index doesn't exist, which is fine

            result = db.posts.insert_one(post_data)
            if result.inserted_id:
                return jsonify({ 
                    "message": "Post created successfully", 
                    "post_id": str(result.inserted_id),
                    "expires_in_days": ttl // (24 * 3600) 
                }), 201
            return jsonify({"error": "Failed to create post"}), 500
        except Exception as e:
            logging.error(f"Error creating post: {str(e)}")
            return jsonify({"error": "Failed to create post"}), 500
    
    # Retrieve all posts if the request method is GET
    elif request.method == "GET": 
        try:
            # Get all posts that haven't expired
            current_time = datetime.utcnow()
            posts = list(db.posts.find({
                "expires_at": {"$gt": current_time}
            }).sort("likes", -1))

            # Convert ObjectId to string for JSON serialization
            for post in posts:
                post["_id"] = str(post["_id"])
                post["created_at"] = post["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                post["expires_at"] = post["expires_at"].strftime("%Y-%m-%d %H:%M:%S")
                # Calculate days until expiration
                expires_at = datetime.fromisoformat(post["expires_at"].replace("Z", "+00:00"))
                post["expires_in"] = max(0, (expires_at - current_time).days)

            return jsonify(posts), 200
        except Exception as e:
            logging.error(f"Error retrieving posts: {str(e)}")
            return jsonify({"error": "Failed to retrieve posts"}), 500

# Route to like a post
@posts_bp.route("/<post_id>/like", methods=["POST"])
def like_post(post_id):
    try:
        result = db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"likes": 1}}
        )
        if result.modified_count > 0:
            return jsonify({"message": "Post liked successfully"}), 200
        return jsonify({"error": "Post not found"}), 404
    except Exception as e:
        logging.error(f"Error liking post: {str(e)}")
        return jsonify({"error": "Failed to like post"}), 500

# Route to add a comment to a post
@posts_bp.route("/<post_id>/comments", methods=["POST"])
def add_comment(post_id):
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        content = data.get("content")
        author = data.get("author")
        ttl = data.get("ttl", 3600)  # Default to 1 hour if not specified

        # Debug logging
        logging.info(f"Received comment data: {data}")
        logging.info(f"TTL value: {ttl}, type: {type(ttl)}")

        if not content or not author:
            return jsonify({"error": "Content and author are required"}), 400

        # Convert TTL to integer with multiple checks
        try:
            # First convert to float to handle decimal strings
            ttl_float = float(ttl)
            logging.info(f"After float conversion: {ttl_float}, type: {type(ttl_float)}")
            
            # Then convert to int, rounding down
            ttl_int = int(ttl_float)
            logging.info(f"After int conversion: {ttl_int}, type: {type(ttl_int)}")
            
            if ttl_int <= 0:
                raise ValueError("TTL must be positive")
            ttl = ttl_int
        except (ValueError, TypeError) as e:
            logging.error(f"Invalid TTL value received: {ttl}, error: {str(e)}")
            return jsonify({"error": f"Invalid TTL value: {str(e)}"}), 400

        # Get post to check its expiration time
        try:
            post = db.posts.find_one({"_id": ObjectId(post_id)})
            if not post:
                return jsonify({"error": "Post not found"}), 404
        except Exception as e:
            logging.error(f"Error finding post: {str(e)}")
            return jsonify({"error": "Invalid post ID"}), 400

        # Calculate maximum allowed TTL for comment
        try:
            # Debug log the post data
            logging.info(f"Post data: {post}")
            logging.info(f"Post expires_at: {post['expires_at']}, type: {type(post['expires_at'])}")
            
            # Handle both string and datetime objects for expires_at
            if isinstance(post['expires_at'], str):
                post_expires_at = datetime.fromisoformat(post['expires_at'].replace('Z', '+00:00'))
            else:
                post_expires_at = post['expires_at']
            
            current_time = datetime.utcnow()
            logging.info(f"Current time: {current_time}")
            
            # Calculate max TTL in seconds
            max_ttl = int((post_expires_at - current_time).total_seconds())
            logging.info(f"Max TTL calculated: {max_ttl} seconds")
            
            if max_ttl <= 0:
                return jsonify({"error": "Post has already expired"}), 400
            
            # Enforce minimum TTL of 1 hour or remaining post time if less
            min_ttl = min(3600, max_ttl)
            logging.info(f"Min TTL: {min_ttl} seconds")
            
            # Ensure comment TTL doesn't exceed post expiration
            ttl = min(ttl, max_ttl)
            ttl = max(ttl, min_ttl)
            logging.info(f"Final adjusted TTL: {ttl} seconds")
            
        except Exception as e:
            logging.error(f"Error calculating TTL: {str(e)}")
            logging.error(f"Post data: {post}")
            return jsonify({"error": f"Error calculating comment TTL: {str(e)}"}), 500

        logging.info(f"Final TTL value: {ttl}, type: {type(ttl)}")

        comment_data = {
            "content": content,
            "author": author,
            "id": generate_id(),
            "ttl": ttl,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=ttl)
        }

        try:
            result = db.posts.update_one(
                {"_id": ObjectId(post_id)},
                {"$push": {"comments": comment_data}}
            )
            
            if result.modified_count > 0:
                return jsonify({"message": "Comment added successfully", "comment": comment_data}), 201
            return jsonify({"error": "Failed to add comment"}), 500
        except Exception as e:
            logging.error(f"Error updating post with comment: {str(e)}")
            return jsonify({"error": "Failed to save comment"}), 500

    except Exception as e:
        logging.error(f"Unexpected error in add_comment: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Route to update a post reaction
@posts_bp.route("/<post_id>/reaction", methods=["POST"])
def update_post_reaction(post_id):
    try:
        data = request.json
        reaction_type = data.get("type")  # "like" or "dislike"

        if not reaction_type or reaction_type not in ["like", "dislike"]:
            return jsonify({"error": "Invalid reaction type"}), 400

        # Update the appropriate counter
        update_field = "likes" if reaction_type == "like" else "dislikes"
        result = db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {update_field: 1}}
        )
        
        if result.modified_count > 0:
            return jsonify({"message": "Reaction updated successfully"}), 200
        return jsonify({"error": "Post not found"}), 404
    except Exception as e:
        logging.error(f"Error updating post reaction: {str(e)}")
        return jsonify({"error": str(e)}), 500

# A class to handle HTTP requests in a Vercel-compatible manner
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests."""
        # Prepare the environment for the Flask app
        env = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": self.path,
            "SERVER_PROTOCOL": self.request_version,
            "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
            "CONTENT_TYPE": self.headers.get("Content-Type"),
        }
        body = self.rfile.read(int(env["CONTENT_LENGTH"])) if env["CONTENT_LENGTH"] else None

        # Create a Flask Request object
        req = Request.from_values(
            path=env["PATH_INFO"],
            environ=env,
            input_stream=body,
        )

        # Route the request through Flask's WSGI app
        response = Response.force_type(app.full_dispatch_request(), req)

        # Respond to the client
        self.send_response(response.status_code)
        for key, value in response.headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(response.get_data())

    def do_POST(self):
        """Handle POST requests."""
        self.do_GET()

    def do_PUT(self):
        """Handle PUT requests."""
        self.do_GET()

    def do_PATCH(self):
        """Handle PATCH requests."""
        self.do_GET()

    def log_message(self, format, *args):
        """Log handler activity."""
        logging.debug(
            "%s - - [%s] %s\n"
            % (self.address_string(), self.log_date_time_string(), format % args)
        )

    def log_date_time_string(self):
        """Generate timestamp for logging."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
