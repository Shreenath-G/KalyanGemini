# OpenAPI Specification Enhancements

This document describes the enhanced OpenAPI specification for the Adaptive Ad Intelligence Platform API.

## Authentication

All API endpoints (except `/api/health` and `/`) require authentication using API keys.

### API Key Authentication

Include your API key in the `X-API-Key` header:

```
X-API-Key: your_api_key_here
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_FAILED` | 401 | Invalid or missing API key |
| `AUTHORIZATION_FAILED` | 403 | Insufficient permissions |
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `AGENT_TIMEOUT` | 504 | Agent did not respond in time |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |

## Rate Limiting

- **Default Limit:** 100 requests per minute per account
- **Bid Endpoint:** 10,000 requests per second (no per-account limit)

When rate limit is exceeded, the API returns:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": "Rate limit: 100 requests per minute",
    "retry_after": 60
  }
}
```

## Common Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `X-API-Key` | Yes (most endpoints) | API authentication key |
| `Content-Type` | Yes (POST/PATCH) | Must be `application/json` |
| `Accept` | No | Response format (default: `application/json`) |

## Common Response Headers

| Header | Description |
|--------|-------------|
| `X-Request-ID` | Unique request identifier for tracing |
| `X-RateLimit-Limit` | Rate limit ceiling |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |

## Pagination

List endpoints support pagination using query parameters:

- `limit`: Number of items per page (default: 50, max: 100)
- `offset`: Number of items to skip (default: 0)

Response includes pagination metadata:

```json
{
  "campaigns": [...],
  "total": 150,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

## Filtering

Campaign list endpoint supports filtering:

- `status`: Filter by campaign status (draft, active, paused, completed)

Example: `GET /api/v1/campaigns?status=active&limit=20`

## Timestamps

All timestamps are in ISO 8601 format with UTC timezone:

```
2025-11-09T10:30:00Z
```

## Currency

All monetary values are in USD unless otherwise specified.

## Versioning

The API uses URL-based versioning: `/api/v1/...`

Current version: **v1**

Version compatibility is maintained for at least 12 months after a new version is released.

## Webhook Endpoints

### Bid Request Webhook

**Endpoint:** `POST /api/v1/bidding/bid-request`

**Purpose:** Receive real-time bid requests from ad exchanges

**Performance:** Must respond within 100ms

**Authentication:** Webhook signature verification (implementation-specific)

### Bid Result Webhook

**Endpoint:** `POST /api/v1/bidding/bid-result`

**Purpose:** Receive auction results (win/loss notifications)

**Authentication:** Webhook signature verification (implementation-specific)

## Data Export

### Export Formats

- **JSON:** Structured, nested format suitable for programmatic processing
- **CSV:** Flat format suitable for spreadsheet applications

### GDPR Compliance

The data export endpoints support GDPR data portability requirements:

- `GET /api/v1/data/export` - Export all account data
- `GET /api/v1/data/export/campaign/{campaign_id}` - Export specific campaign
- `DELETE /api/v1/data/account?confirm=true` - Delete all account data

## Performance Metrics

### Metric Definitions

| Metric | Formula | Description |
|--------|---------|-------------|
| **ROAS** | Revenue / Spend | Return on Ad Spend |
| **CPA** | Spend / Conversions | Cost Per Acquisition |
| **CTR** | (Clicks / Impressions) × 100 | Click-Through Rate (%) |
| **Conversion Rate** | (Conversions / Clicks) × 100 | Percentage of clicks that convert |

### Update Frequency

- Performance metrics are updated every **15 minutes**
- Real-time bid statistics are updated immediately
- Campaign status changes are reflected within **30 seconds**

## Error Response Format

All error responses follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional context or resolution guidance",
    "retry_after": 60,
    "timestamp": "2025-11-09T10:30:00Z"
  }
}
```

## Best Practices

### 1. Error Handling

Always check the `error.code` field to handle specific error types:

```python
if response.status_code != 200:
    error_code = response.json()["error"]["code"]
    if error_code == "RATE_LIMIT_EXCEEDED":
        # Wait and retry
        time.sleep(response.json()["error"]["retry_after"])
    elif error_code == "AGENT_TIMEOUT":
        # Campaign creation in progress, poll for status
        pass
```

### 2. Idempotency

Campaign creation is not idempotent. To avoid duplicate campaigns, store the returned `campaign_id` immediately.

### 3. Polling

When creating campaigns, the orchestrator may take up to 30 seconds to coordinate agents. If you receive a response indicating processing is in progress, poll the campaign details endpoint:

```python
campaign_id = create_response["campaign_id"]
while True:
    campaign = get_campaign(campaign_id)
    if campaign["status"] != "draft":
        break
    time.sleep(5)
```

### 4. Optimization Timing

- Allow campaigns to run for at least **4 hours** before manual optimization
- Automatic optimizations occur every **15 minutes** (standard mode) or **6 hours** (aggressive mode)
- Wait at least **100 clicks** per variant before pausing underperformers

### 5. Budget Management

- Monitor `remaining_budget` in performance metrics
- System automatically reduces bids when budget is low (<10% remaining)
- Set up alerts for budget depletion to avoid campaign pauses

## Support

For API support, contact: api-support@example.com

For technical documentation: https://docs.example.com/api
