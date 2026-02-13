# Agent Builder CLI Configuration Guide

This document provides detailed information about all configuration parameters for the Agent Builder CLI.

## Configuration Methods

The Agent Builder CLI can be configured in three ways:

1. **Configuration File**: A YAML file named `config.yaml` or `ab-cli.yaml` in the current directory
2. **Environment Variables**: Prefixed with `AB_` (e.g., `AB_CLIENT_SECRET`)
3. **.env File**: A .env file containing environment variables

## Required Parameters

| Parameter | Environment Variable | Description | 
|-----------|---------------------|-------------|
| `environment_id` | `AB_ENVIRONMENT_ID` | HxP environment ID for your tenant |
| `client_id` | `AB_CLIENT_ID` | OAuth2 client ID for authentication |
| `client_secret` | `AB_CLIENT_SECRET` | OAuth2 client secret for authentication |

## API Endpoint Configuration

| Parameter | Environment Variable | Default | Description |
|-----------|---------------------|---------|-------------|
| `api_endpoint` | `AB_API_ENDPOINT` | `https://api.agentbuilder.experience.hyland.com/` | Base URL for the Agent Builder API |
| `auth_endpoint` | `AB_AUTH_ENDPOINT` | `https://auth.iam.experience.hyland.com/idp/connect/token` | OAuth2 token endpoint URL |

### Environment Specific Endpoints

#### Production Environment
```yaml
api_endpoint: "https://api.agentbuilder.experience.hyland.com/"
auth_endpoint: "https://auth.iam.experience.hyland.com/idp/connect/token"
```

#### Development Environment
```yaml
api_endpoint: "https://api.agentbuilder.dev.experience.hyland.com/"
auth_endpoint: "https://auth.iam.dev.experience.hyland.com/idp/connect/token"
```

## Authentication Settings

| Parameter | Environment Variable | Default | Description |
|-----------|---------------------|---------|-------------|
| `auth_scope` | `AB_AUTH_SCOPE` | `["hxp"]` | OAuth2 scopes to request |
| `grant_type` | `AB_GRANT_TYPE` | `client_credentials` | OAuth2 grant type |

### Grant Type Options

The following grant types are supported by the IAM system:

- `client_credentials` (default, for service accounts)
- `urn:hyland:params:oauth:grant-type:api-credentials` (for API credentials)

See the OpenID Configuration at `https://auth.iam.dev.experience.hyland.com/idp/.well-known/openid-configuration` for more information.

## HTTP Settings

| Parameter | Environment Variable | Default | Range | Description |
|-----------|---------------------|---------|-------|-------------|
| `timeout` | `AB_TIMEOUT` | `30.0` | 1.0 - 300.0 | HTTP request timeout in seconds |
| `max_retries` | `AB_MAX_RETRIES` | `3` | 0 - 10 | Maximum number of retry attempts |
| `retry_backoff` | `AB_RETRY_BACKOFF` | `2.0` | 1.0 - 10.0 | Exponential backoff multiplier for retries |

## Output Preferences

| Parameter | Environment Variable | Default | Options | Description |
|-----------|---------------------|---------|---------|-------------|
| `default_output_format` | `AB_DEFAULT_OUTPUT_FORMAT` | `table` | `table`, `json`, `yaml` | Default output format for commands |

## Audit Settings

| Parameter | Environment Variable | Default | Description |
|-----------|---------------------|---------|-------------|
| `record_updates` | `AB_RECORD_UPDATES` | `false` | Whether to save API payloads for create/update operations |

When `record_updates` is enabled, all API payloads for create and update operations will be saved to an `audit` folder next to the configuration file. Each file is named with the operation name and a timestamp, e.g., `create_agent_20260212_203822.json`.

## Complete Configuration Example

```yaml
# Agent Builder CLI Configuration
# Required parameters
environment_id: "your-environment-id"
client_id: "your-client-id"
client_secret: "your-client-secret"

# API Endpoints (optional - defaults shown)
api_endpoint: "https://api.agentbuilder.experience.hyland.com/"
auth_endpoint: "https://auth.iam.experience.hyland.com/idp/connect/token"

# OAuth2 settings (optional)
grant_type: "client_credentials"
auth_scope:
  - "hxp"

# HTTP Settings (optional)
timeout: 30.0       # Request timeout in seconds
max_retries: 3      # Maximum retry attempts for transient errors
retry_backoff: 2.0  # Exponential backoff multiplier

# Output preferences (optional)
default_output_format: "table"

# Audit settings (optional)
record_updates: false
```

## Configuration File Location

The CLI will look for configuration files in the following order:

1. File specified by the `--config` option
2. `config.yaml` in the current directory
3. `ab-cli.yaml` in the current directory

## Validation

You can validate your configuration using the `validate` command:

```bash
# Validate configuration
ab validate

# Show loaded configuration values
ab validate --show-config
```
