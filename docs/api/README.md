# Adaptive Ad Intelligence Platform API Documentation

Welcome to the Adaptive Ad Intelligence Platform API documentation. This API enables you to create, manage, and optimize digital advertising campaigns using AI-powered multi-agent orchestration.

## Quick Start

### 1. Get Your API Key

Sign up at [https://platform.example.com](https://platform.example.com) to receive your API key.

### 2. Make Your First Request

```bash
curl -X GET "https://api.example.com/api/health" \
  -H "Accept: application/json"
```

### 3. Create a Campaign

```bash
curl -X POST "https://api.example.com/api/v1/campaigns" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "business_goal": "increase_sales",
    "monthly_budget": 5000.0,
    "target_audience": "small business owners aged 30-50",
    "products": ["CRM Software"],
    "optimization_mode": "standard"
  }'
```

## Documentation Structure

### Core Documentation

- **[OpenAPI Enhancements](./openapi_enhancements.md)** - Complete API reference with authentication, error codes, and best practices
- **[Integration Patterns](./integration_patterns.md)** - Common integration patterns and workflows

### Code Examples

- **[Python Client](./examples/python_client.py)** - Full-featured Python client with examples
- **[JavaScript Client](./examples/javascript_client.js)** - Node.js client implementation
- **[cURL Examples](./examples/curl_examples.sh)** - Command-line examples for all endpoints

## Key Features

### 🤖 AI-Powered Campaign Creation

Create campaigns that leverage multiple AI agents to:
- Generate creative variations (headlines, body copy, CTAs)
- Identify optimal audience segments
- Allocate budgets across platforms
- Calculate optimal bid strategies

### 📊 Real-time Performance Monitoring

Track campaign performance with:
- Aggregate metrics (ROAS, CPA, CTR)
- Breakdowns by variant, segment, and platform
- 15-minute update frequency

### ⚡ Automated Optimization

Let AI agents optimize your campaigns:
- Pause underperforming variants
- Scale high performers
- Adjust targeting and budgets
- Real-time bid adjustments

### 🎯 Programmatic Bidding

Execute real-time bids with:
- <100ms response time
- Intelligent bid price calculation
- Budget-aware bidding
- Win rate optimization

## API Endpoints

### Campaign Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/campaigns` | POST | Create a new campaign |
| `/api/v1/campaigns/{id}` | GET | Get campaign details |
| `/api/v1/campaigns/{id}` | PATCH | Update campaign settings |
| `/api/v1/campaigns/{id}` | DELETE | Delete campaign (soft delete) |
| `/api/v1/campaigns` | GET | List campaigns |

### Performance & Optimization

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/campaigns/{id}/performance` | GET | Get performance metrics |
| `/api/v1/campaigns/{id}/optimize` | POST | Trigger optimization |
| `/api/v1/campaigns/{id}/performance/variants` | GET | Variant performance |
| `/api/v1/campaigns/{id}/performance/segments` | GET | Segment performance |
| `/api/v1/campaigns/{id}/performance/platforms` | GET | Platform performance |

### Real-time Bidding

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/bidding/bid-request` | POST | Handle bid request (webhook) |
| `/api/v1/bidding/bid-result` | POST | Track bid result (webhook) |
| `/api/v1/bidding/campaigns/{id}/bid-stats` | GET | Get bid statistics |

### Data Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/data/export` | GET | Export account data |
| `/api/v1/data/export/campaign/{id}` | GET | Export campaign data |
| `/api/v1/data/export/performance-report` | GET | Export performance report |
| `/api/v1/data/account` | DELETE | Delete account data |

### System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |

## Authentication

All API requests (except `/api/health`) require authentication using an API key:

```
X-API-Key: your_api_key_here
```

## Rate Limits

- **Standard Endpoints:** 100 requests per minute per account
- **Bid Endpoint:** 10,000 requests per second (no per-account limit)

## Response Format

All responses are in JSON format:

```json
{
  "campaign_id": "camp_a1b2c3d4e5f6",
  "status": "active",
  "message": "Campaign created successfully"
}
```

### Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": "monthly_budget: must be between 100 and 100000"
  }
}
```

## Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_FAILED` | 401 | Invalid or missing API key |
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `AGENT_TIMEOUT` | 504 | Agent did not respond in time |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |

