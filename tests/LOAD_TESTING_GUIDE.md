# Load Testing Guide

This guide explains how to perform load testing on the Adaptive Ad Intelligence Platform to verify performance requirements and identify bottlenecks.

## Requirements

The system must meet the following performance requirements (Requirement 10.5):

1. **Campaign Creation**: Handle 1000 concurrent campaign creation requests
2. **Bid Execution**: Process 10,000 bid requests per second with <100ms P99 latency
3. **Auto-Scaling**: Scale from 1 to 100 Cloud Run instances based on load
4. **Latency**: Maintain acceptable response times under load

## Installation

Install load testing dependencies:

```bash
pip install locust pytest pytest-asyncio
```

## Load Testing Tools

### 1. Pytest-based Load Tests

Located in `tests/test_load_performance.py`, these tests provide programmatic load testing with detailed metrics.

**Run all load tests:**
```bash
pytest tests/test_load_performance.py -v -s --tb=short
```

**Run specific tests:**
```bash
# Test 1000 concurrent campaigns
pytest tests/test_load_performance.py::test_1000_concurrent_campaigns -v -s

# Test bid execution high load
pytest tests/test_load_performance.py::test_bid_execution_high_load -v -s

# Test auto-scaling behavior
pytest tests/test_load_performance.py::test_auto_scaling_behavior -v -s

# Test latency bottlenecks
pytest tests/test_load_performance.py::test_latency_bottlenecks -v -s
```

**Run as standalone script:**
```bash
python tests/test_load_performance.py
```

### 2. Locust-based Load Tests

Located in `tests/locustfile.py`, Locust provides realistic HTTP load testing with a web UI.

**Basic usage:**
```bash
# Start Locust web UI
locust -f tests/locustfile.py --host=http://localhost:8080

# Then open http://localhost:8089 in your browser
```

**Headless mode (no UI):**
```bash
# Campaign creation load test
locust -f tests/locustfile.py --host=http://localhost:8080 \
  --users 1000 --spawn-rate 100 --run-time 5m \
  --headless --only-summary CampaignUser

# Bid execution load test
locust -f tests/locustfile.py --host=http://localhost:8080 \
  --users 1000 --spawn-rate 100 --run-time 2m \
  --headless --only-summary BidExecutionUser

# Mixed workload test
locust -f tests/locustfile.py --host=http://localhost:8080 \
  --users 500 --spawn-rate 50 --run-time 5m \
  --headless --only-summary MixedWorkloadUser
```

**Step load test (auto-scaling):**
```bash
locust -f tests/locustfile.py --host=http://localhost:8080 \
  --headless --only-summary StepLoadShape
```

**Spike load test (resilience):**
```bash
locust -f tests/locustfile.py --host=http://localhost:8080 \
  --headless --only-summary SpikeLoadShape
```

## Test Scenarios

### Scenario 1: Campaign Creation Load Test

**Objective**: Verify system can handle 1000 concurrent campaign creation requests

**Expected Results**:
- Success rate: >= 95%
- P95 latency: < 5000ms
- P99 latency: < 10000ms
- Throughput: >= 50 campaigns/sec

**Run with pytest:**
```bash
pytest tests/test_load_performance.py::test_1000_concurrent_campaigns -v -s
```

**Run with Locust:**
```bash
locust -f tests/locustfile.py --host=http://localhost:8080 \
  --users 1000 --spawn-rate 100 --run-time 5m \
  --headless CampaignUser
```

### Scenario 2: Bid Execution High Throughput

**Objective**: Verify system can process 10,000 bid requests per second

**Expected Results**:
- Success rate: >= 95%
- P99 latency: < 100ms
- Throughput: >= 8000 req/sec
- No timeouts or connection errors

**Run with pytest:**
```bash
pytest tests/test_load_performance.py::test_bid_execution_high_load -v -s
```

**Run with Locust:**
```bash
locust -f tests/locustfile.py --host=http://localhost:8080 \
  --users 1000 --spawn-rate 100 --run-time 2m \
  --headless BidExecutionUser
```

### Scenario 3: Auto-Scaling Behavior

**Objective**: Verify Cloud Run auto-scales from 1 to 100 instances under load

**Expected Results**:
- System scales up as load increases
- Latency remains acceptable during scaling
- No significant degradation at peak load
- System scales down after load decreases

**Run with pytest:**
```bash
pytest tests/test_load_performance.py::test_auto_scaling_behavior -v -s
```

**Run with Locust (step load):**
```bash
locust -f tests/locustfile.py --host=http://localhost:8080 \
  --headless StepLoadShape
```

**Monitor scaling:**
```bash
# Watch Cloud Run instances
gcloud run services describe adaptive-ad-intelligence \
  --region=us-central1 \
  --format="value(status.traffic[0].latestRevision)" | \
  xargs -I {} gcloud run revisions describe {} \
  --region=us-central1 \
  --format="value(status.containerStatuses[0].imageDigest)"

# Monitor metrics in Cloud Console
# Navigate to: Cloud Run > Service > Metrics
```

### Scenario 4: Latency Bottleneck Analysis

**Objective**: Identify performance bottlenecks and optimization opportunities

**Expected Results**:
- Identify slow endpoints
- Measure agent response times
- Detect database query bottlenecks
- Recommend optimizations

