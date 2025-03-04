# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()  # Take environment variables from .env file

import logging
import os
import webbrowser
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import app after environment variables are loaded
from app import app

def open_browser():
    """Open browser automatically after a short delay"""
    time.sleep(1.5)  # Slightly longer delay to ensure app is running
    url = "http://localhost:5000"
    try:
        webbrowser.open(url)
        logger.info(f"Opening browser at {url}")
    except Exception as e:
        logger.error(f"Failed to open browser: {str(e)}")

if __name__ == "__main__":
    # Print startup message
    logger.info("Starting JobHunterAI application...")
    logger.info(f"Using OpenAI API key: {'Set' if os.environ.get('OPENAI_API_KEY') else 'Not set'}")
    logger.info(f"Database URL: {os.environ.get('DATABASE_URL', 'sqlite:///instance/job_application_system.db')}")
    
    # Start a thread to open the browser automatically
    # Don't open browser if we're in test mode
    if not os.environ.get("NO_BROWSER"):
        logger.info("Browser auto-launch enabled")
        threading.Thread(target=open_browser, daemon=True).start()
    else:
        logger.info("Browser auto-launch disabled")
    
    # Initialize sample jobs
    from routes import job_scraper
    with app.app_context():
        try:
            job_scraper.initialize_sample_jobs()
            logger.info("Sample jobs initialized")
        except Exception as e:
            logger.error(f"Error initializing sample jobs: {str(e)}")

    # Run the Flask app
    logger.info("Starting Flask server...")
    app.run(host="127.0.0.1", port=5000, debug=True)
