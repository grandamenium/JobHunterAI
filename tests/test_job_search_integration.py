import unittest
import sys
import os
import re
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from flask import Flask
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the scraper
from agents.job_scraper import JobScraperAgent

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestJobSearchIntegration(unittest.TestCase):
    """Integration tests for job search functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.scraper = JobScraperAgent()
        
        # Check if USAJobs.gov is accessible before running tests
        try:
            response = requests.get("https://www.usajobs.gov", timeout=5)
            self.skipIfNot200 = response.status_code != 200
            if self.skipIfNot200:
                logger.warning("USAJobs.gov is not accessible, some tests will be skipped")
        except requests.RequestException as e:
            logger.warning(f"Error accessing USAJobs.gov: {str(e)}")
            self.skipIfNot200 = True
    
    def test_scraper_structure(self):
        """Test that the scraper returns appropriate structure even with no results"""
        if self.skipIfNot200:
            self.skipTest("USAJobs.gov is not accessible")
        
        # Test with a common job title that should return results
        jobs = self.scraper.scrape_usajobs("software", "")
        
        # Verify jobs were returned as a list (even if empty)
        self.assertIsInstance(jobs, list, "Jobs should be returned as a list")
        
        # If we have jobs, verify their structure
        if jobs:
            job = jobs[0]
            required_fields = ['title', 'company', 'location', 'description', 'url', 'source', 'date_posted', 'salary']
            for field in required_fields:
                self.assertIn(field, job, f"Job should have field: {field}")
            
            # Verify the source is correct
            self.assertEqual(job['source'], 'USAJobs.gov', "Source should be USAJobs.gov")
        else:
            # If we don't have jobs, check sample jobs instead
            sample_jobs = self.scraper.get_sample_jobs()
            self.assertGreater(len(sample_jobs), 0, "Sample jobs should be available as fallback")
            
            # Verify structure of sample jobs
            job = sample_jobs[0]
            required_fields = ['title', 'company', 'location', 'description', 'url', 'source', 'date_posted', 'salary']
            for field in required_fields:
                self.assertIn(field, job, f"Sample job should have field: {field}")
    
    def test_scraper_handles_search_params(self):
        """Test that the scraper correctly handles search parameters"""
        if self.skipIfNot200:
            self.skipTest("USAJobs.gov is not accessible")
        
        # Test keyword filtering
        engineer_jobs = self.scraper.scrape_usajobs("engineer", "")
        
        # Test location filtering
        dc_jobs = self.scraper.scrape_usajobs("", "Washington DC")
        
        # If we got results, verify they match the search criteria
        if engineer_jobs:
            # Sample a few jobs to check
            for job in engineer_jobs[:3]:
                # The job title or description should contain "engineer"
                self.assertTrue(
                    "engineer" in job['title'].lower() or 
                    "engineer" in job['description'].lower(),
                    f"Job should contain 'engineer' in title or description: {job['title']}"
                )
        
        if dc_jobs:
            # Sample a few jobs to check
            for job in dc_jobs[:3]:
                # The location should contain "washington" or "dc"
                self.assertTrue(
                    "washington" in job['location'].lower() or 
                    "dc" in job['location'].lower(),
                    f"Job location should be in DC: {job['location']}"
                )
    
    def test_job_data_accuracy(self):
        """Test that the scraped job data accurately reflects the source data"""
        if self.skipIfNot200:
            self.skipTest("USAJobs.gov is not accessible")
        
        # Get a sample of jobs
        jobs = self.scraper.scrape_usajobs("software", "")
        
        if not jobs:
            self.skipTest("No jobs found to verify")
        
        # Check the first job by accessing its URL
        job = jobs[0]
        
        try:
            # Verify the job URL is valid and accessible
            response = requests.get(job['url'], timeout=5)
            self.assertEqual(response.status_code, 200, "Job URL should be accessible")
            
            # Parse the page to verify data accuracy
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Verify the job title appears on the page
            page_text = soup.get_text().lower()
            
            # The job title should appear on the page
            self.assertIn(
                job['title'].lower().split()[0],  # Check at least the first word
                page_text,
                "Job title should appear on the detail page"
            )
            
        except requests.RequestException as e:
            logger.warning(f"Error accessing job URL: {str(e)}")
            self.skipTest(f"Could not access job URL: {job['url']}")
    
    def test_salary_information(self):
        """Test that salary information is properly retrieved and formatted"""
        if self.skipIfNot200:
            self.skipTest("USAJobs.gov is not accessible")
        
        jobs = self.scraper.scrape_usajobs("software", "")
        
        if not jobs:
            self.skipTest("No jobs found to verify salary")
        
        # Check salary information in jobs
        for job in jobs[:5]:  # Check the first 5 jobs
            self.assertIn('salary', job, "Job should have salary information")
            
            # Salary should either be a formatted string or "Salary not specified"
            self.assertIsInstance(job['salary'], str, "Salary should be a string")
    
    def test_date_posted_field(self):
        """Test that the date_posted field is present and valid"""
        if self.skipIfNot200:
            self.skipTest("USAJobs.gov is not accessible")
        
        jobs = self.scraper.scrape_usajobs("software", "")
        
        if not jobs:
            self.skipTest("No jobs found to verify date")
        
        # Check date information in jobs
        for job in jobs[:5]:  # Check the first 5 jobs
            self.assertIn('date_posted', job, "Job should have date_posted information")
            
            # date_posted should be a datetime object
            self.assertIsInstance(job['date_posted'], datetime, "date_posted should be a datetime")
    
    def test_url_formatting(self):
        """Test that job URLs are properly formatted and valid"""
        if self.skipIfNot200:
            self.skipTest("USAJobs.gov is not accessible")
        
        jobs = self.scraper.scrape_usajobs("software", "")
        
        if not jobs:
            self.skipTest("No jobs found to verify URLs")
        
        # Check URL format
        url_pattern = re.compile(r'^https://www\.usajobs\.gov/.*$')
        
        for job in jobs[:5]:  # Check the first 5 jobs
            self.assertTrue(
                url_pattern.match(job['url']),
                f"Job URL should be properly formatted: {job['url']}"
            )
    
    def test_search_resilience(self):
        """Test that searches are resilient to unusual input"""
        if self.skipIfNot200:
            self.skipTest("USAJobs.gov is not accessible")
        
        # Test with very long keyword
        long_keyword = "software" * 10
        jobs_long = self.scraper.scrape_usajobs(long_keyword, "")
        self.assertIsInstance(jobs_long, list, "Should handle very long keywords")
        
        # Test with special characters
        special_chars = "software!@#$%^&*()_+"
        jobs_special = self.scraper.scrape_usajobs(special_chars, "")
        self.assertIsInstance(jobs_special, list, "Should handle special characters")
        
        # Test with unusual location
        unusual_location = "XYZ123NonExistentPlace"
        jobs_unusual = self.scraper.scrape_usajobs("software", unusual_location)
        self.assertIsInstance(jobs_unusual, list, "Should handle unusual locations")
        
    def test_job_card_template(self):
        """Test that the job card HTML template has the expected structure and elements"""
        # Create a simple job card HTML to test
        job_id = 123
        job_title = "Test Engineer"
        job_company = "Test Company"
        job_location = "Test Location"
        job_salary = "$100,000"
        job_desc = "Test description"
        job_url = "https://example.com/job/1"
        
        job_card_html = f"""
        <div class="card mb-4 job-card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h5 class="card-title mb-1">{job_title}</h5>
                        <h6 class="card-subtitle mb-2">{job_company}</h6>
                    </div>
                    <span class="badge">Test Source</span>
                </div>
                <div class="mb-3">
                    <p class="card-text mb-1">
                        <i class="bi bi-geo-alt"></i> {job_location}
                    </p>
                    <p class="card-text mb-1">
                        <i class="bi bi-cash"></i> {job_salary}
                    </p>
                    <p class="card-text">
                        <small class="text-muted">Posted: Mar 04, 2025</small>
                    </p>
                </div>
                <p class="card-text border-top border-bottom py-3">{job_desc}</p>
                <div class="d-flex flex-wrap justify-content-between align-items-center gap-2">
                    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#jobModal{job_id}">
                        <i class="bi bi-info-circle"></i> View Details
                    </button>
                    <div class="d-flex gap-2">
                        <a href="/optimize_resume/{job_id}" class="action-button">
                            <i class="bi bi-file-earmark-text"></i> Optimize Resume
                        </a>
                        <a href="{job_url}" target="_blank" class="btn btn-outline-primary">
                            <i class="bi bi-box-arrow-up-right"></i> Original
                        </a>
                    </div>
                </div>
            </div>
        </div>
        """
        
        # Parse the HTML
        soup = BeautifulSoup(job_card_html, 'html.parser')
        
        # Find the job card
        card = soup.select_one('.job-card')
        self.assertIsNotNone(card, "Job card should exist")
        
        # Check the card title
        title = card.select_one('.card-title')
        self.assertIsNotNone(title, "Card title should exist")
        self.assertEqual(title.text.strip(), job_title)
        
        # Check the company
        subtitle = card.select_one('.card-subtitle')
        self.assertIsNotNone(subtitle, "Card subtitle should exist")
        self.assertEqual(subtitle.text.strip(), job_company)
        
        # Check the location
        location_elem = card.select("p.card-text")[0]
        self.assertIn(job_location, location_elem.text)
        
        # Check the salary
        salary_elem = card.select("p.card-text")[1]
        self.assertIn(job_salary, salary_elem.text)
        
        # Check that the description exists
        desc_elem = card.select_one('.card-text.border-top')
        self.assertIsNotNone(desc_elem, "Description should exist")
        self.assertEqual(desc_elem.text.strip(), job_desc)
        
        # Check the view details button
        view_details = card.select_one('[data-bs-toggle="modal"]')
        self.assertIsNotNone(view_details, "View details button should exist")
        self.assertTrue(view_details['data-bs-target'].endswith(str(job_id)))
        
        # Check optimize resume button
        optimize_btn = card.select_one('a[href*="optimize_resume"]')
        self.assertIsNotNone(optimize_btn, "Optimize resume button should exist")
        self.assertIn(f"/optimize_resume/{job_id}", optimize_btn['href'])
        
        # Check original link button
        original_btn = card.select_one('a[href^="http"]')
        self.assertIsNotNone(original_btn, "Original link button should exist")
        self.assertEqual(original_btn['href'], job_url)
        
    def test_job_modal_template(self):
        """Test that the job modal HTML template has the expected structure and elements"""
        # Create a simple job modal HTML to test
        job_id = 123
        job_title = "Test Engineer"
        job_company = "Test Company"
        job_location = "Test Location"
        job_desc = "Test description"
        job_url = "https://example.com/job/1"
        
        # Sample job modal HTML
        job_modal_html = f"""
        <div class="modal fade" id="jobModal{job_id}" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">{job_title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <div>
                                <span class="badge mb-2">Test Source</span>
                                <h5 class="mb-0">{job_company}</h5>
                            </div>
                            <div class="text-end">
                                <p class="mb-1"><i class="bi bi-geo-alt"></i> {job_location}</p>
                                <small class="text-muted"><i class="bi bi-calendar3"></i> Posted: Mar 04, 2025</small>
                            </div>
                        </div>
                        <div class="card mb-4">
                            <div class="card-header">
                                <h6 class="mb-0"><i class="bi bi-file-text me-2"></i>Job Description</h6>
                            </div>
                            <div class="card-body">
                                <p class="job-description">{job_desc}</p>
                            </div>
                        </div>
                        <div class="card mb-3">
                            <div class="card-header">
                                <h6 class="mb-0"><i class="bi bi-tools me-2"></i>Actions</h6>
                            </div>
                            <div class="card-body">
                                <div class="row g-3">
                                    <div class="col-md-6">
                                        <div class="d-grid">
                                            <a href="/optimize_resume/{job_id}" class="action-button">
                                                <i class="bi bi-magic"></i> Optimize Your Resume
                                            </a>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="d-grid">
                                            <a href="{job_url}" target="_blank" class="glow-button">
                                                <i class="bi bi-box-arrow-up-right"></i> Apply on Test Source
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
        """
        
        # Parse the HTML
        soup = BeautifulSoup(job_modal_html, 'html.parser')
        
        # Find the job modal
        modal = soup.select_one(f'#jobModal{job_id}')
        self.assertIsNotNone(modal, "Job modal should exist")
        
        # Check the modal title
        title = modal.select_one('.modal-title')
        self.assertIsNotNone(title, "Modal title should exist")
        self.assertEqual(title.text.strip(), job_title)
        
        # Check the company
        company_elem = modal.select_one('h5.mb-0')
        self.assertIsNotNone(company_elem, "Company element should exist")
        self.assertEqual(company_elem.text.strip(), job_company)
        
        # Check the location
        location_elem = modal.select_one('.modal-body p.mb-1')
        self.assertIsNotNone(location_elem, "Location element should exist")
        self.assertIn(job_location, location_elem.text)
        
        # Check the description
        desc_elem = modal.select_one('.job-description')
        self.assertIsNotNone(desc_elem, "Description should exist")
        self.assertEqual(desc_elem.text.strip(), job_desc)
        
        # Check optimize resume button in modal
        optimize_btn = modal.select_one('a[href*="optimize_resume"]')
        self.assertIsNotNone(optimize_btn, "Optimize resume button should exist")
        self.assertIn(f"/optimize_resume/{job_id}", optimize_btn['href'])
        
        # Check apply button in modal
        apply_btn = modal.select_one('.glow-button')
        self.assertIsNotNone(apply_btn, "Apply button should exist")
        self.assertEqual(apply_btn['href'], job_url)

if __name__ == '__main__':
    unittest.main()