#!/usr/bin/env python
"""
Tests for the JobHunterAI application authentication system.
"""
import os
import sys
import unittest
import tempfile
import shutil
from app import app, db
from models import User
from werkzeug.security import check_password_hash, generate_password_hash

class AuthenticationTests(unittest.TestCase):
    """Test authentication (login and registration) functionality."""
    
    def setUp(self):
        """Set up a test environment."""
        # Create a temporary directory for the test database
        self.test_dir = tempfile.mkdtemp()
        test_db_path = os.path.join(self.test_dir, 'test.db')
        
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{test_db_path}'
        
        # Create the database and tables
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create a test client
        self.client = app.test_client()
        
        # Create a test user
        test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(test_user)
        db.session.commit()
    
    def tearDown(self):
        """Clean up after the test."""
        # Remove the database and clean up the session
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_login_page_loads(self):
        """Test that the login page loads correctly."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)
    
    def test_register_page_loads(self):
        """Test that the register page loads correctly."""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data)
        
    def test_valid_registration(self):
        """Test registering a new user."""
        response = self.client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123'
        }, follow_redirects=True)
        
        # Check that registration was successful
        self.assertEqual(response.status_code, 200)
        
        # Verify the user was added to the database
        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'newuser@example.com')
        
        # Check that the user is redirected to the jobs page
        self.assertIn(b'Welcome to JobHunterAI', response.data)
    
    def test_duplicate_email_registration(self):
        """Test registering with an existing email."""
        response = self.client.post('/register', data={
            'username': 'another',
            'email': 'test@example.com',  # This email already exists
            'password': 'password123'
        }, follow_redirects=True)
        
        # Verify the error message
        self.assertIn(b'Email already registered', response.data)
    
    def test_valid_login(self):
        """Test logging in with valid credentials."""
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Check that login was successful and redirected to jobs
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'testuser', response.data)  # Username should appear
    
    def test_invalid_login(self):
        """Test logging in with invalid credentials."""
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        # Verify the error message
        self.assertIn(b'Invalid email or password', response.data)

def run_tests():
    """Run the tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

if __name__ == '__main__':
    run_tests()