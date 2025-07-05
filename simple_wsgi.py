#!/usr/bin/env python3
"""
Simple WSGI Entry Point for Fire Safety NOC System
Optimized for Render deployment - Flask only (no SocketIO)
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app only
from app import app

# Create simple WSGI application
application = app

# Ensure port binding
port = int(os.environ.get('PORT', 5000))
print(f"🚀 Fire Safety NOC System - Simple WSGI mode")
print(f"🌐 Port: {port}")
print(f"🔧 Ready for Gunicorn deployment")

# For development mode
if __name__ == "__main__":
    host = os.environ.get('HOST', '0.0.0.0')
    print(f"🚀 Starting Fire Safety NOC System on {host}:{port}")
    app.run(host=host, port=port, debug=False)