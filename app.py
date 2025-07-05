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
from fire.app import app

# Add root level service worker route
@app.route('/service-worker.js')
def root_service_worker():
    """Serve service worker from root level"""
    from flask import send_from_directory, make_response
    import os
    try:
        # Try to serve from root directory
        return send_from_directory('.', 'service-worker.js')
    except:
        # Fallback service worker
        sw_content = '''// Fire Shakti PWA Service Worker
const CACHE_NAME = 'fire-shakti-v1';
self.addEventListener('install', function(event) {
  console.log('🔥 Fire Shakti Service Worker installing...');
  self.skipWaiting();
});
self.addEventListener('activate', function(event) {
  console.log('✅ Fire Shakti Service Worker activating...');
  event.waitUntil(self.clients.claim());
});
self.addEventListener('fetch', function(event) {
  event.respondWith(fetch(event.request));
});
console.log('🔥 Fire Shakti Service Worker loaded!');'''
        response = make_response(sw_content)
        response.headers['Content-Type'] = 'application/javascript'
        response.headers['Cache-Control'] = 'no-cache'
        return response

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(host='0.0.0.0', port=port, debug=False)
