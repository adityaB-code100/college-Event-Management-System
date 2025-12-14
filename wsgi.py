"""
WSGI entry point for the College Event Management application.
This file is used by Gunicorn and other WSGI servers.
"""

from app import app

if __name__ == "__main__":
    app.run()