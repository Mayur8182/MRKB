#!/usr/bin/env python3
"""
Simple WSGI Entry Point for Fire Safety NOC System
Optimized for Render deployment - Flask only (no SocketIO)
"""

import os
import sys

# Add the fire directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
fire_dir = os.path.join(current_dir, 'fire')
sys.path.insert(0, fire_dir)

# Import the Flask app from fire directory
try:
    from app import app
    print("✅ Successfully imported Flask app from fire directory")
except ImportError as e:
    print(f"❌ Error importing Flask app: {e}")
    # Try alternative import
    sys.path.insert(0, current_dir)
    try:
        from fire.app import app
        print("✅ Successfully imported Flask app using fire.app")
    except ImportError as e2:
        print(f"❌ Failed both import methods: {e2}")
        raise

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