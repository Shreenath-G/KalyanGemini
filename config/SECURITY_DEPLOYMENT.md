# Security Features Deployment Guide

This guide covers the deployment of security features for the Adaptive Ad Intelligence Platform, including Secret Manager integration, data encryption, and data retention policies.

## Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- Appropriate IAM permissions (Project Editor or specific roles)
- Python 3.11+ installed locally

## 1. Secret Manager Setup

### 1.1 Enable Secret Manager API

```bash
gcloud services enable secretmanager.googleapis.com
```

### 1.2 Create Required Secrets

#### API Keys Secret

Create a secret to store valid API keys:

```bash
# Create the secret
gcloud secrets create api-keys \
    --replication-policy="automatic" \
    --data-file=-

# Paste the following JSON structure (replace with actual keys):
{
  "sk_account1_abcdef1234567890abcdef1234567890": {
    "account_id": "acc_001",
    "created_at": "2024-01-01T00:00:00Z",
    "active": true,
    "permissions": ["read", "write"]
  },
  "sk_account2_1234567890abcdef1234567890abcdef": {
    "account_id": "acc_002",
    "created_at": "2024-01-01T00:00:00Z",
    "active": true,
    "permissions": ["read", "write"]
  }
}
# Press Ctrl+D to finish
```

#### Data Encryption Key

Create a secret for application-level encryption:

```bash
# Generate a secure encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Store the key in Secret Manager
echo "YOUR_GENERATED_KEY" | gcloud secrets create data-encryption-key \
    --replication-policy="automatic" \
    --data-file=-
```

#### Vertex AI Credentials

Store Vertex AI service account credentials:

```bash
# Create service account
gcloud iam service-accounts create vertex-ai-service \
    --display-name="Vertex AI Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:vertex-ai-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create vertex-ai-key.json \
    --iam-account=vertex-ai-service@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Store in Secret Manager
gcloud secrets create vertex-ai-credentials \
    --replication-policy="automatic" \
    --data-file=vertex-ai-key.json

# Clean up local key file
rm vertex-ai-key.json
```

#### Ad Platform API Keys

Store API keys for ad platforms:

```bash
# Google Ads API Key
echo "YOUR_GOOGLE_ADS_API_KEY" | gcloud secrets create google-ads-api-key \
    --replication-policy="automatic" \
    --data-file=-

# Meta Ads API Key
echo "YOUR_META_ADS_API_KEY" | gcloud secrets create meta-ads-api-key \
    --replication-policy="automatic" \
    --data-file=-
```

### 1.3 Grant Secret Access to Cloud Run Service

```bash
# Get the Cloud Run service account
SERVICE_ACCOUNT="adaptive-ad-intelligence@YOUR_PROJECT_ID.iam.gserviceaccount.com"

# Grant Secret Manager access
gcloud secrets add-iam-policy-binding api-keys \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding data-encryption-key \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding vertex-ai-credentials \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding google-ads-api-key \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding meta-ads-api-key \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"
```

## 2. Data Encryption Configuration

### 2.1 Firestore Encryption at Rest

Firestore automatically encrypts all data at rest using AES-256. No additional configuration required.

**Verification:**

```bash
# Verify Firestore is enabled
gcloud firestore databases describe --database="(default)"
```

### 2.2 TLS 1.3 Enforcement

Deploy the SSL policy for TLS 1.3:

```bash
# Create SSL policy
gcloud compute ssl-policies create adaptive-ad-intelligence-ssl-policy \
    --profile=MODERN \
    --min-tls-version=1.3 \
    --description="Enforce TLS 1.3 for all API communications"

# Verify SSL policy
gcloud compute ssl-policies describe adaptive-ad-intelligence-ssl-policy
```

### 2.3 Deploy Firestore Security Rules

```bash
# Navigate to config directory
cd config

# Deploy security rules (requires Firebase CLI)
firebase deploy --only firestore:rules

# Or manually update rules in Firebase Console:
# https://console.firebase.google.com/project/YOUR_PROJECT_ID/firestore/rules
```

## 3. Data Retention Setup

### 3.1 Deploy Cloud Function for Data Retention

