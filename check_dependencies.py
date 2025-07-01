#!/usr/bin/env python

"""
Dependency checker script for Fire Safety NOC System
This script checks if all required dependencies are installed correctly.
"""

import importlib.util
import sys

def check_dependency(package_name):
    """Check if a package is installed and return its version."""
    try:
        spec = importlib.util.find_spec(package_name)
        if spec is None:
            return False, None
        
        # Try to get the version
        try:
            package = importlib.import_module(package_name)
            version = getattr(package, '__version__', 'Unknown')
            return True, version
        except (ImportError, AttributeError):
            return True, 'Unknown'
    except Exception as e:
        return False, str(e)

def main():
    """Main function to check dependencies."""
    print("\n🔍 Checking dependencies for Fire Safety NOC System...\n")
    print(f"Python version: {sys.version}\n")
    
    # List of core dependencies to check
    dependencies = [
        'flask', 'flask_mail', 'flask_wtf', 'flask_socketio', 'flask_cors',
        'bcrypt', 'werkzeug', 'pymongo', 'dnspython', 'PIL', 'cv2', 'pytesseract',
        'sklearn', 'numpy', 'dotenv', 'reportlab', 'qrcode', 'pdfkit',
        'requests', 'pandas', 'openpyxl', 'wtforms', 'dateutil', 'pytz',
        'jinja2', 'markupsafe', 'itsdangerous', 'click', 'blinker', 'six',
        'urllib3', 'certifi', 'charset_normalizer', 'idna'
    ]
    
    all_installed = True
    for dep in dependencies:
        installed, version = check_dependency(dep)
        status = "✅ Installed" if installed else "❌ Not installed"
        version_info = f"(version: {version})" if version and version != 'Unknown' else ""
        print(f"{dep}: {status} {version_info}")
        
        if not installed:
            all_installed = False
    
    print("\n" + "-" * 50)
    if all_installed:
        print("✅ All dependencies are installed!")
    else:
        print("⚠️ Some dependencies are missing. Please install them using pip.")
    print("-" * 50)

if __name__ == "__main__":
    main()