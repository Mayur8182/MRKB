#!/usr/bin/env python3
"""
WSGI Entry Point for Fire Safety NOC System
Optimized for Render deployment with Gunicorn + SocketIO
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app and SocketIO
from app import app, socketio

# Create WSGI application for Gunicorn
# Use SocketIO's WSGI app for proper eventlet compatibility
application = socketio.wsgi_app

# Ensure port binding
port = int(os.environ.get('PORT', 5000))
print(f"🚀 Fire Safety NOC System - WSGI mode")
print(f"🌐 Port: {port}")
print(f"🔧 Ready for Gunicorn with SocketIO support")

# For development mode
if __name__ == "__main__":
    host = os.environ.get('HOST', '0.0.0.0')
    print(f"🚀 Starting Fire Safety NOC System on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=False)
