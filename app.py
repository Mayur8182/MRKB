#!/usr/bin/env python3
"""
Fire Safety NOC System - Main Application Entry Point
This file serves as the main entry point for the Fire Safety NOC System.
It imports the Flask app from the fire subdirectory.
"""

import sys
import os

# Add the fire directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fire'))

# Import the Flask app from the fire directory
try:
    from fire.app import app
    print("✅ Successfully imported Flask app from fire directory")
except ImportError as e:
    print(f"❌ Error importing Flask app: {e}")
    # Fallback import
    import sys
    sys.path.insert(0, 'fire')
    from app import app

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(host='0.0.0.0', port=port, debug=False)
