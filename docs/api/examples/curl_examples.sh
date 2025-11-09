#!/bin/bash

# cURL Examples for Adaptive Ad Intelligence Platform API
#
# This script demonstrates how to interact with the API using cURL.
# Replace YOUR_API_KEY with your actual API key.
#
# Usage:
#     chmod +x curl_examples.sh
#     ./curl_examples.sh

# Configuration
API_KEY="YOUR_API_KEY"
BASE_URL="https://api.example.com"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "Adaptive Ad Intelligence Platform - cURL Examples"
echo "=================================================="
echo ""

# ============================================================================
# 1. Health Check
# ============================================================================
echo -e "${GREEN}1. Health Check${NC}"
echo "GET /api/health"
echo ""

curl -X GET "${BASE_URL}/api/health" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 2. Create Campaign
# ============================================================================
echo -e "${GREEN}2. Create Campaign${NC}"
echo "POST /api/v1/campaigns"
echo ""

CAMPAIGN_RESPONSE=$(curl -X POST "${BASE_URL}/api/v1/campaigns" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "business_goal": "increase_sales",
    "monthly_budget": 5000.0,
    "target_audience": "small business owners aged 30-50 interested in productivity tools",
    "products": ["CRM Software", "Project Management Tool"],
    "optimization_mode": "standard"
  }')

echo "$CAMPAIGN_RESPONSE" | jq '.'

# Extract campaign ID for subsequent requests
CAMPAIGN_ID=$(echo "$CAMPAIGN_RESPONSE" | jq -r '.campaign_id')
echo ""
echo -e "${BLUE}Campaign ID: ${CAMPAIGN_ID}${NC}"
echo ""
echo "---"
echo ""

# ============================================================================
# 3. Get Campaign Details
# ============================================================================
echo -e "${GREEN}3. Get Campaign Details${NC}"
echo "GET /api/v1/campaigns/{campaign_id}"
echo ""

curl -X GET "${BASE_URL}/api/v1/campaigns/${CAMPAIGN_ID}" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 4. Update Campaign
# ============================================================================
echo -e "${GREEN}4. Update Campaign${NC}"
echo "PATCH /api/v1/campaigns/{campaign_id}"
echo ""

curl -X PATCH "${BASE_URL}/api/v1/campaigns/${CAMPAIGN_ID}?budget=7500.0&status=active" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 5. List Campaigns
# ============================================================================
echo -e "${GREEN}5. List Campaigns${NC}"
echo "GET /api/v1/campaigns"
echo ""

curl -X GET "${BASE_URL}/api/v1/campaigns?status=active&limit=10" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 6. Get Campaign Performance
# ============================================================================
echo -e "${GREEN}6. Get Campaign Performance${NC}"
echo "GET /api/v1/campaigns/{campaign_id}/performance"
echo ""

curl -X GET "${BASE_URL}/api/v1/campaigns/${CAMPAIGN_ID}/performance" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 7. Get Variant Performance Breakdown
# ============================================================================
echo -e "${GREEN}7. Get Variant Performance Breakdown${NC}"
echo "GET /api/v1/campaigns/{campaign_id}/performance/variants"
echo ""

curl -X GET "${BASE_URL}/api/v1/campaigns/${CAMPAIGN_ID}/performance/variants" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 8. Get Segment Performance Breakdown
# ============================================================================
echo -e "${GREEN}8. Get Segment Performance Breakdown${NC}"
echo "GET /api/v1/campaigns/{campaign_id}/performance/segments"
echo ""

curl -X GET "${BASE_URL}/api/v1/campaigns/${CAMPAIGN_ID}/performance/segments" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 9. Get Platform Performance Breakdown
# ============================================================================
echo -e "${GREEN}9. Get Platform Performance Breakdown${NC}"
echo "GET /api/v1/campaigns/{campaign_id}/performance/platforms"
echo ""

curl -X GET "${BASE_URL}/api/v1/campaigns/${CAMPAIGN_ID}/performance/platforms" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 10. Trigger Optimization (Suggest Mode)
# ============================================================================
echo -e "${GREEN}10. Trigger Optimization (Suggest Mode)${NC}"
echo "POST /api/v1/campaigns/{campaign_id}/optimize"
echo ""

curl -X POST "${BASE_URL}/api/v1/campaigns/${CAMPAIGN_ID}/optimize?optimization_type=suggest" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 11. Trigger Optimization (Auto Mode)
# ============================================================================
echo -e "${GREEN}11. Trigger Optimization (Auto Mode)${NC}"
echo "POST /api/v1/campaigns/{campaign_id}/optimize"
echo ""

