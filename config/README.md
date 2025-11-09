# Configuration Files

This directory contains configuration files for deploying and monitoring the Adaptive Ad Intelligence Platform on Google Cloud.

## Files Overview

### Deployment Configuration

#### `cloud_run_service.yaml`
Cloud Run service configuration including:
- Resource allocation (CPU, memory)
- Auto-scaling settings
- Environment variables
- VPC connector configuration

#### `adk_config.yaml`
Google Agent Development Kit (ADK) configuration for agent orchestration.

#### `deploy.sh`
Main deployment script for deploying the application to Cloud Run.

#### `gcloud_setup.sh`
Initial Google Cloud project setup script that:
- Enables required APIs
- Creates service accounts
- Sets up IAM permissions
- Configures Firestore and other services

### Monitoring Configuration

#### `monitoring_dashboard.json`
Comprehensive Cloud Monitoring dashboard configuration with 40+ widgets covering:
- **System Health**: API performance, agent status, error rates
- **Campaign Performance**: ROAS, spend, conversions, optimization actions
- **Cost Tracking**: Budget utilization, infrastructure costs
- **Resource Monitoring**: Cloud Run, Firestore, Vertex AI metrics

See [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md) for detailed documentation.

#### `monitoring_alerts.yaml`
Alert policy definitions for:
- API performance alerts (latency, error rate)
- Agent performance alerts (failures, timeouts, fallbacks)
- Bid execution alerts (latency, win rate)
- Campaign performance alerts (low ROAS)
- System resource alerts (Firestore, Vertex AI errors)

#### `setup_monitoring.sh`
Automated monitoring setup script that:
- Enables Cloud Monitoring APIs
- Creates notification channels
- Creates log-based metrics
- Deploys monitoring dashboard
- Configures alert policies

#### `deploy_dashboard.sh`
Dedicated script for deploying or updating the monitoring dashboard.

#### `DASHBOARD_GUIDE.md`
Comprehensive guide to using the monitoring dashboard including:
- Detailed explanation of each metric
- Threshold values and alerts
- Action items for each metric
- Daily monitoring checklist
- Troubleshooting guide

## Quick Start

### Initial Setup

1. **Set up Google Cloud project:**
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"
cd config
chmod +x gcloud_setup.sh
./gcloud_setup.sh
```

2. **Set up monitoring:**
```bash
chmod +x setup_monitoring.sh
./setup_monitoring.sh
```

3. **Deploy the application:**
```bash
chmod +x deploy.sh
./deploy.sh
```

### Deploy Monitoring Dashboard

```bash
cd config
chmod +x deploy_dashboard.sh
./deploy_dashboard.sh
```

The script will output the dashboard URL.

### Update Dashboard

After modifying `monitoring_dashboard.json`:

```bash
cd config
./deploy_dashboard.sh
```

### Configure Alerts

1. Create notification channels:
```bash
gcloud alpha monitoring channels create \
  --display-name="Team Email" \
  --type=email \
  --channel-labels=email_address=team@example.com
