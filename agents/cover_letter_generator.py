import os
import logging
from openai import OpenAI

class CoverLetterGenerator:
    def __init__(self):
        # Use a dummy key if OPENAI_API_KEY is not set
        api_key = os.environ.get("OPENAI_API_KEY", "dummy-key-for-testing")
        self.openai = OpenAI(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        
        # Warn if using dummy key
        if api_key == "dummy-key-for-testing":
            self.logger.warning("Using dummy OpenAI API key. Cover letter generation will not work correctly.")

    def generate_cover_letter(self, job_description, resume, company_name):
        """Generate a personalized cover letter"""
        prompt = f"""Create a professional cover letter for this job based on the resume:

        Job Description:
        {job_description}

        Resume:
        {resume}

        Company:
        {company_name}

        Generate a personalized cover letter that highlights relevant experience and shows enthusiasm for the role.
        Return in JSON format:
        {{
            "cover_letter": "string",
            "personalization_points": ["string"]
        }}"""

        response = self.openai.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
