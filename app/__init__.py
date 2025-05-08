from flask import Flask
from flask_pymongo import PyMongo
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('app.config')

# Initialize MongoDB
mongo = PyMongo(app)
db = mongo.db

# Add datetime utility to db for use in queries
db.datetime = datetime

# Import and register routes
from app.routes import register_routes
register_routes(app)

# Import scheduler (for background tasks)
from app.services.scheduler import SchedulerService

# Create global scheduler instance
scheduler = SchedulerService()

# Start scheduler when app starts
@app.before_first_request
def start_scheduler():
    scheduler.start()

# Create database indexes
@app.before_first_request
def create_indexes():
    # User indexes
    db.users.create_index('email', unique=True)
    
    # Listing indexes
    db.listings.create_index('external_id', unique=True)
    db.listings.create_index('address')
    db.listings.create_index('status')
    db.listings.create_index('date_found')
    
    # Match indexes
    db.matches.create_index([('user_id', 1), ('listing_id', 1)], unique=True)
    db.matches.create_index('status')
    db.matches.create_index('contacted')
    db.matches.create_index('date_matched')
    
    # Communication indexes
    db.communications.create_index([('user_id', 1), ('listing_id', 1)])
    db.communications.create_index('status')
    db.communications.create_index('created_at')

# Export flask app
from app import routes