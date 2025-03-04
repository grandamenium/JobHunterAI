"""
Configuration module for JobHunterAI.
This file imports sensitive values from config_secret.py, which should not be committed to version control.
"""
import os
from dotenv import load_dotenv

# Try to load from .env file first
load_dotenv()

# Application settings
DEBUG = True
APP_PORT = 5000

# Try to import secret configuration
try:
    from config.config_secret import (
        OPENAI_API_KEY,
        DATABASE_URL,
        SECRET_KEY
    )
except ImportError:
    # If import fails, try environment variables
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instance/job_application_system.db")
    SECRET_KEY = os.getenv("SESSION_SECRET", os.urandom(24).hex())

# Validate API key
if not OPENAI_API_KEY:
    print("WARNING: No OpenAI API key found. Some features will not work.")

# Flask configuration
FLASK_CONFIG = {
    "SECRET_KEY": SECRET_KEY,
    "SQLALCHEMY_DATABASE_URI": DATABASE_URL,
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    "DEBUG": DEBUG
}

# OpenAI configuration
OPENAI_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 1000
TEMPERATURE = 0.7