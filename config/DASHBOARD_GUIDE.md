# Cloud Monitoring Dashboard Guide

This guide explains the comprehensive monitoring dashboard for the Adaptive Ad Intelligence Platform.

## Overview

The dashboard provides real-time visibility into:
- **System Health**: API performance, agent status, and error rates
- **Campaign Performance**: ROAS, spend, conversions, and optimization actions
- **Cost Tracking**: Budget utilization and infrastructure costs
- **Resource Monitoring**: Cloud Run, Firestore, and Vertex AI metrics

## Dashboard Sections

### 1. System Health Overview

#### API Request Latency (p50, p95, p99)
- **What it shows**: Request latency percentiles for all API endpoints
- **Why it matters**: Identifies performance degradation and slow endpoints
- **Thresholds**: 
  - p95 > 5 seconds triggers alert
  - Target: p95 < 3 seconds
- **Action items**:
  - If p95 > 5s: Check agent response times and external service latency
  - If p99 >> p95: Investigate outliers and timeout issues

#### API Request Rate & Error Rate
- **What it shows**: Total requests per second and failed requests per second
- **Why it matters**: Monitors traffic patterns and system reliability
- **Thresholds**:
  - Error rate > 5% triggers alert
  - Target: Error rate < 1%
- **Action items**:
  - High error rate: Check logs for error types and patterns
  - Sudden traffic spike: Verify auto-scaling is working

#### Active Campaigns
- **What it shows**: Current number of active campaigns
- **Why it matters**: Indicates platform usage and workload
- **Expected values**: Varies by customer base
- **Action items**:
  - Sudden drop: Check for campaign failures or pausing issues
  - Rapid growth: Ensure infrastructure can scale

### 2. Agent Performance

#### Agent Response Times by Agent (p95)
- **What it shows**: Response time for each specialist agent
- **Why it matters**: Identifies slow agents causing bottlenecks
- **Thresholds**:
  - p95 > 30 seconds triggers alert (causes timeouts)
  - Target: < 15 seconds for all agents
- **Action items**:
  - Creative Generator slow: Check Vertex AI latency
  - Audience Targeting slow: Review LLM prompt complexity
  - Budget Optimizer slow: Check Firestore query performance

#### Agent Failure Rate by Agent
- **What it shows**: Failures per second for each agent
- **Why it matters**: Indicates agent reliability and fallback usage
- **Thresholds**:
  - Failure rate > 10% triggers alert
  - Target: < 2% failure rate
- **Action items**:
  - High failures: Check agent logs for error types
  - Persistent failures: Review Vertex AI quota and availability
  - Multiple agents failing: Check network or authentication issues

#### Agent Fallback Usage
- **What it shows**: How often fallback strategies are used
- **Why it matters**: Fallbacks reduce campaign quality
- **Thresholds**:
  - Fallback rate > 20% triggers alert
  - Target: < 5% fallback usage
- **Action items**:
  - High fallback usage: Investigate root cause of agent failures
  - Specific agent: Focus troubleshooting on that agent

### 3. Bid Execution

#### Bid Execution Latency (p95)
- **What it shows**: Time to evaluate and submit bids
- **Why it matters**: Must be < 100ms to win bids
- **Thresholds**:
  - p95 > 100ms triggers alert
  - Target: p95 < 80ms
- **Action items**:
  - High latency: Check Firestore budget queries
  - Optimize segment matching algorithm
  - Review budget check caching

#### Bid Win Rate by Campaign
- **What it shows**: Percentage of bids won for each campaign
- **Why it matters**: Indicates bidding strategy effectiveness
- **Thresholds**:
  - Win rate < 15% triggers alert
  - Target: 20-40% win rate
- **Action items**:
  - Low win rate: Increase bid prices
  - High win rate (>40%): May be overbidding, reduce prices
  - Check competition levels and budget constraints

### 4. Campaign Performance Metrics

#### Campaign ROAS by Campaign
- **What it shows**: Return on Ad Spend for each campaign
- **Why it matters**: Primary success metric for campaigns
- **Thresholds**:
  - ROAS < 0.5 triggers alert (losing money)
  - ROAS < 1.0: Warning (not profitable)
  - ROAS > 3.0: Excellent performance
- **Action items**:
  - Low ROAS: Review creative variants and audience targeting
  - Trigger manual optimization
  - Consider pausing underperforming campaigns

