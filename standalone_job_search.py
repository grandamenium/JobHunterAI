#!/usr/bin/env python
"""
Standalone Job Search Application for JobHunterAI
"""
import webbrowser
import threading
import time
import logging
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'standalone-job-search-key'
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

# Job Scraper implementation
class JobScraperAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_sample_jobs(self):
        """Return sample jobs without database dependencies"""
        self.logger.info("Returning sample jobs")
        
        # Tech industry job samples for variety
        sample_jobs = [
            {
                'title': 'Software Engineer',
                'company': 'Google',
                'location': 'Mountain View, CA',
                'description': 'Design and develop innovative software solutions for Google products. Experience with Python, Java, and large-scale distributed systems required.',
                'url': 'https://careers.google.com/sample/1',
                'source': 'Sample Data',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Data Scientist',
                'company': 'Microsoft',
                'location': 'Redmond, WA',
                'description': 'Analyze large datasets to extract insights and build machine learning models. Strong background in statistics and programming required.',
                'url': 'https://careers.microsoft.com/sample/2',
                'source': 'Sample Data',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Frontend Developer',
                'company': 'Meta',
                'location': 'Menlo Park, CA',
                'description': 'Build engaging user interfaces for Meta products. Expert knowledge of React, JavaScript, and responsive design required.',
                'url': 'https://careers.meta.com/sample/3',
                'source': 'Sample Data',
                'date_posted': datetime.utcnow()
            }
        ]
        
        return sample_jobs
    
    def scrape_jobs(self, keywords, location):
        """Search jobs based on keywords and location"""
        self.logger.info(f"Searching jobs - Keywords: {keywords}, Location: {location}")
        
        # First try to scrape from USAJobs
        jobs_from_api = self.scrape_usajobs(keywords, location)
        
        # If no results, fall back to sample jobs and filter them
        if not jobs_from_api:
            self.logger.info("No jobs from USAJobs, falling back to sample data")
            sample_jobs = self.get_sample_jobs()
            filtered_jobs = []
            
            for job in sample_jobs:
                keyword_match = not keywords or (
                    keywords.lower() in job['title'].lower() or
                    keywords.lower() in job['description'].lower() or
                    keywords.lower() in job['company'].lower()
                )
                
                location_match = not location or (
                    location.lower() in job['location'].lower() or
                    location.lower() in job['company'].lower()
                )
                
                if keyword_match and location_match:
                    filtered_jobs.append(job)
            
            return filtered_jobs
        
        return jobs_from_api
    
    def scrape_usajobs(self, keywords, location, job_type="full-time"):
        """
        Scrape jobs from USAJobs.gov using their search API
        """
        self.logger.info(f"Scraping USAJobs - Keywords: {keywords}, Location: {location}, Type: {job_type}")
        
        try:
            # Format search parameters
            keyword_param = keywords.replace(" ", "+") if keywords else ""
            location_param = location.replace(" ", "+") if location else ""
            
            # Base URL for USA Jobs search
            base_url = "https://www.usajobs.gov/Search/Results"
            
            # Construct search URL - using their URL pattern
            search_url = f"{base_url}?k={keyword_param}&l={location_param}"
            
            # Add job type parameter if specified
            if job_type and job_type != "all":
                if job_type == "full-time":
                    search_url += "&ft=1"  # Full-time parameter
                elif job_type == "part-time":
                    search_url += "&ft=2"  # Part-time parameter
                elif job_type == "internship":
                    search_url += "&hp=student"  # Student/internship parameter
            
            # Make request with appropriate headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            
            response = requests.get(search_url, headers=headers)
            
            # Check response status
            if response.status_code != 200:
                self.logger.error(f"Error scraping USAJobs: Status code {response.status_code}")
                return []
                
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job listings
            job_listings = []
            
            # USAJobs uses a specific structure for job listings
            # Each job is in a div with class 'usajobs-search-result--core'
            job_divs = soup.select('.usajobs-search-result--core')
            
            for job_div in job_divs:
                try:
                    # Extract job details
                    title_elem = job_div.select_one('.usajobs-search-result__title a')
                    company_elem = job_div.select_one('.usajobs-search-result__department')
                    location_elem = job_div.select_one('.usajobs-search-result__location')
                    
                    # Skip if essential elements are missing
                    if not title_elem or not company_elem:
                        continue
                        
                    # Get job title and URL
                    title = title_elem.text.strip()
                    job_url = "https://www.usajobs.gov" + title_elem['href'] if title_elem.has_attr('href') else ""
                    
                    # Get company/agency
                    company = company_elem.text.strip() if company_elem else "Unknown Agency"
                    
                    # Get location
                    location = location_elem.text.strip() if location_elem else "Various Locations"
                    
                    # Try to get description snippet
                    description_elem = job_div.select_one('.usajobs-search-result__body')
                    description = description_elem.text.strip() if description_elem else "No description available."
                    
                    # Create job dictionary
                    job = {
                        'title': title,
                        'company': company,
                        'location': location,
                        'description': description,
                        'url': job_url,
                        'source': 'USAJobs.gov',
                        'date_posted': datetime.utcnow()
                    }
                    
                    job_listings.append(job)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing job listing: {str(e)}")
                    continue
            
            self.logger.info(f"Scraped {len(job_listings)} jobs from USAJobs")
            return job_listings
            
        except Exception as e:
            self.logger.error(f"Error scraping USAJobs: {str(e)}")
            return []
    
    def filter_jobs(self, jobs, preferences):
        """Apply additional filtering if needed - currently returns all jobs as they're pre-filtered"""
        return jobs if jobs else []