**Run with pytest:**
```bash
pytest tests/test_load_performance.py::test_latency_bottlenecks -v -s
```

## Interpreting Results

### Success Metrics

**Campaign Creation:**
- ✓ Success rate >= 95%
- ✓ P95 latency < 5000ms
- ✓ Throughput >= 50 req/sec
- ✓ Error rate < 5%

**Bid Execution:**
- ✓ Success rate >= 95%
- ✓ P99 latency < 100ms
- ✓ Throughput >= 8000 req/sec
- ✓ No timeouts

**Auto-Scaling:**
- ✓ Scales to handle peak load
- ✓ Latency degradation < 100%
- ✓ No cascading failures
- ✓ Graceful scale-down

### Common Issues

**High Latency:**
- Check agent response times
- Verify Firestore query performance
- Review Vertex AI API latency
- Check network connectivity

**Low Throughput:**
- Verify Cloud Run instance limits
- Check CPU/memory utilization
- Review connection pool settings
- Verify rate limiting configuration

**Scaling Issues:**
- Check Cloud Run scaling settings
- Verify cold start times
- Review instance startup logs
- Check resource quotas

**High Error Rate:**
- Review application logs
- Check timeout configurations
- Verify agent fallback strategies
- Review error handling logic

## Monitoring During Load Tests

### Cloud Monitoring

**View metrics in Cloud Console:**
1. Navigate to Cloud Run > adaptive-ad-intelligence
2. Click "Metrics" tab
3. Monitor:
   - Request count
   - Request latency (P50, P95, P99)
   - Instance count
   - CPU utilization
   - Memory utilization
   - Error rate

**Create custom dashboard:**
```bash
gcloud monitoring dashboards create --config-from-file=config/monitoring_dashboard.json
```

### Application Logs

**View logs during test:**
```bash
# Stream logs
gcloud logging tail "resource.type=cloud_run_revision" \
  --format="table(timestamp, severity, textPayload)"

# Filter by severity
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit 50 \
  --format json
```

### Locust Web UI

When running Locust with web UI (http://localhost:8089):

1. **Statistics Tab**: View request counts, response times, failures
2. **Charts Tab**: Real-time graphs of RPS and response times
3. **Failures Tab**: Detailed error information
4. **Exceptions Tab**: Application exceptions
5. **Download Data**: Export results as CSV

## Performance Optimization Tips

### Campaign Creation Optimization

1. **Cache LLM Responses**: Cache common creative patterns
2. **Optimize Firestore Queries**: Add composite indexes
3. **Batch Agent Communication**: Group messages to reduce overhead
4. **Async Processing**: Use background tasks for non-critical operations

### Bid Execution Optimization

1. **In-Memory Caching**: Cache segment matching data
2. **Pre-load Budget Data**: Keep budget info in memory
3. **Optimize Matching Algorithm**: Use efficient data structures
4. **Connection Pooling**: Reuse database connections

### Infrastructure Optimization

1. **Increase Min Instances**: Reduce cold starts (cost vs performance)
2. **Optimize Container Size**: Right-size CPU and memory
3. **Use VPC Connector**: Reduce latency to private resources
4. **Enable HTTP/2**: Improve connection efficiency

## Continuous Load Testing

### CI/CD Integration

Add load tests to your CI/CD pipeline:

```yaml
# .github/workflows/load-test.yml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Run daily at 2 AM
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
        run: pytest tests/test_load_performance.py -v --tb=short
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: test-results/
```

### Scheduled Testing

Run load tests regularly to catch performance regressions:

```bash
# Weekly comprehensive test
0 2 * * 0 cd /path/to/project && pytest tests/test_load_performance.py

# Daily quick test
0 2 * * * cd /path/to/project && pytest tests/test_load_performance.py::test_latency_bottlenecks
```

## Troubleshooting

### Test Fails to Start

**Issue**: Cannot connect to host
**Solution**: Verify service is running and accessible

```bash
# Check service status
curl http://localhost:8080/api/health

# Check Cloud Run service
gcloud run services describe adaptive-ad-intelligence --region=us-central1
```

### High Error Rate During Test

**Issue**: Many requests failing
**Solution**: Check logs and reduce load

```bash
# View recent errors
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit 20

# Reduce concurrent users in Locust
# Or reduce target RPS in pytest tests
```

### Inconsistent Results

**Issue**: Results vary significantly between runs
**Solution**: Ensure consistent test environment

- Run tests during off-peak hours
- Use dedicated test environment
- Warm up system before measuring
- Run multiple iterations and average results

## Best Practices

1. **Start Small**: Begin with low load and gradually increase
2. **Monitor Continuously**: Watch metrics during tests
3. **Test Realistic Scenarios**: Use production-like data and patterns
4. **Document Baselines**: Record baseline performance for comparison
5. **Test Regularly**: Run load tests on schedule to catch regressions
6. **Analyze Failures**: Investigate all failures and errors
7. **Optimize Iteratively**: Make one change at a time and measure impact
8. **Test Edge Cases**: Include spike loads and sustained high load

## References

- [Locust Documentation](https://docs.locust.io/)
- [Cloud Run Performance Best Practices](https://cloud.google.com/run/docs/tips/general)
- [Cloud Monitoring](https://cloud.google.com/monitoring/docs)
- [Performance Testing Guide](https://cloud.google.com/architecture/performance-testing-overview)
