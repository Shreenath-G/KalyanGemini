# Firestore Security Configuration

## Encryption at Rest

Firestore automatically encrypts all data at rest using AES-256 encryption. This is enabled by default and requires no additional configuration.

**Verification:**
- All data stored in Firestore is automatically encrypted
- Encryption keys are managed by Google Cloud
- No action required from developers

**Reference:** Requirement 13.1, 13.2

## Data Isolation Between Accounts

All Firestore queries enforce account-level isolation through the `account_id` field:

### Campaign Queries
```python
# Always filter by account_id
query = db.collection("campaigns").where(
    filter=FieldFilter("account_id", "==", account_id)
)
```

### Security Rules (Firestore Rules)

Deploy the following Firestore security rules to enforce data isolation at the database level:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Helper function to check authentication
    function isAuthenticated() {
      return request.auth != null;
    }
    
    // Helper function to get account_id from custom claims
    function getAccountId() {
      return request.auth.token.account_id;
    }
    
    // Campaigns collection
    match /campaigns/{campaignId} {
      allow read, write: if isAuthenticated() 
        && resource.data.account_id == getAccountId();
      allow create: if isAuthenticated()
        && request.resource.data.account_id == getAccountId();
    }
    
    // Creative variants collection
    match /creative_variants/{variantId} {
      allow read, write: if isAuthenticated()
        && get(/databases/$(database)/documents/campaigns/$(resource.data.campaign_id)).data.account_id == getAccountId();
    }
    
    // Audience segments collection
    match /audience_segments/{segmentId} {
      allow read, write: if isAuthenticated()
        && get(/databases/$(database)/documents/campaigns/$(resource.data.campaign_id)).data.account_id == getAccountId();
    }
    
    // Budget allocations collection
    match /budget_allocations/{campaignId} {
      allow read, write: if isAuthenticated()
        && get(/databases/$(database)/documents/campaigns/$(campaignId)).data.account_id == getAccountId();
    }
    
    // Performance metrics collection
    match /performance_metrics/{metricId} {
      allow read: if isAuthenticated()
        && get(/databases/$(database)/documents/campaigns/$(resource.data.campaign_id)).data.account_id == getAccountId();
      allow write: if false; // Only backend can write metrics
    }
    
    // Metrics snapshots collection
    match /metrics_snapshots/{snapshotId} {
      allow read: if isAuthenticated()
        && get(/databases/$(database)/documents/campaigns/$(resource.data.campaign_id)).data.account_id == getAccountId();
      allow write: if false; // Only backend can write snapshots
    }
    
    // Bid decisions collection
    match /bid_decisions/{requestId} {
      allow read: if isAuthenticated()
        && get(/databases/$(database)/documents/campaigns/$(resource.data.campaign_id)).data.account_id == getAccountId();
      allow write: if false; // Only backend can write bid decisions
    }
    
    // Bidding strategies collection
    match /bidding_strategies/{campaignId} {
      allow read: if isAuthenticated()
        && get(/databases/$(database)/documents/campaigns/$(campaignId)).data.account_id == getAccountId();
      allow write: if false; // Only backend can write strategies
    }
    
    // Deny all other access
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

## Deployment Instructions

### 1. Deploy Firestore Security Rules

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase in your project
firebase init firestore

# Deploy security rules
firebase deploy --only firestore:rules
```

### 2. Create Firestore Indexes

Create the following indexes for optimal query performance:

```bash
# campaigns collection
gcloud firestore indexes composite create \
  --collection-group=campaigns \
  --field-config field-path=account_id,order=ascending \
  --field-config field-path=status,order=ascending \
  --field-config field-path=created_at,order=descending

# performance_metrics collection
gcloud firestore indexes composite create \
  --collection-group=performance_metrics \
  --field-config field-path=campaign_id,order=ascending \
  --field-config field-path=timestamp,order=descending

# metrics_snapshots collection
gcloud firestore indexes composite create \
  --collection-group=metrics_snapshots \
  --field-config field-path=campaign_id,order=ascending \
  --field-config field-path=timestamp,order=ascending
```

### 3. Verify Data Isolation

Run the data isolation verification script:

```bash
python -m src.utils.data_isolation_test
```

## Encryption in Transit (TLS 1.3)

All API communications are encrypted using TLS 1.3:

### Cloud Run Configuration

The Cloud Run service is configured to enforce TLS 1.3 through:

1. **SSL Policy**: Defined in `config/cloud_run_service.yaml`
   - Minimum TLS version: TLS_1_3
   - Profile: MODERN
   - Enforced at the load balancer level

2. **Managed Certificates**: Automatic SSL certificate provisioning and renewal

3. **HTTPS-only**: All HTTP requests are automatically redirected to HTTPS

### Verification

Test TLS configuration:

```bash
# Check TLS version
openssl s_client -connect adaptive-ad-intelligence.example.com:443 -tls1_3

# Verify SSL policy
gcloud compute ssl-policies describe adaptive-ad-intelligence-ssl-policy
```

## Application-Level Encryption

For additional security, sensitive fields can be encrypted at the application level using the `EncryptionService`:

```python
from src.utils.encryption import get_encryption_service

encryption_service = get_encryption_service()

# Encrypt sensitive data before storing
encrypted_data = encryption_service.encrypt(sensitive_string)

# Decrypt when retrieving
decrypted_data = encryption_service.decrypt(encrypted_data)
```

### Fields Recommended for Application-Level Encryption

- API keys for ad platforms
- User contact information (if stored)
- Payment information (if stored)
- Any PII (Personally Identifiable Information)

## Monitoring and Auditing

### Data Access Auditing

All data access attempts are logged:

```python
from src.utils.data_isolation import get_data_isolation_validator

validator = get_data_isolation_validator()

# Audit access attempt
await validator.audit_data_access(
    account_id="acc_123",
    resource_type="campaign",
    resource_id="camp_456",
    action="read",
    success=True
)
```

### Security Monitoring

Monitor for security violations:

1. **Cloud Logging Filters**:
   ```
   severity >= WARNING
   jsonPayload.message =~ "Data isolation violation"
   ```

2. **Alerting Policies**:
   - Alert on failed authentication attempts
   - Alert on cross-account access attempts
   - Alert on encryption failures

3. **Regular Audits**:
   - Review access logs weekly
   - Verify data isolation monthly
   - Test security rules quarterly

## Compliance

This configuration ensures compliance with:

- **Requirement 13.1**: Encryption at rest (AES-256)
- **Requirement 13.2**: Encryption in transit (TLS 1.3)
- **Requirement 13.4**: Data isolation between accounts

## References

- [Firestore Security Rules](https://firebase.google.com/docs/firestore/security/get-started)
- [Cloud Run Security](https://cloud.google.com/run/docs/securing/using-https)
- [Google Cloud Encryption](https://cloud.google.com/security/encryption-at-rest)
