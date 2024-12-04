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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}}, methods=["GET", "POST", "DELETE"])

# Register blueprints
app.register_blueprint(encode_bp)
app.register_blueprint(decode_bp)
app.register_blueprint(posts_bp)

# Health check route
@app.route("/")
def health_check():
    return {"status": "running"}, 200

# Register routes
if __name__ == "__main__":
    with app.test_request_context():
        print("\nRegistered Routes:")
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint} -> {rule.rule}")

    # Start Flask app
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
