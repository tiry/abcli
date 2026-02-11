# Testing the Agent Builder CLI

This document provides comprehensive instructions for testing the Agent Builder CLI project. It covers both unit tests and integration tests, along with instructions for running tests and writing new ones.

## Table of Contents

- [Unit Tests](#unit-tests)
- [Integration Tests](#integration-tests)
- [Test Coverage](#test-coverage)
- [Writing New Tests](#writing-new-tests)
- [CI/CD Testing](#cicd-testing)

## Unit Tests

The Agent Builder CLI uses pytest for unit testing. Unit tests are located in the `tests/` directory and are organized to mirror the project structure.

### Running All Unit Tests

To run all unit tests:

```bash
# Make sure you're in the project root directory
cd ab-cli

# Run all tests
pytest
```

### Running Specific Tests

```bash
# Run tests in a specific file
pytest tests/test_config/test_settings.py

# Run tests in a specific directory
pytest tests/test_api/

# Run tests matching a pattern
pytest -k "test_agent"
```

### Running Tests with Verbose Output

For more detailed output:

```bash
pytest -v
```

For even more detailed output:

```bash
pytest -vv
```

### Testing with Coverage

To check test coverage:

```bash
# Run tests with coverage
pytest --cov=ab_cli

# Generate an HTML coverage report
pytest --cov=ab_cli --cov-report=html

# The report will be available in htmlcov/index.html
```

## Integration Tests

Integration tests are designed to test the CLI against an actual Agent Builder API endpoint. These tests verify that all parts of the system work together correctly.

### Prerequisites for Integration Tests

1. Valid API credentials with access to the Agent Builder API
2. Proper configuration (same as for regular CLI usage)
3. Permissions to create, update, and delete agents in your environment

### Running Integration Tests

```bash
# Make sure you have a valid config.yaml file in the project root
# Run integration tests with default config
python -m tests.integration.integration_tests

# Run with a specific config file
python -m tests.integration.integration_tests --config /path/to/config.yaml

# Run with verbose output for detailed logs
python -m tests.integration.integration_tests --verbose
```

### What the Integration Tests Cover

The integration tests perform a sequence of operations:

1. List all agents and agent types
2. List available models and guardrails
3. Create a new test agent
4. Get agent details and versions
5. Invoke the agent with various methods
6. Patch and update the agent
7. Delete the test agent and verify deletion

### Interpreting Integration Test Results

After running integration tests, you'll see a summary report:

```
================================================================================
 Test Results Summary
================================================================================
✅ PASS: List agents
✅ PASS: List agents (JSON format)
✅ PASS: List agent types
✅ PASS: List models
✅ PASS: List models (JSON format)
✅ PASS: List models filtered by agent type
✅ PASS: List guardrails
✅ PASS: List guardrails (JSON format)
✅ PASS: Create agent
✅ PASS: Get agent JSON format
✅ PASS: List versions
✅ PASS: List versions (JSON format)
✅ PASS: Get version
✅ PASS: Call new agent
✅ PASS: Call agent with JSON format
✅ PASS: Patch agent
✅ PASS: Update agent
✅ PASS: Delete agent

Passed 18/18 tests (100.0%)
```

Any failed tests will be highlighted in red with details about what failed.

### Troubleshooting Integration Tests

If integration tests fail, check the following:

1. **API Credentials**: Ensure your credentials are valid and have proper permissions
2. **Network Connectivity**: Check connectivity to the API endpoints
3. **Test Agent Creation**: Ensure you have permission to create agents
4. **Agent Configuration**: The test agent config file might need updates if the API changes

## Test Coverage

The project maintains high test coverage across all components with an overall coverage of **77%**:

### Coverage Highlights

| Module                 | Coverage | Notes                                       |
|------------------------|----------|---------------------------------------------|
| ab_cli/api/auth.py     | 98%      | Full test coverage for token management     |
| ab_cli/cli/invoke.py   | 90%      | Enhanced coverage for error handling        |
| ab_cli/config/         | 100%     | Complete coverage of configuration handling |
| ab_cli/models/         | 100%     | All data models fully tested                |

### Test Statistics

- **224 tests** covering all major components
- **1,477 lines of code** with **1,125 lines** covered
- **288 branch points** with **242 branches** covered

### Checking Current Coverage

```bash
# Generate a basic coverage report
pytest --cov=ab_cli

# For more detailed reporting with missing lines
pytest --cov=ab_cli --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=ab_cli --cov-report=html

# Generate XML coverage report for CI tools
pytest --cov=ab_cli --cov-report=xml
```

### Coverage Badge

The project includes a coverage badge in the README.md, which is automatically updated by the GitHub Actions workflow. The current coverage is displayed as:

![Coverage](https://raw.githubusercontent.com/hyland/ab-cli/badges/.github/coverage.svg)

## Writing New Tests

When adding new features, please also add corresponding tests:

### Unit Test Guidelines

1. **Test Location**: Add tests in the `tests/` directory, mirroring the structure of the code
2. **Test Naming**: Name test files with the prefix `test_`, e.g., `test_client.py`
3. **Test Functions**: Name test functions with the prefix `test_`, e.g., `test_list_models()`
4. **Fixtures**: Use pytest fixtures for setup and teardown
5. **Mocking**: Use the `unittest.mock` module or pytest's `monkeypatch` to mock external dependencies

### Example Unit Test

```python
def test_list_models(monkeypatch):
    """Test listing LLM models."""
    # Mock the API response
    mock_response = {
        "models": [{"id": "model1", "name": "Test Model"}],
        "pagination": {"limit": 10, "offset": 0, "totalItems": 1}
    }
    
    # Set up the mock
    monkeypatch.setattr(
        "ab_cli.api.client.AgentBuilderClient._make_request",
        lambda self, method, path, **kwargs: mock_response
    )
    
    # Create the client and call the method
    client = AgentBuilderClient(ABSettings())
    result = client.list_models()
    
    # Verify the result
    assert len(result.models) == 1
    assert result.models[0].id == "model1"
    assert result.models[0].name == "Test Model"
```

### Integration Test Guidelines

When adding a new feature that interacts with the API, consider adding an integration test:

1. Add a new method to the `IntegrationTests` class in `tests/integration/integration_tests.py`
2. Add the new test method to the `run_all_tests()` method
3. Include proper error handling and result verification

## CI/CD Testing

The project includes a complete GitHub Actions workflow for continuous integration located in `.github/workflows/ci.yml`. This workflow runs automatically on all pull requests and pushes to the main branch.

### GitHub Actions Workflow

The CI workflow consists of three parallel jobs:

1. **Test Job**:
   - Runs the complete test suite with pytest
   - Generates coverage reports and a coverage badge
   - Adds a coverage report comment to PRs
   - Archives the HTML coverage report as an artifact

2. **Lint Job**:
   - Runs ruff to check code for linting issues
   - Verifies code formatting

3. **Type Check Job**:
   - Runs mypy for static type checking

### Running CI Locally

You can run the same checks locally that the CI runs:

```bash
# Run unit tests with coverage
pytest --cov=ab_cli --cov-report=term-missing --cov-report=xml --cov-report=html

# Run linting
ruff check ab_cli/

# Check formatting
ruff format --check ab_cli/

# Run type checking
mypy ab_cli/ --ignore-missing-imports
```

### Coverage Badge

The CI workflow automatically generates and updates a coverage badge that is displayed in the README.md. The badge is stored on a separate `badges` branch and is updated on each push to the main branch.

### Integration Tests in CI

Integration tests should typically be run in a separate workflow with proper credentials provided as secrets. These tests are not included in the standard CI workflow because they require valid API credentials.
