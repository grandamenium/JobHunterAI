#\!/usr/bin/env python
"""
Minimal JobHunterAI app that only handles login, registration, and a simple jobs page
"""
import webbrowser
import threading
import time
import logging
import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from agents.job_scraper import JobScraperAgent

# Create the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'simple-test-key'
app.config['DEBUG'] = True

# Initialize the login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# In-memory user storage
users = {}
next_user_id = 1

# Define User class
class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize job scraper
job_scraper = JobScraperAgent()

# Define simple Job class
class Job:
    def __init__(self, id, title, company, location, description, url="", source="Sample", date_posted=None):
        self.id = id
        self.title = title
        self.company = company
        self.location = location
        self.description = description
        self.url = url
        self.source = source
        self.date_posted = date_posted or datetime.utcnow()

# Sample job listings
jobs_list = [
    Job(1, "Software Engineer", "Google", "Mountain View, CA", "Build amazing software.", 
        url="https://careers.google.com/sample/1", source="Sample Data"),
    Job(2, "Data Scientist", "Microsoft", "Redmond, WA", "Work with big data.",
        url="https://careers.microsoft.com/sample/2", source="Sample Data"),
    Job(3, "Frontend Developer", "Meta", "Menlo Park, CA", "Create user interfaces.",
        url="https://careers.meta.com/sample/3", source="Sample Data")
]

# Store scraped jobs
scraped_jobs = []
next_job_id = len(jobs_list) + 1

# User loader function
@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

