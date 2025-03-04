import os
from openai import OpenAI
import json
import logging

class ResumeOptimizerAgent:
    def __init__(self):
        # Use a dummy key if OPENAI_API_KEY is not set
        api_key = os.environ.get("OPENAI_API_KEY", "dummy-key-for-testing")
        self.openai = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # Warn if using dummy key
        if api_key == "dummy-key-for-testing":
            self.logger.warning("Using dummy OpenAI API key. Resume optimization will not work correctly.")

    def analyze_job_description(self, job_description):
        """Extract key requirements and skills from job description"""
        prompt = f"""Analyze this job description and extract key requirements and skills:
        {job_description}

        Return the result as JSON with these fields:
        - required_skills
        - preferred_skills
        - experience_level
        - key_responsibilities"""

        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            self.logger.error(f"Error analyzing job description: {str(e)}")
            return None

    def optimize_resume(self, resume_text, job_description):
        """Optimize resume based on job description"""
        self.logger.debug("Starting resume optimization")
        self.logger.debug(f"Resume length: {len(resume_text)}")
        self.logger.debug(f"Job description length: {len(job_description)}")

        try:
            prompt = f"""Please customize this resume based on the following job description. 
            Keep general statements and personal experience the same, only update relevant information 
            to tailor the resume for this specific position.

            Job Description:
            {job_description}

            Current Resume:
            {resume_text}

            Please provide the result in JSON format with these fields:
            - optimized_resume: the tailored resume text
            - changes_made: list of specific changes made
            - tailored_sections: list of sections that were modified"""

            self.logger.debug("Sending request to OpenAI")
            response = self.openai.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                response_format={"type": "json_object"}
            )

            self.logger.debug("Received response from OpenAI")
            result = json.loads(response.choices[0].message.content)

            # Validate the response structure
            if not all(key in result for key in ['optimized_resume', 'changes_made', 'tailored_sections']):
                raise ValueError("Invalid response format from OpenAI")

            self.logger.info("Successfully optimized resume")
            return result

        except Exception as e:
            self.logger.error(f"Error optimizing resume: {str(e)}")
            return {
                "optimized_resume": resume_text,
                "changes_made": [f"Error: {str(e)}"],
                "tailored_sections": []
            }