#!/usr/bin/env python
"""
Direct test script for registration and login functionality in JobHunterAI.
This script creates a test user and verifies it can be retrieved from the database.
"""
import os
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test if the database connection is working."""
    logger.info("Testing database connection...")
    try:
        with app.app_context():
            # Check if we can query users
            user_count = User.query.count()
            logger.info(f"Database connection successful. User count: {user_count}")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}", exc_info=True)
        return False

def test_user_creation():
    """Test if we can create a user in the database."""
    logger.info("Testing user creation...")
    
    # Generate a unique test user
    import random
    random_suffix = random.randint(1000, 9999)
    username = f"testuser{random_suffix}"
    email = f"testuser{random_suffix}@example.com"
    password = "password123"
    
    try:
        with app.app_context():
            # Create a test user
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            
            # Add and commit to database
            db.session.add(user)
            db.session.commit()
            
            # Verify the user was added
            new_user = User.query.filter_by(email=email).first()
            if new_user:
                logger.info(f"User created successfully with ID: {new_user.id}")
                
                # Verify password hashing works
                if check_password_hash(new_user.password_hash, password):
                    logger.info("Password verification successful")
                    return True
                else:
                    logger.error("Password verification failed")
                    return False
            else:
                logger.error("User not found after creation")
                return False
    except Exception as e:
        logger.error(f"User creation failed: {str(e)}", exc_info=True)
        return False

def run_all_tests():
    """Run all tests."""
    logger.info("Starting authentication tests...")
    
    # Test database connection
    db_connection = test_database_connection()
    
    # Test user creation
    user_creation = test_user_creation() if db_connection else False
    
    # Print summary
    logger.info("\n=== TEST RESULTS ===")
    logger.info(f"Database connection: {'SUCCESS' if db_connection else 'FAILED'}")
    logger.info(f"User creation: {'SUCCESS' if user_creation else 'FAILED'}")
    
    return db_connection and user_creation

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)