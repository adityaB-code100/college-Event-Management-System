import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
import logging
import secrets
from datetime import datetime, timedelta
import os

# Set up basic logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Configure CORS for API endpoints
# Allow requests from Vercel frontend and local development
frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
CORS(app, 
     origins=[frontend_url, 'http://localhost:3000', 'http://localhost:5173'],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Load configuration from config.json or environment variables

# Check if config.json exists
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
if os.path.exists(config_path):
    with open(config_path) as f:
        config = json.load(f)
        app.secret_key = config.get('secret_key', os.environ.get('SECRET_KEY', 'fallback-secret-key'))
        
        # MongoDB configuration from config.json
        MONGO_CONFIG = config.get('mongodb', {})
else:
    # Fallback to environment variables
    app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret-key')
    
    # MongoDB configuration from environment variables
    MONGO_CONFIG = {
        'host': os.environ.get('MONGODB_HOST', 'localhost'),
        'port': int(os.environ.get('MONGODB_PORT', 27017)),
        'database': os.environ.get('MONGODB_DATABASE', 'college_events'),
        'username': os.environ.get('MONGODB_USERNAME', ''),
        'password': os.environ.get('MONGODB_PASSWORD', '')
    }

# Global connection variable
_db_connection = None

def get_db_connection():
    """
    Establishes a connection to the MongoDB database.
    Returns the database object.
    """
    global _db_connection
    try:
        if _db_connection is None:
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
            
            _db_connection = client[MONGO_CONFIG['database']]
            logging.info("Connected to MongoDB database")
        
        return _db_connection
    except Exception as e:
        logging.error(f"Database Connection Error: {e}")
        flash("Could not connect to the database. Please check server status.", "danger")
        return None

# def get_db_connection():
#     """
#     Establishes a connection to MongoDB (supports both local and Atlas).
#     Returns the database object.
#     """
#     global _db_connection
#     try:
#         if _db_connection is None:
#             # Check for MongoDB Atlas connection string in environment variable (preferred)
#             mongo_uri = os.environ.get('MONGODB_URI')
            
#             if mongo_uri:
#                 # Use connection string from environment variable
#                 # Format: mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
#                 client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
#                 # Extract database name from URI or use default
#                 db_name = os.environ.get('MONGODB_DATABASE', 'college_events')
#                 _db_connection = client[db_name]
#                 logging.info("Connected to MongoDB Atlas using connection string")
#             else:
#                 # Check config.json for MongoDB Atlas connection string
#                 if 'connection_string' in MONGO_CONFIG:
#                     # Use connection string from config.json
#                     client = MongoClient(MONGO_CONFIG['connection_string'], serverSelectionTimeoutMS=5000)
#                     db_name = MONGO_CONFIG.get('database', 'college_events')
#                     _db_connection = client[db_name]
#                     logging.info("Connected to MongoDB Atlas using config.json connection string")
#                 else:
#                     # Fallback to individual connection parameters (local or Atlas)
#                     host = MONGO_CONFIG.get('host', 'localhost')
#                     port = MONGO_CONFIG.get('port', 27017)
#                     username = MONGO_CONFIG.get('username', '')
#                     password = MONGO_CONFIG.get('password', '')
#                     database = MONGO_CONFIG.get('database', 'college_events')
                    
#                     # Check if it's an Atlas host (contains .mongodb.net)
#                     if '.mongodb.net' in host:
#                         # MongoDB Atlas - use mongodb+srv:// protocol
#                         if username and password:
#                             connection_string = f"mongodb+srv://{username}:{password}@{host}/{database}?retryWrites=true&w=majority"
#                         else:
#                             connection_string = f"mongodb+srv://{host}/{database}?retryWrites=true&w=majority"
#                         client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
#                         _db_connection = client[database]
#                         logging.info("Connected to MongoDB Atlas using individual parameters")
#                     else:
#                         # Local MongoDB
#                         if username and password:
#                             client = MongoClient(
#                                 host=host,
#                                 port=port,
#                                 username=username,
#                                 password=password,
#                                 serverSelectionTimeoutMS=5000
#                             )
#                         else:
#                             client = MongoClient(
#                                 host=host,
#                                 port=port,
#                                 serverSelectionTimeoutMS=5000
#                             )
#                         _db_connection = client[database]
#                         logging.info(f"Connected to local MongoDB at {host}:{port}")
            
#             # Test the connection
#             _db_connection.client.admin.command('ping')
#             logging.info("Database connection verified successfully")
        
#         return _db_connection
#     except Exception as e:
#         logging.error(f"Database Connection Error: {e}")
#         _db_connection = None  # Reset connection on error
#         flash("Could not connect to the database. Please check server status.", "danger")
#         return None

# ==================== NOTIFICATION FUNCTIONS ====================

def create_notification(user_id, title, message, notif_type='info', related_url=None):
    """Create a new notification for a user"""
    db_conn = get_db_connection()
    if db_conn is None:
        return False
    
    try:
        # Convert user_id to ObjectId if it's a string
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except InvalidId:
                logging.error(f"Invalid user_id format: {user_id}")
                return False
        
        db_conn.notifications.insert_one({
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notif_type,
            "related_url": related_url,
            "is_read": False,
            "created_at": datetime.now()
        })
        return True
    except Exception as e:
        logging.error(f"Create notification error: {e}")
        return False

def get_user_notifications(user_id, limit=10, unread_only=False):
    """Get notifications for a user"""
    db_conn = get_db_connection()
    if db_conn is None:
        return []
    
    try:
        # Convert user_id to ObjectId if it's a string
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except InvalidId:
                logging.error(f"Invalid user_id format: {user_id}")
                return []
        
        query = {"user_id": user_id}
        if unread_only:
            query["is_read"] = False
        
        notifications = list(db_conn.notifications.find(query).sort("created_at", -1).limit(limit))
        return notifications
    except Exception as e:
        logging.error(f"Get notifications error: {e}")
        return []

def mark_notification_read(notification_id, user_id):
    """Mark a notification as read"""
    # Validate ObjectId
    try:
        ObjectId(notification_id)
    except InvalidId:
        return False
    
    db_conn = get_db_connection()
    if db_conn is None:
        return False
    
    try:
        # Convert user_id to ObjectId if it's a string
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except InvalidId:
                logging.error(f"Invalid user_id format: {user_id}")
                return False
        
        result = db_conn.notifications.update_one(
            {"_id": ObjectId(notification_id), "user_id": user_id},
            {"$set": {"is_read": True}}
        )
        return result.modified_count > 0
    except Exception as e:
        logging.error(f"Mark notification read error: {e}")
        return False

# ---------------- HOME -----------------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

# ---------------- LOGIN -----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("Enter both email and password!", "danger")
            return redirect(url_for('login'))

        db_conn = get_db_connection()
        if db_conn is None:
             flash("Database connection failed. Try again later.", "danger")
             return redirect(url_for('login'))

        try:
            user = db_conn.users.find_one({"email": email, "password": password})

            if user:
                session.clear()
                session['user_id'] = str(user['_id'])
                session['username'] = user['name']
                session['role'] = user['role']
                session['email'] = user.get('email')
                
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid email or password!", "danger")
        except Exception as e:
            logging.error(f"Login database query error: {e}")
            flash(f"An internal error occurred: {e}", "danger")

    return render_template('login.html')

# ---------------- DASHBOARD -----------------
from datetime import datetime, timedelta

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    username = session['username']
    role = session['role']
    
    # Get upcoming events (next 30 days)
    db_conn = get_db_connection()
    upcoming_events = []
    
    if db_conn is not None:
        try:
            # Calculate date range for upcoming events
            today = datetime.now()
            next_month = today + timedelta(days=30)
            
            events_data = list(db_conn.events.find({
                "date": {"$gte": today, "$lte": next_month}
            }).sort("date", 1).limit(5))
            
            # Calculate days remaining for each event
            today_date = today.date()
            for event in events_data:
                event_date = event['date']
                if isinstance(event_date, datetime):
                    event_date = event_date.date()
                elif isinstance(event_date, str):
                    event_date = datetime.strptime(event_date, '%Y-%m-%d').date()
                
                days_remaining = (event_date - today_date).days
                upcoming_events.append({
                    'id': str(event['_id']),
                    'title': event['title'],
                    'date': event['date'],
                    'location': event.get('location', 'TBA'),
                    'description': event.get('description', ''),
                    'days_remaining': days_remaining,
                    'is_today': days_remaining == 0,
                    'is_tomorrow': days_remaining == 1
                })
                
        except Exception as e:
            logging.error(f"Upcoming events query error: {e}")
    
    return render_template('dashboard.html', 
                         username=username, 
                         role=role, 
                         upcoming_events=upcoming_events)

# ---------------- LOGOUT -----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))

# ---------------- REGISTER -----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data with .get() method
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'student')
        
        # Debug print
        print(f"Registration attempt: name='{name}', email='{email}', role='{role}'")
        
        # Validate required fields
        if not name:
            flash("Full name is required!", "danger")
            return redirect(url_for('register'))
        
        if not email:
            flash("Email is required!", "danger")
            return redirect(url_for('register'))
            
        if not password:
            flash("Password is required!", "danger")
            return redirect(url_for('register'))
            
        if len(password) < 6:
            flash("Password must be at least 6 characters!", "danger")
            return redirect(url_for('register'))

        db_conn = get_db_connection()
        if db_conn is None:
             flash("Database connection failed. Try again later.", "danger")
             return redirect(url_for('register'))

        try:
            # Check if email already exists
            if db_conn.users.find_one({"email": email}):
                flash("Email already registered! Please use a different email.", "danger")
                return redirect(url_for('register'))
            
            db_conn.users.insert_one({
                "name": name,
                "email": email,
                "password": password,
                "role": role
            })
            flash("Registered successfully! Please login.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            logging.error(f"Registration database query error: {e}")
            flash(f"Error registering: {e}", "danger")

    return render_template('register.html')

# ---------------- ADD EVENT -----------------
# ---------------- ADD EVENT -----------------
@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied. Only administrators can add events.", "danger")
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        date = request.form.get('date', '').strip()
        hour = request.form.get('hour', '').strip()
        minute = request.form.get('minute', '').strip()
        ampm = request.form.get('ampm', '').strip()
        location = request.form.get('location', '').strip()
        
        # Validation
        if not all([title, date, hour, minute, ampm, location]):
            flash('All required fields must be filled!', 'error')
            return render_template('add_event.html')
        
        # Validate location is not empty
        if not location:
            flash('Location is required!', 'error')
            return render_template('add_event.html')
        
        # Validate hour and minute
        try:
            hour_int = int(hour)
            minute_int = int(minute)
            
            if not (1 <= hour_int <= 12):
                flash('Hour must be between 1 and 12', 'error')
                return render_template('add_event.html')
                
            if not (0 <= minute_int <= 59):
                flash('Minute must be between 0 and 59', 'error')
                return render_template('add_event.html')
                
        except ValueError:
            flash('Invalid hour or minute format', 'error')
            return render_template('add_event.html')
        
        # Convert AM/PM to 24-hour format
        if ampm == 'PM' and hour_int != 12:
            hour_24 = hour_int + 12
        elif ampm == 'AM' and hour_int == 12:
            hour_24 = 0
        else:
            hour_24 = hour_int
        
        # Format time as HH:MM (24-hour format)
        time_24h = f"{hour_24:02d}:{minute_int:02d}"
        
        # Combine date and time for validation
        try:
            event_datetime = datetime.strptime(f"{date} {time_24h}", "%Y-%m-%d %H:%M")
            # Store as datetime object for MongoDB
            event_datetime_obj = event_datetime
        except ValueError:
            flash('Invalid date or time format', 'error')
            return render_template('add_event.html')
        
        # Validate date is not in past
        current_datetime = datetime.now()
        if event_datetime < current_datetime:
            flash('Cannot create event in the past! Please select a future date and time.', 'error')
            return render_template('add_event.html')
        
        # Get database connection
        db_conn = get_db_connection()
        if db_conn is None:
            flash('Database connection failed!', 'error')
            return render_template('add_event.html')
        
        # Check for duplicate events (same title, date, time, location)
        # Note: Adjust field names based on your actual MongoDB schema
        duplicate = db_conn.events.find_one({
            'title': title,
            'date': event_datetime_obj,  # Using datetime object
            'location': location
        })
        
        if duplicate:
            flash('An event with the same title, date, time, and location already exists!', 'error')
            return render_template('add_event.html')
        
        # Insert new event
        try:
            # Prepare event data for MongoDB
            event_data = {
                'title': title,
                'description': description,
                'date': event_datetime_obj,  # Store as datetime object
                'location': location,
                'created_by': session.get('username', 'Unknown'),
                'created_by_id': ObjectId(session['user_id']) if 'user_id' in session else None,
                'created_at': datetime.now(),
                'status': 'active'
            }
            
            # Insert into MongoDB
            result = db_conn.events.insert_one(event_data)
            event_id = result.inserted_id
            
            # Create notification for admin
            create_notification(
                ObjectId(session['user_id']),
                "Event Created",
                f'Event "{title}" has been created successfully',
                'success',
                url_for('view_events')  # CHANGED: Fixed to use existing route
            )
            
            flash(f'Event "{title}" added successfully!', 'success')
            return redirect(url_for('view_events'))  # CHANGED: Redirect to events page
            
        except Exception as e:
            flash(f'Error adding event: {str(e)}', 'error')
            return render_template('add_event.html')
    
    # GET request - show the form
    return render_template('add_event.html')

# ---------------- EDIT EVENT -----------------
@app.route('/edit_event/<event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    # Validate ObjectId
    try:
        ObjectId(event_id)
    except InvalidId:
        flash("Invalid event ID.", "danger")
        return redirect(url_for('view_events'))
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard'))

    db_conn = get_db_connection()
    if db_conn is None:
        return redirect(url_for('view_events'))

    event = None
    try:
        event = db_conn.events.find_one({"_id": ObjectId(event_id)})
    except (Exception, InvalidId) as e:
        logging.error(f"Fetch event (edit) database query error: {e}")
        flash(f"Error retrieving event details: {e}", "danger")
        
    if not event:
        flash("Event not found.", "danger")
        return redirect(url_for('view_events'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        date = request.form.get('date', '').strip()
        location = request.form.get('location', '').strip()

        if not title or not date:
            flash("Title and Date are required!", "danger")
            return redirect(url_for('edit_event', event_id=event_id))
        
        # Convert to datetime for MongoDB storage
        try:
            event_datetime = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            flash("Invalid date format!", "danger")
            return redirect(url_for('edit_event', event_id=event_id))
        
        try:
            db_conn.events.update_one(
                {"_id": ObjectId(event_id)},
                {"$set": {
                    "title": title,
                    "description": description,
                    "date": event_datetime,
                    "location": location
                }}
            )
            flash(f"Event '{title}' updated successfully!", "success")
            return redirect(url_for('view_events'))
        except Exception as e:
            logging.error(f"Update event database query error: {e}")
            flash(f"Error updating event: {e}", "danger")
            return redirect(url_for('edit_event', event_id=event_id))
    
    # GET request handler - format event for template
    # Convert ObjectId to string
    event['id'] = str(event['_id'])
    
    # Format date for HTML date input (YYYY-MM-DD)
    event_date = event.get('date')
    if isinstance(event_date, datetime):
        event['date'] = event_date.strftime('%Y-%m-%d')
    elif isinstance(event_date, str):
        try:
            # Try to parse and reformat
            parsed_date = datetime.strptime(event_date, '%Y-%m-%d')
            event['date'] = parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            try:
                parsed_date = datetime.strptime(event_date, '%Y-%m-%d %H:%M:%S')
                event['date'] = parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                event['date'] = event_date
    
    return render_template('edit_event.html', event=event)

# ---------------- DELETE EVENT CONFIRMATION -----------------
@app.route('/delete_event_confirm/<event_id>')
def delete_event_confirm(event_id):
    # Validate ObjectId
    try:
        ObjectId(event_id)
    except InvalidId:
        flash("Invalid event ID.", "danger")
        return redirect(url_for('view_events'))
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied. Only administrators can delete events.", "danger")
        return redirect(url_for('dashboard'))

    db_conn = get_db_connection()
    if db_conn is None:
        return redirect(url_for('view_events'))

    event = None
    try:
        event = db_conn.events.find_one({"_id": ObjectId(event_id)})
    except (Exception, InvalidId) as e:
        logging.error(f"Fetch event (delete confirm) database query error: {e}")
        flash(f"Error fetching event details: {e}", "danger")

    if not event:
        flash("Event not found.", "danger")
        return redirect(url_for('view_events'))
    
    # Format event for template
    event['id'] = str(event['_id'])
    
    # Format date if it's a datetime object
    if isinstance(event.get('date'), datetime):
        event['date'] = event['date'].strftime('%Y-%m-%d')
    elif isinstance(event.get('date'), str) and len(event.get('date', '')) > 10:
        # If it's a datetime string, extract just the date part
        try:
            parsed_date = datetime.strptime(event['date'], '%Y-%m-%d %H:%M:%S')
            event['date'] = parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            pass
        
    return render_template('delete_event_confirm.html', event=event)

# ---------------- DELETE EVENT (FINAL EXECUTION) -----------------
@app.route('/delete_event/<event_id>', methods=['POST'])
def delete_event(event_id):
    # Validate ObjectId
    try:
        ObjectId(event_id)
    except InvalidId:
        flash("Invalid event ID.", "danger")
        return redirect(url_for('view_events'))
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard'))

    db_conn = get_db_connection()
    if db_conn is None:
        return redirect(url_for('view_events'))

    try:
        # 1. Delete associated registrations first (to maintain foreign key constraints)
        db_conn.registrations.delete_many({"event_id": ObjectId(event_id)})
        # 2. Delete the event itself
        db_conn.events.delete_one({"_id": ObjectId(event_id)})
        flash("Event and all associated registrations deleted successfully.", "success")
    except Exception as e:
        logging.error(f"Delete event database query error: {e}")
        flash(f"Error deleting event: {e}", "danger")

    return redirect(url_for('view_events'))

# ---------------- VIEW EVENTS -----------------
# ---------------- VIEW ALL EVENTS (LISTING PAGE) -----------------
@app.route('/events')
def view_events():  # Note: function name is 'view_events'
    """View all events listing"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db_conn = get_db_connection()
    if db_conn is None:
        events_list = []
    else:
        try:
            events_list = list(db_conn.events.find().sort("date", 1))
            
            # Add is_past flag to each event and convert ObjectId to string
            today = datetime.now().date()
            for event in events_list:
                # Convert ObjectId to string for template use
                event['id'] = str(event['_id'])
                
                # Handle date conversion
                event_date = event['date']
                if isinstance(event_date, datetime):
                    event_date = event_date.date()
                elif isinstance(event_date, str):
                    try:
                        event_date = datetime.strptime(event_date, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            event_date = datetime.strptime(event_date, '%Y-%m-%d %H:%M:%S').date()
                        except ValueError:
                            event_date = today
                
                event['is_past'] = event_date < today
                
        except Exception as e:
            logging.error(f"Fetch events database query error: {e}")
            flash(f"Error fetching events: {e}", "danger")
            events_list = []
    
    current_user_data = {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role')
    }

    # Pass today's date to template for days calculation
    today = datetime.now().date()
    
    return render_template('events.html', 
                         events=events_list, 
                         current_user=current_user_data,
                         today=today)
# ---------------- VIEW REGISTRATIONS FOR SPECIFIC EVENT -----------------
# ---------------- VIEW REGISTRATIONS FOR SPECIFIC EVENT -----------------
@app.route('/view_registrations/<event_id>')
def view_registrations(event_id):
    # Validate ObjectId
    try:
        ObjectId(event_id)
    except InvalidId:
        flash("Invalid event ID.", "danger")
        return redirect(url_for('view_events'))
    
    if 'role' not in session or session['role'] != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard'))

    db_conn = get_db_connection()
    if db_conn is None:
        return redirect(url_for('view_events'))

    registrations = []
    event_title = "Unknown Event"

    try:
        # Get registrations for this event
        raw_registrations = list(db_conn.registrations.find({
            "event_id": ObjectId(event_id)
        }).sort("registered_at", -1))  # Sort by most recent first

        # Get event details
        event = db_conn.events.find_one({"_id": ObjectId(event_id)})
        if event:
            event_title = event['title']
        
        # For each registration, get student details
        registrations = []
        for reg in raw_registrations:
            # Get student/user details
            try:
                student_id = reg.get('student_id')
                
                # Handle both ObjectId and string formats
                if isinstance(student_id, str):
                    student = db_conn.users.find_one({"_id": ObjectId(student_id)})
                else:
                    student = db_conn.users.find_one({"_id": student_id})
                
                if student:
                    registrations.append({
                        'id': str(reg['_id']),
                        'student_name': student.get('name', 'Unknown Student'),
                        'phone': reg.get('phone', 'N/A'),
                        'comments': reg.get('comments', 'None')
                    })
                else:
                    # If student not found, still show the registration
                    registrations.append({
                        'id': str(reg['_id']),
                        'student_name': 'Unknown Student',
                        'phone': reg.get('phone', 'N/A'),
                        'comments': reg.get('comments', 'None')
                    })
                    
            except Exception as e:
                logging.error(f"Error processing registration {reg.get('_id')}: {e}")
                continue
                
    except Exception as e:
        logging.error(f"View registrations database query error: {e}")
        flash(f"Error fetching registrations: {e}", "danger")
        registrations = []

    return render_template('view_registrations.html',
                          registrations=registrations,
                          event_title=event_title)
# ==================== REDIRECT FOR EMPTY REGISTER EVENT ROUTE ====================
@app.route('/register_event/')
def register_event_redirect():
    """Redirect /register_event/ to /events page"""
    flash("Please select an event to register for.", "info")
    return redirect(url_for('view_events'))

# ==================== UPDATED REGISTER EVENT ROUTE ====================
@app.route('/register_event/<event_id>', methods=['GET', 'POST'])
def register_event(event_id):
    # Validate ObjectId
    try:
        ObjectId(event_id)
    except InvalidId:
        flash("Invalid event ID.", "danger")
        return redirect(url_for('view_events'))
    
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db_conn = get_db_connection()
    if db_conn is None:
        flash("Database connection failed", "danger")
        return redirect(url_for('view_events'))

    # Fetch event info
    event = None
    try:
        event = db_conn.events.find_one({"_id": ObjectId(event_id)})
    except Exception as e:
        logging.error(f"Fetch event error: {e}")
        flash(f"Error retrieving event: {e}", "danger")
        return redirect(url_for('view_events'))
    
    if not event:
        flash("Event not found!", "danger")
        return redirect(url_for('view_events'))
    
    # Check if event is in the past
    event_date = event['date']
    event_datetime = None
    
    # Parse event datetime
    if isinstance(event_date, datetime):
        event_datetime = event_date
        event_date = event_date.date()
    elif isinstance(event_date, str):
        try:
            event_datetime = datetime.strptime(event_date, '%Y-%m-%d %H:%M:%S')
            event_date = event_datetime.date()
        except ValueError:
            try:
                event_datetime = datetime.strptime(event_date, '%Y-%m-%d %H:%M')
                event_date = event_datetime.date()
            except ValueError:
                try:
                    event_datetime = datetime.strptime(event_date, '%Y-%m-%d')
                    event_date = event_datetime.date()
                except ValueError:
                    flash("Invalid event date format", "danger")
                    return redirect(url_for('view_events'))
    
    today = datetime.now().date()
    
    if event_date < today:
        flash(f'Event "{event["title"]}" has already ended. Registration is closed.', 'warning')
        return redirect(url_for('view_events'))

    student_id = session['user_id']
    existing_registration = None
    
    # Check if student is already registered for THIS SPECIFIC event
    try:
        existing_registration = db_conn.registrations.find_one({
            "student_id": ObjectId(student_id),
            "event_id": ObjectId(event_id),
            "status": "active"
        })
        
    except Exception as e:
        logging.error(f"Check existing registration error: {e}")
        existing_registration = None

    # If student is already registered for this specific event, block registration
    if existing_registration:
        if request.method == 'GET':
            return render_template('register_event.html', 
                                 event=event, 
                                 active_registration=existing_registration)
        elif request.method == 'POST':
            flash(f'You are already registered for "{event["title"]}".', 'danger')
            return redirect(url_for('view_events'))
    
    # NEW: Check for time conflict with other events (only if event_datetime is available)
    if event_datetime:
        try:
            # Find all active registrations for this student
            student_registrations = list(db_conn.registrations.find({
                "student_id": ObjectId(student_id),
                "status": "active"
            }))
            
            if student_registrations:
                # Get event IDs from registrations
                registered_event_ids = [reg['event_id'] for reg in student_registrations]
                
                # Get details of all events the student is registered for
                registered_events = list(db_conn.events.find({
                    "_id": {"$in": registered_event_ids}
                }))
                
                # Check for time conflicts
                for registered_event in registered_events:
                    registered_event_datetime = registered_event['date']
                    
                    # Parse registered event datetime
                    reg_event_dt = None
                    if isinstance(registered_event_datetime, datetime):
                        reg_event_dt = registered_event_datetime
                    elif isinstance(registered_event_datetime, str):
                        try:
                            reg_event_dt = datetime.strptime(registered_event_datetime, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            try:
                                reg_event_dt = datetime.strptime(registered_event_datetime, '%Y-%m-%d %H:%M')
                            except ValueError:
                                try:
                                    reg_event_dt = datetime.strptime(registered_event_datetime, '%Y-%m-%d')
                                except ValueError:
                                    continue  # Skip if can't parse
                    
                    if reg_event_dt:
                        # Check if the events are on the same date
                        if event_datetime.date() == reg_event_dt.date():
                            # Check for time overlap (assuming 2-hour buffer for events)
                            # Calculate with 2-hour buffer (1 hour before + 1 hour after event)
                            event_start = event_datetime - timedelta(hours=1)
                            event_end = event_datetime + timedelta(hours=2)  # 1 hour event + 1 hour buffer
                            
                            registered_event_start = reg_event_dt - timedelta(hours=1)
                            registered_event_end = reg_event_dt + timedelta(hours=2)
                            
                            # Check for overlap
                            if (event_start < registered_event_end and event_end > registered_event_start):
                                # Format time for display
                                reg_event_time = reg_event_dt.strftime("%I:%M %p")
                                current_event_time = event_datetime.strftime("%I:%M %p")
                                
                                flash(f'Time conflict! You are already registered for "{registered_event["title"]}" at {reg_event_time}. You cannot register for "{event["title"]}" at {current_event_time} on the same day.', 'warning')
                                return redirect(url_for('view_events'))
                                
        except Exception as e:
            logging.error(f"Time conflict check error: {e}")
            # Continue with registration if time check fails (don't block registration due to error)

    # Handle POST request
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        comments = request.form.get('comments', '').strip()
        
        # Validate phone number
        if not phone:
            flash("Phone number is required!", "danger")
            return redirect(url_for('register_event', event_id=event_id))
        
        # Phone number validation - must be exactly 10 digits
        if not phone.isdigit() or len(phone) != 10:
            flash("Phone number must be exactly 10 digits", "danger")
            return redirect(url_for('register_event', event_id=event_id))

        try:
            # Final check for race condition
            if db_conn.registrations.find_one({
                "student_id": ObjectId(student_id),
                "event_id": ObjectId(event_id),
                "status": "active"
            }):
                flash(f'You are already registered for "{event["title"]}".', 'danger')
                return redirect(url_for('view_events'))
                
            # Final time conflict check (in case of concurrent registrations)
            if event_datetime:
                student_registrations = list(db_conn.registrations.find({
                    "student_id": ObjectId(student_id),
                    "status": "active"
                }))
                
                if student_registrations:
                    registered_event_ids = [reg['event_id'] for reg in student_registrations]
                    registered_events = list(db_conn.events.find({
                        "_id": {"$in": registered_event_ids}
                    }))
                    
                    for registered_event in registered_events:
                        registered_event_datetime = registered_event['date']
                        reg_event_dt = None
                        
                        if isinstance(registered_event_datetime, datetime):
                            reg_event_dt = registered_event_datetime
                        elif isinstance(registered_event_datetime, str):
                            try:
                                reg_event_dt = datetime.strptime(registered_event_datetime, '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                try:
                                    reg_event_dt = datetime.strptime(registered_event_datetime, '%Y-%m-%d %H:%M')
                                except ValueError:
                                    continue
                        
                        if reg_event_dt and event_datetime.date() == reg_event_dt.date():
                            event_start = event_datetime - timedelta(hours=1)
                            event_end = event_datetime + timedelta(hours=2)
                            registered_event_start = reg_event_dt - timedelta(hours=1)
                            registered_event_end = reg_event_dt + timedelta(hours=2)
                            
                            if (event_start < registered_event_end and event_end > registered_event_start):
                                flash(f'Time conflict detected! You are already registered for another event at the same time.', 'warning')
                                return redirect(url_for('view_events'))

            # INSERT with status
            registration_id = db_conn.registrations.insert_one({
                "event_id": ObjectId(event_id),
                "student_id": ObjectId(student_id),
                "phone": phone,
                "comments": comments,
                "status": "active",
                "registered_at": datetime.now()
            }).inserted_id
            
            create_notification(
                ObjectId(student_id),
                "Event Registration Confirmed",
                f'You have successfully registered for "{event["title"]}"',
                'success',
                url_for('my_registrations')
            )
            
            flash(f'Successfully registered for "{event["title"]}"!', 'success')
            return redirect(url_for('my_registrations')) 
            
        except Exception as err:
            logging.error(f"Registration error: {err}")
            flash(f'Database error: {err}', 'danger')
            return redirect(url_for('my_registrations'))

    # GET request
    return render_template('register_event.html', 
                         event=event, 
                         active_registration=existing_registration)
# ==================== CANCEL REGISTRATION ROUTE ====================
@app.route('/cancel_registration/<registration_id>', methods=['POST'])
def cancel_registration(registration_id):
    # Validate ObjectId
    try:
        ObjectId(registration_id)
    except InvalidId:
        flash("Invalid registration ID.", "danger")
        return redirect(url_for('my_registrations'))
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    student_id = session['user_id']
    
    db_conn = get_db_connection()
    if db_conn is None:
        flash("Database connection error", "danger")
        return redirect(url_for('my_registrations'))
    
    try:
        # Verify registration belongs to student
        registration = db_conn.registrations.find_one({
            "_id": ObjectId(registration_id),
            "student_id": ObjectId(student_id),
            "status": "active"
        })
        
        if not registration:
            flash("Registration not found or already cancelled", "danger")
            return redirect(url_for('my_registrations'))
        
        # Cancel it
        db_conn.registrations.update_one(
            {"_id": ObjectId(registration_id)},
            {"$set": {"status": "cancelled"}}
        )
        
        # Get event title for the notification and flash message
        cancelled_event = db_conn.events.find_one({"_id": registration["event_id"]})
        event_title = cancelled_event["title"] if cancelled_event else "Unknown Event"
        
        create_notification(
            student_id,
            "Registration Cancelled",
            f'Your registration for "{event_title}" has been cancelled.',
            'warning',
            url_for('view_events')
        )
        
        flash(f'Registration for "{event_title}" cancelled.', 'success')
            
    except Exception as e:
        logging.error(f"Cancel error: {e}")
        flash("Error cancelling", "danger")
    
    return redirect(url_for('my_registrations'))

# ==================== UPDATED MY REGISTRATIONS ROUTE ====================
@app.route('/my-registrations')
def my_registrations():
    if 'user_id' not in session:
        flash("Please login first")
        return redirect(url_for('login'))

    db_conn = get_db_connection()
    if db_conn is None:
        return redirect(url_for('dashboard'))

    student_id = session['user_id']
    my_events = []
    
    try:
        my_events = list(db_conn.registrations.find({
            "student_id": ObjectId(student_id)
        }).sort("status", 1))
        
        # Add event details to each registration
        for reg in my_events:
            event = db_conn.events.find_one({"_id": reg["event_id"]})
            if event:
                reg["event"] = event
        
    except Exception as e:
        logging.error(f"My registrations error: {e}")
        flash(f"Error fetching registrations: {e}", "danger")
        
    return render_template('my_registrations.html', events=my_events)
# --- ALL REGISTRATIONS (ADMIN ONLY) ---
@app.route('/all_registrations')
def all_registrations():
    if 'role' not in session or session['role'] != 'admin':
        flash('Access denied. You must be an administrator.', 'danger')
        return redirect(url_for('dashboard'))
    
    db_conn = get_db_connection()
    if db_conn is None:
        return redirect(url_for('view_events'))
        
    all_registrations_data = []
    
    try:
        raw_registrations = list(db_conn.registrations.find().sort("registered_at", -1))
        
        for row_dict in raw_registrations:
            event = db_conn.events.find_one({"_id": row_dict['event_id']})
            
            # Handle both string and ObjectId formats for student_id (backward compatibility)
            student = None
            if isinstance(row_dict['student_id'], str):
                # Try to find student by string _id
                student = db_conn.users.find_one({"_id": row_dict['student_id']})
                
            if not student:
                # Try ObjectId format
                try:
                    student = db_conn.users.find_one({"_id": ObjectId(row_dict['student_id'])})
                except:
                    pass
            
            # Skip registrations with missing event or student data
            if not event or not student:
                continue
            
            all_registrations_data.append({
                'id': str(row_dict['_id']),
                'event_name': event.get('title', 'Unknown Event'),
                'student_name': student.get('name', 'Unknown Student'),
                'email': student.get('email', 'N/A'),
                'phone': row_dict.get('phone', 'N/A'),
                'comments': row_dict.get('comments', ''),
                'registered_at': str(row_dict['registered_at']).split('.')[0] if row_dict.get('registered_at') else '',
                'status': row_dict.get('status', 'active')
            })
            print(all_registrations_data)
        if not all_registrations_data:
            flash('No registrations yet.', 'info') 
            
    except Exception as e:
        logging.error(f"All registrations error: {e}")
        flash(f'Database error: {e}', 'danger')
        
    return render_template('all_registrations.html', registrations=all_registrations_data)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash("Please enter your email address", "danger")
            return redirect(url_for('forgot_password'))
        
        db_conn = get_db_connection()
        if db_conn is None:
            flash("Database connection failed. Please try again.", "danger")
            return redirect(url_for('forgot_password'))
        
        try:
            # Check if user exists
            user = db_conn.users.find_one({"email": email})
            
            if user:
                # Generate secure reset token
                reset_token = secrets.token_urlsafe(32)
                token_expiry = datetime.now() + timedelta(hours=1)  # 1 hour expiry
                
                # Store token in database
                db_conn.users.update_one(
                    {"email": email},
                    {"$set": {
                        "reset_token": reset_token,
                        "reset_token_expiry": token_expiry
                    }}
                )
                
                # Generate reset URL
                reset_url = url_for('reset_password', token=reset_token, _external=True)
                
                # For development: Show the link (remove in production)
                flash(f"Password reset link has been generated. For testing, use: {reset_url}", "info")
                
                # In production, you would send an email here:
                # send_password_reset_email(user['email'], user['name'], reset_url)
                # flash("Password reset instructions have been sent to your email.", "success")
                
            else:
                # Don't reveal whether email exists (security)
                flash("If an account with that email exists, password reset instructions have been sent.", "info")
            
            return redirect(url_for('login'))
            
        except Exception as e:
            logging.error(f"Forgot password error: {e}")
            flash("An error occurred. Please try again.", "danger")
            return redirect(url_for('forgot_password'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    db_conn = get_db_connection()
    if db_conn is None:
        flash("Database connection failed. Please try again.", "danger")
        return redirect(url_for('forgot_password'))
    
    try:
        # Verify token is valid and not expired
        user = db_conn.users.find_one({
            "reset_token": token,
            "reset_token_expiry": {"$gt": datetime.now()}
        })
        
        if not user:
            flash("Invalid or expired reset token. Please request a new password reset.", "danger")
            return redirect(url_for('forgot_password'))
        
        if request.method == 'POST':
            new_password = request.form.get('password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            # Validation
            if not new_password or not confirm_password:
                flash("Please fill in all fields", "danger")
                return render_template('reset_password.html', token=token)
            
            if new_password != confirm_password:
                flash("Passwords do not match", "danger")
                return render_template('reset_password.html', token=token)
            
            if len(new_password) < 6:
                flash("Password must be at least 6 characters long", "danger")
                return render_template('reset_password.html', token=token)
            
            # Update password and clear reset token
            db_conn.users.update_one(
                {"_id": user['_id']},
                {"$set": {
                    "password": new_password,
                    "reset_token": None,
                    "reset_token_expiry": None
                }}
            )
            
            flash("Password reset successfully! You can now login with your new password.", "success")
            return redirect(url_for('login'))
        
        return render_template('reset_password.html', token=token)
        
    except Exception as e:
        logging.error(f"Reset password error: {e}")
        flash("An error occurred. Please try again.", "danger")
        return redirect(url_for('forgot_password'))

# ---------------- NOTIFICATIONS -----------------
@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    db_conn = get_db_connection()
    
    if db_conn is None:
        flash("Database connection failed", "danger")
        return redirect(url_for('dashboard'))
    
    try:
        # Get all notifications for the user
        notifications_list = get_user_notifications(user_id, limit=50)
        
        # Convert ObjectId to string and format for template
        formatted_notifications = []
        for notif in notifications_list:
            formatted_notifications.append({
                'id': str(notif['_id']),
                'title': notif.get('title', 'Notification'),
                'message': notif.get('message', ''),
                'type': notif.get('type', 'info'),
                'is_read': notif.get('is_read', False),
                'created_at': notif.get('created_at', datetime.now()),
                'related_url': notif.get('related_url')
            })
        
        # Count unread notifications
        unread_count = len([n for n in formatted_notifications if not n['is_read']])
        
    except Exception as e:
        logging.error(f"Notifications error: {e}")
        flash(f"Error fetching notifications: {e}", "danger")
        formatted_notifications = []
        unread_count = 0
    
    return render_template('notifications.html', 
                         notifications=formatted_notifications,
                         unread_count=unread_count)

@app.route('/notifications/read/<notification_id>', methods=['GET', 'POST'])
def mark_notification_read_route(notification_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    
    try:
        success = mark_notification_read(notification_id, user_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Notification not found'}), 404
    except Exception as e:
        logging.error(f"Mark notification read error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/notifications/read-all', methods=['POST'])
def mark_all_notifications_read():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    db_conn = get_db_connection()
    
    if db_conn is None:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    try:
        # Convert user_id to ObjectId if it's a string
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except InvalidId:
                return jsonify({'success': False, 'error': 'Invalid user ID'}), 400
        
        result = db_conn.notifications.update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True}}
        )
        return jsonify({'success': True, 'updated': result.modified_count})
    except Exception as e:
        logging.error(f"Mark all notifications read error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ---------------- STUDENT DASHBOARD -----------------
@app.route('/student_dashboard')
def student_dashboard():
    """Redirect to main dashboard (students and admins use the same dashboard)"""
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    # Initial connection attempt check
    db = get_db_connection()
    if db is not None:
        logging.info("Initial database connection successful.")
    else:
        logging.warning("Application starting with no initial database connection.")
    
    # Only run in debug mode if not in production
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))