import logging
from flask import render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import io
from app import app, db
from models import User, Job, JobApplication
from agents.job_scraper import JobScraperAgent
from agents.resume_optimizer import ResumeOptimizerAgent
from agents.cover_letter_generator import CoverLetterGenerator
from agents.application_submitter import ApplicationSubmitter
from agents.application_tracker import ApplicationTracker
import json

# Initialize agents
job_scraper = JobScraperAgent()
resume_optimizer = ResumeOptimizerAgent()
cover_letter_generator = CoverLetterGenerator()
application_submitter = ApplicationSubmitter()
application_tracker = ApplicationTracker()

# Initialize sample jobs within app context - do this after app is running
# This will be called later in a more controlled way

ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # If user is logged in, redirect to jobs page
    if current_user.is_authenticated:
        return redirect(url_for('jobs'))
    return render_template('index.html')

@app.route('/jobs')
@login_required
def jobs():
    # Get all jobs regardless of resume status
    try:
        jobs = Job.query.all()
        logging.info(f"Retrieved {len(jobs)} jobs for user {current_user.username}")
        
        # Only show the upload resume message if they want to search for jobs
        if request.args.get('search') and not current_user.resume_filename:
            flash('Please upload your resume before searching for jobs', 'warning')
            return redirect(url_for('resume'))
            
        return render_template('jobs.html', jobs=jobs)
    except Exception as e:
        logging.error(f"Error retrieving jobs: {str(e)}")
        flash('Error loading jobs. Please try again.', 'danger')
        return render_template('jobs.html', jobs=[])

@app.route('/search-jobs')
@login_required
def search_jobs():
    if not current_user.resume_filename:
        flash('Please upload your resume before searching for jobs', 'warning')
        return redirect(url_for('resume'))

    keywords = request.args.get('keywords', '').strip()
    location = request.args.get('location', '').strip()
    job_type = request.args.get('job-type', '')

    if not keywords and not location:
        flash('Please enter keywords or location to search for jobs', 'info')
        return render_template('jobs.html', jobs=[])

    logging.info(f"Starting job search - Keywords: {keywords}, Location: {location}, Type: {job_type}")

    jobs = job_scraper.scrape_jobs(keywords, location)
    if not jobs:
        flash('No jobs found. Try different keywords or location.', 'info')
        return render_template('jobs.html', jobs=[])

    preferences = {'title': keywords, 'location': location}
    filtered_jobs = job_scraper.filter_jobs(jobs, preferences)

    logging.info(f"Found {len(filtered_jobs)} matching jobs")
    return render_template('jobs.html', jobs=filtered_jobs)

