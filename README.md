[README.md](https://github.com/user-attachments/files/23439047/README.md)
# Adaptive Ad Intelligence Platform

A multi-agent serverless application for optimizing digital advertising campaigns using Google Cloud Run and Agent Development Kit (ADK).

## Overview

The Adaptive Ad Intelligence Platform automates digital advertising campaign management for small and medium businesses through intelligent AI agents that collaborate to create, optimize, and execute advertising campaigns across multiple platforms.

## Features

- **Intelligent Campaign Management**: Automated strategy development, creative generation, and audience targeting
- **Dynamic Creative Optimization**: Real-time testing and optimization of ad variations
- **Programmatic Bidding**: Millisecond-level bid decisions on ad inventory
- **Multi-Agent Architecture**: Six specialized AI agents working in coordination
- **Serverless Deployment**: Scalable Cloud Run deployment with automatic scaling

## Architecture

The system consists of six specialized agents:

1. **Campaign Orchestrator Agent**: Coordinates campaign creation and specialist agents
2. **Creative Generator Agent**: Produces ad copy variations and creative content
3. **Audience Targeting Agent**: Identifies optimal audience segments
4. **Budget Optimizer Agent**: Allocates spend and calculates optimal bids
5. **Performance Analyzer Agent**: Monitors metrics and triggers optimizations
6. **Bid Execution Agent**: Executes real-time programmatic bidding

## Prerequisites

- Python 3.11+
- Google Cloud Project with billing enabled
- Google Cloud SDK (`gcloud` CLI)
- Docker (for containerization)

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd adaptive-ad-intelligence
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID
- `GOOGLE_CLOUD_REGION`: Deployment region (default: us-central1)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account key file

### 5. Set Up Google Cloud Infrastructure

```bash
# Make the setup script executable
chmod +x config/gcloud_setup.sh

# Run the setup script
./config/gcloud_setup.sh
```

This script will:
- Enable required Google Cloud APIs
- Create Firestore database
- Set up Pub/Sub topics and subscriptions
- Create Secret Manager secrets
- Configure IAM permissions

## Local Development

### Run the Application

```bash
# Using Python directly
python -m src.main

# Or using uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

The API will be available at `http://localhost:8080`

### API Documentation

Once running, access the interactive API documentation:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

## Deployment

### Build Docker Image

```bash
docker build -t gcr.io/${GOOGLE_CLOUD_PROJECT}/adaptive-ad-intelligence:latest .
```

### Push to Google Container Registry

```bash
docker push gcr.io/${GOOGLE_CLOUD_PROJECT}/adaptive-ad-intelligence:latest
```

### Deploy to Cloud Run

```bash
# Update PROJECT_ID in config/cloud_run_service.yaml
# Then deploy:
gcloud run services replace config/cloud_run_service.yaml --region=us-central1
```

Or use the gcloud command directly:

```bash
gcloud run deploy adaptive-ad-intelligence \
  --image gcr.io/${GOOGLE_CLOUD_PROJECT}/adaptive-ad-intelligence:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 100 \
  --memory 4Gi \
  --cpu 2
```

## Project Structure

```
.
├── config/
│   ├── adk_config.yaml           # ADK agent configuration
│   ├── cloud_run_service.yaml    # Cloud Run service definition
│   └── gcloud_setup.sh           # Google Cloud setup script
├── src/
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   └── config.py                 # Application configuration
├── .env.example                  # Example environment variables
├── .gitignore
├── Dockerfile                    # Container definition
├── requirements.txt              # Python dependencies
└── README.md
```

## Configuration

### ADK Configuration

Agent behavior is configured in `config/adk_config.yaml`. Key settings:

- Agent timeouts and retry policies
- LLM model selection
- Communication protocols
- State management backend

### Environment Variables

See `.env.example` for all available configuration options.

## Health Check

Check application health:

```bash
curl http://localhost:8080/api/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "agents": {
    "campaign_orchestrator": "ready",
    "creative_generator": "ready",
    "audience_targeting": "ready",
    "budget_optimizer": "ready",
    "performance_analyzer": "ready",
    "bid_execution": "ready"
  }
}
```

## Monitoring

The application integrates with Google Cloud services for monitoring:

- **Cloud Logging**: All agent communications and errors
- **Cloud Monitoring**: Performance metrics and alerts
- **Cloud Trace**: Request tracing across agents

## Security

- API key authentication for all endpoints
- Secrets stored in Google Secret Manager
- TLS 1.3 encryption for all communications
- Data encryption at rest in Firestore
- Account-level data isolation

## License

[Your License Here]

## Support

For issues and questions, please open an issue in the repository.
