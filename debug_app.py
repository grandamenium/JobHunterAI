#\!/usr/bin/env python
"""
Super simple JobHunterAI app with debug mode enabled
"""
import os
import logging
import webbrowser
import threading
import time
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-for-testing'
app.config['DEBUG'] = True

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Simple in-memory user storage
users = {}
next_user_id = 1

# User class
class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.resume_text = "Sample resume text"
        self.resume_file = None
        self.resume_filename = "sample.pdf"
        self.resume_content_type = "application/pdf"

# Simple Job class to match the structure expected by templates
class Job:
    def __init__(self, id, title, company, location, description, url, source='Sample'):
        self.id = id
        self.title = title
        self.company = company
        self.location = location
        self.description = description
        self.url = url
        self.source = source
        self.date_posted = datetime.utcnow()
        self.applicants_count = 0
        self.contact_info = "example@company.com"

# Sample job data
job_data = [
    Job(
        id=1,
        title='Software Engineer',
        company='Google',
        location='Mountain View, CA',
        description='Design and develop innovative software solutions for Google products.',
        url='https://careers.google.com/sample/1',
        source='Google Careers'
    ),
    Job(
        id=2,
        title='Data Scientist',
        company='Microsoft',
        location='Redmond, WA',
        description='Analyze large datasets to extract insights and build machine learning models.',
        url='https://careers.microsoft.com/sample/2',
        source='Microsoft Careers'
    ),
    Job(
        id=3,
        title='Frontend Developer',
        company='Meta',
        location='Menlo Park, CA',
        description='Build engaging user interfaces for Meta products.',
        url='https://careers.meta.com/sample/3',
        source='Meta Careers'
    )
]

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('jobs_page'))
    return render_template('index.html')

@app.route('/jobs')
@login_required
def jobs_page():
    return render_template('jobs.html', jobs=job_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Find user by email
        user = next((u for u in users.values() if u.email == email), None)
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            logger.info(f"User {user.username} logged in")
            return redirect(url_for('jobs_page'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    global next_user_id
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Simple validation
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        # Check if email already exists
        if any(u.email == email for u in users.values()):
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        # Create new user
        user_id = next_user_id
        next_user_id += 1
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        # Add to our in-memory store
        users[user_id] = user
        
        # Log in the new user
        login_user(user)
        
        flash('Registration successful\!', 'success')
        return redirect(url_for('jobs_page'))
    
    return render_template('register.html')

@app.route('/resume')
@login_required
def resume():
    return render_template('resume.html')

@app.route('/applications')
@login_required
def applications():
    return render_template('applications.html', applications=[])

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def open_browser():
    """Open browser automatically after a short delay"""
    time.sleep(1.5)
    url = "http://localhost:8088"
    try:
        webbrowser.open(url)
        logger.info(f"Opening browser at {url}")
    except Exception as e:
        logger.error(f"Failed to open browser: {str(e)}")

if __name__ == '__main__':
    # Start a thread to open the browser
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Add a test user
    test_user = User(
        id=0,
        username='testuser',
        email='test@example.com',
        password_hash=generate_password_hash('password')
    )
    users[0] = test_user
    
    logger.info("Starting simplified JobHunterAI application with debug mode...")
    logger.info("Test user created: email=test@example.com, password=password")
    
    # Get port from environment variable or use default
    port = int(os.environ.get('FLASK_RUN_PORT', 8088))
    logger.info(f"Starting server on port {port}")
    app.run(host='127.0.0.1', port=port, debug=True)
