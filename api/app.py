from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from api.mongodb_client import MongoDBClient
from api.encode import encode_bp
from api.decode import decode_bp
from api.posts import posts_bp
import os
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
flask_app = Flask(__name__)
flask_app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Set 16MB max file size for uploads

# Enable CORS with specific configuration
CORS(flask_app, 
     resources={r"/api/*": {"origins": ["http://localhost:3000", "https://ciphare.vercel.app"]}},
     methods=["GET", "POST", "DELETE"],
     supports_credentials=True)

# Initialize MongoDB client
try:
    mongodb_client = MongoDBClient()
    logger.info("MongoDB client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MongoDB client: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    mongodb_client = None

# Register blueprints
flask_app.register_blueprint(encode_bp, url_prefix="/api/encode")
flask_app.register_blueprint(decode_bp, url_prefix="/api/decode")
flask_app.register_blueprint(posts_bp, url_prefix="/api/posts")

# Test endpoint
@flask_app.route("/api/test", methods=["GET"])
def test_endpoint():
    try:
        logger.info("Test endpoint called")
        if mongodb_client is None:
            return jsonify({
                "status": "error",
                "message": "MongoDB connection not available"
            }), 500
        
        # Test MongoDB connection
        mongodb_client.client.server_info()
        return jsonify({
            "status": "ok",
            "message": "Backend server is running",
            "mongodb": "connected"
        }), 200
    except Exception as e:
        logger.error(f"Error in test endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Health check route
@flask_app.route("/")
def health_check():
    logger.info("Health check endpoint called")
    return {"status": "running"}, 200

# Log all requests
@flask_app.before_request
def log_request_info():
    logger.debug('Request URL: %s', request.url)
    logger.debug('Request Method: %s', request.method)
    logger.debug('Request Headers: %s', dict(request.headers))
    logger.debug('Request Body: %s', request.get_data())

# Log all responses
@flask_app.after_request
def log_response_info(response):
    logger.debug('Response Status: %s', response.status)
    logger.debug('Response Headers: %s', dict(response.headers))
    logger.debug('Response Body: %s', response.get_data())
    return response

# Error handler
@flask_app.errorhandler(Exception)
def handle_error(error):
    logger.error('Unhandled error: %s', str(error))
    logger.error('Traceback: %s', traceback.format_exc())
    return jsonify({
        "error": str(error),
        "message": "An unexpected error occurred"
    }), 500

if __name__ == "__main__":
    try:
        # Get port from environment variable or default to 5328
        port = int(os.environ.get("PORT", 5328))
        host = os.environ.get("HOST", "127.0.0.1")  # Changed to 127.0.0.1 for local development
        
        logger.info(f"Starting Flask server on {host}:{port}")
        logger.info(f"Environment variables loaded: {list(os.environ.keys())}")
        flask_app.run(host=host, port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
