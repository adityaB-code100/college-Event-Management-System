import json
from pymongo import MongoClient
from datetime import datetime

def init_mongodb():
    """Initialize MongoDB with sample data"""
    
    # Load configuration from config.json
    import os
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path) as f:
        config = json.load(f)
    
    # MongoDB configuration
    MONGO_CONFIG = config['mongodb']
    
    try:
        # Create MongoDB client
        if MONGO_CONFIG['username'] and MONGO_CONFIG['password']:
            client = MongoClient(
                host=MONGO_CONFIG['host'],
                port=MONGO_CONFIG['port'],
                username=MONGO_CONFIG['username'],
                password=MONGO_CONFIG['password']
            )
        else:
            client = MongoClient(
                host=MONGO_CONFIG['host'],
                port=MONGO_CONFIG['port']
            )
        
        db = client[MONGO_CONFIG['database']]
        print(f"Connected to MongoDB database: {MONGO_CONFIG['database']}")
        
        # Clear existing collections
        db.users.delete_many({})
        db.events.delete_many({})
        db.registrations.delete_many({})
        db.notifications.delete_many({})
        
        # Insert sample users
        users = [
            {
                "name": "Avantika",
                "email": "avantika@gmail.com",
                "password": "12345",
                "role": "student"
            },
            {
                "name": "Rutuja",
                "email": "rutujadeshmukh559@gmail.com",
                "password": "12345",
                "role": "student"
            },
            {
                "name": "Sonalika",
                "email": "rutujadeshmukh123123@gmail.com",
                "password": "123456",
                "role": "admin"
            },
            {
                "name": "Admin User",
                "email": "admin@gmail.com",
                "password": "admin123",
                "role": "admin"
            }
        ]
        
        user_ids = []
        for user in users:
            result = db.users.insert_one(user)
            user_ids.append(result.inserted_id)
            print(f"Inserted user: {user['name']} with ID: {result.inserted_id}")
        
        # Insert sample events
        events = [
            {
                "title": "TechFest 2025",
                "description": "A two-day inter-college technical festival with coding, robotics, and paper presentation competitions",
                "date": datetime(2025, 10, 15),
                "location": "College Main Auditorium",
                "created_by": str(user_ids[2])  # Sonalika (admin)
            },
            {
                "title": "Cultural Night",
                "description": "An evening of dance, drama, and music performances by students and guest artists.",
                "date": datetime(2025, 10, 20),
                "location": "Open Air Theatre",
                "created_by": str(user_ids[2])  # Sonalika (admin)
            },
            {
                "title": "Hackthon",
                "description": "24-hour coding hackathon to build innovative solutions to real-world problems",
                "date": datetime(2025, 11, 22),
                "location": "Innovation Center",
                "created_by": str(user_ids[2])  # Sonalika (admin)
            },
            {
                "title": "Blood Donation Camp",
                "description": "Organized with Red Cross Society to encourage students to donate blood.",
                "date": datetime(2025, 10, 2),
                "location": "College Health Center",
                "created_by": str(user_ids[2])  # Sonalika (admin)
            },
            {
                "title": "Entrepreneurship Talk",
                "description": "Guest lecture by a successful startup founder on building products and raising funds.",
                "date": datetime(2025, 11, 3),
                "location": "Seminar Hall 1",
                "created_by": str(user_ids[2])  # Sonalika (admin)
            }
        ]
        
        event_ids = []
        for event in events:
            result = db.events.insert_one(event)
            event_ids.append(result.inserted_id)
            print(f"Inserted event: {event['title']} with ID: {result.inserted_id}")
        
        # Insert sample registrations
        registrations = [
            {
                "event_id": event_ids[2],  # Hackthon
                "student_id": str(user_ids[1]),  # Rutuja
                "phone": "99222956971",
                "comments": "no",
                "status": "active",
                "registered_at": datetime.now()
            },
            {
                "event_id": event_ids[4],  # Entrepreneurship Talk
                "student_id": str(user_ids[1]),  # Rutuja
                "phone": "99222956971",
                "comments": "no",
                "status": "active",
                "registered_at": datetime.now()
            }
        ]
        
        for registration in registrations:
            result = db.registrations.insert_one(registration)
            print(f"Inserted registration with ID: {result.inserted_id}")
        
        print("\n✅ MongoDB initialization completed successfully!")
        print(f"📊 Inserted {len(users)} users, {len(events)} events, and {len(registrations)} registrations")
        
    except Exception as e:
        print(f"❌ Error initializing MongoDB: {e}")

if __name__ == "__main__":
    init_mongodb()