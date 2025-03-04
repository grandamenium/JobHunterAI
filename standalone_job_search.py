#!/usr/bin/env python
"""
Standalone Job Search Application for JobHunterAI
"""
import webbrowser
import threading
import time
import logging
import os
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.usajobs.gov/'
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
            
            # USAJobs may have updated their class names, try different selectors
            # Each job is in a div with either class 'usajobs-search-result--core' or similar
            job_divs = soup.select('.usajobs-search-result--core, .usajobs-search-result, article.usajobs-search-result')
            
            # If we didn't find any jobs with the selectors, try looking for article tags
            if not job_divs:
                job_divs = soup.select('article')
            
            for job_div in job_divs:
                try:
                    # Extract job details - try multiple selectors to handle different HTML structures
                    # Title selectors
                    title_elem = (
                        job_div.select_one('.usajobs-search-result__title a') or
                        job_div.select_one('h3.usajobs-search-result__title a') or
                        job_div.select_one('h3 a') or
                        job_div.select_one('a[data-test="job-title"]') or
                        job_div.select_one('a.usa-link')
                    )
                    
                    # Company selectors
                    company_elem = (
                        job_div.select_one('.usajobs-search-result__department') or
                        job_div.select_one('.agency') or
                        job_div.select_one('.department') or
                        job_div.select_one('[data-test="agency-name"]') or
                        job_div.select_one('div.usajobs-search-result__header span')
                    )
                    
                    # Location selectors
                    location_elem = (
                        job_div.select_one('.usajobs-search-result__location') or
                        job_div.select_one('.location') or
                        job_div.select_one('[data-test="location"]') or
                        job_div.select_one('div[itemprop="jobLocation"]')
                    )
                    
                    # Skip if essential elements are missing
                    if not title_elem:
                        self.logger.warning(f"Skipping job: unable to find title element")
                        continue
                        
                    # Get job title and URL
                    title = title_elem.text.strip()
                    # Handle different URL formats
                    if title_elem.has_attr('href'):
                        href = title_elem['href']
                        if href.startswith('http'):
                            job_url = href
                        else:
                            job_url = "https://www.usajobs.gov" + href
                    else:
                        job_url = "https://www.usajobs.gov/Search/Results"
                    
                    # Get company/agency
                    company = company_elem.text.strip() if company_elem else "Unknown Agency"
                    
                    # Get location
                    location = location_elem.text.strip() if location_elem else "Various Locations"
                    
                    # Try to get description snippet with multiple selectors
                    description_elem = (
                        job_div.select_one('.usajobs-search-result__body') or
                        job_div.select_one('.summary') or
                        job_div.select_one('[data-test="job-description"]') or
                        job_div.select_one('div[itemprop="description"]') or
                        job_div.select_one('p.usa-prose')
                    )
                    description = description_elem.text.strip() if description_elem else "No description available."
                    
                    # Extract salary information if available - try multiple selectors
                    salary_elem = (
                        job_div.select_one('.usajobs-search-result__salary') or
                        job_div.select_one('.salary') or
                        job_div.select_one('[data-test="salary"]') or
                        job_div.select_one('div[itemprop="baseSalary"]') or
                        job_div.select_one('div.salary')
                    )
                    salary = salary_elem.text.strip() if salary_elem else "Salary not specified"
                    
                    # Create job dictionary
                    job = {
                        'title': title,
                        'company': company,
                        'location': location,
                        'description': description,
                        'salary': salary,
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
    def __init__(self, id, title, company, location, description, url="", source="Sample", date_posted=None, salary="Salary not specified"):
        self.id = id
        self.title = title
        self.company = company
        self.location = location
        self.description = description
        self.url = url
        self.source = source
        self.date_posted = date_posted or datetime.utcnow()
        self.salary = salary

# Store scraped jobs
scraped_jobs = []
next_job_id = 4  # Start after the sample jobs

# Sample job listings
jobs_list = [
    Job(1, "Software Engineer", "Google", "Mountain View, CA", "Build amazing software.", 
        url="https://careers.google.com/sample/1", source="Sample Data", salary="$120,000 - $180,000 per year"),
    Job(2, "Data Scientist", "Microsoft", "Redmond, WA", "Work with big data.",
        url="https://careers.microsoft.com/sample/2", source="Sample Data", salary="$130,000 - $190,000 per year"),
    Job(3, "Frontend Developer", "Meta", "Menlo Park, CA", "Create user interfaces.",
        url="https://careers.meta.com/sample/3", source="Sample Data", salary="$110,000 - $170,000 per year")
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
    
    try:
        # Clear previous scraped jobs
        global scraped_jobs, next_job_id
        scraped_jobs = []
        
        # If no search parameters, use default searches that should return results
        if not keywords and not location:
            # Use a list of guaranteed popular jobs that exist on USAJobs frequently
            default_searches = [
                {"keywords": "analyst", "location": ""},             # Very common job title
                {"keywords": "assistant", "location": ""},           # Very common job title
                {"keywords": "specialist", "location": ""},          # Very common job title
                {"keywords": "technician", "location": ""},          # Common technical job
                {"keywords": "administrator", "location": ""},       # Common admin job
                {"keywords": "clerk", "location": ""},               # Very common entry-level
                {"keywords": "coordinator", "location": ""},         # Common job title
                {"keywords": "program", "location": ""},             # Matches program manager/analyst
                {"keywords": "IT ", "location": ""},                 # IT positions (note space to avoid matching "position")
                {"keywords": "nursing", "location": ""},             # Healthcare positions
                {"keywords": "security", "location": ""}             # Security positions
            ]
            
            # Also try some location-specific searches if keyword searches fail
            location_searches = [
                {"keywords": "", "location": "Washington DC"},      # DC has many federal jobs
                {"keywords": "", "location": "Arlington VA"},       # VA has many federal jobs
                {"keywords": "", "location": "Remote"}              # Remote jobs
            ]
            
            # First try keyword-based searches
            usajobs_results = []
            for search in default_searches:
                # Try each default search until we get some results
                logger.info(f"Trying default search - Keywords: {search['keywords']}, Location: {search['location']}")
                results = job_scraper.scrape_usajobs(search['keywords'], search['location'], job_type)
                if results and len(results) > 0:
                    logger.info(f"Found {len(results)} jobs with default search")
                    usajobs_results = results
                    break
                # Small delay to avoid rate limiting
                time.sleep(0.5)
            
            # If all keyword searches failed, try location-based searches
            if not usajobs_results:
                logger.info("Keyword searches failed, trying location-based searches")
                for search in location_searches:
                    logger.info(f"Trying location search - Location: {search['location']}")
                    results = job_scraper.scrape_usajobs(search['keywords'], search['location'], job_type)
                    if results and len(results) > 0:
                        logger.info(f"Found {len(results)} jobs with location search")
                        usajobs_results = results
                        break
                    # Small delay to avoid rate limiting
                    time.sleep(0.5)
            
            # If all searches failed, try one final broad search
            if not usajobs_results:
                logger.info("Trying generic searches")
                # Try a few very basic terms that should always return results
                for term in ["job", "position", "vacancy", "career", "work"]:
                    results = job_scraper.scrape_usajobs(term, "", job_type)
                    if results and len(results) > 0:
                        logger.info(f"Found {len(results)} jobs with generic '{term}' search")
                        usajobs_results = results
                        break
                    # Small delay to avoid rate limiting
                    time.sleep(0.5)
                    
                # If absolutely everything failed, fall back to sample data
                if not usajobs_results:
                    logger.info("All searches failed, using sample data")
                    usajobs_results = job_scraper.get_sample_jobs()
        else:
            # User provided search parameters
            logger.info(f"Searching jobs - Keywords: {keywords}, Location: {location}, Type: {job_type}")
            usajobs_results = job_scraper.scrape_usajobs(keywords, location, job_type)
            
            # If no USAJobs results, try multiple alternative approaches
            if not usajobs_results:
                logger.info("No USAJobs results, trying alternative searches")
                
                # 1. Try without location constraint if one was provided
                if location:
                    logger.info(f"Trying search without location - Keywords: {keywords}")
                    usajobs_results = job_scraper.scrape_usajobs(keywords, "", job_type)
                
                # 2. Try with broader keyword if specific keywords were provided
                if not usajobs_results and keywords and len(keywords) > 3:
                    # Get the first word of the keywords as a more general search
                    broader_term = keywords.split()[0]
                    if broader_term != keywords:
                        logger.info(f"Trying broader search term: {broader_term}")
                        usajobs_results = job_scraper.scrape_usajobs(broader_term, "", job_type)
                
                # 3. Try with similar/related keywords
                if not usajobs_results and keywords:
                    # Map of related job titles to try
                    related_terms = {
                        "engineer": ["engineering", "developer", "technical"],
                        "developer": ["engineer", "programmer", "software"],
                        "manager": ["director", "supervisor", "lead"],
                        "analyst": ["specialist", "consultant", "researcher"],
                        "assistant": ["aide", "support", "coordinator"],
                        "administrator": ["manager", "specialist", "coordinator"]
                    }
                    
                    # Check if any word in the keywords matches our related terms
                    for word in keywords.lower().split():
                        if word in related_terms:
                            for related in related_terms[word]:
                                logger.info(f"Trying related search term: {related}")
                                related_results = job_scraper.scrape_usajobs(related, "", job_type)
                                if related_results:
                                    usajobs_results = related_results
                                    break
                            if usajobs_results:
                                break
                
                # 4. If still no results, fall back to sample data with filtering
                if not usajobs_results:
                    logger.info("All alternative searches failed, falling back to sample data")
                    sample_data = job_scraper.get_sample_jobs()
                    
                    # For sample data, apply fuzzy matching to keywords
                    for job_dict in sample_data:
                        # More flexible keyword matching
                        keyword_match = True  # Default true if no keywords provided
                        if keywords:
                            # Break keywords into parts and check if ANY part matches
                            keyword_parts = keywords.lower().split()
                            keyword_match = any(
                                part in job_dict['title'].lower() or
                                part in job_dict['description'].lower() or
                                part in job_dict['company'].lower()
                                for part in keyword_parts
                            )
                        
                        # Location matching (unchanged)
                        location_match = not location or (
                            location.lower() in job_dict['location'].lower() or
                            location.lower() in job_dict['company'].lower()
                        )
                        
                        if keyword_match and location_match:
                            usajobs_results.append(job_dict)
        
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
                date_posted=job_dict['date_posted'],
                salary=job_dict.get('salary', 'Salary not specified')
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
    port = int(os.environ.get('FLASK_RUN_PORT', 9091))  # Get port from environment or default
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
    
    # Get port from environment variable or use default
    port = int(os.environ.get('FLASK_RUN_PORT', 9091))
    logger.info(f"Starting server on port {port}")
    app.run(host='127.0.0.1', port=port, debug=True)