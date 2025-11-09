# CI/CD Setup Guide

This guide explains how to set up automated deployment pipelines for the Adaptive Ad Intelligence Platform using either GitHub Actions or Google Cloud Build.

## Overview

The platform supports two CI/CD approaches:

1. **GitHub Actions**: Best for GitHub-hosted repositories with external CI/CD
2. **Cloud Build**: Best for Google Cloud-native workflows with Cloud Source Repositories

Both pipelines include:
- Automated testing before deployment
- Docker image building and pushing to GCR
- Deployment to Cloud Run
- Health check verification
- Deployment notifications

## Option 1: GitHub Actions

### Prerequisites

1. GitHub repository with the code
2. Google Cloud project with billing enabled
3. Service account with deployment permissions

### Setup Steps

#### 1. Create Service Account

```bash
# Set project ID
export PROJECT_ID="your-project-id"

# Create service account
gcloud iam service-accounts create github-actions-deployer \
  --display-name="GitHub Actions Deployer" \
  --project=$PROJECT_ID

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com
```

#### 2. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

- **GCP_PROJECT_ID**: Your Google Cloud project ID
- **GCP_SA_KEY**: Contents of `github-actions-key.json` file

#### 3. Enable GitHub Actions

The workflow file is located at `.github/workflows/deploy.yml` and will automatically run on:
- Push to `main` branch (runs tests, builds, and deploys)
- Pull requests to `main` (runs tests only)
- Manual trigger via GitHub Actions UI

#### 4. Verify Setup

1. Push a commit to the `main` branch
2. Go to GitHub Actions tab in your repository
3. Watch the workflow execution
4. Check the deployment summary for service URL

### GitHub Actions Workflow Details

The workflow consists of 4 jobs:

1. **test**: Runs unit and integration tests
2. **build**: Builds and pushes Docker image to GCR
3. **deploy**: Deploys to Cloud Run and verifies health
4. **notify**: Sends deployment status notification

### Customization

Edit `.github/workflows/deploy.yml` to customize:

```yaml
env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: us-central1  # Change region
  SERVICE_NAME: adaptive-ad-intelligence  # Change service name
```

## Option 2: Google Cloud Build

### Prerequisites

1. Google Cloud project with billing enabled
2. Cloud Build API enabled
3. Cloud Source Repository or GitHub repository connected

### Setup Steps

#### 1. Enable Required APIs

```bash
export PROJECT_ID="your-project-id"

gcloud services enable cloudbuild.googleapis.com \
  --project=$PROJECT_ID

gcloud services enable run.googleapis.com \
  --project=$PROJECT_ID

gcloud services enable containerregistry.googleapis.com \
  --project=$PROJECT_ID
```

#### 2. Grant Cloud Build Permissions

```bash
# Get Cloud Build service account
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Grant Cloud Run Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/run.admin"

# Grant Service Account User role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/iam.serviceAccountUser"

# Grant Storage Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/storage.admin"
```

#### 3. Create Build Trigger

##### Option A: Using Cloud Source Repositories

```bash
# Create trigger for main branch
gcloud builds triggers create cloud-source-repositories \
  --repo=adaptive-ad-intelligence \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml \
  --description="Deploy on push to main"
```

##### Option B: Using GitHub Repository

```bash
# Connect GitHub repository first via Cloud Console
# Then create trigger
gcloud builds triggers create github \
  --repo-name=adaptive-ad-intelligence \
  --repo-owner=your-github-username \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml \
  --description="Deploy on push to main"
```

#### 4. Manual Build Trigger

```bash
# Trigger build manually
gcloud builds submit --config=cloudbuild.yaml .
```

#### 5. Verify Setup

```bash
# List recent builds
gcloud builds list --limit=5

# View build logs
gcloud builds log <BUILD_ID>
```

### Cloud Build Configuration Details

The `cloudbuild.yaml` file defines 6 steps:

1. **run-tests**: Executes pytest test suite
2. **build-image**: Builds Docker image
3. **push-image**: Pushes image with commit SHA tag
4. **push-latest**: Pushes image with latest tag
5. **deploy-cloud-run**: Deploys to Cloud Run
6. **verify-deployment**: Runs health check

### Customization

Edit `cloudbuild.yaml` to customize:

```yaml
substitutions:
  _REGION: 'us-central1'  # Change region
  _SERVICE_NAME: 'adaptive-ad-intelligence'  # Change service name

options:
  machineType: 'N1_HIGHCPU_8'  # Change machine type
  timeout: '1200s'  # Change timeout
```

## Testing the Pipeline

### Test Without Deployment

