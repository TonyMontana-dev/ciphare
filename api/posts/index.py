"""
Vercel serverless function for posts API
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from serverless_wsgi import handle_request
from api.app import flask_app

def handler(request):
    """Vercel serverless function handler"""
    return handle_request(flask_app, request)

