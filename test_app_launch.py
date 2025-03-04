"""
Test script to verify that the JobHunterAI app opens correctly in a browser.
"""
import unittest
import os
import sys
import subprocess
import time
import requests
import signal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppLaunchTest(unittest.TestCase):
    """Test that the app can be launched and responds to HTTP requests."""
    
    def setUp(self):
        """Set up the test environment."""
        # Make sure we're testing against a clean environment
        if "OPENAI_API_KEY" in os.environ:
            self.original_api_key = os.environ["OPENAI_API_KEY"]
        else:
            self.original_api_key = None
        
        # Set a dummy API key for testing
        os.environ["OPENAI_API_KEY"] = "test-key-for-unittest"
        
        # Path to the main.py file
        self.main_script = os.path.join(os.path.dirname(__file__), "main.py")
        self.process = None
    
    def tearDown(self):
        """Clean up after the test."""
        # Restore the original API key
        if self.original_api_key is not None:
            os.environ["OPENAI_API_KEY"] = self.original_api_key
        else:
            del os.environ["OPENAI_API_KEY"]
        
        # Terminate the Flask process if it's still running
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            logger.info("Process terminated")
    
    def test_app_launches_and_responds(self):
        """Test that the app launches and responds to HTTP requests."""
        # Start the Flask app process but suppress browser opening
        env = os.environ.copy()
        env["FLASK_APP"] = "app.py"
        env["FLASK_ENV"] = "testing"
        env["NO_BROWSER"] = "1"  # Custom env var to prevent browser launch in our test
        
        # Launch the app in a subprocess
        logger.info("Starting Flask app")
        self.process = subprocess.Popen(
            [sys.executable, "app.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give the server time to start
        time.sleep(2)
        
        # Try to connect to the server
        try:
            logger.info("Testing connection to server")
            response = requests.get("http://localhost:5000", timeout=5)
            
            # Verify the server responds with a success status code
            self.assertEqual(response.status_code, 200)
            logger.info("App successfully responded with status code 200")
            
            # Check if the response contains expected content
            self.assertIn("JobHunterAI", response.text)
            logger.info("Response contains expected content")
            
        except requests.RequestException as e:
            # If we can't connect, the test fails
            self.fail(f"Failed to connect to the Flask app: {e}")

if __name__ == "__main__":
    unittest.main()