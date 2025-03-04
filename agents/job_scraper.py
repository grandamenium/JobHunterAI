import logging
import requests
from bs4 import BeautifulSoup
import json
import time
import random
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
                'salary': '$120,000 - $180,000 per year',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Data Scientist',
                'company': 'Microsoft',
                'location': 'Redmond, WA',
                'description': 'Analyze large datasets to extract insights and build machine learning models. Strong background in statistics and programming required.',
                'url': 'https://careers.microsoft.com/sample/2',
                'source': 'Microsoft Careers',
                'salary': '$130,000 - $190,000 per year',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Frontend Developer',
                'company': 'Meta',
                'location': 'Menlo Park, CA',
                'description': 'Build engaging user interfaces for Meta products. Expert knowledge of React, JavaScript, and responsive design required.',
                'url': 'https://careers.meta.com/sample/3',
                'source': 'Meta Careers',
                'salary': '$110,000 - $170,000 per year',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'DevOps Engineer',
                'company': 'Amazon Web Services',
                'location': 'Seattle, WA',
                'description': 'Design and implement CI/CD pipelines and cloud infrastructure. Experience with AWS services, Docker, and Kubernetes required.',
                'url': 'https://aws.amazon.com/careers/sample/4',
                'source': 'AWS Careers',
                'salary': '$125,000 - $185,000 per year',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Product Manager',
                'company': 'Apple',
                'location': 'Cupertino, CA',
                'description': 'Lead product development from conception to launch. Strong understanding of user experience design and technical requirements needed.',
                'url': 'https://apple.com/careers/sample/5',
                'source': 'Apple Careers',
                'salary': '$140,000 - $200,000 per year',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Neuroscience Research Scientist',
                'company': 'Yale School of Medicine',
                'location': 'New Haven, CT',
                'description': 'Conduct brain imaging studies and analyze neural activity patterns in cognitive processing.',
                'url': 'https://medicine.yale.edu/careers/sample/1',
                'source': 'Yale Careers',
                'salary': '$90,000 - $120,000 per year',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Clinical Neuroscience Fellow',
                'company': 'Yale Medical School',
                'location': 'New Haven, CT',
                'description': 'Fellowship position in clinical neuroscience, focusing on neurological disorders.',
                'url': 'https://medicine.yale.edu/careers/sample/2',
                'source': 'Yale Medicine',
                'salary': '$70,000 - $85,000 per year',
                'date_posted': datetime.utcnow()
            },
            {
                'title': 'Neurobiology Lab Manager',
                'company': 'Yale University',
                'location': 'New Haven, CT',
                'description': 'Manage research laboratory operations in the Neurobiology department.',
                'url': 'https://medicine.yale.edu/careers/sample/3',
                'source': 'Yale Careers',
                'salary': '$80,000 - $95,000 per year',
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
            # Format search parameters (ensure not None)
            keyword_param = keywords.replace(" ", "+") if keywords else ""
            location_param = location.replace(" ", "+") if location else ""
            
            # Base URL for USA Jobs search
            base_url = "https://www.usajobs.gov/Search/Results"
            
            # Construct search URL - using their URL pattern
            search_url = f"{base_url}?k={keyword_param}"
            
            # Only add location if provided
            if location_param:
                search_url += f"&l={location_param}"
                
            # Add sorting parameter to get newest jobs first
            search_url += "&sd=desc"
            
            # Add job type parameter if specified
            if job_type and job_type != "all":
                if job_type == "full-time":
                    search_url += "&ft=1"  # Full-time parameter
                elif job_type == "part-time":
                    search_url += "&ft=2"  # Part-time parameter
                elif job_type == "internship":
                    search_url += "&hp=student"  # Student/internship parameter
            
            # Make request with different user agent (mimicking a regular browser more effectively)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'DNT': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
            
            self.logger.info(f"Making request to USAJobs: {search_url}")
            
            # Try multiple times with backoff
            max_retries = 3
            for retry in range(max_retries):
                try:
                    response = requests.get(search_url, headers=headers, timeout=15)
                    
                    # Check response status
                    if response.status_code != 200:
                        self.logger.error(f"Error scraping USAJobs: Status code {response.status_code}")
                        if retry < max_retries - 1:
                            wait_time = (retry + 1) * 2  # Exponential backoff
                            self.logger.info(f"Retrying in {wait_time} seconds...")
                            time.sleep(wait_time)
                            continue
                        return []
                    
                    # Debug: Check response text length and content
                    content_length = len(response.text)
                    self.logger.info(f"Received USAJobs response: {content_length} bytes")
                    
                    # Check if we got an actual results page
                    if 'job-search-results' in response.text or 'usajobs-search-results' in response.text:
                        self.logger.info("Found job search results in response")
                    elif 'No jobs found' in response.text:
                        self.logger.info("USAJobs reported 'No jobs found'")
                    elif content_length < 5000:
                        self.logger.warning("Received suspiciously short response - might be a redirect or error page")
                    
                    # Write HTML to diagnostic file for debugging if needed (uncomment to use)
                    # with open('/tmp/usajobs_debug.html', 'w') as f:
                    #     f.write(response.text)
                        
                    # If successful, break retry loop
                    break
                    
                except requests.RequestException as e:
                    self.logger.error(f"Request error: {str(e)}")
                    if retry < max_retries - 1:
                        wait_time = (retry + 1) * 2  # Exponential backoff
                        self.logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        return []
            
            # Write HTML to temporary debug file if needed
            # with open('/tmp/usajobs_debug.html', 'w') as f:
            #     f.write(response.text)
                
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job listings
            job_listings = []
            
            # Try multiple selector patterns to find job listings
            # USAJobs may have updated their class names, try different selectors
            job_divs = []
            
            # Try a wide range of selectors to find jobs
            selectors = [
                # Standard USAJobs selectors (historical)
                '.usajobs-search-result--core, .usajobs-search-result, article.usajobs-search-result',
                # Generic article tags
                'article',
                # Common job result containers
                'div.job-search-result, div[data-job-id], div[data-search-result-item]',
                # Sections that could be job listings
                'section.usajobs-search-result-card',
                # Recent USAJobs selectors
                '.usajobs-search-result-card',
                # Table rows that might contain jobs
                'table.usajobs-search-results-table tr.usajobs-search-result-row',
                # Very generic job-like containers
                'div.job-listing, div.vacancy-listing, div.position-listing',
                # USAJobs v3 class patterns 
                'div[class*="search-result"], div[class*="job-result"]',
                # List items that might be jobs
                'ul.search-results li, ul.job-list li',
                # Any div with an ID pattern that looks like a job listing
                'div[id*="job-"], div[id*="position-"], div[id*="vacancy-"]',
                # Absolutely last resort - any div with content that suggests it's a job
                'div:has(h3), div:has(span.position-title)'
            ]
            
            # Try each selector in order
            job_divs = []
            for i, selector in enumerate(selectors):
                job_divs = soup.select(selector)
                self.logger.info(f"Selector {i+1}: Found {len(job_divs)} job divs with '{selector}'")
                if job_divs:
                    break
                    
            # If we still don't have results, look for any divs with job-like content
            if not job_divs:
                self.logger.info("Trying content-based detection for job listings")
                # Look for job title elements
                title_elements = soup.select('h3.job-title, h3[class*="title"], h4[class*="title"], span[class*="title"], h3 a, h4 a')
                if title_elements:
                    # Use parent elements of these title elements
                    self.logger.info(f"Found {len(title_elements)} potential job title elements, using their parent containers")
                    job_divs = [title.parent.parent for title in title_elements[:10]]  # Limit to first 10 to avoid weird matches
            
            for job_div in job_divs:
                try:
                    # Set of all possible title selectors to try
                    title_selectors = [
                        '.usajobs-search-result__title a', 
                        'h3.usajobs-search-result__title a', 
                        'h3 a', 
                        'a[data-test="job-title"]', 
                        'a.usa-link',
                        '.position-title',
                        'h3.job-title a',
                        '.job-title a',
                        'span[class*="title"]',
                        'div[class*="title"] a',
                        'h3', 
                        'h4',
                        'a[href*="job-announcement"]',
                        'a[href*="vacancy"]',
                        'a[href*="job-details"]',
                        'a[title*="job"]',
                        'a.title'
                    ]
                    
                    # Try each title selector
                    title_elem = None
                    for selector in title_selectors:
                        title_elem = job_div.select_one(selector)
                        if title_elem:
                            break
                    
                    # Company/agency selectors
                    agency_selectors = [
                        '.usajobs-search-result__department', 
                        '.agency', 
                        '.department',
                        '[data-test="agency-name"]',
                        'div.usajobs-search-result__header span',
                        '.agency-name',
                        '.company',
                        '.organization',
                        'span[class*="agency"]',
                        'span[class*="department"]',
                        'div[class*="agency"]',
                        'div[class*="employer"]'
                    ]
                    
                    # Try each agency selector
                    company_elem = None
                    for selector in agency_selectors:
                        company_elem = job_div.select_one(selector)
                        if company_elem:
                            break
                    
                    # Location selectors
                    location_selectors = [
                        '.usajobs-search-result__location',
                        '.location',
                        '[data-test="location"]',
                        'div[itemprop="jobLocation"]',
                        '.job-location',
                        'span[class*="location"]',
                        'div[class*="location"]',
                        'span.location-text',
                        'p[class*="location"]'
                    ]
                    
                    # Try each location selector
                    location_elem = None
                    for selector in location_selectors:
                        location_elem = job_div.select_one(selector)
                        if location_elem:
                            break
                    
                    # Skip if we can't find a title 
                    if not title_elem:
                        self.logger.warning(f"Skipping job: unable to find title element")
                        continue
                        
                    # Extract job title text, with fallback
                    if hasattr(title_elem, 'text'):
                        title = title_elem.text.strip()
                    elif hasattr(title_elem, 'string') and title_elem.string:
                        title = title_elem.string.strip()
                    else:
                        title = "Untitled Position"
                        
                    # Handle different URL formats
                    if title_elem.has_attr('href'):
                        href = title_elem['href']
                        if href.startswith('http'):
                            job_url = href
                        elif href.startswith('//'):
                            job_url = "https:" + href
                        else:
                            job_url = "https://www.usajobs.gov" + href
                    else:
                        # Look for any nearby link
                        parent_links = job_div.select('a[href]')
                        if parent_links:
                            href = parent_links[0]['href']
                            if href.startswith('http'):
                                job_url = href
                            elif href.startswith('//'):
                                job_url = "https:" + href 
                            else:
                                job_url = "https://www.usajobs.gov" + href
                        else:
                            job_url = "https://www.usajobs.gov/Search/Results"
                    
                    # Get company/agency with aggressive text extraction
                    if company_elem:
                        if hasattr(company_elem, 'text'):
                            company = company_elem.text.strip()
                        else:
                            company = str(company_elem).strip()
                    else:
                        # Try to find text that looks like an agency name
                        all_text = job_div.get_text()
                        agency_indicators = ["Department of", "Bureau of", "Office of", "Agency for", "U.S.", "Federal"]
                        for line in all_text.split('\n'):
                            line = line.strip()
                            if any(indicator in line for indicator in agency_indicators) and len(line) < 100:
                                company = line
                                break
                        else:
                            company = "U.S. Government"
                    
                    # Remove excessive whitespace from company name
                    company = ' '.join(company.split())
                    
                    # Get location with fallback to content analysis if not found
                    if location_elem:
                        if hasattr(location_elem, 'text'):
                            location = location_elem.text.strip()
                        else:
                            location = str(location_elem).strip()
                    else:
                        # Try to find text that looks like a location
                        all_text = job_div.get_text()
                        location_candidates = []
                        common_locations = ["Washington", "DC", "New York", "Virginia", "California", "Remote", "Telework"]
                        for line in all_text.split('\n'):
                            line = line.strip()
                            if any(loc in line for loc in common_locations) and len(line) < 50:
                                location_candidates.append(line)
                        
                        if location_candidates:
                            location = location_candidates[0]
                        else:
                            location = "Various Locations"
                    
                    # Clean up location text
                    location = ' '.join(location.split())
                    
                    # Description selectors
                    description_selectors = [
                        '.usajobs-search-result__body',
                        '.summary',
                        '[data-test="job-description"]',
                        'div[itemprop="description"]',
                        'p.usa-prose',
                        '.job-description',
                        '.vacancy-description',
                        'p[class*="description"]',
                        'div[class*="description"]',
                        'span[class*="description"]'
                    ]
                    
                    # Try each description selector
                    description_elem = None
                    for selector in description_selectors:
                        description_elem = job_div.select_one(selector)
                        if description_elem:
                            break
                            
                    # Get description with aggressive fallback
                    if description_elem:
                        description = description_elem.text.strip()
                    else:
                        # Use all text from the job div, excluding title and company
                        all_text = job_div.get_text()
                        exclude_texts = [title, company, location]
                        description_lines = []
                        
                        for line in all_text.split('\n'):
                            line = line.strip()
                            if line and not any(exclude in line for exclude in exclude_texts):
                                description_lines.append(line)
                                
                        if description_lines:
                            # Limit to a reasonable length
                            description = ' '.join(description_lines[:5])
                        else:
                            description = "Position at " + company
                            
                    # Clean up description (remove excess whitespace)
                    description = ' '.join(description.split())
                    if len(description) > 500:  # Truncate very long descriptions
                        description = description[:497] + "..."
                    
                    # Salary selectors
                    salary_selectors = [
                        '.usajobs-search-result__salary',
                        '.salary',
                        '[data-test="salary"]',
                        'div[itemprop="baseSalary"]',
                        'div.salary',
                        'span[class*="salary"]',
                        'div[class*="salary"]',
                        'span[class*="pay"]',
                        'div[class*="pay"]',
                        'span[class*="compensation"]'
                    ]
                    
                    # Try each salary selector
                    salary_elem = None
                    for selector in salary_selectors:
                        salary_elem = job_div.select_one(selector)
                        if salary_elem:
                            break
                            
                    # Extract salary information
                    if salary_elem:
                        salary = salary_elem.text.strip()
                    else:
                        # Look for salary-like text (numbers with dollar signs or "per")
                        all_text = job_div.get_text()
                        salary_candidates = []
                        for line in all_text.split('\n'):
                            line = line.strip()
                            if ('$' in line or ' per ' in line.lower()) and len(line) < 100:
                                salary_candidates.append(line)
                                
                        if salary_candidates:
                            salary = salary_candidates[0]
                        else:
                            salary = "Salary not specified"
                            
                    # Clean up salary text
                    salary = ' '.join(salary.split())
                    
                    # Create job dictionary
                    job = {
                        'title': title,
                        'company': company,
                        'location': location,
                        'description': description,
                        'salary': salary,
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