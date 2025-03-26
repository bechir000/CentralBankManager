import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Set maximum file upload size to 16MB
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# Initialize the app with the extension
db.init_app(app)

# Add context processor for current year
from datetime import datetime
@app.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

# Import routes after initializing the app to avoid circular imports
from routes import *

# Create database tables
with app.app_context():
    # Import models here to ensure they are registered with SQLAlchemy
    import models
    db.create_all()
    logger.info("Database tables created successfully")