## Quick Examples

### Python

```python
from ad_intelligence_client import AdIntelligenceClient

client = AdIntelligenceClient(api_key="your_api_key")

# Create campaign
campaign = client.create_campaign(
    business_goal="increase_sales",
    monthly_budget=5000.0,
    target_audience="small business owners",
    products=["CRM Software"]
)

# Get performance
metrics = client.get_performance(campaign['campaign_id'])
print(f"ROAS: {metrics['roas']:.2f}")

# Optimize
result = client.optimize_campaign(
    campaign['campaign_id'],
    optimization_type="auto"
)
```

### JavaScript

```javascript
const AdIntelligenceClient = require('./ad_intelligence_client');

const client = new AdIntelligenceClient('your_api_key');

// Create campaign
const campaign = await client.createCampaign({
    businessGoal: 'increase_sales',
    monthlyBudget: 5000.0,
    targetAudience: 'small business owners',
    products: ['CRM Software']
});

// Get performance
const metrics = await client.getPerformance(campaign.campaign_id);
console.log(`ROAS: ${metrics.roas.toFixed(2)}`);

// Optimize
const result = await client.optimizeCampaign(
    campaign.campaign_id,
    'auto'
);
```

### cURL

```bash
# Create campaign
curl -X POST "https://api.example.com/api/v1/campaigns" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "business_goal": "increase_sales",
    "monthly_budget": 5000.0,
    "target_audience": "small business owners",
    "products": ["CRM Software"]
  }'

# Get performance
curl -X GET "https://api.example.com/api/v1/campaigns/CAMPAIGN_ID/performance" \
  -H "X-API-Key: YOUR_API_KEY"

# Optimize
curl -X POST "https://api.example.com/api/v1/campaigns/CAMPAIGN_ID/optimize?optimization_type=auto" \
  -H "X-API-Key: YOUR_API_KEY"
```

## Workflow Examples

### Complete Campaign Lifecycle

1. **Create Campaign** → AI agents generate strategy (30 seconds)
2. **Wait for Ready** → Poll status until active
3. **Monitor Performance** → Check metrics every 15 minutes
4. **Optimize** → Trigger manual or automatic optimization
5. **Export Data** → Download performance reports

### Real-time Bidding Integration

1. **Receive Bid Request** → From ad exchange webhook
2. **Forward to API** → POST to `/api/v1/bidding/bid-request`
3. **Get Bid Response** → Within 100ms
4. **Track Result** → POST win/loss to `/api/v1/bidding/bid-result`

## Best Practices

1. ✅ **Implement retry logic** with exponential backoff
2. ✅ **Handle rate limits** gracefully
3. ✅ **Poll campaign status** after creation
4. ✅ **Monitor performance** regularly
5. ✅ **Set up alerts** for low ROAS
6. ✅ **Verify webhook signatures** for security
7. ✅ **Export data** regularly for backup
8. ✅ **Test in development** before production

## Support & Resources

### Documentation
- [OpenAPI Specification](./openapi_enhancements.md)
- [Integration Patterns](./integration_patterns.md)
- [Code Examples](./examples/)

### Support Channels
- **Email:** api-support@example.com
- **Documentation:** https://docs.example.com/api
- **Status Page:** https://status.example.com
- **Community Forum:** https://community.example.com

### SDKs & Tools
- [Python SDK](https://github.com/example/python-sdk)
- [JavaScript SDK](https://github.com/example/js-sdk)
- [Postman Collection](https://www.postman.com/example/collections)

## Changelog

### v1.0.0 (Current)
- Initial release
- Campaign management endpoints
- Performance monitoring
- Automated optimization
- Real-time bidding
- Data export

## License

API access is subject to the [Terms of Service](https://example.com/terms).

---

**Ready to get started?** [Sign up for an API key](https://platform.example.com/signup) and create your first campaign in minutes!
