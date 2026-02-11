# Installing Agent Builder CLI

This guide provides instructions for installing and setting up the Agent Builder CLI.

## Prerequisites

Before installing the Agent Builder CLI, you'll need:

- Python 3.10 or higher
- pip (Python package installer)
- Git (for cloning the repository)
- Valid API credentials for the Agent Builder Platform

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ab-cli
```

### 2. Create and Activate a Virtual Environment

#### On macOS/Linux:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

#### On Windows:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```

### 3. Install the Package

#### Development Installation (recommended for contributors)

```bash
# Install in development mode with development dependencies
pip install -e ".[dev]"
```

#### Standard Installation

```bash
# Install only the core package
pip install -e .
```

### 4. Verify the Installation

```bash
# Verify the CLI is installed
ab --version
```

You should see output showing the version of the Agent Builder CLI.

## Configuration

After installation, you need to create a configuration file with your API credentials.

### Creating a Configuration File

1. Copy the example configuration file:

```bash
cp config.example.yaml config.yaml
```

2. Edit `config.yaml` with your credentials:

```yaml
# Agent Builder API Configuration
api_endpoint: https://your-api-endpoint.com/
auth_endpoint: https://your-auth-endpoint.com/oauth2/token
environment_id: your-environment-id
client_id: your-client-id
client_secret: your-client-secret
```

3. Verify your configuration:

```bash
ab validate --show-config
```

## Building from Source

If you need to build the package from source:

```bash
# Install build tools
pip install build

# Build the package
python -m build

# This will create both wheel (.whl) and source (.tar.gz) distributions
# in the dist/ directory
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**

   If you see authentication errors, verify your credentials in `config.yaml` and ensure they have the necessary permissions.

   ```bash
   ab check --auth-only
   ```

2. **Missing Dependencies**

   If you encounter missing dependencies, ensure you've installed the package correctly:

   ```bash
   pip install -e ".[dev]"
   ```

3. **Python Version Issues**

   Ensure you're using Python 3.10 or higher:

   ```bash
   python --version
   ```

4. **Path Issues**

   If the `ab` command isn't found, ensure your virtual environment is activated and the package is properly installed.

### Getting Help

If you continue to experience issues, try:

```bash
# Get help with the CLI
ab --help

# Get help with a specific command
ab agents --help
```

## Upgrading

To upgrade to the latest version:

```bash
# Pull the latest changes
git pull

# Reinstall the package
pip install -e ".[dev]"
```

## Uninstalling

If you need to uninstall:

```bash
pip uninstall ab-cli