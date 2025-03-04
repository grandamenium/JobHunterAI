import unittest
import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the minimal app directly for testing
import minimal_app as app

# Setup test logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestJobSearchIntegration(unittest.TestCase):
    """Integration tests for job search functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Configure test client
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
        
        # Create a test user
        app.users[100] = app.User(
            id=100,
            username='testuser',
            email='test@example.com',
            password_hash=app.generate_password_hash('password123')
        )
        
    def login(self):
        """Helper method to log in a test user"""
        return self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
    def test_job_page_access(self):
        """Test job page access with and without authentication"""
        # Without login should redirect to login page
        response = self.client.get('/jobs')
        self.assertEqual(response.status_code, 302)  # Redirect status
        
        # Login and then access jobs page
        self.login()
        response = self.client.get('/jobs')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Job Listings', response.data)
        
    @patch('agents.job_scraper.JobScraperAgent.scrape_usajobs')
    def test_job_search_functionality(self, mock_scrape):
        """Test the job search functionality with mocked scraper"""
        # Mock the job scraper to return test data
        mock_scrape.return_value = [{
            'title': 'Test Engineer',
            'company': 'Test Agency',
            'location': 'Test City, XX',
            'description': 'This is a test job description for integration testing.',
            'url': 'https://example.com/job/123',
            'source': 'Test Source',
            'date_posted': app.datetime.utcnow()
        }]
        
        # Login
        self.login()
        
        # Perform a search
        response = self.client.get('/jobs?keywords=engineer&location=test')
        
        # Verify the scraper was called with correct parameters
        mock_scrape.assert_called_once_with('engineer', 'test', 'full-time')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Engineer', response.data)
        self.assertIn(b'Test Agency', response.data)
        self.assertIn(b'Test City, XX', response.data)
        
    @patch('agents.job_scraper.JobScraperAgent.scrape_usajobs')
    def test_empty_search_results(self, mock_scrape):
        """Test search with no results"""
        # Mock scraper to return empty results
        mock_scrape.return_value = []
        
        # Login
        self.login()
        
        # Perform a search
        response = self.client.get('/jobs?keywords=nonexistent&location=nowhere')
        
        # Verify behavior with no results
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No jobs found', response.data)
        
    @patch('agents.job_scraper.JobScraperAgent.scrape_usajobs')
    def test_error_handling(self, mock_scrape):
        """Test error handling in job search"""
        # Mock scraper to raise an exception
        mock_scrape.side_effect = Exception("Test error")
        
        # Login
        self.login()
        
        # Perform a search
        response = self.client.get('/jobs?keywords=error&location=test')
        
        # Verify error handling
        self.assertEqual(response.status_code, 200)
        # Should show flash message and default jobs
        self.assertIn(b'An error occurred', response.data)
        
    def test_api_endpoint(self):
        """Test the job search API endpoint"""
        # Login
        self.login()
        
        # Mock the scraper just within this test
        with patch('agents.job_scraper.JobScraperAgent.scrape_usajobs') as mock_scrape:
            # Setup mock return value
            mock_scrape.return_value = [{
                'title': 'API Test Job',
                'company': 'API Company',
                'location': 'API City',
                'description': 'API test description',
                'url': 'https://example.com/api/job',
                'source': 'API Source',
                'date_posted': app.datetime.utcnow()
            }]
            
            # Call the API
            response = self.client.post('/api/search-jobs', 
                                       json={'keywords': 'api', 'location': 'test'})
            
            # Verify response
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data['success'])
            self.assertEqual(len(data['jobs']), 1)
            self.assertEqual(data['jobs'][0]['title'], 'API Test Job')

if __name__ == '__main__':
    unittest.main()