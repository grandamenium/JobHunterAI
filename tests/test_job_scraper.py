import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import logging
import requests
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.job_scraper import JobScraperAgent

# Setup test logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestJobScraper(unittest.TestCase):
    """Test cases for the JobScraperAgent class"""

    def setUp(self):
        """Set up the test environment"""
        self.scraper = JobScraperAgent()

    def test_initialization(self):
        """Test that the JobScraperAgent is initialized correctly"""
        self.assertIsNotNone(self.scraper.logger)

    @patch('requests.get')
    def test_usajobs_scraper_response_handling(self, mock_get):
        """Test that the scraper handles responses from USAJobs correctly"""
        # Setup the mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Sample HTML response</body></html>"
        mock_get.return_value = mock_response

        # Test the scraper with basic parameters
        result = self.scraper.scrape_usajobs("software", "new york")
        
        # Assert that requests.get was called with the expected URL
        mock_get.assert_called_once()
        call_args = mock_get.call_args[0][0]
        
        self.assertIn("usajobs.gov", call_args)
        self.assertIn("k=software", call_args)
        self.assertIn("l=new+york", call_args)
        
        # It's an empty result because our mock HTML doesn't contain job listings
        self.assertEqual(len(result), 0)

    @patch('requests.get')
    def test_usajobs_error_handling(self, mock_get):
        """Test how the scraper handles errors"""
        # Test connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection error")
        result = self.scraper.scrape_usajobs("developer", "remote")
        self.assertEqual(len(result), 0)  # Should return empty list on error
        
        # Test bad status code
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.side_effect = None
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_usajobs("developer", "remote")
        self.assertEqual(len(result), 0)  # Should return empty list on error

    @patch('requests.get')
    def test_usajobs_job_parsing(self, mock_get):
        """Test the job parsing functionality with a simulated response"""
        # Create a mock response with a sample job listing structure
        html_content = """
        <html>
        <body>
            <div class="usajobs-search-result--core">
                <div class="usajobs-search-result__title">
                    <a href="/job/123456">Software Engineer</a>
                </div>
                <div class="usajobs-search-result__department">Department of Defense</div>
                <div class="usajobs-search-result__location">Washington, DC</div>
                <div class="usajobs-search-result__body">
                    Develop software applications for military systems.
                </div>
            </div>
            <div class="usajobs-search-result--core">
                <div class="usajobs-search-result__title">
                    <a href="/job/789012">Data Scientist</a>
                </div>
                <div class="usajobs-search-result__department">NASA</div>
                <div class="usajobs-search-result__location">Houston, TX</div>
                <div class="usajobs-search-result__body">
                    Analyze space mission data and develop predictive models.
                </div>
            </div>
        </body>
        </html>
        """
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html_content
        mock_get.return_value = mock_response
        
        # Run the scraper
        result = self.scraper.scrape_usajobs("engineer", "washington")
        
        # Verify the parsed results
        self.assertEqual(len(result), 2)
        
        # Check the first job
        first_job = result[0]
        self.assertEqual(first_job['title'], "Software Engineer")
        self.assertEqual(first_job['company'], "Department of Defense")
        self.assertEqual(first_job['location'], "Washington, DC")
        self.assertIn("military systems", first_job['description'])
        self.assertEqual(first_job['url'], "https://www.usajobs.gov/job/123456")
        self.assertEqual(first_job['source'], "USAJobs.gov")
        
        # Check the second job
        second_job = result[1]
        self.assertEqual(second_job['title'], "Data Scientist")
        self.assertEqual(second_job['company'], "NASA")
        self.assertEqual(second_job['location'], "Houston, TX")
        
    def test_live_usajobs_connection(self):
        """Test a real connection to USAJobs (skip in CI environment)"""
        # Skip this test if running in a CI environment
        if os.environ.get('CI') == 'true':
            self.skipTest("Skipping live API test in CI environment")
            
        # Perform a live test with minimal parameters
        result = self.scraper.scrape_usajobs("developer", "")
        
        # Just verify we got a response, don't validate the content
        self.assertIsInstance(result, list)
        
        # Log the number of results
        logger.info(f"Live USAJobs API returned {len(result)} results")
        
        # If results exist, check the structure of the first job
        if result and len(result) > 0:
            job = result[0]
            required_keys = ['title', 'company', 'location', 'description', 'url']
            for key in required_keys:
                self.assertIn(key, job)
                self.assertIsNotNone(job[key])

if __name__ == '__main__':
    unittest.main()