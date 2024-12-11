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
flask_app = Flask(__name__)
flask_app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Set 16MB max file size for uploads

# Enable CORS
CORS(flask_app, resources={r"/api/*": {"origins": "*"}}, methods=["GET", "POST", "DELETE"])

# Register blueprints
flask_app.register_blueprint(encode_bp, url_prefix="/api/encode")
flask_app.register_blueprint(decode_bp, url_prefix="/api/decode")
flask_app.register_blueprint(posts_bp, url_prefix="/api/posts")

# Health check route
@flask_app.route("/")
def health_check():
    return {"status": "running"}, 200

# Handler for Vercel compatibility
from werkzeug.wrappers import Request, Response
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        response = flask_app.full_dispatch_request()
        self.send_response(response.status_code)
        for key, value in response.headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(response.get_data())

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
        response = Response.force_type(flask_app.full_dispatch_request(), req)
        self.send_response(response.status_code)
        for key, value in response.headers.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(response.get_data())

if __name__ == "__main__":
    # Run Flask app locally
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="127.0.0.1", port=port)