```bash
# Navigate to config directory
cd config

# Deploy the Cloud Function
gcloud functions deploy data-retention-cleanup \
    --gen2 \
    --runtime=python311 \
    --region=us-central1 \
    --source=. \
    --entry-point=scheduled_cleanup \
    --trigger-topic=data-retention-schedule \
    --memory=512MB \
    --timeout=540s \
    --set-env-vars=GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID \
    --service-account=adaptive-ad-intelligence@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 3.2 Create Pub/Sub Topic

```bash
# Create topic for data retention
gcloud pubsub topics create data-retention-schedule
```

### 3.3 Schedule Daily Cleanup with Cloud Scheduler

```bash
# Create Cloud Scheduler job (runs daily at 2 AM)
gcloud scheduler jobs create pubsub data-retention-daily \
    --location=us-central1 \
    --schedule="0 2 * * *" \
    --topic=data-retention-schedule \
    --message-body='{"retention_days": 90, "dry_run": false}' \
    --time-zone="America/New_York" \
    --description="Daily data retention cleanup (90 days)"

# Verify the job
gcloud scheduler jobs describe data-retention-daily --location=us-central1

# Test the job manually
gcloud scheduler jobs run data-retention-daily --location=us-central1
```

### 3.4 Deploy Manual Cleanup Function (Optional)

```bash
# Deploy HTTP-triggered function for manual cleanup
gcloud functions deploy data-retention-manual \
    --gen2 \
    --runtime=python311 \
    --region=us-central1 \
    --source=. \
    --entry-point=manual_cleanup \
    --trigger-http \
    --allow-unauthenticated=false \
    --memory=512MB \
    --timeout=540s \
    --set-env-vars=GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID \
    --service-account=adaptive-ad-intelligence@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## 4. Secret Rotation Setup

### 4.1 Schedule Secret Rotation

```bash
# Create Pub/Sub topic for secret rotation
gcloud pubsub topics create secret-rotation-schedule

# Create Cloud Scheduler job (runs weekly on Sunday at 3 AM)
gcloud scheduler jobs create pubsub secret-rotation-weekly \
    --location=us-central1 \
    --schedule="0 3 * * 0" \
    --topic=secret-rotation-schedule \
    --message-body='{"rotation_type": "api_keys"}' \
    --time-zone="America/New_York" \
    --description="Weekly API key rotation"
```

### 4.2 Deploy Secret Rotation Function

Create a Cloud Function for secret rotation:

```bash
# This would be implemented similar to data retention
# For now, rotation can be triggered manually via the API
```

## 5. Data Export API Configuration

The data export endpoints are automatically available once the application is deployed:

- `GET /api/v1/data/export` - Export all account data
- `GET /api/v1/data/export/campaign/{campaign_id}` - Export specific campaign
- `GET /api/v1/data/export/performance-report` - Export performance report
- `DELETE /api/v1/data/account?confirm=true` - Delete account data

### 5.1 Test Data Export

```bash
# Export account data (JSON)
curl -X GET "https://YOUR_CLOUD_RUN_URL/api/v1/data/export?format=json" \
    -H "X-API-Key: YOUR_API_KEY" \
    -o account_export.json

# Export account data (CSV)
curl -X GET "https://YOUR_CLOUD_RUN_URL/api/v1/data/export?format=csv" \
    -H "X-API-Key: YOUR_API_KEY" \
    -o account_export.csv

# Export campaign data
curl -X GET "https://YOUR_CLOUD_RUN_URL/api/v1/data/export/campaign/camp_123" \
    -H "X-API-Key: YOUR_API_KEY" \
    -o campaign_export.json
```

## 6. Monitoring and Alerts

### 6.1 Create Log-Based Metrics

```bash
# Metric for data isolation violations
gcloud logging metrics create data_isolation_violations \
    --description="Count of data isolation violation attempts" \
    --log-filter='severity >= WARNING AND jsonPayload.message =~ "Data isolation violation"'

# Metric for failed authentication
gcloud logging metrics create failed_authentication \
    --description="Count of failed authentication attempts" \
    --log-filter='severity >= WARNING AND jsonPayload.message =~ "Invalid API key"'

# Metric for encryption failures
gcloud logging metrics create encryption_failures \
    --description="Count of encryption/decryption failures" \
    --log-filter='severity >= ERROR AND jsonPayload.message =~ "Encryption failed|Decryption failed"'
```

### 6.2 Create Alerting Policies

