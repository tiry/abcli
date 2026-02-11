# Test Coverage and CI Implementation

## Overview

This specification outlines:
1. The test coverage improvements made to the ab-cli project
2. The implementation of a GitHub Actions CI workflow for automated testing and code quality checks

## Test Coverage Improvements

### Goals

- Improve overall test coverage to >75%
- Achieve near-complete coverage for critical modules (auth, config)
- Implement tests for previously untested or undertested code paths
- Fix skipped and failing tests

### Coverage Improvements Achieved

| Module                 | Before | After | Improvement |
|------------------------|--------|-------|-------------|
| ab_cli/api/auth.py     | 32%    | 98%   | +66%        |
| ab_cli/cli/invoke.py   | 59%    | 90%   | +31%        |
| Overall Coverage       | 69%    | 77%   | +8%         |

### New Test Files Added

1. `tests/test_api/test_auth.py`
   - Comprehensive tests for the TokenInfo class
   - Tests for AuthClient initialization, token caching/refreshing, error handling, and context management
   - Coverage for error scenarios and token expiration logic

2. `tests/test_cli/test_invoke_utils.py`
   - Tests for utility functions in the invoke module
   - Coverage for output formatting (JSON, YAML, table)
   - Tests for client initialization and configuration

3. `tests/test_cli/test_invoke_errors.py`
   - Tests for error handling in invoke commands
   - Coverage for API errors, file not found errors, and other error scenarios
   - Tests for keyboard interrupt handling

### Test Fixes Implemented

1. Fixed skipped interactive test in `tests/test_cli/test_invoke.py`
   - Implemented a comprehensive test for the interactive chat feature
   - Added testing for conversation history management and special commands

2. Fixed failing tests in `tests/test_cli/test_agents.py`
   - Corrected assertions to match table output formatting
   - Updated mocks to match current implementation

### Remaining Areas for Improvement

- The main CLI entry point (`ab_cli/cli/main.py`) remains at 16% coverage
- This module would benefit from more integration tests
- Extending test coverage for utils module (currently at 0%)

## CI Workflow Implementation

A GitHub Actions workflow will be implemented to automate testing, code quality checks, and coverage reporting.

### CI Workflow Components

1. **Test Job**
   - Run pytest with coverage reporting
   - Generate coverage badge
   - Create coverage summary for PRs
   - Archive HTML coverage report as an artifact

2. **Lint Job**
   - Run ruff for linting
   - Check code formatting

3. **Type Check Job**
   - Run mypy for static type checking

### Implementation Plan

1. Create GitHub Actions workflow file at `.github/workflows/ci.yml`
2. Configure workflow to run on:
   - Push to main/master branches
   - Pull requests to main/master
   - Manual workflow dispatch

3. Set up the jobs to execute in parallel
4. Configure appropriate permissions for PR comments and badge updates

## GitHub Actions Workflow File

The workflow file will be based on the ingest-cli project's CI workflow, with adaptations for the ab-cli project structure.

```yaml
name: CI

on:
  push:
    branches: [ main, master ]
    paths-ignore:
      - '.github/coverage.svg'
  pull_request:
    branches: [ main, master ]
    paths-ignore:
      - '.github/coverage.svg'
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  test:
    runs-on: ubuntu-latest
    if: github.ref != 'refs/heads/badges'
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
        cache: 'pip'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
        pip install coverage-badge
        
    - name: Run tests with coverage
      run: |
        pytest tests/ --cov=ab_cli --cov-report=term-missing --cov-report=xml --cov-report=html
        
    - name: Generate coverage badge
      run: |
        coverage-badge -o .github/coverage.svg -f
        
    - name: Code Coverage Summary
      uses: irongut/CodeCoverageSummary@v1.3.0
      with:
        filename: coverage.xml
        badge: true
        format: markdown
        output: both
        
    - name: Add Coverage PR Comment
      uses: marocchino/sticky-pull-request-comment@v2
      if: github.event_name == 'pull_request'
      with:
        recreate: true
        path: code-coverage-results.md
        
    - name: Commit coverage badge to badges branch
      if: (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master') && github.event_name == 'push'
      run: |
        git config --local user.email "github-actions[bot]@users.noreply.github.com"
        git config --local user.name "github-actions[bot]"
        
        # Copy badge to temp location (outside git working directory)
        cp .github/coverage.svg /tmp/coverage.svg
        
        # Remove the coverage.svg from working directory to avoid conflicts
        rm -f .github/coverage.svg
        
        # Try to fetch and checkout badges branch, or create it if it doesn't exist
        if git fetch origin badges:badges 2>/dev/null; then
          # Branch exists, check it out
          git checkout badges
        else
          # Branch doesn't exist, create orphan branch
          git checkout --orphan badges
          # Clean all files from the new branch
          git rm -rf . 2>/dev/null || true
        fi
        
        # Create .github directory and copy badge back
        mkdir -p .github
        cp /tmp/coverage.svg .github/coverage.svg
        
        # Commit and push
        git add .github/coverage.svg
        git diff --quiet && git diff --staged --quiet || git commit -m "Update coverage badge"
        git push origin badges
        
    - name: Archive coverage HTML report
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: coverage-report
        path: htmlcov/
        retention-days: 30

  lint:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
        cache: 'pip'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
        
    - name: Run ruff check
      run: |
        ruff check ab_cli/
        
    - name: Run ruff format check
      run: |
        ruff format --check ab_cli/

  typecheck:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
        cache: 'pip'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
        
    - name: Run mypy
      run: |
        mypy ab_cli/ --ignore-missing-imports
```

## Implementation Steps

1. Create the directory structure for GitHub Actions:
   ```
   mkdir -p ab-cli/.github/workflows
   ```

2. Create the CI workflow file:
   ```
   touch ab-cli/.github/workflows/ci.yml
   ```

3. Add the workflow file content as defined above.

4. Ensure dev dependencies are properly defined in `pyproject.toml`:
   - pytest
   - pytest-cov
   - coverage-badge
   - ruff
   - mypy

5. Commit the changes and push to the repository.

## Future Enhancements

- Add dependency scanning for security vulnerabilities
- Implement automated release workflow for publishing to PyPI
- Consider adding integration tests with the Agent Builder API (using mocks)