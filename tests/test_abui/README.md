# UI Testing Documentation

This directory contains tests for the Agent Builder UI components based on Streamlit.

## Overview

The UI tests are organized into several categories:

1. **Component Tests**: Tests for individual UI components (e.g., agent_card.py)
2. **View Tests**: Tests for views/pages (e.g., agents.py, agent_details.py, edit_agent.py)
3. **Provider Tests**: Tests for data providers that supply data to the UI
4. **Helper Tests**: Tests for utility functions and components

## Test Implementation Approach

Streamlit presents unique testing challenges because it uses session state and its own rendering lifecycle. 
Our approach leverages several techniques to effectively test Streamlit applications:

### 1. Mock Session State

The `streamlit_test_wrapper.py` module provides utilities to simulate Streamlit session state and 
component rendering. This allows us to test Streamlit-dependent code in a standard pytest environment.

### 2. Test Data Provider

The `MockTestingProvider` class in `test_data_provider.py` extends the standard `MockDataProvider` with
testing-specific enhancements:

- Loads test data from the `test_data` directory
- Provides method call tracking for assertions
- Supports error simulation for testing error paths
- Includes the `add_test_agent` method for creating test-specific agent data

This provider is used across UI tests to provide consistent test data.

## Best Practices

- Use `streamlit_test_wrapper.py` functions to simulate Streamlit components
- Initialize each test with a clean session state
- Use `MockTestingProvider` for controlled data access
- Test both happy paths and error conditions
- Keep tests focused on specific functionality

## Warning Prevention

To prevent common warnings in the test suite:

1. **Pytest Collection Warnings**: The `MockTestingProvider` class includes `__test__ = False` to prevent
   pytest from trying to collect it as a test class.

2. **Datetime Deprecation Warnings**: Use `datetime.now(UTC)` instead of the deprecated `datetime.utcnow()`.

## Adding New Tests

When adding new tests:

1. Create a new test file named `test_<component>.py`
2. Import necessary fixtures from `conftest.py`
3. Use the patterns in existing tests for consistency
4. Ensure session state is properly initialized for each test
5. Clean up any mock data added during tests

## Test Coverage

The UI tests aim to cover:

- Basic functionality of all views
- Error handling and edge cases
- User interactions and workflows
- Data provider integration

## Running Tests

Run the UI tests with:

```bash
# Run all UI tests
python -m pytest tests/test_abui/

# Run specific UI test file
python -m pytest tests/test_abui/test_agents_list.py

# Run with verbose output
python -m pytest tests/test_abui/ -v```
