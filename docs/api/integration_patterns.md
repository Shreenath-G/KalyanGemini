# Integration Patterns

This document describes common integration patterns for the Adaptive Ad Intelligence Platform API.

## Table of Contents

1. [Campaign Creation Workflow](#campaign-creation-workflow)
2. [Performance Monitoring](#performance-monitoring)
3. [Automated Optimization](#automated-optimization)
4. [Real-time Bidding Integration](#real-time-bidding-integration)
5. [Data Export and Reporting](#data-export-and-reporting)
6. [Error Handling and Retry Logic](#error-handling-and-retry-logic)
7. [Webhook Integration](#webhook-integration)
8. [Multi-Campaign Management](#multi-campaign-management)

---

## Campaign Creation Workflow

### Pattern: Create and Wait for Ready

When creating a campaign, the AI agents may take up to 30 seconds to generate the strategy. Use this pattern to wait for the campaign to be ready:

```python
# Create campaign
response = client.create_campaign(
    business_goal="increase_sales",
    monthly_budget=5000.0,
    target_audience="small business owners",
    products=["CRM Software"]
)

campaign_id = response['campaign_id']

# Poll until ready
max_attempts = 12  # 60 seconds with 5-second intervals
for attempt in range(max_attempts):
    campaign = client.get_campaign(campaign_id)
    
    if campaign['status'] != 'draft':
        print(f"Campaign ready: {campaign['status']}")
        break
    
    time.sleep(5)
else:
    print("Campaign still processing, check back later")
```

### Pattern: Async Campaign Creation

For non-blocking campaign creation, use a callback or webhook approach:

```python
# Create campaign
response = client.create_campaign(...)
campaign_id = response['campaign_id']

# Store campaign_id for later retrieval
database.save_pending_campaign(campaign_id)

# Set up periodic check (e.g., every 5 minutes)
scheduler.add_job(
    check_campaign_status,
    args=[campaign_id],
    trigger='interval',
    minutes=5
)
```

---

## Performance Monitoring

### Pattern: Real-time Dashboard

Update a dashboard with campaign performance every 15 minutes:

```python
def update_dashboard():
    # Get all active campaigns
    campaigns = client.list_campaigns(status='active')
    
    for campaign in campaigns['campaigns']:
        # Get performance metrics
        metrics = client.get_performance(campaign['campaign_id'])
        
        # Update dashboard
        dashboard.update({
            'campaign_id': campaign['campaign_id'],
            'spend': metrics['total_spend'],
            'conversions': metrics['total_conversions'],
            'roas': metrics['roas'],
            'cpa': metrics['cpa']
        })
        
        # Check for alerts
        if metrics['roas'] < 1.0:
            alert.send(f"Low ROAS alert: {campaign['campaign_id']}")

# Schedule every 15 minutes
scheduler.add_job(update_dashboard, trigger='interval', minutes=15)
```

### Pattern: Performance Comparison

Compare performance across campaigns to identify top performers:

```python
def analyze_campaign_performance():
    campaigns = client.list_campaigns(status='active')
    
    performance_data = []
    for campaign in campaigns['campaigns']:
        metrics = client.get_performance(campaign['campaign_id'])
        performance_data.append({
            'campaign_id': campaign['campaign_id'],
            'roas': metrics['roas'],
            'spend': metrics['total_spend'],
            'conversions': metrics['total_conversions']
        })
    
    # Sort by ROAS
    performance_data.sort(key=lambda x: x['roas'], reverse=True)
    
    # Identify top 20% performers
    top_performers = performance_data[:len(performance_data)//5]
    
    # Scale top performers
    for campaign in top_performers:
        if campaign['roas'] > 3.0:
            client.update_campaign(
                campaign['campaign_id'],
                budget=campaign['spend'] * 1.5  # Increase budget by 50%
            )
```

---

## Automated Optimization

### Pattern: Scheduled Optimization

Run optimization checks on a schedule:

```python
def optimize_all_campaigns():
    campaigns = client.list_campaigns(status='active')
    
    for campaign in campaigns['campaigns']:
        # Get optimization suggestions
        suggestions = client.optimize_campaign(
            campaign['campaign_id'],
            optimization_type='suggest'
        )
        
        # Review and apply high-confidence optimizations
        for action in suggestions['actions']:
            if action['type'] == 'pause_variant':
                # Auto-apply pause actions for very low ROAS
                if 'roas' in action['reason'] and float(action['reason'].split(':')[1]) < 0.5:
                    client.optimize_campaign(
                        campaign['campaign_id'],
                        optimization_type='auto'
                    )
                    break

# Run daily at 2 AM
scheduler.add_job(optimize_all_campaigns, trigger='cron', hour=2)
```

### Pattern: Threshold-based Optimization

Trigger optimization when specific thresholds are met:

```python
def check_optimization_triggers():
    campaigns = client.list_campaigns(status='active')
    
    for campaign in campaigns['campaigns']:
        metrics = client.get_performance(campaign['campaign_id'])
        
        # Trigger optimization if ROAS drops below 1.5
        if metrics['roas'] < 1.5:
            result = client.optimize_campaign(
                campaign['campaign_id'],
                optimization_type='auto'
            )
            
            # Log optimization
            logger.info(f"Auto-optimized {campaign['campaign_id']}: {result['message']}")
        
        # Trigger optimization if CPA exceeds target
        target_cpa = campaign.get('target_cpa', 50.0)
        if metrics['cpa'] > target_cpa * 1.2:  # 20% over target
            result = client.optimize_campaign(
                campaign['campaign_id'],
                optimization_type='auto'
            )
```

---

## Real-time Bidding Integration

### Pattern: Bid Request Handler

Implement a webhook handler for real-time bid requests:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook/bid-request")
async def handle_bid_request(request: Request):
    bid_request = await request.json()
    
    # Forward to Ad Intelligence Platform
    response = requests.post(
        "https://api.example.com/api/v1/bidding/bid-request",
        json=bid_request,
        timeout=0.095  # 95ms to ensure <100ms total
    )
    
    return response.json()
```

### Pattern: Bid Result Tracking

Track bid results to monitor win rates:

```python
@app.post("/webhook/bid-result")
async def handle_bid_result(request: Request):
    result = await request.json()
    
    # Forward to Ad Intelligence Platform
    requests.post(
        "https://api.example.com/api/v1/bidding/bid-result",
        params={
            'request_id': result['request_id'],
            'status': result['status'],
            'win_price': result.get('win_price')
        }
    )
    
    # Update internal analytics
    analytics.track_bid_result(result)
    
    return {"success": True}
```

---

## Data Export and Reporting

### Pattern: Weekly Performance Report

Generate and email weekly performance reports:

```python
def generate_weekly_report():
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Export performance report
    report = client.export_performance_report(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    
    # Generate PDF or HTML report
    pdf = generate_pdf_report(report)
    
    # Email to stakeholders
    email.send(
        to=['marketing@example.com'],
        subject=f'Weekly Ad Performance Report - {start_date.strftime("%Y-%m-%d")}',
        attachments=[pdf]
    )

# Run every Monday at 9 AM
scheduler.add_job(generate_weekly_report, trigger='cron', day_of_week='mon', hour=9)
```

### Pattern: GDPR Data Export

Handle GDPR data export requests:

```python
def handle_gdpr_export_request(account_id):
    # Export all account data
    data = client.export_account_data(
        format='json',
        include_metrics=True
    )
    
    # Save to secure storage
    filename = f"gdpr_export_{account_id}_{datetime.now().strftime('%Y%m%d')}.json"
    secure_storage.save(filename, data)
    
    # Generate download link (expires in 7 days)
    download_link = secure_storage.generate_link(filename, expires_in=7*24*3600)
    
    # Email to user
    email.send(
        to=user.email,
        subject='Your Data Export is Ready',
        body=f'Download your data: {download_link}'
    )
```

---

## Error Handling and Retry Logic

### Pattern: Exponential Backoff

Implement exponential backoff for transient errors:

```python
import time
from requests.exceptions import HTTPError

def create_campaign_with_retry(max_retries=3, **campaign_params):
    for attempt in range(max_retries):
        try:
            return client.create_campaign(**campaign_params)
        except HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                retry_after = e.response.json()['error'].get('retry_after', 60)
                time.sleep(retry_after)
            elif e.response.status_code >= 500:  # Server error
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise  # Don't retry client errors
    
    raise Exception(f"Failed after {max_retries} attempts")
```

### Pattern: Circuit Breaker

Implement circuit breaker pattern to prevent cascading failures:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
    
    def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        self.failure_count = 0
        self.state = 'closed'
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'

# Usage
breaker = CircuitBreaker()
result = breaker.call(client.create_campaign, **params)
```

---

## Webhook Integration

### Pattern: Webhook Signature Verification

Verify webhook signatures for security:

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    """Verify webhook signature"""
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

@app.post("/webhook/campaign-update")
async def handle_campaign_update(request: Request):
    # Get signature from header
    signature = request.headers.get('X-Webhook-Signature')
    
    # Get raw payload
    payload = await request.body()
    
    # Verify signature
    if not verify_webhook_signature(payload.decode(), signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process webhook
    data = await request.json()
    process_campaign_update(data)
    
    return {"success": True}
```

---

## Multi-Campaign Management

### Pattern: Campaign Portfolio Optimization

Optimize budget allocation across multiple campaigns:

```python
def optimize_portfolio(total_budget):
    campaigns = client.list_campaigns(status='active')
    
    # Calculate performance scores
    scores = []
    for campaign in campaigns['campaigns']:
        metrics = client.get_performance(campaign['campaign_id'])
        
        # Score based on ROAS and conversion volume
        score = metrics['roas'] * metrics['total_conversions']
        scores.append({
            'campaign_id': campaign['campaign_id'],
            'score': score,
            'current_budget': campaign['monthly_budget']
        })
    
    # Allocate budget proportional to scores
    total_score = sum(s['score'] for s in scores)
    
    for campaign_score in scores:
        new_budget = total_budget * (campaign_score['score'] / total_score)
        
        # Update campaign budget
        client.update_campaign(
            campaign_score['campaign_id'],
            budget=new_budget
        )
```

### Pattern: A/B Testing Campaigns

Run A/B tests across campaigns:

```python
def create_ab_test(base_params, variations):
    """Create multiple campaign variations for A/B testing"""
    campaigns = []
    
    for i, variation in enumerate(variations):
        params = base_params.copy()
        params.update(variation)
        params['products'] = [f"{params['products'][0]} - Variant {i+1}"]
        
        campaign = client.create_campaign(**params)
        campaigns.append(campaign)
    
    return campaigns

# Example: Test different optimization modes
base_params = {
    'business_goal': 'increase_sales',
    'monthly_budget': 2500.0,
    'target_audience': 'small business owners',
    'products': ['CRM Software']
}

variations = [
    {'optimization_mode': 'standard'},
    {'optimization_mode': 'aggressive'}
]

test_campaigns = create_ab_test(base_params, variations)

# Monitor and compare after 7 days
def compare_ab_test_results(campaign_ids):
    results = []
    for campaign_id in campaign_ids:
        metrics = client.get_performance(campaign_id)
        results.append({
            'campaign_id': campaign_id,
            'roas': metrics['roas'],
            'conversions': metrics['total_conversions']
        })
    
    return results
```

---

## Best Practices Summary

1. **Always implement retry logic** for transient failures
2. **Use exponential backoff** when rate limited
3. **Poll campaign status** after creation until ready
4. **Monitor performance metrics** every 15 minutes
5. **Set up alerts** for low ROAS or high CPA
6. **Verify webhook signatures** for security
7. **Implement circuit breakers** to prevent cascading failures
8. **Export data regularly** for backup and compliance
9. **Optimize campaigns** based on performance thresholds
10. **Test integrations** in a development environment first

---

## Additional Resources

- [API Reference Documentation](./openapi_enhancements.md)
- [Python Client Example](./examples/python_client.py)
- [JavaScript Client Example](./examples/javascript_client.js)
- [cURL Examples](./examples/curl_examples.sh)
- [Error Codes Reference](./openapi_enhancements.md#error-codes)

## Support

For integration support:
- Email: api-support@example.com
- Documentation: https://docs.example.com/api
- Status Page: https://status.example.com
