from datetime import datetime, timedelta
from app import db
from models import JobApplication

class ApplicationTracker:
    def __init__(self):
        self.follow_up_interval = 7  # days

    def track_application(self, user_id, job_id, status="applied"):
        """Create or update application tracking record"""
        application = JobApplication(
            user_id=user_id,
            job_id=job_id,
            status=status,
            applied_date=datetime.utcnow(),
            follow_up_date=datetime.utcnow() + timedelta(days=self.follow_up_interval)
        )
        
        try:
            db.session.add(application)
            db.session.commit()
            return True, "Application tracked successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to track application: {str(e)}"

    def update_status(self, application_id, new_status, notes=None):
        """Update application status and notes"""
        try:
            application = JobApplication.query.get(application_id)
            if application:
                application.status = new_status
                if notes:
                    application.notes = notes
                db.session.commit()
                return True, "Status updated successfully"
            return False, "Application not found"
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to update status: {str(e)}"

    def get_follow_ups_needed(self):
        """Get applications that need follow-up"""
        today = datetime.utcnow()
        return JobApplication.query.filter(
            JobApplication.follow_up_date <= today,
            JobApplication.status.in_(['applied', 'interviewing'])
        ).all()
