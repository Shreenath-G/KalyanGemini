# Load Testing Quick Start

Quick reference for running load tests on the Adaptive Ad Intelligence Platform.

## Prerequisites

```bash
# Install dependencies
pip install pytest pytest-asyncio locust

# Verify installation
pytest --version
locust --version
```

## Quick Test Commands

### 1. Run All Load Tests (Pytest)

```bash
# Run all load tests
pytest tests/test_load_performance.py -v -s

# Run without slow tests
pytest tests/test_load_performance.py -v -s -m "not slow"

# Run only load tests
pytest tests/test_load_performance.py -v -s -m "load"
```

### 2. Individual Test Scenarios

```bash
# Test 1: 1000 concurrent campaigns
pytest tests/test_load_performance.py::test_1000_concurrent_campaigns -v -s

# Test 2: High-throughput bid execution (10k req/sec)
pytest tests/test_load_performance.py::test_bid_execution_high_load -v -s

# Test 3: Auto-scaling behavior
pytest tests/test_load_performance.py::test_auto_scaling_behavior -v -s

# Test 4: Latency bottleneck analysis
pytest tests/test_load_performance.py::test_latency_bottlenecks -v -s
```

### 3. Locust Load Tests

```bash
# Start Locust web UI (interactive)
locust -f tests/locustfile.py --host=http://localhost:8080
# Then open http://localhost:8089

# Campaign creation load (headless)
locust -f tests/locustfile.py --host=http://localhost:8080 \
  --users 1000 --spawn-rate 100 --run-time 5m \
  --headless --only-summary CampaignUser

# Bid execution load (headless)
locust -f tests/locustfile.py --host=http://localhost:8080 \
  --users 1000 --spawn-rate 100 --run-time 2m \
  --headless --only-summary BidExecutionUser

# Step load test (auto-scaling)
locust -f tests/locustfile.py --host=http://localhost:8080 \
  --headless --only-summary StepLoadShape

# Spike load test (resilience)
locust -f tests/locustfile.py --host=http://localhost:8080 \
  --headless --only-summary SpikeLoadShape
```

## Expected Results

### Campaign Creation (Requirement 10.5)
- ✓ Handle 1000 concurrent requests
- ✓ Success rate >= 95%
- ✓ P95 latency < 5000ms
- ✓ Throughput >= 50 req/sec

### Bid Execution (Requirement 10.5)
- ✓ Process 10,000 req/sec
- ✓ Success rate >= 95%
- ✓ P99 latency < 100ms
- ✓ Throughput >= 8000 req/sec

### Auto-Scaling (Requirement 10.5)
- ✓ Scale from 1 to 100 instances
- ✓ Latency degradation < 100%
- ✓ No cascading failures
- ✓ Graceful scale-down

## Monitoring During Tests

### View Cloud Run Metrics
```bash
# Open Cloud Console
gcloud run services describe adaptive-ad-intelligence \
  --region=us-central1 \
  --format="value(status.url)"

# View metrics in browser:
# Cloud Console > Cloud Run > adaptive-ad-intelligence > Metrics
```

### Stream Application Logs
```bash
# Stream all logs
gcloud logging tail "resource.type=cloud_run_revision" \
  --format="table(timestamp, severity, textPayload)"

# Stream errors only
gcloud logging tail "resource.type=cloud_run_revision AND severity>=ERROR"
```

### Monitor Instance Count
```bash
# Watch instance count (requires jq)
watch -n 5 'gcloud run services describe adaptive-ad-intelligence \
  --region=us-central1 \
  --format=json | jq ".status.traffic[0].latestRevision"'
```

## Troubleshooting

### Test Fails to Connect
```bash
# Check if service is running
curl http://localhost:8080/api/health

# Check Cloud Run service
gcloud run services list
```

### High Error Rate
```bash
# View recent errors
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit 20 --format json

# Reduce load and retry
# For Locust: reduce --users
# For pytest: modify test parameters
```

### Slow Performance
```bash
# Check Cloud Run instance limits
gcloud run services describe adaptive-ad-intelligence \
  --region=us-central1 \
  --format="value(spec.template.spec.containerConcurrency)"

# Check CPU/memory allocation
gcloud run services describe adaptive-ad-intelligence \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].resources)"
```

## Performance Optimization

### Quick Wins
1. Increase min instances to reduce cold starts
2. Enable HTTP/2 for better connection efficiency
3. Add composite indexes to Firestore
4. Cache frequently accessed data
5. Use connection pooling

### Configuration Changes
```bash
# Increase min instances
gcloud run services update adaptive-ad-intelligence \
  --region=us-central1 \
  --min-instances=5

# Increase max instances
gcloud run services update adaptive-ad-intelligence \
  --region=us-central1 \
  --max-instances=100

# Increase CPU
gcloud run services update adaptive-ad-intelligence \
  --region=us-central1 \
  --cpu=4

# Increase memory
gcloud run services update adaptive-ad-intelligence \
  --region=us-central1 \
  --memory=8Gi
```

## CI/CD Integration

Add to `.github/workflows/load-test.yml`:

```yaml
name: Load Tests
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run load tests
        run: pytest tests/test_load_performance.py -v
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: test-results/
```

## Best Practices

1. **Start Small**: Begin with 10-50 users, then scale up
2. **Warm Up**: Run a warm-up period before measuring
3. **Monitor**: Watch metrics during tests
4. **Document**: Record baseline performance
5. **Iterate**: Test after each optimization
6. **Schedule**: Run tests regularly to catch regressions

## Support

For detailed documentation, see:
- `tests/LOAD_TESTING_GUIDE.md` - Comprehensive guide
- `tests/test_load_performance.py` - Test implementation
- `tests/locustfile.py` - Locust configuration

For issues or questions:
- Check application logs
- Review Cloud Run metrics
- Consult the troubleshooting section above
