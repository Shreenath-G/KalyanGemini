#!/bin/bash

# Deployment script for Adaptive Ad Intelligence Platform

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE_NAME="adaptive-ad-intelligence"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"

echo "Deploying Adaptive Ad Intelligence Platform"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Image: $IMAGE_NAME"

# Build Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME .

# Push to Google Container Registry
echo "Pushing image to GCR..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 100 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 80 \
  --service-account "$SERVICE_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --set-env-vars "ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_REGION=$REGION"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo "Deployment complete!"
echo "Service URL: $SERVICE_URL"
echo "Health check: $SERVICE_URL/api/health"
echo "API docs: $SERVICE_URL/docs"
