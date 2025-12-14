"""
Test script to verify the application components work correctly
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import get_db_connection
from datetime import datetime, timedelta

def test_database_connection():
    """Test database connection"""
    print("Testing database connection...")
    try:
        db = get_db_connection()
        if db is not None:
            print("✅ Database connection successful")
            
            # Test a simple query
            try:
                events_count = db.events.count_documents({})
                print(f"✅ Found {events_count} events in database")
                
                # Test the dashboard query logic
                today = datetime.now()
                next_month = today + timedelta(days=30)
                
                events_data = list(db.events.find({
                    "date": {"$gte": today, "$lte": next_month}
                }).sort("date", 1).limit(5))
                
                print(f"✅ Dashboard query successful, found {len(events_data)} upcoming events")
                return True
            except Exception as e:
                print(f"❌ Query test failed: {e}")
                return False
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        import flask
        import pymongo
        import json
        import datetime
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    print("Running application tests...\n")
    
    # Test imports
    imports_ok = test_imports()
    
    # Test database connection
    db_ok = test_database_connection()
    
    print("\n" + "="*50)
    if imports_ok and db_ok:
        print("🎉 All tests passed! The application is ready for deployment.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)