curl -X POST "${BASE_URL}/api/v1/campaigns/${CAMPAIGN_ID}/optimize?optimization_type=auto" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 12. Submit Bid Request (Webhook)
# ============================================================================
echo -e "${GREEN}12. Submit Bid Request (Webhook)${NC}"
echo "POST /api/v1/bidding/bid-request"
echo ""

curl -X POST "${BASE_URL}/api/v1/bidding/bid-request" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "request_id": "bid_req_xyz789",
    "user_profile": {
      "user_id": "user_12345",
      "demographics": {
        "age": 35,
        "gender": "male"
      },
      "interests": ["business", "technology", "productivity"],
      "behaviors": ["online_shopping", "software_usage"]
    },
    "inventory": {
      "platform": "programmatic",
      "ad_format": "display",
      "size": "300x250",
      "floor_price": 1.50
    }
  }' \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 13. Track Bid Result (Webhook)
# ============================================================================
echo -e "${GREEN}13. Track Bid Result (Webhook)${NC}"
echo "POST /api/v1/bidding/bid-result"
echo ""

curl -X POST "${BASE_URL}/api/v1/bidding/bid-result?request_id=bid_req_xyz789&status=BID_WON&win_price=2.35" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 14. Get Campaign Bid Statistics
# ============================================================================
echo -e "${GREEN}14. Get Campaign Bid Statistics${NC}"
echo "GET /api/v1/bidding/campaigns/{campaign_id}/bid-stats"
echo ""

curl -X GET "${BASE_URL}/api/v1/bidding/campaigns/${CAMPAIGN_ID}/bid-stats" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 15. Export Account Data (JSON)
# ============================================================================
echo -e "${GREEN}15. Export Account Data (JSON)${NC}"
echo "GET /api/v1/data/export"
echo ""

curl -X GET "${BASE_URL}/api/v1/data/export?format=json&include_metrics=true" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: application/json" \
  -o "account_export.json"

echo "Account data exported to account_export.json"
echo ""
echo "---"
echo ""

# ============================================================================
# 16. Export Account Data (CSV)
# ============================================================================
echo -e "${GREEN}16. Export Account Data (CSV)${NC}"
echo "GET /api/v1/data/export"
echo ""

curl -X GET "${BASE_URL}/api/v1/data/export?format=csv&include_metrics=true" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: text/csv" \
  -o "account_export.csv"

echo "Account data exported to account_export.csv"
echo ""
echo "---"
echo ""

# ============================================================================
# 17. Export Campaign Data
# ============================================================================
echo -e "${GREEN}17. Export Campaign Data${NC}"
echo "GET /api/v1/data/export/campaign/{campaign_id}"
echo ""

curl -X GET "${BASE_URL}/api/v1/data/export/campaign/${CAMPAIGN_ID}?format=json" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: application/json" \
  -o "campaign_export.json"

echo "Campaign data exported to campaign_export.json"
echo ""
echo "---"
echo ""

# ============================================================================
# 18. Export Performance Report
# ============================================================================
echo -e "${GREEN}18. Export Performance Report${NC}"
echo "GET /api/v1/data/export/performance-report"
echo ""

curl -X GET "${BASE_URL}/api/v1/data/export/performance-report?start_date=2025-11-01T00:00:00Z&end_date=2025-11-09T23:59:59Z" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 19. Delete Campaign (Soft Delete)
# ============================================================================
echo -e "${GREEN}19. Delete Campaign (Soft Delete)${NC}"
echo "DELETE /api/v1/campaigns/{campaign_id}"
echo ""

curl -X DELETE "${BASE_URL}/api/v1/campaigns/${CAMPAIGN_ID}" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Accept: application/json"

echo "Campaign marked as completed"
echo ""
echo "---"
echo ""

# ============================================================================
# 20. Error Handling Example - Invalid Budget
# ============================================================================
echo -e "${GREEN}20. Error Handling Example - Invalid Budget${NC}"
echo "POST /api/v1/campaigns (with invalid budget)"
echo ""

curl -X POST "${BASE_URL}/api/v1/campaigns" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "business_goal": "increase_sales",
    "monthly_budget": 150000.0,
    "target_audience": "everyone",
    "products": ["Product"]
  }' \
  | jq '.'

echo ""
echo "---"
echo ""

# ============================================================================
# 21. Error Handling Example - Missing API Key
# ============================================================================
echo -e "${GREEN}21. Error Handling Example - Missing API Key${NC}"
echo "GET /api/v1/campaigns (without API key)"
echo ""

curl -X GET "${BASE_URL}/api/v1/campaigns" \
  -H "Accept: application/json" \
  | jq '.'

echo ""
echo "---"
echo ""

echo "Examples completed!"
echo ""
echo "Note: Replace YOUR_API_KEY with your actual API key"
echo "Update BASE_URL if using a different environment"