# Routes
@app.route('/')
def index():
    # Simple home page that redirects to login or jobs
    if current_user.is_authenticated:
        return redirect(url_for('jobs'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Login page
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Find user by email
        user = next((u for u in users.values() if u.email == email), None)
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            print(f"User {user.username} logged in successfully")
            # Redirect to jobs page after login
            return redirect(url_for('jobs'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Registration page
    global next_user_id
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Simple validation
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        # Create new user
        user_id = next_user_id
        next_user_id += 1
        
        # Add user to our in-memory store
        users[user_id] = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        # Log in the new user
        login_user(users[user_id])
        
        flash('Registration successful\!', 'success')
        return redirect(url_for('jobs'))
    
    return render_template('register.html')

@app.route('/jobs')
@login_required
def jobs():
    # Get search parameters
    keywords = request.args.get('keywords', '')
    location = request.args.get('location', '')
    job_type = request.args.get('job-type', 'full-time')
    
    # If search parameters exist, perform a search
    if keywords or location:
        try:
            # Log the search
            logger.info(f"Searching jobs - Keywords: {keywords}, Location: {location}, Type: {job_type}")
            
            # Clear previous scraped jobs
            global scraped_jobs, next_job_id
            scraped_jobs = []
            
            # Search for jobs on USAJobs
            usajobs_results = job_scraper.scrape_usajobs(keywords, location, job_type)
            
            # Convert the dictionary results to Job objects
            for job_dict in usajobs_results:
                job = Job(
                    id=next_job_id,
                    title=job_dict['title'],
                    company=job_dict['company'],
                    location=job_dict['location'],
                    description=job_dict['description'],
                    url=job_dict['url'],
                    source=job_dict['source'],
                    date_posted=job_dict['date_posted']
                )
                scraped_jobs.append(job)
                next_job_id += 1
                
            # Combine sample and scraped jobs for display
            all_jobs = scraped_jobs
            
            # If no jobs were found, show a message
            if not all_jobs:
                flash("No jobs found matching your criteria. Try broadening your search.", "info")
                return render_template('jobs.html', jobs=jobs_list, searched=True)
                
            return render_template('jobs.html', jobs=all_jobs, searched=True)
            
        except Exception as e:
            logger.error(f"Error searching for jobs: {str(e)}")
            flash("An error occurred while searching for jobs. Please try again.", "danger")
            return render_template('jobs.html', jobs=jobs_list)
    
    # If no search parameters, show sample jobs
    return render_template('jobs.html', jobs=jobs_list)
    
@app.route('/api/search-jobs', methods=['POST'])
@login_required
def search_jobs_api():
    """API endpoint for job searches"""
    try:
        # Get search parameters from JSON request
        data = request.json
        keywords = data.get('keywords', '')
        location = data.get('location', '')
        job_type = data.get('job_type', 'full-time')
        
        # Search for jobs on USAJobs
        usajobs_results = job_scraper.scrape_usajobs(keywords, location, job_type)
        
        # Return the results
        return jsonify({
            'success': True,
            'jobs': usajobs_results,
            'count': len(usajobs_results)
        })
        
    except Exception as e:
        logger.error(f"Error in job search API: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/logout')
def logout():
    # Logout functionality
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Placeholder routes for other pages
@app.route('/resume')
@login_required
def resume():
    return render_template('resume.html')

@app.route('/optimize_resume/<int:job_id>')
@login_required
def optimize_resume(job_id):
    # Find the job by id
    job = next((j for j in jobs_list if j.id == job_id), None)
    if not job:
        flash('Job not found', 'danger')
        return redirect(url_for('jobs'))
    return render_template('optimize_resume.html', job=job)

@app.route('/optimize-resume/<int:job_id>', methods=['POST'])
@login_required
def optimize_resume_api(job_id):
    # Simulate API response for resume optimization
    from flask import jsonify
    import time
    
    # Add a small delay to simulate processing
    time.sleep(1)
    
    # Mock optimization response
    sample_changes = [
        "Added keyword 'Python' to skills section",
        "Highlighted experience with data analysis",
        "Removed irrelevant experience from previous job"
    ]
    
    sample_resume = """
# John Doe
john.doe@example.com | (555) 123-4567 | San Francisco, CA

## Professional Summary
Experienced software engineer with a focus on building scalable applications and user-friendly interfaces.

## Skills
- Programming Languages: Python, JavaScript, TypeScript
- Frameworks: React, Django, Flask
- Tools: Git, Docker, AWS
- Other: Data Analysis, Machine Learning basics

## Experience
**Senior Software Engineer | Tech Company Inc.**
*2020 - Present*
- Developed and maintained web applications using React and Django
- Implemented data processing pipelines using Python
- Mentored junior engineers and led code reviews

**Software Engineer | Startup XYZ**
*2017 - 2020*
- Built responsive frontend interfaces with React
- Created REST APIs with Flask and SQLAlchemy
- Deployed applications to AWS using Docker
    """
    
    return jsonify({
        'success': True,
        'changes': sample_changes,
        'optimized_resume': sample_resume
    })

@app.route('/apply-optimization', methods=['POST'])
@login_required
def apply_optimization():
    # Simple handler for applying optimizations
    from flask import jsonify, request
    
    # In a real app, we would save the optimized resume here
    data = request.json
    
    # Just return success for this mock implementation
    return jsonify({
        'success': True,
        'message': 'Resume updated successfully'
    })

@app.route('/applications')
@login_required
def applications():
    return render_template('applications.html', applications=[])

def open_browser():
    """Open browser automatically after a short delay"""
    time.sleep(1.5)
    port = int(os.environ.get('FLASK_RUN_PORT', 9090))
    url = f"http://localhost:{port}"
    webbrowser.open(url)
    print(f"Opening browser at {url}")

if __name__ == '__main__':
    # Add a test user
    users[0] = User(
        id=0,
        username='testuser',
        email='test@example.com',
        password_hash=generate_password_hash('password')
    )
    
    # Start browser thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("Starting minimal JobHunterAI application...")
    print("Test user created: email=test@example.com, password=password")
    
    # Get port from environment variable or use default
    port = int(os.environ.get('FLASK_RUN_PORT', 9090))
    print(f"Starting server on port {port}")
    app.run(host='127.0.0.1', port=port, debug=True)
