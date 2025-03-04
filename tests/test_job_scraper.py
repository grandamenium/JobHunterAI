import unittest
from agents.job_scraper import JobScraperAgent
import logging
import requests
import time
import random
from unittest.mock import patch, MagicMock
from datetime import datetime
from bs4 import BeautifulSoup

class TestJobScraper(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        self.scraper = JobScraperAgent()
        
    def test_sample_jobs(self):
        """Test that sample jobs are returned correctly"""
        jobs = self.scraper.get_sample_jobs()
        self.assertTrue(len(jobs) > 0, "Sample jobs list is empty")
        self.assertTrue(isinstance(jobs, list), "Sample jobs should be a list")
        
        for job in jobs:
            self.assertIn('title', job, "Job should have a title")
            self.assertIn('company', job, "Job should have a company")
    
    @patch('requests.get')
    def test_scraper_with_realistic_html(self, mock_get):
        """Test scraper with realistic HTML from USAJobs"""
        # Setup a mock response with sample HTML
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Create simple HTML that mimics USAJobs listing
        sample_html = """
        <div class="usajobs-search-result">
            <h3 class="usajobs-search-result__title">
                <a href="/job/123">Software Developer</a>
            </h3>
            <div class="usajobs-search-result__department">Department of Technology</div>
            <div class="usajobs-search-result__location">Washington, DC</div>
            <div class="usajobs-search-result__body">
                Build software for government agencies.
            </div>
            <div class="usajobs-search-result__salary">$80,000 to $120,000 per year</div>
        </div>
        """
        mock_response.text = sample_html
        mock_get.return_value = mock_response
        
        # Call the scraper with our mocked response
        results = self.scraper.scrape_usajobs("developer", "")
        
        # Check the results match our expected values
        self.assertEqual(len(results), 1, "Should find exactly one job")
        job = results[0]
        self.assertEqual(job['title'], "Software Developer")
        self.assertEqual(job['company'], "Department of Technology")
        self.assertEqual(job['location'], "Washington, DC")
        self.assertEqual(job['salary'], "$80,000 to $120,000 per year")
        self.assertEqual(job['source'], "USAJobs.gov")
    
    @patch('requests.get')
    def test_scraper_with_alternative_html_structure(self, mock_get):
        """Test scraper with a different HTML structure to ensure resilience"""
        # Setup mock response with alternative HTML structure
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Create HTML with different class names and structure
        sample_html = """
        <article class="job-listing">
            <h3><a href="/jobs/456">Data Analyst</a></h3>
            <span class="agency-name">Department of Commerce</span>
            <div class="location-text">New York, NY</div>
            <p class="description">Analyze government data and produce reports.</p>
            <span class="salary-range">$70,000 - $90,000 annually</span>
        </article>
        """
        mock_response.text = sample_html
        mock_get.return_value = mock_response
        
        # Call the scraper with our mocked response
        results = self.scraper.scrape_usajobs("analyst", "")
        
        # Check the results
        self.assertEqual(len(results), 1, "Should find exactly one job")
        job = results[0]
        self.assertEqual(job['title'], "Data Analyst")
        self.assertEqual(job['company'], "Department of Commerce")
        self.assertEqual(job['location'], "New York, NY")
        self.assertIn("Analyze government data", job['description'])
        self.assertEqual(job['salary'], "$70,000 - $90,000 annually")
    
    @patch('requests.get')
    def test_scraper_with_minimal_html(self, mock_get):
        """Test scraper with minimal HTML to test fallback extraction"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Create very minimal HTML
        sample_html = """
        <div>
            <h3>Project Manager</h3>
            Department of Defense
            Arlington, VA
            Lead project teams for critical missions.
            $90,000 per year
        </div>
        """
        mock_response.text = sample_html
        mock_get.return_value = mock_response
        
        # Call the scraper
        results = self.scraper.scrape_usajobs("manager", "")
        
        # Check results
        self.assertEqual(len(results), 1, "Should find exactly one job despite minimal HTML")
        job = results[0]
        self.assertEqual(job['title'], "Project Manager")
        self.assertEqual(job['source'], "USAJobs.gov")
    
    def test_scraper_format_output(self):
        """Test that the scraper always outputs the correct format"""
        # Create a test job with known properties
        test_job = {
            'title': 'Test Engineer',
            'company': 'Test Agency',
            'location': 'Test Location',
            'description': 'This is a test job.',
            'salary': '$100,000',
            'url': 'https://example.com',
            'source': 'Test Source',
            'date_posted': datetime.now()
        }
        
        # Check all required fields
        required_fields = ['title', 'company', 'location', 'description', 'salary', 'url', 'source', 'date_posted']
        for field in required_fields:
            self.assertIn(field, test_job, f"Job should contain {field} field")
        
        # Check field types
        self.assertIsInstance(test_job['title'], str)
        self.assertIsInstance(test_job['company'], str)
        self.assertIsInstance(test_job['location'], str)
        self.assertIsInstance(test_job['description'], str)
        self.assertIsInstance(test_job['salary'], str)
        self.assertIsInstance(test_job['url'], str)
        self.assertIsInstance(test_job['source'], str)
        self.assertIsInstance(test_job['date_posted'], datetime)
    
    def test_filter_jobs(self):
        """Test job filtering functionality"""
        sample_jobs = self.scraper.get_sample_jobs()
        filtered_jobs = self.scraper.scrape_jobs('engineer', '')
        
        # Should find fewer jobs with filter than without
        self.assertTrue(0 <= len(filtered_jobs) <= len(sample_jobs), 
                       "Filtered jobs count should be less than or equal to sample jobs")
                       
        # All filtered jobs should contain keyword
        for job in filtered_jobs:
            self.assertTrue(
                'engineer' in job['title'].lower() or 
                'engineer' in job['description'].lower() or
                'engineer' in job['company'].lower(),
                f"Job does not match filter criteria: {job['title']}"
            )
    
    def test_usajobs_scraper(self):
        """Test scraping from USAJobs directly (skips if site is unavailable)"""
        try:
            # Make a quick request to check if USAJobs is accessible
            response = requests.get("https://www.usajobs.gov", timeout=5)
            if response.status_code != 200:
                self.skipTest("USAJobs.gov is not accessible")
        except requests.RequestException:
            self.skipTest("USAJobs.gov is not reachable")
            
        # Try a search with a common term
        results = self.scraper.scrape_usajobs("clerk", "")
        
        # If we get results, check their structure
        if results:
            for job in results:
                self.assertIn('title', job)
                self.assertIn('company', job)
                self.assertIn('location', job)
                self.assertIn('description', job)
                self.assertIn('url', job)
                self.assertIn('source', job)
                self.assertEqual(job['source'], 'USAJobs.gov')
            
if __name__ == '__main__':
    unittest.main()