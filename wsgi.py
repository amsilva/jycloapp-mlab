"""
WSGI entry point for PythonAnywhere deployment.

In the PythonAnywhere Web tab, set the WSGI file to point to this file.
Also set the source directory to: /home/<username>/jycloapp-mlab
"""
import sys
import os

# Ensure the project root is on the path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app.main import app as application
