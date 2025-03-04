# JobHunterAI

A web application that helps users find jobs, optimize their resumes, and track applications.

## Features

- Job search and filtering
- Resume optimization for specific job descriptions
- Cover letter generation
- Application tracking
- User authentication

## Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/JobHunterAI.git
   cd JobHunterAI
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     DATABASE_URL=sqlite:///instance/job_application_system.db
     ```

### Configuration

The application can be configured using:
1. Environment variables (via `.env` file)
2. The `config/config_secret.py` file (copy from the example file)

### Running the Application

Run the main application:
```
python main.py
```

Or use the standalone job search module:
```
python standalone_job_search.py
```

## Project Structure

- `agents/` - AI components for different features
- `config/` - Configuration files
- `static/` - Static assets (CSS, JS)
- `templates/` - HTML templates
- `tests/` - Unit and integration tests
- `app.py` - Main Flask application instance
- `main.py` - Application entry point
- `models.py` - Database models
- `routes.py` - Application routes and endpoints

## Testing

Run tests with:
```
python -m unittest discover
```

## Security Notes

- Never commit API keys or secrets to the repository
- The `.env` file and `config/config_secret.py` are included in `.gitignore`
- Sensitive data is stored safely and not exposed in logs