# Initialize scraper
job_scraper = JobScraperAgent()

# Define Job class 
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

# Store scraped jobs
scraped_jobs = []
next_job_id = 4  # Start after the sample jobs

# Sample job listings
jobs_list = [
    Job(1, "Software Engineer", "Google", "Mountain View, CA", "Build amazing software.", 
        url="https://careers.google.com/sample/1", source="Sample Data"),
    Job(2, "Data Scientist", "Microsoft", "Redmond, WA", "Work with big data.",
        url="https://careers.microsoft.com/sample/2", source="Sample Data"),
    Job(3, "Frontend Developer", "Meta", "Menlo Park, CA", "Create user interfaces.",
        url="https://careers.meta.com/sample/3", source="Sample Data")
]

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
            logger.info(f"User {user.username} logged in successfully")
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
        
        flash('Registration successful!', 'success')
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
                
            # Use scraped jobs for display
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

@app.route('/optimize_resume/<int:job_id>')
@login_required
def optimize_resume(job_id):
    # Find the job by id
    job = next((j for j in jobs_list + scraped_jobs if j.id == job_id), None)
    if not job:
        flash('Job not found', 'danger')
        return redirect(url_for('jobs'))
    return render_template('optimize_resume.html', job=job)

@app.route('/optimize-resume/<int:job_id>', methods=['POST'])
@login_required
def optimize_resume_api(job_id):
    # Simulate API response for resume optimization
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

@app.route('/resume')
@login_required
def resume():
    return render_template('resume.html')

@app.route('/applications')
@login_required
def applications():
    return render_template('applications.html', applications=[])

def open_browser():
    """Open browser automatically after a short delay"""
    time.sleep(1.5)
    port = 9091  # Make sure this matches the port used for app.run
    url = f"http://localhost:{port}"
    webbrowser.open(url)
    logger.info(f"Opening browser at {url}")

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
    
    logger.info("Starting standalone JobHunterAI job search application...")
    logger.info("Test user created: email=test@example.com, password=password")
    
    # Run the Flask app on a different port
    port = 9091  # Changed from 9090 to avoid conflicts
    app.run(host='127.0.0.1', port=port, debug=True)