#### Campaign Spend by Campaign
- **What it shows**: Cumulative spend for each campaign
- **Why it matters**: Tracks budget consumption
- **Expected values**: Should align with budget allocations
- **Action items**:
  - Rapid spend: Check bid prices and impression volume
  - Slow spend: May indicate low bid win rate or narrow targeting

#### Total Campaign Conversions
- **What it shows**: Conversion rate across all campaigns
- **Why it matters**: Indicates overall platform effectiveness
- **Expected values**: Varies by industry and campaign goals
- **Action items**:
  - Declining conversions: Review creative quality and targeting
  - Compare to industry benchmarks

#### Campaign Impressions & Clicks
- **What it shows**: Impression and click rates
- **Why it matters**: Top-of-funnel metrics for campaign reach
- **Expected values**: High impressions, moderate clicks
- **Action items**:
  - Low impressions: Check bid prices and targeting breadth
  - Low CTR: Review creative quality and relevance

#### Optimization Actions by Type
- **What it shows**: Automatic optimization actions taken
- **Why it matters**: Shows system is actively optimizing
- **Action types**:
  - pause_variant: Stopping underperforming creatives
  - scale_variant: Increasing budget for high performers
  - test_variant: Testing new creative variations
- **Action items**:
  - No actions: System may not be detecting opportunities
  - Excessive actions: May indicate unstable performance

### 5. Cost Tracking & Budget Utilization

#### Total Campaign Spend (24h)
- **What it shows**: Total ad spend across all campaigns in last 24 hours
- **Why it matters**: Daily cost tracking
- **Expected values**: Should align with daily budgets
- **Action items**:
  - Overspend: Check budget allocation and bid prices
  - Underspend: May indicate delivery issues

#### Budget Utilization Rate
- **What it shows**: Percentage of allocated budget spent
- **Why it matters**: Ensures budgets are being used effectively
- **Thresholds**:
  - > 90%: Warning (approaching limit)
  - > 105%: Alert (overspend)
- **Action items**:
  - High utilization: Consider increasing budgets for high performers
  - Low utilization: Review bid strategy and targeting

#### Cloud Run Instance Count
- **What it shows**: Number of active container instances
- **Why it matters**: Indicates scaling behavior and costs
- **Expected values**: 1-100 instances based on traffic
- **Action items**:
  - Constant max instances: May need to increase limit
  - Frequent scaling: Normal behavior, monitor costs

#### Cloud Run CPU Utilization
- **What it shows**: CPU usage across instances
- **Why it matters**: Indicates resource constraints
- **Thresholds**:
  - > 70%: Warning (may need more CPU)
  - Target: 40-60% average
- **Action items**:
  - High CPU: Consider increasing CPU allocation
  - Check for inefficient code or blocking operations

#### Cloud Run Memory Utilization
- **What it shows**: Memory usage across instances
- **Why it matters**: Prevents OOM errors
- **Thresholds**:
  - > 80%: Warning
  - Target: < 70% average
- **Action items**:
  - High memory: Check for memory leaks
  - Consider increasing memory allocation

#### Firestore Operations Rate
- **What it shows**: Database operations per second by type
- **Why it matters**: Indicates database load and costs
- **Operation types**: read, write, delete, query
- **Action items**:
  - High read rate: Consider caching
  - High write rate: Review batch operations
  - Monitor costs in billing dashboard

#### Vertex AI API Calls by Agent
- **What it shows**: LLM API calls per agent
- **Why it matters**: Primary cost driver for the platform
- **Expected values**: Varies by campaign creation rate
- **Action items**:
  - High call rate: Review prompt efficiency
  - Consider response caching for common requests
  - Monitor costs in billing dashboard

#### Estimated Infrastructure Cost
- **What it shows**: Monthly cost breakdown
- **Components**:
  - Cloud Run: ~$200
  - Vertex AI: ~$500
  - Firestore: ~$100
  - Cloud Logging: ~$50
  - Other: ~$150
- **Total**: ~$1,000/month (1000 campaigns)
- **Action items**:
  - Monitor actual costs in billing dashboard
  - Costs scale with usage
  - Optimize high-cost components

### 6. System Resources & External Services

#### Firestore Error Rate
- **What it shows**: Database operation failures
- **Why it matters**: Impacts all platform functionality
- **Thresholds**:
  - Error rate > 5% triggers alert
  - Target: < 1% error rate
- **Action items**:
  - Check Firestore service status
  - Review quota limits
  - Check for permission issues

