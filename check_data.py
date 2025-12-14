from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.college_events

print("=== REGISTRATIONS ===")
registrations = list(db.registrations.find())
print(f"Total registrations: {len(registrations)}")

for r in registrations:
    print(f"\nRegistration: {r}")
    event = db.events.find_one({'_id': r['event_id']})
    print(f"  Event: {event}")
    student = db.users.find_one({'_id': r['student_id']})
    print(f"  Student: {student}")

print("\n=== EVENTS ===")
events = list(db.events.find())
print(f"Total events: {len(events)}")
for e in events:
    print(f"Event: {e}")

print("\n=== USERS ===")
users = list(db.users.find())
print(f"Total users: {len(users)}")
for u in users:
    print(f"User: {u}")