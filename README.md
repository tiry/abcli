# Agent Builder CLI (ab-cli)

[![CI](https://github.com/tiry/abcli/actions/workflows/ci.yml/badge.svg)](https://github.com/tiry/abcli/actions/workflows/ci.yml)
[![Coverage](https://raw.githubusercontent.com/tiry/abcli/badges/.github/coverage.svg)](https://github.com/tiry/abcli/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Command-line interface for the [Hyland Content Intelligence Agent Builder Platform](https://hyland.github.io/ContentIntelligence-Docs/AgentBuilderPlatform).

## Overview

The Agent Builder CLI provides a convenient way to create, manage, and invoke AI agents using the Hyland Content Intelligence Agent Builder Platform API. It enables users to interact with the platform through a simple command-line interface, making it easy to integrate AI agents into automation workflows and development pipelines.

Key features include:

- **Agent Management**: Create, list, update, and delete AI agents
- **Version Management**: Create new agent versions and track changes
- **Agent Invocation**: Execute agents with chat messages or structured inputs
- **Resource Discovery**: List available LLM models and guardrails
- **Testing Tools**: Validate configuration and API connectivity

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ab-cli

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

### Configuration

```bash
# Copy and edit the example configuration
cp config.example.yaml config.yaml

# Validate your configuration
ab validate --show-config
```

### Basic Usage

```bash
# List your agents
ab agents list
```

**Example Output:**

```
                            Agents (35 total)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┓
┃ ID                              ┃ Name         ┃ Type ┃ Status  ┃ Created   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━┩
│ 8f6c2178-4f0a-43fb-88d7-f3d8... │ Calculator   │ tool │ CREATED │ 2026-02-… │
│ d9ce3525-0899-48b1-869f-ff9a... │ Document RAG │ rag  │ CREATED │ 2026-02-… │
│ 10238ef8-1882-430c-8cbb-3498... │ Insurance    │ task │ CREATED │ 2026-02-… │
└───────────────────────────────┴──────────────┴──────┴─────────┴───────────┘
```

See [USAGE.md](USAGE.md) for comprehensive command documentation.

## Project Structure

```
ab-cli/
├── ab_cli/                 # Core package directory
│   ├── __init__.py
│   ├── api/                # API client components
│   ├── cli/                # CLI commands and interfaces
│   ├── config/             # Configuration handling
│   ├── models/             # Data models
│   └── utils/              # Utility functions
├── tests/                  # Test suite
├── specs/                  # Specification documents
├── config.example.yaml     # Example configuration
├── pyproject.toml          # Project dependencies
├── README.md               # This file
├── USAGE.md                # Detailed command documentation
├── INSTALL.md              # Installation instructions
└── TESTING.md              # Testing documentation
```

## Core Principles

- **Usability**: Easy to use with intuitive commands and helpful documentation
- **Flexibility**: Support for different output formats (table, JSON, YAML)
- **Reliability**: Robust error handling and detailed feedback
- **Extensibility**: Modular design makes it easy to add new features
- **Testability**: Comprehensive test suite to ensure quality

## Documentation

- [USAGE.md](USAGE.md): Detailed command documentation with examples
- [INSTALL.md](INSTALL.md): Installation and setup instructions
- [TESTING.md](TESTING.md): Instructions for testing the CLI

## Features

- [x] **Configuration Management**: Load from files or environment variables
- [x] **Agent Management**: Create, list, update, patch and delete agents
- [x] **Version Management**: Create, list, and get agent versions
- [x] **Agent Invocation**: Chat, task, and interactive modes
- [x] **Resource Management**: List available LLM models and guardrails
- [x] **Multiple Output Formats**: Table, JSON, and YAML output formats
- [x] **Authentication**: OAuth2 authentication with token caching

## Testing and CI

The project has a comprehensive test suite with over 77% code coverage:

- **224 passing tests** covering all major components
- **Near-complete coverage** of critical modules:
  - Configuration (100%)
  - Authentication (98%)
  - Agent models (100%)
  - Resource models (100%)
  - Invocation utilities (90%)

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage report
pytest --cov=ab_cli --cov-report=term-missing
```

### Continuous Integration

The project uses GitHub Actions for continuous integration with the following workflows:

- **Automated testing** with coverage reporting
- **Code quality checks** using ruff for linting and formatting
- **Type checking** with mypy
- **Coverage badge** generation on the badges branch

See [TESTING.md](TESTING.md) for more information on testing practices and procedures.

## License

MIT
