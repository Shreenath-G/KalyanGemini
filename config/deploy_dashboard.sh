#!/bin/bash

# Deploy Cloud Monitoring Dashboard for Adaptive Ad Intelligence Platform
#
# This script deploys the comprehensive monitoring dashboard to Cloud Monitoring
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
DASHBOARD_FILE="monitoring_dashboard.json"

echo -e "${GREEN}Deploying Cloud Monitoring Dashboard${NC}"
echo "Project: $PROJECT_ID"
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

# Enable Monitoring API
echo -e "${YELLOW}Enabling Cloud Monitoring API...${NC}"
gcloud services enable monitoring.googleapis.com

# Check if dashboard file exists
if [ ! -f "$DASHBOARD_FILE" ]; then
    echo -e "${RED}Error: Dashboard file $DASHBOARD_FILE not found${NC}"
    exit 1
fi

# Deploy dashboard
echo -e "${YELLOW}Deploying dashboard...${NC}"

# Check if dashboard already exists
EXISTING_DASHBOARD=$(gcloud monitoring dashboards list \
    --filter="displayName:'Adaptive Ad Intelligence Platform - Complete Dashboard'" \
    --format="value(name)" 2>/dev/null || echo "")

if [ -n "$EXISTING_DASHBOARD" ]; then
    echo -e "${YELLOW}Dashboard already exists. Updating...${NC}"
    gcloud monitoring dashboards update "$EXISTING_DASHBOARD" \
        --config-from-file="$DASHBOARD_FILE"
    echo -e "${GREEN}Dashboard updated successfully${NC}"
else
    echo -e "${YELLOW}Creating new dashboard...${NC}"
    DASHBOARD_NAME=$(gcloud monitoring dashboards create \
        --config-from-file="$DASHBOARD_FILE" \
        --format="value(name)")
    echo -e "${GREEN}Dashboard created successfully${NC}"
    echo "Dashboard name: $DASHBOARD_NAME"
fi

# Get dashboard URL
DASHBOARD_ID=$(gcloud monitoring dashboards list \
    --filter="displayName:'Adaptive Ad Intelligence Platform - Complete Dashboard'" \
    --format="value(name)" | sed 's/.*\///')

DASHBOARD_URL="https://console.cloud.google.com/monitoring/dashboards/custom/$DASHBOARD_ID?project=$PROJECT_ID"

echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Dashboard URL:"
echo "$DASHBOARD_URL"
echo ""
echo "The dashboard includes:"
echo "  - System Health: API latency, error rates, active campaigns"
echo "  - Agent Performance: Response times, failure rates, fallback usage"
echo "  - Campaign Metrics: ROAS, spend, conversions, impressions, clicks"
echo "  - Cost Tracking: Budget utilization, infrastructure costs"
echo "  - Resource Monitoring: CPU, memory, Firestore, Vertex AI"
echo ""
echo "Next steps:"
echo "1. Ensure your Cloud Run service exposes /metrics endpoint"
echo "2. Configure Prometheus scraping in Cloud Monitoring"
echo "3. Deploy alert policies from config/monitoring_alerts.yaml"
echo ""

