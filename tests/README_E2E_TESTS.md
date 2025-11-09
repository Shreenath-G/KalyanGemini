# End-to-End Test Suite

This directory contains comprehensive end-to-end (E2E) tests for the Adaptive Ad Intelligence Platform.

## Test Files

### 1. test_e2e_campaign_workflow.py
Tests the complete campaign creation workflow including agent coordination and strategy synthesis.

**Coverage:**
- Campaign Orchestrator Agent initialization
- Agent message creation and serialization
- Agent response structure validation
- Campaign request handling with specialist agents
- Strategy synthesis from agent results
- Launch timeline calculation
- Complete end-to-end campaign workflow

**Requirements Covered:** 1.1, 2.1

**Test Count:** 7 tests

### 2. test_e2e_performance_optimization.py
Tests the performance monitoring and optimization workflow.

**Coverage:**
- Performance metrics calculation (ROAS, CPA, CTR)
- Variant-level metrics calculation
- Underperforming variant detection
- Top performing variant detection
- Optimization action generation
- Optimization request handling
- Complete optimization workflow

**Requirements Covered:** 6.1, 9.1, 9.3

**Test Count:** 7 tests

### 3. test_e2e_bid_execution.py
Tests the real-time bid execution workflow with mock ad exchange.

**Coverage:**
- Bid Execution Agent initialization
- Relevance checking for bid opportunities
- User profile to segment matching
- Budget availability checking
- Bid price calculation
- Bid request handling with <100ms response time
- Bid tracking and win rate calculation
- Bidding strategy adjustment
- Complete bid execution workflow

**Requirements Covered:** 7.1, 7.2, 7.3, 7.4, 7.5

**Test Count:** 9 tests

### 4. test_e2e_firestore_persistence.py
Tests data persistence and retrieval from Firestore.

**Coverage:**
- Firestore service initialization
- Campaign CRUD operations
- Campaign retrieval by account
- Creative variants batch persistence
- Audience segments batch persistence
- Budget allocation persistence
- Performance metrics persistence
- Complete persistence workflow

**Requirements Covered:** 13.1, 13.4

**Test Count:** 9 tests

### 5. test_e2e_validation.py
Validation test that verifies the structure and completeness of all E2E tests without requiring Google Cloud dependencies.

**Coverage:**
- Test file existence
- Test structure validation
- Requirements coverage verification
- Documentation quality checks

## Running the Tests

### Prerequisites

Install required dependencies:
```bash
pip install -r requirements.txt
```

Ensure Google Cloud credentials are configured:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### Run All E2E Tests

```bash
# Run all E2E tests
pytest tests/test_e2e_*.py -v

# Run with coverage
pytest tests/test_e2e_*.py -v --cov=src --cov-report=html
```

### Run Individual Test Suites

```bash
# Campaign workflow tests
pytest tests/test_e2e_campaign_workflow.py -v

# Performance optimization tests
pytest tests/test_e2e_performance_optimization.py -v

# Bid execution tests
pytest tests/test_e2e_bid_execution.py -v

# Firestore persistence tests
pytest tests/test_e2e_firestore_persistence.py -v
```

### Run Validation Only (No Dependencies Required)

```bash
# Validate test structure without running actual tests
python tests/test_e2e_validation.py
```

## Test Structure

All E2E tests follow a consistent structure:

1. **Fixtures**: Sample data and service instances
2. **Unit-level tests**: Test individual components
3. **Integration tests**: Test component interactions
4. **Complete workflow test**: End-to-end scenario testing

Each test includes:
- Comprehensive docstrings
- Requirement references
- Assertions with clear error messages
- Detailed output for debugging

## Requirements Coverage

The E2E test suite provides complete coverage of the following requirements:

| Requirement | Description | Test File |
|-------------|-------------|-----------|
| 1.1 | Campaign creation via API | test_e2e_campaign_workflow.py |
| 2.1 | Campaign orchestrator coordination | test_e2e_campaign_workflow.py |
| 6.1 | Performance monitoring | test_e2e_performance_optimization.py |
| 7.1 | Bid execution | test_e2e_bid_execution.py |
| 7.2 | Bid evaluation | test_e2e_bid_execution.py |
| 7.3 | Budget checking | test_e2e_bid_execution.py |
| 7.4 | Bid price calculation | test_e2e_bid_execution.py |
| 7.5 | Bid tracking | test_e2e_bid_execution.py |
| 13.1 | Data persistence | test_e2e_firestore_persistence.py |
| 13.4 | Data retrieval | test_e2e_firestore_persistence.py |

**Total Coverage:** 100% (10/10 requirements)

## Test Metrics

- **Total Test Files:** 5 (4 E2E + 1 validation)
- **Total Test Methods:** 32
- **Documentation Coverage:** 100%
- **Requirements Coverage:** 100%

## Notes

### Mock vs Real Services

Some tests use mock implementations (e.g., MockBidExecutionAgent) to:
- Test logic without external dependencies
- Ensure fast test execution
- Provide deterministic results

### Async Tests

All E2E tests use `@pytest.mark.asyncio` decorator for async/await support.

### Firestore Emulator

For local testing, consider using the Firestore emulator:
```bash
gcloud emulators firestore start
export FIRESTORE_EMULATOR_HOST=localhost:8080
```

### CI/CD Integration

These tests are designed to run in CI/CD pipelines. Ensure:
- Google Cloud credentials are available as secrets
- Firestore emulator is used for isolated testing
- Test results are collected and reported

## Troubleshooting

### Import Errors

If you encounter import errors:
```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Google Cloud Authentication

If authentication fails:
```bash
# Login to Google Cloud
gcloud auth application-default login

# Or set credentials explicitly
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### Firestore Connection Issues

If Firestore connection fails:
- Check network connectivity
- Verify project ID in configuration
- Ensure Firestore API is enabled
- Use Firestore emulator for local testing

## Future Enhancements

Potential improvements for the test suite:

1. **Load Testing Integration**: Add performance benchmarks
2. **Contract Testing**: Verify API contracts with Pact
3. **Chaos Engineering**: Test resilience with fault injection
4. **Visual Regression**: Add screenshot comparison for dashboards
5. **Security Testing**: Add penetration testing scenarios

## Contributing

When adding new E2E tests:

1. Follow the existing test structure
2. Include comprehensive docstrings
3. Reference requirements in comments
4. Add fixtures for reusable test data
5. Update this README with new test coverage
6. Run validation test to ensure structure compliance

## Contact

For questions or issues with the E2E test suite, please contact the development team or open an issue in the project repository.
