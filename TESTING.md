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

# Run only CLI component tests
pytest tests/test_api/ tests/test_cli/ tests/test_config/ tests/test_models/

# Run only UI component tests
pytest tests/test_abui/
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
# Run tests with coverage (CLI components only, as configured in pyproject.toml)
pytest --cov=ab_cli

# Run tests with coverage for UI components only
pytest --cov=ab_cli.abui --cov-report=term --cov-config=/dev/null tests/test_abui/

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

The project maintains separate test coverage metrics for CLI and UI components:

### Coverage Configuration

Coverage settings are defined in the `pyproject.toml` file:

```toml
[tool.coverage.run]
source = ["ab_cli"]
branch = true
omit = ["ab_cli/abui/*", "tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
show_missing = true
```

The default configuration measures coverage for CLI components only. For UI coverage, separate parameters are used in the CI workflow.

### Coverage Highlights

| Component       | Coverage | Notes                                    |
|-----------------|----------|------------------------------------------|
| CLI Components  | ~56%     | Core API client, models, CLI commands    |
| UI Components   | ~36%     | Streamlit-based web interface components |

### Test Statistics

- **280+ tests** covering all major components
- Separate coverage tracking for CLI and UI components
- Coverage reports generated as badges for both components

### Checking Current Coverage

```bash
# Generate a basic coverage report for CLI components
pytest --cov=ab_cli

# For UI component coverage
pytest --cov=ab_cli.abui --cov-report=term --cov-config=/dev/null tests/test_abui/

# For more detailed reporting with missing lines
pytest --cov=ab_cli --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=ab_cli --cov-report=html

# Generate XML coverage report for CI tools
pytest --cov=ab_cli --cov-report=xml
```

### Coverage Badges

The project includes two coverage badges in the README.md, which are automatically updated by the GitHub Actions workflow:

- **CLI Coverage**: ![CLI Coverage](https://raw.githubusercontent.com/tiry/abcli/badges/coverage.svg)
- **UI Coverage**: ![UI Coverage](https://raw.githubusercontent.com/tiry/abcli/badges/coverage_ui.svg)

## Writing New Tests

When adding new features, please also add corresponding tests:

### Unit Test Guidelines

1. **Test Location**: 
   - For CLI components: Add tests in `tests/test_api/`, `tests/test_cli/`, etc.
   - For UI components: Add tests in `tests/test_abui/`

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

The project includes a comprehensive GitHub Actions workflow for continuous integration located in `.github/workflows/ci.yml`. This workflow runs automatically on all pull requests and pushes to the master branch.

### GitHub Actions Workflow

The CI workflow consists of five parallel jobs:

1. **Lint Job**:
   - Runs the `lint.sh` script to check code for linting issues and formatting
   - Runs mypy for static type checking

2. **CLI Test Job**:
   - Runs tests for core CLI components (excluding UI components)
   - Measures coverage for `ab_cli` package (excluding `ab_cli/abui`)
   - Generates a coverage badge for CLI components
   - Uploads the badge as a workflow artifact

3. **UI Test Job**:
   - Runs tests specifically for UI components (`tests/test_abui/`)
   - Measures coverage for the `ab_cli/abui` directory
   - Generates a coverage badge for UI components
   - Uploads the badge as a workflow artifact

4. **Build Job**:
   - Runs only if lint and test jobs pass
   - Builds the Python package (sdist and wheel)
   - Uploads the package artifacts for potential deployment

5. **Badge Update Job**:
   - Runs only on pushes to the master branch
   - Downloads badge artifacts from CLI and UI test jobs
   - Commits and pushes updated badges to the badges branch
   - Ensures badges are always up-to-date in the README

### Running CI Checks Locally

You can run the same checks locally that the CI runs:

```bash
# Run linting and type checking
./lint.sh

# Run CLI tests with coverage
pytest --cov=ab_cli tests/test_api/ tests/test_cli/ tests/test_config/ tests/test_models/

# Run UI tests with coverage
pytest --cov=ab_cli.abui --cov-report=term --cov-config=/dev/null tests/test_abui/

# Build the package
python -m build
```

### Integration Tests in CI

Integration tests should typically be run in a separate workflow with proper credentials provided as secrets. These tests are not included in the standard CI workflow because they require valid API credentials.