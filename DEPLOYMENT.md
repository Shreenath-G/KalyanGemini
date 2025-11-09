# Deployment Guide

This comprehensive guide covers deploying the Adaptive Ad Intelligence Platform to Google Cloud Run, including initial setup, configuration, CI/CD pipelines, and operational procedures.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Configuration](#configuration)
- [Deployment Methods](#deployment-methods)
- [CI/CD Pipelines](#cicd-pipelines)
- [Verification](#verification)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedures](#rollback-procedures)
- [Security Best Practices](#security-best-practices)
- [Cost Optimization](#cost-optimization)

## Prerequisites

### Required Tools

1. **Google Cloud Project**: Create a project with billing enabled
   - Project ID will be referenced as `PROJECT_ID`
   - Recommended region: `us-central1`

2. **Google Cloud SDK**: Install and authenticate `gcloud` CLI
   ```bash
   # Install gcloud CLI
   # Visit: https://cloud.google.com/sdk/docs/install
   
   # Authenticate
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Docker**: Install Docker for building container images
   ```bash
   # Visit: https://docs.docker.com/get-docker/
   # Verify installation
   docker --version
   ```

4. **Python 3.11+**: For local development and testing
   ```bash
   python --version  # Should be 3.11 or higher
   ```

### Required IAM Roles

Ensure your user account or service account has the following roles:

- **Cloud Run Admin** (`roles/run.admin`)
- **Service Account Admin** (`roles/iam.serviceAccountAdmin`)
- **Service Account User** (`roles/iam.serviceAccountUser`)
- **Secret Manager Admin** (`roles/secretmanager.admin`)
- **Firestore Admin** (`roles/datastore.owner`)
- **Vertex AI User** (`roles/aiplatform.user`)
- **Storage Admin** (`roles/storage.admin`)
- **Cloud Build Editor** (`roles/cloudbuild.builds.editor`)

### Required Google Cloud APIs

The following APIs must be enabled (automated by setup script):

- Cloud Run API
- Firestore API
- Vertex AI API
- Secret Manager API
- Cloud Logging API
- Cloud Monitoring API
- Cloud Tasks API
- Pub/Sub API
- Container Registry API
- Cloud Build API (for CI/CD)

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/adaptive-ad-intelligence.git
cd adaptive-ad-intelligence
```

### 2. Set Environment Variables

```bash
# Set your Google Cloud project ID and region
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_REGION="us-central1"

# Configure gcloud
gcloud config set project $GOOGLE_CLOUD_PROJECT
gcloud config set run/region $GOOGLE_CLOUD_REGION
```

### 3. Run Initial Setup Script

The setup script will:
- Enable all required Google Cloud APIs
- Create service accounts with proper permissions
- Set up Firestore database
- Configure IAM policies
- Create initial secrets in Secret Manager

```bash
cd config
chmod +x gcloud_setup.sh
./gcloud_setup.sh
```

**Expected output:**
```
✓ Enabling required APIs...
✓ Creating service accounts...
✓ Setting up Firestore...
✓ Configuring IAM policies...
✓ Creating secrets...
Setup complete!
```

### 4. Configure Secrets

Create and populate secrets in Secret Manager:

```bash
# Vertex AI API Key (if required beyond default credentials)
echo "your-vertex-ai-api-key" | gcloud secrets create vertex-ai-api-key \
  --data-file=- \
  --replication-policy="automatic"

# API Keys for client authentication
echo "your-api-key-1,your-api-key-2" | gcloud secrets create api-keys \
  --data-file=- \
  --replication-policy="automatic"

# Ad Platform API Keys
echo "your-google-ads-api-key" | gcloud secrets create ad-platform-google-key \
  --data-file=- \
  --replication-policy="automatic"

echo "your-meta-ads-api-key" | gcloud secrets create ad-platform-meta-key \
  --data-file=- \
  --replication-policy="automatic"

# Firestore credentials (if using custom service account)
gcloud secrets create firestore-credentials \
  --data-file=path/to/service-account.json \
  --replication-policy="automatic"
```

### 5. Grant Secret Access to Service Account

```bash
# Grant the Cloud Run service account access to secrets
for SECRET in vertex-ai-api-key api-keys ad-platform-google-key ad-platform-meta-key firestore-credentials; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:adaptive-ad-intelligence@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

### 6. Set Up VPC Connector (Optional)

If you need to access private resources (e.g., private Firestore, VPC-only services):

```bash
# Create VPC network (if not exists)
gcloud compute networks create adaptive-ad-vpc \
  --subnet-mode=custom

# Create subnet
gcloud compute networks subnets create adaptive-ad-subnet \
  --network=adaptive-ad-vpc \
  --region=$GOOGLE_CLOUD_REGION \
  --range=10.8.0.0/28

# Create VPC connector
gcloud compute networks vpc-access connectors create adaptive-ad-vpc-connector \
  --region=$GOOGLE_CLOUD_REGION \
  --subnet=adaptive-ad-subnet \
  --subnet-project=$GOOGLE_CLOUD_PROJECT \
  --min-instances=2 \
  --max-instances=10
```

Then update `config/cloud_run_service.yaml` to uncomment the VPC connector configuration.

## Configuration

### Environment Variables

The application uses the following environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Deployment environment | `production` | Yes |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | - | Yes |
| `GOOGLE_CLOUD_REGION` | GCP region | `us-central1` | Yes |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `VERTEX_AI_LOCATION` | Vertex AI region | `us-central1` | No |
| `VERTEX_AI_MODEL` | Vertex AI model name | `gemini-pro` | No |
| `ADK_CONFIG_PATH` | ADK configuration file path | `config/adk_config.yaml` | No |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | `100` | No |
| `AGENT_TIMEOUT_SECONDS` | Agent response timeout | `30` | No |
| `PERFORMANCE_CHECK_INTERVAL_MINUTES` | Performance monitoring interval | `15` | No |

### Secrets Configuration

Secrets are stored in Google Secret Manager and injected as environment variables:

| Secret Name | Description | Format |
|-------------|-------------|--------|
| `vertex-ai-api-key` | Vertex AI API key | String |
| `firestore-credentials` | Firestore service account JSON | JSON file |
| `api-keys` | Client API keys (comma-separated) | String |
| `ad-platform-google-key` | Google Ads API key | String |
| `ad-platform-meta-key` | Meta Ads API key | String |

### Scaling Configuration

Configure auto-scaling in `config/cloud_run_service.yaml`:

```yaml
annotations:
  autoscaling.knative.dev/minScale: '1'    # Minimum instances
  autoscaling.knative.dev/maxScale: '100'  # Maximum instances
  autoscaling.knative.dev/target: '80'     # Target concurrent requests
```

**Recommendations:**
- **Development**: minScale=0, maxScale=10
- **Staging**: minScale=1, maxScale=50
- **Production**: minScale=1, maxScale=100

### Resource Configuration

Configure CPU and memory in `config/cloud_run_service.yaml`:

```yaml
resources:
  limits:
    cpu: '2'      # 2 vCPU
    memory: 4Gi   # 4 GB RAM
```

**Recommendations:**
- **Light load** (<100 campaigns): cpu=1, memory=2Gi
- **Medium load** (100-1000 campaigns): cpu=2, memory=4Gi
- **Heavy load** (>1000 campaigns): cpu=4, memory=8Gi

## Deployment Methods

### Method 1: Using the Deployment Script (Recommended)

The deployment script automates the entire build and deployment process:

```bash
cd config
chmod +x deploy.sh
./deploy.sh
```

**What it does:**
1. Builds Docker image
2. Pushes to Google Container Registry
3. Deploys to Cloud Run
4. Outputs service URL and health check endpoint

### Method 2: Manual Deployment

For more control over the deployment process:

#### Step 1: Build Docker Image

```bash
docker build \
  --tag gcr.io/$GOOGLE_CLOUD_PROJECT/adaptive-ad-intelligence:latest \
  --tag gcr.io/$GOOGLE_CLOUD_PROJECT/adaptive-ad-intelligence:$(git rev-parse --short HEAD) \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse HEAD) \
  .
```

#### Step 2: Push to Container Registry

```bash
# Configure Docker to use gcloud credentials
gcloud auth configure-docker

# Push images
docker push gcr.io/$GOOGLE_CLOUD_PROJECT/adaptive-ad-intelligence:latest
docker push gcr.io/$GOOGLE_CLOUD_PROJECT/adaptive-ad-intelligence:$(git rev-parse --short HEAD)
```

#### Step 3: Deploy to Cloud Run

```bash
gcloud run deploy adaptive-ad-intelligence \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/adaptive-ad-intelligence:latest \
  --platform managed \
  --region $GOOGLE_CLOUD_REGION \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 100 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 80 \
  --service-account "adaptive-ad-intelligence@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
  --set-env-vars "ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_REGION=$GOOGLE_CLOUD_REGION,LOG_LEVEL=INFO" \
  --set-secrets "VERTEX_AI_API_KEY=vertex-ai-api-key:latest,FIRESTORE_CREDENTIALS=firestore-credentials:latest,API_KEYS=api-keys:latest,AD_PLATFORM_GOOGLE_KEY=ad-platform-google-key:latest,AD_PLATFORM_META_KEY=ad-platform-meta-key:latest" \
  --labels "environment=production,app=adaptive-ad-intelligence"
```

### Method 3: Using Cloud Run YAML Configuration

Deploy using the YAML configuration file:

```bash
# Update PROJECT_ID in config/cloud_run_service.yaml
sed -i "s/PROJECT_ID/$GOOGLE_CLOUD_PROJECT/g" config/cloud_run_service.yaml

# Deploy using YAML
gcloud run services replace config/cloud_run_service.yaml \
  --region $GOOGLE_CLOUD_REGION
```

## CI/CD Pipelines

The platform supports automated deployment via CI/CD pipelines. See [config/CI_CD_SETUP.md](config/CI_CD_SETUP.md) for detailed setup instructions.

### GitHub Actions

Automated deployment on push to `main` branch:

1. **Setup**: Configure GitHub secrets (see CI_CD_SETUP.md)
2. **Workflow**: `.github/workflows/deploy.yml`
3. **Trigger**: Push to main or manual trigger
4. **Steps**: Test → Build → Deploy → Verify

### Google Cloud Build

Automated deployment using Cloud Build triggers:

1. **Setup**: Configure Cloud Build permissions (see CI_CD_SETUP.md)
2. **Configuration**: `cloudbuild.yaml`
3. **Trigger**: Push to main or manual trigger
4. **Steps**: Test → Build → Push → Deploy → Verify

### Quick CI/CD Setup

```bash
# For GitHub Actions
# 1. Add secrets to GitHub repository
# 2. Push to main branch

# For Cloud Build
gcloud builds submit --config=cloudbuild.yaml .
```

## Verification

### 1. Get Service URL

```bash
SERVICE_URL=$(gcloud run services describe adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --format 'value(status.url)')

echo "Service URL: $SERVICE_URL"
```

### 2. Test Health Endpoint

```bash
curl $SERVICE_URL/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "agents": {
    "campaign_orchestrator": "ready",
    ...
  }
}
```

### 3. Access API Documentation

Open in browser:
```
$SERVICE_URL/docs
```

## Post-Deployment Configuration

### Update Environment Variables

```bash
gcloud run services update adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --set-env-vars "LOG_LEVEL=DEBUG,RATE_LIMIT_PER_MINUTE=200"
```

### Update Scaling Configuration

```bash
gcloud run services update adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --min-instances 2 \
  --max-instances 200 \
  --concurrency 100
```

### Update Resource Limits

```bash
gcloud run services update adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --memory 8Gi \
  --cpu 4
```

### Update Secrets

```bash
# Update a secret value
echo "new-api-key" | gcloud secrets versions add vertex-ai-api-key --data-file=-

# Cloud Run will automatically use the latest version
# Or specify a specific version in cloud_run_service.yaml
```

## Monitoring

### View Logs

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=adaptive-ad-intelligence" \
  --limit 50 \
  --format json
```

### Monitor Metrics

Access Cloud Monitoring dashboard:
```
https://console.cloud.google.com/monitoring
```

Key metrics to monitor:
- Request latency (p50, p95, p99)
- Request count
- Error rate
- Container instance count
- CPU and memory utilization

### Set Up Alerts

Create alert policies for:
- High error rate (>5%)
- High latency (>5s)
- Low availability (<99%)

## Troubleshooting

### Container Fails to Start

Check logs:
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit 100
```

Common issues:
- Missing environment variables
- Invalid credentials
- Port configuration mismatch

### High Latency

- Check agent timeout settings in `config/adk_config.yaml`
- Increase CPU/memory allocation
- Review Vertex AI API quotas

### Authentication Errors

- Verify service account permissions
- Check Secret Manager access
- Ensure API keys are valid

## Rollback Procedures

### Quick Rollback to Previous Revision

```bash
# List recent revisions
gcloud run revisions list \
  --service adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --limit 10

# Rollback to specific revision (100% traffic)
gcloud run services update-traffic adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --to-revisions REVISION_NAME=100
```

### Gradual Rollback (Canary)

```bash
# Route 90% to previous revision, 10% to current
gcloud run services update-traffic adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --to-revisions PREVIOUS_REVISION=90,CURRENT_REVISION=10

# Monitor metrics, then complete rollback
gcloud run services update-traffic adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --to-revisions PREVIOUS_REVISION=100
```

### Rollback via Re-deployment

```bash
# Deploy a specific image tag
gcloud run deploy adaptive-ad-intelligence \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/adaptive-ad-intelligence:COMMIT_SHA \
  --region $GOOGLE_CLOUD_REGION
```

### Emergency Rollback Checklist

1. **Identify the issue**: Check logs and metrics
2. **Find last good revision**: `gcloud run revisions list`
3. **Execute rollback**: Use commands above
4. **Verify health**: Check `/api/health` endpoint
5. **Monitor metrics**: Watch for 5-10 minutes
6. **Document incident**: Record what happened and why

## Advanced Deployment Scenarios

### Blue-Green Deployment

Deploy new version alongside existing version:

```bash
# Deploy new version with tag
gcloud run deploy adaptive-ad-intelligence-green \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/adaptive-ad-intelligence:new-version \
  --region $GOOGLE_CLOUD_REGION \
  --no-traffic

# Test the green deployment
curl https://adaptive-ad-intelligence-green-xxx.run.app/api/health

# Switch traffic
gcloud run services update-traffic adaptive-ad-intelligence \
  --to-revisions adaptive-ad-intelligence-green=100
```

### Canary Deployment

Gradually roll out new version:

```bash
# Deploy new revision with no traffic
gcloud run deploy adaptive-ad-intelligence \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/adaptive-ad-intelligence:new-version \
  --region $GOOGLE_CLOUD_REGION \
  --no-traffic

# Route 10% traffic to new revision
gcloud run services update-traffic adaptive-ad-intelligence \
  --to-revisions NEW_REVISION=10,OLD_REVISION=90

# Monitor metrics for 30 minutes

# Increase to 50%
gcloud run services update-traffic adaptive-ad-intelligence \
  --to-revisions NEW_REVISION=50,OLD_REVISION=50

# Complete rollout
gcloud run services update-traffic adaptive-ad-intelligence \
  --to-latest
```

### Multi-Region Deployment

Deploy to multiple regions for high availability:

```bash
# Deploy to us-central1
gcloud run deploy adaptive-ad-intelligence \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/adaptive-ad-intelligence:latest \
  --region us-central1

# Deploy to europe-west1
gcloud run deploy adaptive-ad-intelligence \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/adaptive-ad-intelligence:latest \
  --region europe-west1

# Deploy to asia-east1
gcloud run deploy adaptive-ad-intelligence \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/adaptive-ad-intelligence:latest \
  --region asia-east1

# Set up global load balancer (requires additional configuration)
```

## Operational Procedures

### Daily Operations

**Morning Checklist:**
1. Check Cloud Monitoring dashboard
2. Review error logs from past 24 hours
3. Verify all agents are responding
4. Check campaign performance metrics
5. Review cost and budget utilization

**Commands:**
```bash
# Check service status
gcloud run services describe adaptive-ad-intelligence --region $GOOGLE_CLOUD_REGION

# View recent logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50 --format=json

# Check error rate
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=20
```

### Scaling Operations

**Scale up for high traffic:**
```bash
gcloud run services update adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --min-instances 5 \
  --max-instances 200
```

**Scale down for cost savings:**
```bash
gcloud run services update adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --min-instances 1 \
  --max-instances 50
```

### Maintenance Windows

**Schedule maintenance:**
1. Announce maintenance window to users
2. Scale down to minimum instances
3. Perform updates/changes
4. Verify health checks
5. Scale back up
6. Monitor for issues

**Maintenance deployment:**
```bash
# Scale down
gcloud run services update adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --min-instances 0 \
  --max-instances 10

# Deploy changes
./config/deploy.sh

# Verify
curl https://your-service-url/api/health

# Scale back up
gcloud run services update adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --min-instances 1 \
  --max-instances 100
```

### Backup and Recovery

**Backup Firestore data:**
```bash
# Export Firestore data
gcloud firestore export gs://$GOOGLE_CLOUD_PROJECT-backups/$(date +%Y%m%d)

# List backups
gsutil ls gs://$GOOGLE_CLOUD_PROJECT-backups/
```

**Restore from backup:**
```bash
# Import Firestore data
gcloud firestore import gs://$GOOGLE_CLOUD_PROJECT-backups/20240101
```

**Backup secrets:**
```bash
# Export all secret values (store securely!)
for SECRET in vertex-ai-api-key api-keys ad-platform-google-key ad-platform-meta-key; do
  gcloud secrets versions access latest --secret=$SECRET > backup-$SECRET.txt
done
```

### Disaster Recovery

**Complete service failure:**
1. Check Cloud Run service status
2. Review recent deployments
3. Rollback to last known good revision
4. Check Firestore connectivity
5. Verify Secret Manager access
6. Check Vertex AI API status

**Recovery steps:**
```bash
# 1. Check service status
gcloud run services describe adaptive-ad-intelligence --region $GOOGLE_CLOUD_REGION

# 2. View recent revisions
gcloud run revisions list --service adaptive-ad-intelligence --region $GOOGLE_CLOUD_REGION

# 3. Rollback if needed
gcloud run services update-traffic adaptive-ad-intelligence \
  --to-revisions LAST_GOOD_REVISION=100 \
  --region $GOOGLE_CLOUD_REGION

# 4. Force new deployment
gcloud run services update adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --update-env-vars FORCE_RESTART=$(date +%s)
```

## Security Best Practices

### Authentication and Authorization

1. **API Key Management**
   - Store API keys in Secret Manager
   - Rotate keys every 90 days
   - Use separate keys for different environments
   - Monitor key usage

2. **Service Account Security**
   - Use least privilege principle
   - Separate service accounts per environment
   - Regularly audit permissions
   - Enable service account key rotation

3. **Network Security**
   - Use VPC connector for private resources
   - Enable Cloud Armor for DDoS protection
   - Implement rate limiting (100 req/min)
   - Use TLS 1.3 for all communications

### Data Protection

1. **Encryption**
   - Data at rest: AES-256 (Firestore default)
   - Data in transit: TLS 1.3 (enforced)
   - Secrets: Encrypted in Secret Manager

2. **Access Control**
   - Account-level data isolation
   - Role-based access control (RBAC)
   - Campaign ownership validation
   - Audit logging enabled

3. **Compliance**
   - 90-day data retention policy
   - Data export capabilities
   - GDPR compliance measures
   - Regular security audits

### Security Checklist

- [ ] All secrets stored in Secret Manager
- [ ] Service accounts use least privilege
- [ ] TLS 1.3 enforced for all endpoints
- [ ] Rate limiting configured (100 req/min)
- [ ] Audit logging enabled
- [ ] VPC connector configured (if needed)
- [ ] Cloud Armor enabled
- [ ] Regular security scans scheduled
- [ ] Incident response plan documented
- [ ] Security contacts configured

### Security Monitoring

```bash
# Check for unauthorized access attempts
gcloud logging read "resource.type=cloud_run_revision AND httpRequest.status>=400" --limit=50

# Monitor secret access
gcloud logging read "resource.type=secretmanager.googleapis.com/Secret" --limit=50

# Check IAM policy changes
gcloud logging read "protoPayload.methodName=SetIamPolicy" --limit=20
```

## Cost Optimization

### Cost Breakdown (Estimated for 1000 campaigns/month)

| Service | Monthly Cost | Optimization Tips |
|---------|--------------|-------------------|
| Cloud Run | ~$200 | Adjust min instances, use CPU throttling |
| Vertex AI | ~$500 | Use efficient models, cache responses |
| Firestore | ~$100 | Optimize queries, use batch operations |
| Cloud Logging | ~$50 | Adjust retention, filter logs |
| Other Services | ~$150 | Monitor usage, disable unused features |
| **Total** | **~$1,000** | |

### Cost Optimization Strategies

1. **Cloud Run Optimization**
   ```bash
   # Reduce minimum instances during low traffic
   gcloud run services update adaptive-ad-intelligence \
     --region $GOOGLE_CLOUD_REGION \
     --min-instances 0  # Allow scale to zero
   
   # Enable CPU throttling (reduces cost when idle)
   # Already configured in cloud_run_service.yaml
   ```

2. **Vertex AI Optimization**
   - Use Gemini Flash instead of Gemini Pro for faster, cheaper responses
   - Implement response caching for common queries
   - Batch requests when possible
   - Set appropriate token limits

3. **Firestore Optimization**
   ```bash
   # Create indexes for common queries
   gcloud firestore indexes composite create \
     --collection-group=campaigns \
     --field-config field-path=account_id,order=ASCENDING \
     --field-config field-path=created_at,order=DESCENDING
   
   # Archive old campaigns
   # Implement data lifecycle policies
   ```

4. **Logging Optimization**
   ```bash
   # Reduce log retention
   gcloud logging sinks update _Default \
     --log-filter='resource.type="cloud_run_revision" AND severity>=WARNING'
   
   # Set retention to 7 days for debug logs
   ```

5. **Monitoring Costs**
   ```bash
   # View current month costs
   gcloud billing accounts list
   
   # Set up budget alerts
   gcloud billing budgets create \
     --billing-account=BILLING_ACCOUNT_ID \
     --display-name="Adaptive Ad Intelligence Budget" \
     --budget-amount=1500 \
     --threshold-rule=percent=80 \
     --threshold-rule=percent=100
   ```

### Cost Monitoring Commands

```bash
# View Cloud Run costs
gcloud run services describe adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --format="value(status.url)"

# Check instance count
gcloud run services describe adaptive-ad-intelligence \
  --region $GOOGLE_CLOUD_REGION \
  --format="value(spec.template.metadata.annotations)"

# View Firestore usage
gcloud firestore operations list

# Monitor Vertex AI usage
gcloud ai models list --region=$GOOGLE_CLOUD_REGION
```

### Cost Alerts Setup

```bash
# Create budget alert
gcloud billing budgets create \
  --billing-account=$(gcloud billing accounts list --format="value(name)" --limit=1) \
  --display-name="Monthly Budget Alert" \
  --budget-amount=1500 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=80 \
  --threshold-rule=percent=100 \
  --threshold-rule=percent=120
```

## Reference Documentation

### Related Documentation

- [CI/CD Setup Guide](config/CI_CD_SETUP.md) - Detailed CI/CD pipeline setup
- [Monitoring Guide](MONITORING.md) - Logging and metrics configuration
- [Development Guide](DEVELOPMENT.md) - Local development setup
- [Dashboard Guide](config/DASHBOARD_GUIDE.md) - Monitoring dashboard usage
- [Security Implementation](SECURITY_IMPLEMENTATION_SUMMARY.md) - Security features

### Useful Commands Reference

```bash
# Service Management
gcloud run services list
gcloud run services describe SERVICE_NAME --region REGION
gcloud run services delete SERVICE_NAME --region REGION

# Revision Management
gcloud run revisions list --service SERVICE_NAME --region REGION
gcloud run revisions describe REVISION_NAME --region REGION
gcloud run revisions delete REVISION_NAME --region REGION

# Traffic Management
gcloud run services update-traffic SERVICE_NAME --to-latest
gcloud run services update-traffic SERVICE_NAME --to-revisions REV1=50,REV2=50

# Logs and Monitoring
gcloud logging read "resource.type=cloud_run_revision" --limit=100
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR"
gcloud monitoring dashboards list

# Secret Management
gcloud secrets list
gcloud secrets versions access latest --secret=SECRET_NAME
gcloud secrets versions add SECRET_NAME --data-file=FILE

# IAM Management
gcloud projects get-iam-policy PROJECT_ID
gcloud run services get-iam-policy SERVICE_NAME --region REGION
gcloud run services add-iam-policy-binding SERVICE_NAME --member=USER --role=ROLE
```

### Environment-Specific Configurations

#### Development Environment
```bash
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG
export MIN_INSTANCES=0
export MAX_INSTANCES=10
```

#### Staging Environment
```bash
export ENVIRONMENT=staging
export LOG_LEVEL=INFO
export MIN_INSTANCES=1
export MAX_INSTANCES=50
```

#### Production Environment
```bash
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export MIN_INSTANCES=1
export MAX_INSTANCES=100
```

## Support and Troubleshooting

### Getting Help

1. **Check Documentation**
   - Review this deployment guide
   - Check troubleshooting section above
   - Review related documentation

2. **Check Logs**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision" --limit=100
   ```

3. **Check Service Status**
   ```bash
   gcloud run services describe adaptive-ad-intelligence --region $GOOGLE_CLOUD_REGION
   ```

4. **Contact Support**
   - Email: devops@example.com
   - Slack: #adaptive-ad-intelligence
   - On-call: Check PagerDuty

### Incident Response

**Severity Levels:**
- **P0 (Critical)**: Service completely down, immediate response required
- **P1 (High)**: Major functionality impaired, response within 1 hour
- **P2 (Medium)**: Minor functionality impaired, response within 4 hours
- **P3 (Low)**: Cosmetic issues, response within 24 hours

**Incident Response Steps:**
1. Assess severity and impact
2. Notify stakeholders
3. Begin investigation (check logs, metrics, recent changes)
4. Implement fix or rollback
5. Verify resolution
6. Document incident and post-mortem

### Emergency Contacts

- **DevOps Team**: devops@example.com
- **Platform Team**: platform@example.com
- **Security Team**: security@example.com
- **On-Call Engineer**: Check PagerDuty rotation

## Appendix

### Deployment Checklist

Pre-Deployment:
- [ ] Code reviewed and approved
- [ ] Tests passing (unit, integration)
- [ ] Security scan completed
- [ ] Documentation updated
- [ ] Stakeholders notified

Deployment:
- [ ] Backup current state
- [ ] Deploy to staging first
- [ ] Run smoke tests
- [ ] Deploy to production
- [ ] Verify health checks
- [ ] Monitor metrics for 30 minutes

Post-Deployment:
- [ ] Verify all features working
- [ ] Check error rates
- [ ] Monitor performance metrics
- [ ] Update deployment log
- [ ] Notify stakeholders of completion

### Rollback Checklist

- [ ] Identify issue and severity
- [ ] Notify stakeholders
- [ ] Find last known good revision
- [ ] Execute rollback
- [ ] Verify health checks
- [ ] Monitor for 15 minutes
- [ ] Document incident
- [ ] Schedule post-mortem

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| 503 Service Unavailable | Cold start or scaling | Increase min instances |
| 504 Gateway Timeout | Long-running request | Increase timeout or optimize code |
| 401 Unauthorized | Invalid API key | Check Secret Manager configuration |
| 500 Internal Server Error | Application error | Check logs for stack trace |
| High latency | Resource constraints | Increase CPU/memory |
| High costs | Over-provisioning | Optimize scaling settings |

### Version History

| Version | Date | Changes | Deployed By |
|---------|------|---------|-------------|
| 1.0.0 | 2024-01-15 | Initial deployment | DevOps Team |
| 1.1.0 | 2024-02-01 | Added monitoring | DevOps Team |
| 1.2.0 | 2024-03-01 | Performance improvements | Platform Team |

---

**Last Updated**: 2024-03-15  
**Maintained By**: DevOps Team  
**Review Schedule**: Quarterly
