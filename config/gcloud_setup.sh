#!/bin/bash

# Google Cloud Setup Script for Adaptive Ad Intelligence Platform
# This script configures the necessary Google Cloud services

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE_NAME="adaptive-ad-intelligence"

echo "Setting up Google Cloud project: $PROJECT_ID"
echo "Region: $REGION"

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling Google Cloud APIs..."
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com \
  logging.googleapis.com \
  cloudtasks.googleapis.com \
  pubsub.googleapis.com \
  compute.googleapis.com

# Create Firestore database (if not exists)
echo "Setting up Firestore..."
gcloud firestore databases create --location=$REGION --type=firestore-native || echo "Firestore already exists"

# Create Pub/Sub topics
echo "Creating Pub/Sub topics..."
gcloud pubsub topics create campaign-events || echo "Topic campaign-events already exists"
gcloud pubsub topics create bid-events || echo "Topic bid-events already exists"

# Create Pub/Sub subscriptions
gcloud pubsub subscriptions create analytics-pipeline-sub \
  --topic=campaign-events \
  --ack-deadline=60 || echo "Subscription already exists"

# Create Secret Manager secrets (placeholders)
echo "Creating Secret Manager secrets..."
echo "placeholder-key" | gcloud secrets create vertex-ai-api-key \
  --data-file=- \
  --replication-policy="automatic" || echo "Secret vertex-ai-api-key already exists"

echo "placeholder-key" | gcloud secrets create firestore-credentials \
  --data-file=- \
  --replication-policy="automatic" || echo "Secret firestore-credentials already exists"

# Create service account for Cloud Run
echo "Creating service account..."
gcloud iam service-accounts create $SERVICE_NAME \
  --display-name="Adaptive Ad Intelligence Service Account" || echo "Service account already exists"

SERVICE_ACCOUNT="$SERVICE_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# Grant necessary permissions
echo "Granting IAM permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudtasks.enqueuer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/pubsub.publisher"

echo "Google Cloud setup complete!"
echo ""
echo "Next steps:"
echo "1. Update secrets in Secret Manager with actual credentials"
echo "2. Build and deploy the application to Cloud Run"
echo "3. Configure environment variables in Cloud Run service"