#### Vertex AI Error Rate
- **What it shows**: LLM API call failures
- **Why it matters**: Causes agent failures
- **Thresholds**:
  - Error rate > 5% triggers alert
  - Target: < 1% error rate
- **Action items**:
  - Check Vertex AI service status
  - Review API quota limits
  - Check authentication

#### Campaign Creation Success Rate
- **What it shows**: Successful vs failed campaign creations
- **Why it matters**: Primary user-facing operation
- **Target**: > 95% success rate
- **Action items**:
  - High failures: Check agent coordination
  - Review validation errors
  - Check external service availability

#### Agent Communication Errors
- **What it shows**: Errors in agent-to-agent messaging
- **Why it matters**: Indicates coordination issues
- **Target**: Near zero errors
- **Action items**:
  - Check ADK configuration
  - Review message format validation
  - Check for timeout issues

#### Cloud Run Request Count
- **What it shows**: Total requests to the service
- **Why it matters**: Overall traffic monitoring
- **Expected values**: Varies by usage
- **Action items**:
  - Compare to API request metrics
  - Monitor for DDoS or unusual patterns

## Using the Dashboard

### Daily Monitoring

Check these metrics daily:
1. API error rate (should be < 1%)
2. Campaign ROAS (identify underperformers)
3. Total campaign spend (budget tracking)
4. Agent failure rates (should be < 2%)

### Weekly Review

Review these metrics weekly:
1. Cost trends (infrastructure and campaign spend)
2. Performance trends (ROAS, conversions)
3. Optimization action patterns
4. Resource utilization trends

### Incident Response

When alerts fire:
1. Check dashboard for affected metrics
2. Review related metrics for context
3. Check Cloud Logging for detailed errors
4. Follow action items for specific metrics

### Performance Optimization

Use dashboard to identify:
1. Slow agents (optimize or increase resources)
2. High-cost operations (optimize or cache)
3. Underperforming campaigns (optimize or pause)
4. Resource bottlenecks (scale or optimize)

## Deployment

### Deploy Dashboard

```bash
cd config
chmod +x deploy_dashboard.sh
./deploy_dashboard.sh
```

### Update Dashboard

Edit `config/monitoring_dashboard.json` and redeploy:

```bash
cd config
./deploy_dashboard.sh
```

### Access Dashboard

After deployment, access at:
```
https://console.cloud.google.com/monitoring/dashboards?project=YOUR_PROJECT_ID
```

Look for: "Adaptive Ad Intelligence Platform - Complete Dashboard"

## Customization

### Add New Metrics

1. Edit `config/monitoring_dashboard.json`
2. Add new tile to `tiles` array
3. Configure metric filter and visualization
4. Redeploy dashboard

### Modify Thresholds

Update threshold values in widget configurations:

```json
"thresholds": [{
  "value": 5.0,
  "color": "RED",
  "direction": "ABOVE"
}]
```

### Change Time Ranges

Modify `alignmentPeriod` in aggregations:
- `60s`: 1 minute (real-time)
- `300s`: 5 minutes (recent trends)
- `3600s`: 1 hour (hourly trends)

## Troubleshooting

### Dashboard Not Showing Data

1. Verify Cloud Run service is deployed
2. Check `/metrics` endpoint is accessible
3. Verify Prometheus scraping is configured
4. Check metric names match dashboard filters

### Missing Metrics

1. Check if metrics are being exported
2. Verify metric registration in code
3. Check for metric name typos
4. Review Cloud Logging for export errors

### Incorrect Values

1. Verify aggregation settings
2. Check time alignment periods
3. Review metric labels and filters
4. Compare with raw metric data

## Best Practices

1. **Monitor regularly**: Check dashboard daily
2. **Set up alerts**: Don't rely on manual monitoring
3. **Track trends**: Look for patterns over time
4. **Correlate metrics**: Use multiple metrics for diagnosis
5. **Document incidents**: Note what metrics indicated issues
6. **Iterate**: Refine thresholds based on experience
7. **Share access**: Ensure team can view dashboard
8. **Export data**: Use for reports and analysis

## References

- [Cloud Monitoring Documentation](https://cloud.google.com/monitoring/docs)
- [Dashboard Configuration](https://cloud.google.com/monitoring/dashboards)
- [Prometheus Metrics](https://prometheus.io/docs/concepts/metric_types/)
- [Alert Policies](../config/monitoring_alerts.yaml)
- [Monitoring Guide](../MONITORING.md)
