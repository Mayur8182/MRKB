#!/usr/bin/env python3
"""
Startup script for Fire Safety NOC System
This script helps with initial setup and deployment verification
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Check if all required environment variables are set"""
    print("🔍 Checking environment configuration...")
    
    required_vars = [
        'DATABASE_URL',
        'MONGODB_URI', 
        'SECRET_KEY',
        'MAIL_USERNAME',
        'MAIL_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_database_connection():
    """Test MongoDB connection"""
    print("🗄️ Testing database connection...")
    
    try:
        from pymongo import MongoClient
        
        mongodb_uri = os.getenv('MONGODB_URI', os.getenv('DATABASE_URL'))
        db_name = os.getenv('DB_NAME', 'aek_noc')
        
        client = MongoClient(mongodb_uri)
        client.admin.command('ping')
        
        db = client[db_name]
        collections = db.list_collection_names()
        
        print(f"✅ Successfully connected to MongoDB Atlas")
        print(f"📊 Database: {db_name}")
        print(f"📁 Collections: {len(collections)} found")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def create_directories():
    """Create required directories"""
    print("📁 Creating required directories...")
    
    directories = [
        'static/profile_images',
        'static/certificates', 
        'static/reports',
        'static/inspection_photos',
        'uploads'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def main():
    """Main startup function"""
    print("🚀 Fire Safety NOC System - Startup Script")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed. Please configure environment variables.")
        sys.exit(1)
    
    # Test database connection
    if not test_database_connection():
        print("❌ Database connection failed. Please check your MongoDB Atlas configuration.")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    print("\n🎉 Startup checks completed successfully!")
    print("✅ Your Fire Safety NOC System is ready to run")
    print("\n📋 Next steps:")
    print("1. For local development: python app.py")
    print("2. For production: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app")
    print("3. Deploy to Render using the deployment guide")

if __name__ == '__main__':
    main()
