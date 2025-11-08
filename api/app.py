"""
Main Flask application for Ciphare encryption service
"""
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize Flask app
flask_app = Flask(__name__)
flask_app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # Set 500MB max file size for uploads
flask_app.config['JSON_SORT_KEYS'] = False

# Enable CORS with more restrictive settings for production
cors_origins = os.getenv("CORS_ORIGINS", "*")
CORS(
    flask_app,
    resources={r"/api/*": {"origins": cors_origins.split(",") if cors_origins != "*" else "*"}},
    methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"]
)

# Register blueprints
try:
    from api.encode import encode_bp
    from api.decode import decode_bp
    from api.posts import posts_bp
    
    flask_app.register_blueprint(encode_bp, url_prefix="/api/encode")
    flask_app.register_blueprint(decode_bp, url_prefix="/api/decode")
    flask_app.register_blueprint(posts_bp, url_prefix="/api/posts")
except ImportError as e:
    logging.error(f"Failed to import blueprints: {e}")

# Health check route
@flask_app.route("/")
@flask_app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "running", "service": "ciphare"}), 200

# Error handlers
@flask_app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@flask_app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@flask_app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File too large. Maximum size is 500MB"}), 413

# Application entry point for Gunicorn
app = flask_app

if __name__ == "__main__":
    # Run Flask app locally
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "False") == "True")
