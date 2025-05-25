#!/usr/bin/env python3
"""
Direct database update to fix manager role
"""

from pymongo import MongoClient
from datetime import datetime

def fix_manager_role():
    """Update mkbhh user role to manager directly in database"""

    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['aek_noc']  # Correct database name
        users = db['users']

        print("🔧 Fixing manager role in database...")
        print("📋 Checking database connection and users...")

        # List all databases
        databases = client.list_database_names()
        print(f"Available databases: {databases}")

        # List all collections in aek_noc
        if 'aek_noc' in databases:
            collections = db.list_collection_names()
            print(f"Collections in aek_noc: {collections}")

            # Count users
            user_count = users.count_documents({})
            print(f"Total users in database: {user_count}")

            # List all usernames
            all_users = list(users.find({}, {'username': 1, 'role': 1, '_id': 0}))
            print(f"All users: {all_users}")

            # Try to find user with different case or partial match
            user_variations = [
                users.find_one({'username': 'mkbhh'}),
                users.find_one({'username': 'MKBHH'}),
                users.find_one({'username': {'$regex': 'mkbhh', '$options': 'i'}}),
                users.find_one({'email': 'mayurbharvad734@gmail.com'})
            ]

            user = None
            for variation in user_variations:
                if variation:
                    user = variation
                    break

            if user:
                print(f"Found user: {user['username']}")
                print(f"Current role: {user.get('role', 'None')}")
                print(f"Email: {user.get('email', 'None')}")

                # Update role to manager
                result = users.update_one(
                    {'_id': user['_id']},
                    {'$set': {
                        'role': 'manager',
                        'updated_at': datetime.now(),
                        'department': 'Management',
                        'designation': 'Fire Safety Manager'
                    }}
                )

                if result.modified_count > 0:
                    print("✅ Successfully updated user role to manager!")

                    # Verify the update
                    updated_user = users.find_one({'_id': user['_id']})
                    print(f"Updated role: {updated_user.get('role')}")
                    print(f"Department: {updated_user.get('department')}")
                    print(f"Designation: {updated_user.get('designation')}")

                    print("\n🎉 Manager role fixed! Please refresh your browser and try accessing the manager dashboard.")
                    print("The 403 errors should now be resolved.")

                else:
                    print("❌ Failed to update user role")
            else:
                print("❌ No matching user found in database")
                print("Available users:", [u.get('username') for u in all_users])
        else:
            print("❌ Database 'aek_noc' not found")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure MongoDB is running and accessible")

if __name__ == "__main__":
    fix_manager_role()