#### GitHub Actions
Create a pull request to test without deploying:
```bash
git checkout -b test-pipeline
git push origin test-pipeline
# Create PR on GitHub
```

#### Cloud Build
Run build without deploying:
```bash
gcloud builds submit --config=cloudbuild.yaml --no-source
```

### Test Deployment

#### GitHub Actions
Push to main branch:
```bash
git checkout main
git push origin main
```

#### Cloud Build
Trigger manual build:
```bash
gcloud builds submit --config=cloudbuild.yaml .
```

## Monitoring Deployments

### GitHub Actions

1. Go to repository → Actions tab
2. Click on workflow run
3. View logs for each job
4. Check deployment summary

### Cloud Build

1. Go to Cloud Console → Cloud Build → History
2. Click on build
3. View detailed logs
4. Check build artifacts

### Cloud Run Deployment

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe adaptive-ad-intelligence \
  --region us-central1 \
  --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/api/health

# View recent logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

## Rollback Procedures

### Rollback to Previous Revision

```bash
# List revisions
gcloud run revisions list \
  --service=adaptive-ad-intelligence \
  --region=us-central1

# Rollback to specific revision
gcloud run services update-traffic adaptive-ad-intelligence \
  --region=us-central1 \
  --to-revisions=REVISION_NAME=100
```

### Rollback via Re-deployment

#### GitHub Actions
1. Go to Actions tab
2. Find successful previous deployment
3. Click "Re-run all jobs"

#### Cloud Build
```bash
# Find previous successful build
gcloud builds list --filter="status=SUCCESS" --limit=5

# Re-run build
gcloud builds submit --config=cloudbuild.yaml --substitutions=COMMIT_SHA=<previous-sha> .
```

## Troubleshooting

### Build Failures

**Tests Failing**
```bash
# Run tests locally
pytest tests/ -v

# Check test environment variables
cat .env.example
```

**Docker Build Failing**
```bash
# Build locally
docker build -t test-image .

# Check Dockerfile syntax
docker build --no-cache -t test-image .
```

**Deployment Failing**
```bash
# Check Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit=100

# Verify service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:adaptive-ad-intelligence@*"
```

### Permission Issues

**GitHub Actions**
- Verify GCP_SA_KEY secret is correct
- Check service account has required roles
- Ensure service account key is not expired

**Cloud Build**
- Verify Cloud Build service account has roles
- Check API enablement
- Verify service account exists

### Timeout Issues

**GitHub Actions**
Increase timeout in workflow:
```yaml
jobs:
  deploy:
    timeout-minutes: 30  # Increase from default
```

**Cloud Build**
Increase timeout in cloudbuild.yaml:
```yaml
options:
  timeout: '1800s'  # Increase from 1200s
```

## Best Practices

1. **Always run tests before deployment**
   - Both pipelines run tests automatically
   - Fix failing tests before merging

2. **Use semantic versioning for tags**
   - Tag releases: `git tag v1.0.0`
   - Push tags: `git push --tags`

3. **Monitor deployment metrics**
   - Check Cloud Run metrics after deployment
   - Verify health endpoint responds correctly

4. **Set up notifications**
   - Configure Slack/email notifications for failures
   - Monitor build status regularly

5. **Secure secrets properly**
   - Never commit secrets to repository
   - Rotate service account keys regularly
   - Use Secret Manager for application secrets

6. **Test in staging first**
   - Create staging environment
   - Deploy to staging before production
   - Run smoke tests on staging

7. **Document deployment changes**
   - Update DEPLOYMENT.md with changes
   - Document configuration changes
   - Keep runbooks up to date

## Cost Optimization

### GitHub Actions
- Free tier: 2,000 minutes/month for private repos
- Optimize by caching dependencies
- Use matrix builds for parallel testing

### Cloud Build
- Free tier: 120 build-minutes/day
- Use smaller machine types when possible
- Cache Docker layers for faster builds

## Security Considerations

1. **Service Account Keys**
   - Store securely in GitHub Secrets or Secret Manager
   - Rotate keys every 90 days
   - Use least privilege principle

2. **Container Images**
   - Scan images for vulnerabilities
   - Use minimal base images
   - Keep dependencies updated

3. **Deployment Permissions**
   - Restrict who can trigger deployments
   - Use branch protection rules
   - Require code reviews before merge

## Support

For CI/CD issues:
1. Check build logs for error messages
2. Verify all prerequisites are met
3. Review troubleshooting section
4. Contact DevOps team

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Cloud Run Deployment](https://cloud.google.com/run/docs/deploying)
- [Container Registry](https://cloud.google.com/container-registry/docs)
