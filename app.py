import os
import secrets
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy.orm import DeclarativeBase
    from flask_login import LoginManager
    logger.info("Successfully imported Flask and extensions")
except ImportError as e:
    logger.error(f"Error importing Flask dependencies: {e}")
    raise

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", secrets.token_hex(32))

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///instance/job_application_system.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

# Import routes after app initialization to avoid circular imports
from routes import *
from models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Make sure instance directory exists with proper permissions
import os
instance_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance'))
logger = logging.getLogger(__name__)

if not os.path.exists(instance_dir):
    try:
        os.makedirs(instance_dir, mode=0o777)
        logger.info(f"Created instance directory at {instance_dir}")
    except Exception as e:
        logger.error(f"Error creating instance directory: {str(e)}")
else:
    # Update permissions on existing directory
    try:
        os.chmod(instance_dir, 0o777)
        logger.info(f"Updated permissions on instance directory at {instance_dir}")
    except Exception as e:
        logger.error(f"Error updating permissions on instance directory: {str(e)}")

# Set proper database path with absolute path
db_path = os.path.join(instance_dir, 'job_application_system.db')
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
logger.info(f"Using database at {db_path}")

# Set SQLAlchemy echo to debug SQL queries
app.config["SQLALCHEMY_ECHO"] = True

# Create database tables if they don't exist
with app.app_context():
    try:
        # Explicitly specify the database file permissions
        if os.path.exists(db_path):
            os.chmod(db_path, 0o666)
            logger.info(f"Updated permissions on database file: {db_path}")
            
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")