from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from api.encode import encode_bp
from api.decode import decode_bp
from api.posts import posts_bp
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Set 16MB max file size for uploads

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}}, methods=["GET", "POST", "DELETE"])

# Register blueprints
app.register_blueprint(encode_bp, url_prefix="/api/encode")
app.register_blueprint(decode_bp, url_prefix="/api/decode")
app.register_blueprint(posts_bp, url_prefix="/api/posts")

# Export Flask app as "app" for Vercel compatibility
app = app

# Health check route
@app.route("/")
def health_check():
    return {"status": "running"}, 200

# Debugging routes locally
if __name__ == "__main__":
    with app.test_request_context():
        print("\nRegistered Routes:")
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint} -> {rule.rule}")
    
    # Run Flask app locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
