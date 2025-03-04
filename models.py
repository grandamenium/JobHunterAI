from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    resume_text = db.Column(db.Text)
    resume_file = db.Column(db.LargeBinary)  # For storing the actual file
    resume_filename = db.Column(db.String(128))  # To store original filename
    resume_content_type = db.Column(db.String(64))  # To store file type
    applications = db.relationship('JobApplication', backref='user', lazy=True)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200))
    url = db.Column(db.String(500), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50))
    applicants_count = db.Column(db.Integer)
    contact_info = db.Column(db.String(500))

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    modified_resume = db.Column(db.Text)
    cover_letter = db.Column(db.Text)
    response_received = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)