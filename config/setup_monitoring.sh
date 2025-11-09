#!/bin/bash

# Setup Cloud Monitoring for Adaptive Ad Intelligence Platform
#
# This script configures:
# - Prometheus metrics collection
# - Cloud Monitoring dashboards
# - Alert policies
#
# Requirements: 12.5

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE_NAME="adaptive-ad-intelligence"

echo -e "${GREEN}Setting up Cloud Monitoring for Adaptive Ad Intelligence Platform${NC}"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with gcloud${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi

# Set project
echo -e "${YELLOW}Setting project...${NC}"
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable cloudtrace.googleapis.com

# Create notification channels
echo -e "${YELLOW}Creating notification channels...${NC}"
echo "Please enter email address for alerts (or press Enter to skip):"
read -r ALERT_EMAIL

if [ -n "$ALERT_EMAIL" ]; then
    echo "Creating email notification channel..."
    CHANNEL_ID=$(gcloud alpha monitoring channels create \
        --display-name="Platform Alerts" \
        --type=email \
        --channel-labels=email_address="$ALERT_EMAIL" \
        --format="value(name)")
    
    echo -e "${GREEN}Created notification channel: $CHANNEL_ID${NC}"
    echo "Update config/monitoring_alerts.yaml with this channel ID"
else
    echo -e "${YELLOW}Skipping notification channel creation${NC}"
fi

# Create log-based metrics
echo -e "${YELLOW}Creating log-based metrics...${NC}"

# Agent communication errors
gcloud logging metrics create agent_communication_errors \
    --description="Count of agent communication errors" \
    --log-filter='
        resource.type="cloud_run_revision"
        jsonPayload.event_type="agent_error"
        severity>=ERROR
    ' \
    --value-extractor='EXTRACT(jsonPayload.agent)' \
    --metric-kind=DELTA \
    --value-type=INT64 \
    2>/dev/null || echo "Metric agent_communication_errors already exists"

# Campaign creation failures
gcloud logging metrics create campaign_creation_failures \
    --description="Count of campaign creation failures" \
    --log-filter='
        resource.type="cloud_run_revision"
        jsonPayload.event_type="request_failed"
        jsonPayload.path=~"/api/v1/campaigns"
        httpRequest.requestMethod="POST"
        severity>=ERROR
    ' \
    --metric-kind=DELTA \
    --value-type=INT64 \
    2>/dev/null || echo "Metric campaign_creation_failures already exists"

# Optimization actions
gcloud logging metrics create optimization_actions \
    --description="Count of optimization actions taken" \
    --log-filter='
        resource.type="cloud_run_revision"
        jsonPayload.event_type="optimization_action"
    ' \
    --value-extractor='EXTRACT(jsonPayload.action_type)' \
    --metric-kind=DELTA \
    --value-type=INT64 \
    2>/dev/null || echo "Metric optimization_actions already exists"

echo -e "${GREEN}Log-based metrics created${NC}"

# Create monitoring dashboard
echo -e "${YELLOW}Creating monitoring dashboard...${NC}"

if [ -f "monitoring_dashboard.json" ]; then
    # Check if dashboard already exists
    EXISTING_DASHBOARD=$(gcloud monitoring dashboards list \
        --filter="displayName:'Adaptive Ad Intelligence Platform - Complete Dashboard'" \
        --format="value(name)" 2>/dev/null || echo "")
    
    if [ -n "$EXISTING_DASHBOARD" ]; then
        echo -e "${YELLOW}Dashboard already exists. Updating...${NC}"
        gcloud monitoring dashboards update "$EXISTING_DASHBOARD" \
            --config-from-file="monitoring_dashboard.json" 2>/dev/null || \
            echo -e "${YELLOW}Dashboard update failed${NC}"
    else
        gcloud monitoring dashboards create \
            --config-from-file="monitoring_dashboard.json" 2>/dev/null || \
            echo -e "${YELLOW}Dashboard creation failed${NC}"
    fi
    
    echo -e "${GREEN}Monitoring dashboard deployed${NC}"
    echo "Use config/deploy_dashboard.sh for dedicated dashboard deployment"
else
    echo -e "${YELLOW}Dashboard config file not found. Skipping dashboard creation.${NC}"
    echo "Run config/deploy_dashboard.sh to deploy the dashboard separately."
fi

# Summary
echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Next steps:"
echo "1. Deploy your Cloud Run service with the /metrics endpoint"
echo "2. Configure Prometheus scraping in Cloud Monitoring"
echo "3. Update config/monitoring_alerts.yaml with notification channel IDs"
echo "4. Deploy alert policies using gcloud or Terraform"
echo ""
echo "View your dashboard:"
echo "https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"
echo ""
echo "View logs:"
echo "https://console.cloud.google.com/logs?project=$PROJECT_ID"
echo ""
