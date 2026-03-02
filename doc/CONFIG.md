# Agent Builder CLI Configuration Guide

This document provides detailed information about all configuration parameters for the Agent Builder CLI.

## Configuration Methods

The Agent Builder CLI can be configured in three ways:

1. **Configuration File**: A YAML file named `config.yaml` or `ab-cli.yaml` in the current directory
2. **Environment Variables**: Prefixed with `AB_` (e.g., `AB_CLIENT_SECRET`)
3. **.env File**: A .env file containing environment variables

## Configuration Profiles

Profiles allow you to maintain multiple environment configurations (dev, staging, prod) in a single configuration file. You can switch between profiles using the `--profile` flag.

### Defining Profiles

Add a `profiles` section to your configuration file:

```yaml
# Base configuration (default)
client_id: "default-client-id"
client_secret: "default-secret"
api_endpoint: "https://api.agentbuilder.experience.hyland.com/"
timeout: 30.0

# Environment-specific profiles
profiles:
  dev:
    client_id: "dev-client-id"
    client_secret: "dev-secret"
    api_endpoint: "https://api.agentbuilder.dev.experience.hyland.com/"
    timeout: 60.0
  
  staging:
    client_id: "staging-client-id"
    client_secret: "staging-secret"
    api_endpoint: "https://api.agentbuilder.staging.experience.hyland.com/"
    max_retries: 5
  
  prod:
    client_id: "prod-client-id"
    client_secret: "prod-secret"
    api_endpoint: "https://api.agentbuilder.experience.hyland.com/"
    timeout: 45.0
    default_output_format: "json"
```

### Using Profiles

```bash
# Use dev profile
ab --profile dev agents list

# Use prod profile  
ab --profile prod invoke my-agent "Hello"

# Without profile, uses base configuration
ab agents list
```

### Managing Profiles

```bash
# List all available profiles
ab profiles list

# Show configuration for a specific profile
ab profiles show dev

# Show default (base) configuration
ab profiles show
```

### Profile Configuration Rules

1. **Deep Merging**: Profile settings are deeply merged with the base configuration
2. **Override Behavior**: Profile values override base configuration values
3. **Nested Support**: Nested settings (like `ui.data_provider`) are properly merged
4. **Profiles are Optional**: You can omit the profiles section entirely

**Example of Nested Merging:**

```yaml
# Base configuration
timeout: 30.0
ui:
  data_provider: "cli"

profiles:
  dev:
    timeout: 60.0
    ui:
      data_provider: "direct"  # Overrides only this nested value
```

Result when using `--profile dev`:
- `timeout`: 60.0 (overridden)
- `ui.data_provider`: "direct" (overridden)

## Required Parameters

| Parameter | Environment Variable | Description | 
|-----------|---------------------|-------------|
| `client_id` | `AB_CLIENT_ID` | OAuth2 client ID for authentication |
| `client_secret` | `AB_CLIENT_SECRET` | OAuth2 client secret for authentication |

## Optional Tenant Parameters

| Parameter | Environment Variable | Default | Description |
|-----------|---------------------|---------|-------------|
| `environment_id` | `AB_ENVIRONMENT_ID` | `None` | HxP environment ID for your tenant (optional - can be derived from API) |

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
| `auth_scope` | `AB_AUTH_SCOPE` | `["hxp environment_authorization"]` | OAuth2 scopes to request |
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

## Editor Settings

| Parameter | Environment Variable | Default | Description |
|-----------|---------------------|---------|-------------|
| `editor` | `AB_EDITOR` | `None` | Text editor command for interactive agent editing |

The `editor` parameter specifies which text editor to use for the `ab agents edit` command. If not specified, the CLI follows this priority chain:

1. `--editor` command-line flag
2. `editor` setting in config.yaml
3. `$VISUAL` environment variable
4. `$EDITOR` environment variable
5. Platform default (`vi` on Unix/macOS, `notepad.exe` on Windows)

### Editor Examples

```yaml
# VS Code (wait for editor to close)
editor: "code --wait"

# Vim
editor: "vim"

# Nano
editor: "nano"

# Emacs
editor: "emacs"

# Sublime Text
editor: "subl --wait"

# Windows Notepad
editor: "notepad.exe"
```

### Important Notes

- **Wait Flag**: For GUI editors like VS Code or Sublime Text, use the `--wait` flag to ensure the CLI waits for you to finish editing
- **Command with Arguments**: You can include command-line arguments in the editor string
- **Path to Editor**: If the editor is not in your PATH, provide the full path: `editor: "/usr/local/bin/vim"`

### Editor Profile Example

You can set different editors for different profiles:

```yaml
# Base configuration
editor: "vi"

profiles:
  dev:
    editor: "code --wait"  # VS Code for development
  
  prod:
    editor: "vim"  # Vim for production
```

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

## Configuration Validation and Testing

### Validating Configuration

You can validate your configuration file structure and values using the `validate` command:

```bash
# Validate configuration file
ab validate

# Show loaded configuration values
ab validate --show-config
```

**Example Output:**

```
Validating: config.yaml

✅ Configuration is valid

Configuration values:
  API endpoint:     https://api.agentbuilder.experience.hyland.com/
  Auth endpoint:    https://auth.iam.experience.hyland.com/idp/connect/token
  Environment ID:   your-environment-id
  Client ID:        your-cli...cret
  Client secret:    ********************
```

### Testing Connectivity

You can test both authentication and API connectivity using the `check` command:

```bash
# Test full connectivity (authentication + API)
ab check

# Test authentication only
ab check --auth-only
```

**Example Output:**

```
=== Agent Builder API Connectivity Check ===

Step 1/3: Loading configuration
  Config file: config.yaml
  ✓ Configuration loaded successfully

Step 2/3: Testing authentication
  ✓ Valid OAuth2 token received!

Step 3/3: Testing API connectivity
  ✓ API responded successfully!

=== Check Complete ===
  All API endpoints are working correctly!
```

For more details on configuration validation and testing, see the [Usage Guide](USAGE.md#configuration).
