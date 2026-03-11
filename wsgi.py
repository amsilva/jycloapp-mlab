"""
WSGI entry point for PythonAnywhere deployment.

FastAPI is ASGI-based. PythonAnywhere uses WSGI. We use a2wsgi to bridge them.
"""
import sys
import os

project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables here directly
os.environ.setdefault('DATABASE_URL', 'sqlite:///./jycloapp.db')  # Override on server!
os.environ.setdefault('SECRET_KEY', 'change-me-on-server')        # Override on server!

from app.main import app
from a2wsgi import ASGIMiddleware

# This is what PythonAnywhere's WSGI server will call
application = ASGIMiddleware(app)

