#!/usr/bin/env python3
"""
WSGI Entry Point for Fire Safety NOC System
This file serves as the WSGI entry point for deployment platforms like Render.
"""

import sys
import os

# Add the fire directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
fire_dir = os.path.join(current_dir, 'fire')
sys.path.insert(0, fire_dir)

# Import the Flask app from the fire directory
try:
    from app import app
    print("✅ Successfully imported Flask app from fire directory")
except ImportError as e:
    print(f"❌ Error importing Flask app: {e}")
    raise

# This is what Gunicorn will look for
application = app

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