@app.route('/resume', methods=['GET', 'POST'])
@login_required
def resume():
    if request.method == 'POST':
        if 'resume-file' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(request.url)

        file = request.files['resume-file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload PDF or DOCX files only.', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                file_data = file.read()

                if len(file_data) > MAX_FILE_SIZE:
                    flash('File size too large. Maximum size is 5MB.', 'danger')
                    return redirect(request.url)

                # Store the raw file content
                current_user.resume_file = file_data
                current_user.resume_filename = filename
                current_user.resume_content_type = file.content_type

                # Store the text content
                file.seek(0)  # Reset file pointer
                text_content = file.read().decode('utf-8', errors='ignore')
                current_user.resume_text = text_content

                db.session.commit()

                flash('Resume uploaded successfully!', 'success')
                return redirect(url_for('jobs'))
            except Exception as e:
                logging.error(f"Error uploading resume: {str(e)}")
                flash('Error uploading resume. Please try again.', 'danger')
                return redirect(request.url)

    return render_template('resume.html')

@app.route('/download-resume')
@login_required
def download_resume():
    if not current_user.resume_file:
        flash('No resume found', 'danger')
        return redirect(url_for('resume'))

    return send_file(
        io.BytesIO(current_user.resume_file),
        mimetype=current_user.resume_content_type,
        as_attachment=True,
        download_name=current_user.resume_filename
    )

@app.route('/optimize-resume/<int:job_id>', methods=['GET', 'POST'])
@login_required
def optimize_resume(job_id):
    job = Job.query.get_or_404(job_id)

    if request.method == 'GET':
        return render_template('optimize_resume.html', job=job)

    try:
        if not current_user.resume_text:
            logging.warning("No resume text found for user")
            return jsonify({
                'success': False,
                'message': 'Please upload your resume first'
            })

        # Get optimization suggestions from GPT
        logging.info(f"Starting resume optimization for job {job_id}")
        optimization_result = resume_optimizer.optimize_resume(
            current_user.resume_text,
            job.description
        )

        if optimization_result and 'optimized_resume' in optimization_result:
            logging.info("Resume optimization successful")
            return jsonify({
                'success': True,
                'optimized_resume': optimization_result['optimized_resume'],
                'changes': optimization_result['changes_made']
            })
        else:
            logging.error("Invalid optimization result format")
            return jsonify({
                'success': False,
                'message': 'Failed to optimize resume'
            })

    except Exception as e:
        logging.error(f"Error in resume optimization: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/apply-optimization', methods=['POST'])
@login_required
def apply_optimization():
    try:
        optimized_resume = request.json.get('optimized_resume')
        if optimized_resume:
            current_user.resume_text = optimized_resume
            db.session.commit()
            logging.info("Successfully applied resume optimization")
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'No optimized resume provided'})
    except Exception as e:
        logging.error(f"Error applying optimization: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/applications')
@login_required
def applications():
    user_applications = JobApplication.query.filter_by(user_id=current_user.id).all()
    return render_template('applications.html', applications=user_applications)

@app.route('/apply-job/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)

    try:
        # Generate cover letter
        cover_letter_result = cover_letter_generator.generate_cover_letter(
            job.description, 
            current_user.resume_text,
            job.company
        )

        # Parse the JSON string if needed
        if isinstance(cover_letter_result, str):
            cover_letter_data = json.loads(cover_letter_result)
            cover_letter = cover_letter_data.get('cover_letter', '')
        else:
            cover_letter = cover_letter_result.get('cover_letter', '')

        # Submit application
        success, message = application_submitter.submit_application(
            job,
            current_user.resume_text,
            cover_letter,
            current_user.email
        )

        if success:
            # Track the application
            application_tracker.track_application(current_user.id, job_id)
            return jsonify({'success': True})

        return jsonify({'success': False, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/update-application/<int:application_id>', methods=['POST'])
@login_required
def update_application(application_id):
    status = request.form.get('status')
    notes = request.form.get('notes')

    success, message = application_tracker.update_status(application_id, status, notes)
    return jsonify({'success': success, 'message': message})

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate inputs
        if not email or not password:
            flash('Email and password are required', 'danger')
            return render_template('login.html')

        # Log attempt for debugging
        logger = logging.getLogger(__name__)
        logger.info(f"Login attempt for email: {email}")
        
        try:
            logger.debug(f"Querying database for user with email: {email}")
            user = User.query.filter_by(email=email).first()
            
            # Log user query result
            if user:
                logger.debug(f"Found user: {user.username} (ID: {user.id})")
                
                # Verify password
                if check_password_hash(user.password_hash, password):
                    logger.debug(f"Password correct for user: {user.username}")
                    
                    # Log in the user
                    login_user(user)
                    logger.info(f"User {user.username} (ID: {user.id}) logged in successfully")
                    
                    # Redirect to jobs page if they were trying to access it
                    next_page = request.args.get('next')
                    if next_page and next_page.startswith('/jobs'):
                        return redirect(next_page)
                    return redirect(url_for('jobs'))
                else:
                    logger.warning(f"Incorrect password for user: {user.username}")
                    flash('Invalid email or password', 'danger')
            else:
                logger.warning(f"Login attempt for non-existent user: {email}")
                flash('Invalid email or password', 'danger')
                
        except Exception as e:
            logger.error(f"Error during login: {str(e)}", exc_info=True)
            flash(f'Login error: {str(e)}', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate inputs
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
            
        # Log registration attempt with detailed info
        logger = logging.getLogger(__name__)
        logger.info(f"Registration attempt for email: {email}, username: {username}")

        try:
            # Check for existing email
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                logger.warning(f"Registration failed: Email {email} already exists")
                flash('Email already registered', 'danger')
                return render_template('register.html')
            
            # Check for existing username
            existing_username = User.query.filter_by(username=username).first()
            if existing_username:
                logger.warning(f"Registration failed: Username {username} already exists")
                flash('Username already taken', 'danger')
                return render_template('register.html')

            # Create new user
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            
            # Add and commit to database
            logger.debug(f"Adding new user to database: {username}, {email}")
            db.session.add(user)
            db.session.commit()
            
            # Get the user ID after commit
            user_id = user.id
            logger.info(f"User registered successfully: {username}, {email}, ID: {user_id}")
            
            # Automatically log in the new user
            logger.debug(f"Attempting to log in newly registered user: {username}")
            login_user(user)
            
            flash('Registration successful! Welcome to JobHunterAI!', 'success')
            return redirect(url_for('jobs'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration: {str(e)}", exc_info=True)
            flash(f'Registration error: {str(e)}', 'danger')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.template_filter('status_color')
def status_color(status):
    colors = {
        'applied': 'primary',
        'interviewing': 'info',
        'offered': 'success',
        'rejected': 'danger'
    }
    return colors.get(status, 'secondary')