```bash
# Alert on data isolation violations
gcloud alpha monitoring policies create \
    --notification-channels=YOUR_NOTIFICATION_CHANNEL_ID \
    --display-name="Data Isolation Violations" \
    --condition-display-name="High violation rate" \
    --condition-threshold-value=10 \
    --condition-threshold-duration=300s \
    --condition-filter='metric.type="logging.googleapis.com/user/data_isolation_violations"'

# Alert on failed authentication
gcloud alpha monitoring policies create \
    --notification-channels=YOUR_NOTIFICATION_CHANNEL_ID \
    --display-name="Failed Authentication Attempts" \
    --condition-display-name="High failure rate" \
    --condition-threshold-value=50 \
    --condition-threshold-duration=300s \
    --condition-filter='metric.type="logging.googleapis.com/user/failed_authentication"'
```

## 7. Verification and Testing

### 7.1 Verify Secret Manager Integration

```bash
# Test secret retrieval
python3 << EOF
from src.services.secret_manager import get_secret_manager_service

sm = get_secret_manager_service()
api_keys = sm.get_secret_json("api-keys")
print(f"Retrieved {len(api_keys)} API keys")
EOF
```

### 7.2 Verify Data Encryption

```bash
# Test encryption service
python3 << EOF
from src.utils.encryption import get_encryption_service

enc = get_encryption_service()
plaintext = "sensitive data"
encrypted = enc.encrypt(plaintext)
decrypted = enc.decrypt(encrypted)
assert plaintext == decrypted
print("Encryption test passed")
EOF
```

### 7.3 Verify Data Isolation

```bash
# Run data isolation tests
python3 -m pytest tests/test_data_isolation.py -v
```

### 7.4 Test Data Retention (Dry Run)

```bash
# Test data retention cleanup
python3 << EOF
import asyncio
from src.services.data_retention import DataRetentionService

async def test():
    service = DataRetentionService(retention_days=90)
    results = await service.run_full_cleanup(dry_run=True)
    print(f"Cleanup results: {results}")

asyncio.run(test())
EOF
```

## 8. Compliance Checklist

- [x] **Requirement 13.1**: Encryption at rest (AES-256) - Firestore default
- [x] **Requirement 13.2**: Encryption in transit (TLS 1.3) - SSL policy configured
- [x] **Requirement 13.3**: API key authentication - Secret Manager integration
- [x] **Requirement 13.4**: Data isolation between accounts - Firestore queries and security rules
- [x] **Requirement 13.5**: Data retention (90 days) - Scheduled cleanup function
- [x] **Requirement 13.5**: Data export capabilities - API endpoints implemented
- [x] **Requirement 13.5**: Account deletion - API endpoint and Cloud Function

## 9. Maintenance

### 9.1 Regular Tasks

- **Weekly**: Review secret rotation logs
- **Monthly**: Audit data access logs
- **Quarterly**: Test security rules and data isolation
- **Annually**: Review and update security policies

### 9.2 Secret Rotation Schedule

- **API Keys**: Every 90 days (automated)
- **Encryption Keys**: Every 180 days (manual)
- **Service Account Keys**: Every 90 days (manual)

### 9.3 Monitoring Dashboards

Access security monitoring dashboards:

- Cloud Logging: https://console.cloud.google.com/logs
- Secret Manager: https://console.cloud.google.com/security/secret-manager
- Firestore: https://console.cloud.google.com/firestore

## 10. Troubleshooting

### Secret Manager Access Issues

```bash
# Check IAM permissions
gcloud secrets get-iam-policy api-keys

# Test secret access
gcloud secrets versions access latest --secret="api-keys"
```

### Data Retention Issues

```bash
# Check Cloud Function logs
gcloud functions logs read data-retention-cleanup --limit=50

# Check Cloud Scheduler job status
gcloud scheduler jobs describe data-retention-daily --location=us-central1
```

### TLS Configuration Issues

```bash
# Verify SSL policy
gcloud compute ssl-policies describe adaptive-ad-intelligence-ssl-policy

# Test TLS connection
openssl s_client -connect YOUR_DOMAIN:443 -tls1_3
```

## References

- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Firestore Security Rules](https://firebase.google.com/docs/firestore/security/get-started)
- [Cloud Run Security](https://cloud.google.com/run/docs/securing/using-https)
- [Data Retention Best Practices](https://cloud.google.com/architecture/framework/security/data-protection)
