import logging
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

class JobScraperAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_sample_jobs(self):
        """Return sample jobs without database dependencies"""
        self.logger.info("Returning sample jobs")
        
        # Tech industry job samples for more variety
        sample_jobs = [
            {
                'title': 'Software Engineer',
                'company': 'Google',
                'location': 'Mountain View, CA',
                'description': 'Design and develop innovative software solutions for Google products. Experience with Python, Java, and large-scale distributed systems required.',
                'url': 'https://careers.google.com/sample/1',
                'source': 'Google Careers',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Data Scientist',
                'company': 'Microsoft',
                'location': 'Redmond, WA',
                'description': 'Analyze large datasets to extract insights and build machine learning models. Strong background in statistics and programming required.',
                'url': 'https://careers.microsoft.com/sample/2',
                'source': 'Microsoft Careers',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Frontend Developer',
                'company': 'Meta',
                'location': 'Menlo Park, CA',
                'description': 'Build engaging user interfaces for Meta products. Expert knowledge of React, JavaScript, and responsive design required.',
                'url': 'https://careers.meta.com/sample/3',
                'source': 'Meta Careers',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'DevOps Engineer',
                'company': 'Amazon Web Services',
                'location': 'Seattle, WA',
                'description': 'Design and implement CI/CD pipelines and cloud infrastructure. Experience with AWS services, Docker, and Kubernetes required.',
                'url': 'https://aws.amazon.com/careers/sample/4',
                'source': 'AWS Careers',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Product Manager',
                'company': 'Apple',
                'location': 'Cupertino, CA',
                'description': 'Lead product development from conception to launch. Strong understanding of user experience design and technical requirements needed.',
                'url': 'https://apple.com/careers/sample/5',
                'source': 'Apple Careers',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Neuroscience Research Scientist',
                'company': 'Yale School of Medicine',
                'location': 'New Haven, CT',
                'description': 'Conduct brain imaging studies and analyze neural activity patterns in cognitive processing.',
                'url': 'https://medicine.yale.edu/careers/sample/1',
                'source': 'Yale Careers',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Clinical Neuroscience Fellow',
                'company': 'Yale Medical School',
                'location': 'New Haven, CT',
                'description': 'Fellowship position in clinical neuroscience, focusing on neurological disorders.',
                'url': 'https://medicine.yale.edu/careers/sample/2',
                'source': 'Yale Medicine',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Neurobiology Lab Manager',
                'company': 'Yale University',
                'location': 'New Haven, CT',
                'description': 'Manage research laboratory operations in the Neurobiology department.',
                'url': 'https://medicine.yale.edu/careers/sample/3',
                'source': 'Yale Careers',
                'date_posted': datetime.utcnow()
            }
        ]
        
        self.logger.info(f"Returning {len(sample_jobs)} sample jobs")
        return sample_jobs
        
    def scrape_jobs(self, keywords, location):
        """Search jobs based on keywords and location"""
        self.logger.info(f"Searching jobs - Keywords: {keywords}, Location: {location}")
        
        # For simplified version, just filter the sample jobs
        # This avoids database dependencies
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
        
        if filtered_jobs:
            self.logger.info(f"Found {len(filtered_jobs)} matching jobs")
        else:
            self.logger.info("No matching jobs found")
            
        return filtered_jobs

    def filter_jobs(self, jobs, preferences):
        """Apply additional filtering if needed - currently returns all jobs as they're pre-filtered"""
        return jobs if jobs else []
        
    def scrape_usajobs(self, keywords, location, job_type="full-time"):
        """
        Scrape jobs from USAJobs.gov using their search API
        
        Args:
            keywords (str): Job title, keywords, or agency name
            location (str): City, state, ZIP, or country
            job_type (str): Type of job (full-time, part-time, etc.)
            
        Returns:
            list: List of job dictionaries
        """
        self.logger.info(f"Scraping USAJobs - Keywords: {keywords}, Location: {location}, Type: {job_type}")
        
        try:
            # Format search parameters
            keyword_param = keywords.replace(" ", "+")
            location_param = location.replace(" ", "+")
            
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
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
            
            # USAJobs uses a specific structure for job listings
            # Each job is in a div with class 'usajobs-search-result--core'
            job_divs = soup.select('.usajobs-search-result--core')
            
            for job_div in job_divs:
                try:
                    # Extract job details
                    title_elem = job_div.select_one('.usajobs-search-result__title a')
                    company_elem = job_div.select_one('.usajobs-search-result__department')
                    location_elem = job_div.select_one('.usajobs-search-result__location')
                    
                    # Skip if essential elements are missing
                    if not title_elem or not company_elem:
                        continue
                        
                    # Get job title and URL
                    title = title_elem.text.strip()
                    job_url = "https://www.usajobs.gov" + title_elem['href'] if title_elem.has_attr('href') else ""
                    
                    # Get company/agency
                    company = company_elem.text.strip() if company_elem else "Unknown Agency"
                    
                    # Get location
                    location = location_elem.text.strip() if location_elem else "Various Locations"
                    
                    # Try to get description snippet
                    description_elem = job_div.select_one('.usajobs-search-result__body')
                    description = description_elem.text.strip() if description_elem else "No description available."
                    
                    # Create job dictionary
                    job = {
                        'title': title,
                        'company': company,
                        'location': location,
                        'description': description,
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
            
    def save_scraped_jobs(self, jobs):
        """
        Save scraped jobs (simplified version that doesn't use database)
        
        Args:
            jobs (list): List of job dictionaries
            
        Returns:
            int: Number of jobs saved
        """
        # In the simplified version, we just log and return the count
        self.logger.info(f"Would save {len(jobs)} jobs (database-free mode)")
        return len(jobs)