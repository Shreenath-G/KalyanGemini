# Development Guide

This guide covers local development setup and best practices for the Adaptive Ad Intelligence Platform.

## Local Development Setup

### 1. Prerequisites

- Python 3.11 or higher
- pip and virtualenv
- Google Cloud SDK
- Docker (optional, for local container testing)

### 2. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd adaptive-ad-intelligence

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# Required variables:
# - GOOGLE_CLOUD_PROJECT
# - GOOGLE_CLOUD_REGION
# - GOOGLE_APPLICATION_CREDENTIALS (path to service account key)
```

### 4. Set Up Google Cloud Credentials

```bash
# Download service account key from Google Cloud Console
# Save as service-account-key.json

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/service-account-key.json"
```

### 5. Run the Application

```bash
# Using Python
python -m src.main

# Or using uvicorn with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

Access the application:
- API: http://localhost:8080
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## Project Structure

```
adaptive-ad-intelligence/
├── config/                      # Configuration files
│   ├── adk_config.yaml         # ADK agent configuration
│   ├── cloud_run_service.yaml  # Cloud Run service definition
│   ├── gcloud_setup.sh         # GCP setup script
│   └── deploy.sh               # Deployment script
├── src/                        # Source code
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Settings management
│   ├── agents/                 # Agent implementations (to be created)
│   ├── models/                 # Data models (to be created)
│   ├── services/               # Business logic (to be created)
│   └── api/                    # API routes (to be created)
├── tests/                      # Test files (to be created)
├── .env.example                # Example environment variables
├── .gitignore
├── Dockerfile                  # Container definition
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup
└── README.md
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the implementation plan in `.kiro/specs/smart-content-moderator/tasks.md`

### 3. Test Locally

```bash
# Run the application
uvicorn src.main:app --reload

# Test endpoints
curl http://localhost:8080/api/health
```

### 4. Commit Changes

```bash
git add .
git commit -m "Implement feature: description"
git push origin feature/your-feature-name
```

## Code Style

### Python Style Guide

Follow PEP 8 guidelines:
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes

Example:

```python
from typing import List, Dict, Optional

def process_campaign(
    campaign_id: str,
    budget: float,
    segments: List[Dict]
) -> Optional[Dict]:
    """
    Process campaign with given parameters.
    
    Args:
        campaign_id: Unique campaign identifier
        budget: Campaign budget in USD
        segments: List of audience segments
        
    Returns:
        Processed campaign data or None if failed
    """
    # Implementation
    pass
```

### Import Organization

```python
# Standard library imports
import os
import logging
from typing import List, Dict

# Third-party imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Local imports
from src.config import settings
from src.models.campaign import Campaign
```

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_agents.py
```

### Writing Tests

```python
import pytest
from src.agents.creative_generator import CreativeGeneratorAgent

@pytest.mark.asyncio
async def test_creative_generation():
    """Test creative variant generation"""
    agent = CreativeGeneratorAgent()
    
    result = await agent.generate_variations(
        product="CRM Software",
        goal="increase_signups",
        count=5
    )
    
    assert len(result) == 5
    assert all(v.compliance_score > 0.8 for v in result)
```

## Debugging

### Enable Debug Logging

```bash
# In .env file
LOG_LEVEL=DEBUG
```

### Using Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

### VS Code Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8080"
      ],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

## Docker Development

### Build Image

```bash
docker build -t adaptive-ad-intelligence:dev .
```

### Run Container

```bash
docker run -p 8080:8080 \
  -e GOOGLE_CLOUD_PROJECT=your-project \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/key.json \
  -v $(pwd)/service-account-key.json:/app/key.json \
  adaptive-ad-intelligence:dev
```

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
      - ENVIRONMENT=development
    volumes:
      - ./src:/app/src
      - ./config:/app/config
    command: uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

Run with:
```bash
docker-compose up
```

## Common Tasks

### Add New Dependency

```bash
# Install package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt
```

### Update Configuration

Edit `config/adk_config.yaml` for agent settings or `.env` for environment variables.

### View Logs

```bash
# Application logs
tail -f logs/app.log

# Or use Python logging
import logging
logger = logging.getLogger(__name__)
logger.info("Message")
```

## Troubleshooting

### Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Google Cloud Authentication

```bash
# Check credentials
gcloud auth list

# Re-authenticate
gcloud auth login

# Set project
gcloud config set project your-project-id
```

### Port Already in Use

```bash
# Find process using port 8080
lsof -i :8080

# Kill process
kill -9 <PID>
```

## Best Practices

1. **Always use virtual environment**: Isolate project dependencies
2. **Keep .env out of git**: Never commit credentials
3. **Write tests**: Aim for >80% code coverage
4. **Use type hints**: Improve code readability and catch errors
5. **Document code**: Write clear docstrings and comments
6. **Follow task list**: Implement features according to the spec
7. **Test locally first**: Verify changes before deploying

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## Getting Help

- Check existing documentation
- Review error logs
- Search for similar issues
- Ask team members
- Create detailed issue reports
