"""
Test script to verify MongoDB Atlas connection
"""
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import json
import os

def test_connection():
    """Test MongoDB Atlas connection"""
    
    # Try connection string from config.json
    try:
        with open('config.json') as f:
            config = json.load(f)
            mongo_config = config.get('mongodb', {})
            connection_string = mongo_config.get('connection_string')
            
            if connection_string:
                print(f"Testing connection with: {connection_string[:50]}...")
                client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)
                
                # Test connection
                client.admin.command('ping')
                print("[OK] Connection successful!")
                
                # Get database
                db = client['college_events']
                print(f"[OK] Database 'college_events' accessible")
                
                # List collections
                collections = db.list_collection_names()
                print(f"[OK] Collections found: {collections}")
                
                client.close()
                return True
            else:
                print("[ERROR] No connection_string found in config.json")
                return False
                
    except FileNotFoundError:
        print("[ERROR] config.json not found")
        return False
    except ConnectionFailure as e:
        print(f"[ERROR] Connection failed: {e}")
        return False
    except ServerSelectionTimeoutError as e:
        print(f"[ERROR] Server selection timeout: {e}")
        print("  This usually means:")
        print("  1. IP address not whitelisted in MongoDB Atlas")
        print("  2. Incorrect credentials")
        print("  3. Network connectivity issues")
        print("  4. Connection string format is incorrect")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("MongoDB Atlas Connection Test")
    print("=" * 50)
    success = test_connection()
    sys.exit(0 if success else 1)

