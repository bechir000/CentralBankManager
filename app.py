import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "super-secret-key-for-development"

# Import database configuration
from config.database import get_database_config

# Configure the database
db_config = get_database_config()
app.config["SQLALCHEMY_DATABASE_URI"] = db_config["SQLALCHEMY_DATABASE_URI"]
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = db_config["SQLALCHEMY_ENGINE_OPTIONS"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Set maximum file upload size to 16MB
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# Initialize the extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Add context processor for current year
from datetime import datetime
@app.context_processor
def inject_global_variables():
    return {
        'current_year': datetime.now().year,
    }

# Import routes after initializing the app to avoid circular imports
from routes import *
from auth_routes import *

# Create database tables and default roles
with app.app_context():
    # Import models here to ensure they are registered with SQLAlchemy
    import models
    db.create_all()

    # Create default roles if they don't exist
    from models import Role
    roles = {
        'admin': 'Administrator with full access to the system',
        'user': 'Regular user with basic access'
    }

    for role_name, description in roles.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=description)
            db.session.add(role)

    db.session.commit()

    # Create admin user if no users exist
    from auth_routes import create_admin_user
    create_admin_user()

    logger.info("Database tables and default roles created successfully")