```

2. Get channel ID:
```bash
gcloud alpha monitoring channels list
```

3. Update `monitoring_alerts.yaml` with channel IDs

4. Deploy alerts (manual or via Terraform)

## Monitoring Dashboard

The dashboard provides real-time visibility into:

### System Health (12 widgets)
- API latency percentiles (p50, p95, p99)
- Request rate and error rate
- Active campaigns
- Agent response times
- Agent failure rates
- Agent fallback usage
- Bid execution latency
- Bid win rates

### Campaign Performance (6 widgets)
- ROAS by campaign
- Spend by campaign
- Total conversions
- Impressions and clicks
- Optimization actions

### Cost Tracking (8 widgets)
- Total campaign spend
- Budget utilization
- Cloud Run instances
- CPU and memory utilization
- Firestore operations
- Vertex AI API calls
- Cost estimates

### System Resources (6 widgets)
- Firestore error rate
- Vertex AI error rate
- Campaign creation success rate
- Agent communication errors
- Cloud Run request count

Total: 32 metric widgets + 8 informational widgets = 40 widgets

## Alert Policies

The platform includes 11 alert policies:

### API Alerts (2)
- High API Latency (p95 > 5s)
- High API Error Rate (> 5%)

### Agent Alerts (4)
- High Agent Failure Rate (> 10%)
- Agent Response Time Degradation (> 30s)
- High Fallback Usage (> 20%)

### Bid Execution Alerts (2)
- Bid Execution Latency (> 100ms)
- Low Bid Win Rate (< 15%)

### Campaign Alerts (1)
- Low Campaign ROAS (< 0.5)

### System Alerts (2)
- High Firestore Error Rate (> 5%)
- High Vertex AI Error Rate (> 5%)

## Log-Based Metrics

The setup script creates 3 log-based metrics:

1. **agent_communication_errors**: Count of agent communication errors
2. **campaign_creation_failures**: Count of campaign creation failures
3. **optimization_actions**: Count of optimization actions by type

These metrics are used in the dashboard and alert policies.

## Environment Variables

Required environment variables:

```bash
# Google Cloud
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"

# Application
export ENVIRONMENT="production"
export LOG_LEVEL="INFO"

# Secrets (stored in Secret Manager)
# - VERTEX_AI_API_KEY
# - FIRESTORE_CREDENTIALS
# - API_KEYS
```

## Cost Estimates

Based on 1000 active campaigns:

- **Cloud Run**: ~$200/month
  - 2 vCPU, 4GB memory
  - 1-100 instances
  - ~1M requests/month

- **Vertex AI**: ~$500/month
  - Gemini Flash model
  - ~100K API calls/month

- **Firestore**: ~$100/month
  - ~10M reads/month
  - ~1M writes/month

- **Cloud Logging**: ~$50/month
  - ~50GB logs/month
  - 30-day retention

- **Other Services**: ~$150/month
  - Cloud Monitoring
  - Secret Manager
  - Cloud Tasks
  - Pub/Sub

**Total**: ~$1,000/month

Actual costs vary based on usage. Monitor in billing dashboard.

## Troubleshooting

### Dashboard Not Showing Data

1. Verify Cloud Run service is deployed
2. Check `/metrics` endpoint: `curl https://your-service-url/metrics`
3. Verify Prometheus scraping is configured
4. Check metric names in dashboard match exported metrics

### Alerts Not Firing

1. Verify notification channels are configured
2. Check alert policy conditions
3. Verify metrics are being collected
4. Check alert policy is enabled

### High Costs

1. Review Vertex AI API usage (largest cost)
2. Check for inefficient Firestore queries
3. Review Cloud Run scaling settings
4. Consider response caching

### Deployment Failures

1. Check gcloud authentication: `gcloud auth list`
2. Verify project ID: `gcloud config get-value project`
3. Check API enablement: `gcloud services list --enabled`
4. Review deployment logs

## Best Practices

1. **Monitor daily**: Check dashboard for anomalies
2. **Set up alerts**: Configure notification channels
3. **Review costs weekly**: Monitor billing dashboard
4. **Update thresholds**: Adjust based on experience
5. **Document incidents**: Track what metrics indicated issues
6. **Test alerts**: Verify notifications are received
7. **Backup configs**: Version control all configuration files
8. **Review logs**: Check Cloud Logging for detailed errors

## References

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Monitoring Documentation](https://cloud.google.com/monitoring/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Dashboard Guide](DASHBOARD_GUIDE.md)
- [Main Monitoring Guide](../MONITORING.md)

## Support

For issues or questions:
1. Check [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md) for metric explanations
2. Review [../MONITORING.md](../MONITORING.md) for logging and metrics
3. Check Cloud Logging for detailed error messages
4. Review alert policy documentation in `monitoring_alerts.yaml`
