# Spec 22: Configuration Wizard Command

## Overview

Add an interactive `configure` command to ab-cli that guides users through creating and editing their configuration file. This command will make initial setup easier and provide a user-friendly way to update configuration values.

## Current State

### Configuration Management
- Config is loaded from YAML files: `config.yaml`, `ab-cli.yaml`, or `~/.ab-cli/config.yaml`
- Users must manually copy `config.example.yaml` and edit values
- The `validate` command checks configuration validity
- The `check` command tests connectivity with current config
- Missing/invalid config causes commands to fail with error messages

### Current User Experience Pain Points
1. **First-time setup is manual**: Users must find, copy, and edit config.example.yaml
2. **No guided process**: Users need to know all required fields and valid values
3. **Error-prone**: Easy to make syntax errors or miss required fields
4. **No easy updates**: Changing a single value requires manual YAML editing

## Requirements

### 1. Interactive Configuration Wizard

**Command**: `ab configure [OPTIONS]`

**Behavior**:
- **First-time configuration**: Prompts for all required fields, offers defaults for optional ones
- **Update existing config**: Loads current values and allows editing each field
- **Both modes supported**:
  - Interactive mode (default): Prompts user for each field
  - Non-interactive mode: Accept values via CLI options

**Required Fields** (must be provided):
- `client_id`: OAuth2 Client ID
- `client_secret`: OAuth2 Client Secret
- `api_endpoint`: Agent Builder API endpoint URL
- `auth_endpoint`: OAuth2 authentication endpoint URL

**Optional Fields** (offer defaults from config.example.yaml):
- `grant_type`: OAuth2 grant type (default: "client_credentials")
- `auth_scope`: OAuth2 scopes (default: ["hxp"])

**Note**: Advanced configuration options (timeout, retries, output format, audit settings, pagination, UI settings) should be configured manually by editing the config file. The `configure` command focuses on the essential authentication and API endpoint settings.

### 2. Command Options

```bash
# Interactive mode (default)
ab configure                                    # Use default location (~/.ab-cli/config.yaml)
ab configure -c config.yaml                     # Specify target file
ab configure --output config.yaml               # Alternative syntax

# Non-interactive mode with CLI options
ab configure \
  --client-id "client-abc" \
  --client-secret "secret-xyz" \
  --api-endpoint "https://api.agentbuilder.experience.hyland.com/" \
  --auth-endpoint "https://auth.iam.experience.hyland.com/idp/connect/token" \
  --output ~/.ab-cli/config.yaml

# Update specific fields (reads existing config, updates specified fields)
ab configure --client-id "new-client-id" -c config.yaml

# Show current configuration (read-only)
ab configure --show

# Interactive update of existing config
ab configure -c existing-config.yaml           # Will prompt for each field with current value as default
```

**Options**:
```
-c, --config PATH          Target configuration file (default: ~/.ab-cli/config.yaml)
-o, --output PATH          Alternative syntax for target file
--client-id TEXT           Set OAuth2 client ID
--client-secret TEXT       Set OAuth2 client secret (prompted securely if not provided)
--api-endpoint URL         Set API endpoint URL
--auth-endpoint URL        Set auth endpoint URL
--grant-type TEXT          Set OAuth2 grant type
--auth-scope TEXT          Set OAuth2 scope (can be repeated)
--show                     Show current configuration and exit
--force                    Overwrite existing file without confirmation
--help                     Show this message and exit
```

### 3. Interactive Mode Flow

When running `ab configure` without non-interactive options:

```
=== Agent Builder CLI Configuration ===

This wizard will help you configure ab-cli.

Configuration file: ~/.ab-cli/config.yaml
File exists: No

Let's configure the required settings.

Required Settings
─────────────────

Client ID: <user input>
  OAuth2 client ID for authentication.

Client Secret: <user input, hidden>
  OAuth2 client secret (input will be hidden).

API Endpoint: <user input>
  Agent Builder API endpoint URL.
  Examples:
    Production: https://api.agentbuilder.experience.hyland.com/
    Development: https://api.agentbuilder.dev.experience.hyland.com/

Auth Endpoint: <user input>
  OAuth2 authentication endpoint URL.
  Examples:
    Production: https://auth.iam.experience.hyland.com/idp/connect/token
    Development: https://auth.iam.dev.experience.hyland.com/idp/connect/token

Optional Settings
─────────────────

Configure optional settings? [y/N]: 

[If yes, prompt for each optional field with defaults]

OAuth2 Grant Type [client_credentials]: 
OAuth2 Scopes [hxp]: 

Configuration Summary
─────────────────────

✓ Client ID:         client-***
✓ Client Secret:     ****************
✓ API Endpoint:      https://api.agentbuilder.experience.hyland.com/
✓ Auth Endpoint:     https://auth.iam.experience.hyland.com/idp/connect/token
✓ Grant Type:        client_credentials
✓ Auth Scopes:       hxp

Save configuration to ~/.ab-cli/config.yaml? [Y/n]: 

✓ Configuration saved successfully!

Next Steps:
  1. Test your configuration: ab check
  2. List available agents: ab agents list
  3. Get help: ab --help
```

### 4. Update Existing Configuration

When the target config file already exists:

```
=== Agent Builder CLI Configuration ===

Configuration file: ~/.ab-cli/config.yaml
File exists: Yes

Loading current configuration...

✓ Current configuration is valid.

You can now update any field. Press Enter to keep the current value.

Required Settings
─────────────────

Client ID [current-client-id]: <user input or Enter>
Client Secret [****************]: <user input or Enter>
API Endpoint [https://api.agentbuilder.experience.hyland.com/]: <user input or Enter>
Auth Endpoint [https://auth.iam.experience.hyland.com/idp/connect/token]: <user input or Enter>

Optional Settings
─────────────────

Update optional settings? [y/N]: 

[If yes, prompt for optional fields with current values as defaults]

OAuth2 Grant Type [client_credentials]: <user input or Enter>
OAuth2 Scopes [hxp]: <user input or Enter>

Configuration Summary
─────────────────────

Modified fields:
✓ Client ID: client-old → client-new
✓ Auth Endpoint: auth.iam.dev... → auth.iam.experience...

Save changes to ~/.ab-cli/config.yaml? [Y/n]: 

✓ Configuration updated successfully!

Would you like to test the connection? [Y/n]: y

Running: ab check
[... check command output ...]
```

### 5. Configuration File Validation

After creating/updating the config file:
1. **Validate structure**: Ensure YAML is valid and all required fields are present
2. **Validate values**: Check that URLs are well-formed, numeric values are in range, etc.
3. **Offer to test**: Suggest running `ab check` to verify connectivity

### 6. Config Requirement Enforcement

**Main CLI Entry Point Changes** (`ab_cli/cli/main.py`):

```python
# Current behavior: Load config if found, continue silently if not
# New behavior: Enforce config requirement

@click.group()
@click.pass_context
def main(ctx: click.Context, verbose: bool, config: Path | None) -> None:
    """Agent Builder CLI - Manage and invoke AI agents."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    
    # Allow these commands without config
    allowed_without_config = ['configure', 'validate', 'version', '--help', '--version']
    command = ctx.invoked_subcommand
    
    if command not in allowed_without_config:
        config_path = config or find_config_file()
        
        if not config_path:
            error_console.print("[red]No configuration file found.[/red]")
            error_console.print("\nSearched locations:")
            error_console.print("  • config.yaml (current directory)")
            error_console.print("  • ab-cli.yaml (current directory)")
            error_console.print("  • ~/.ab-cli/config.yaml")
            error_console.print("\nTo create a configuration file, run:")
            error_console.print("  [cyan]ab configure[/cyan]")
            sys.exit(1)
        
        try:
            ctx.obj["settings"] = load_config(config_path)
            ctx.obj["config_path"] = str(config_path)
        except ConfigurationError as e:
            error_console.print(f"[red]Invalid configuration:[/red] {e}")
            error_console.print("\nTo fix your configuration, run:")
            error_console.print("  [cyan]ab configure[/cyan]")
            sys.exit(1)
```

**Commands that work WITHOUT config**:
- `ab configure` - Create/edit configuration
- `ab validate` - Validate a specific config file
- `ab --version` - Show version
- `ab --help` - Show help

**Commands that REQUIRE config**:
- All other commands (agents, invoke, resources, check, ui, etc.)

### 7. Integration with `check` Command

After successful configuration, offer to run the `check` command:

```
✓ Configuration saved successfully!

Test the configuration now? [Y/n]: y

Running: ab check
[... output from check command ...]
```

## Implementation Details

### File Structure

**New file**: `ab_cli/cli/configure.py`
- Contains the `configure` command implementation
- Interactive prompting logic
- Config file read/write operations
- Field validation

**Modified file**: `ab_cli/cli/main.py`
- Add config requirement check
- Import and register `configure` command
- Update error messages to suggest `ab configure`

**Utility functions** (in `ab_cli/config/` or configure.py):
- `prompt_for_field(name, default=None, required=True, hidden=False)`
- `load_existing_config(path)` - Load and parse existing config
- `save_config(path, config_dict)` - Write config with proper formatting
- `format_config_yaml(config_dict)` - Format YAML with comments
- `validate_config_values(config_dict)` - Validate individual field values

### Technologies

**Click features to use**:
- `click.prompt()` - For input prompts
- `click.confirm()` - For yes/no questions
- `click.password_option()` - For secret input
- `click.Choice()` - For dropdown selections

**Rich features to use**:
- `Console` - Formatted output
- `Prompt` from `rich.prompt` - Enhanced prompts with validation
- `Confirm` from `rich.prompt` - Pretty confirmations
- `Table` - Display configuration summary

### Config File Format

The generated YAML should include helpful comments:

```yaml
# Agent Builder CLI Configuration
# Generated by: ab configure
# Date: 2026-02-18

# HxP Environment ID (required)
environment_id: "env-123"

# OAuth2 Authentication (required)
client_id: "client-abc"
client_secret: "secret-xyz"

# API Endpoints (required)
api_endpoint: "https://api.agentbuilder.experience.hyland.com/"
auth_endpoint: "https://auth.iam.experience.hyland.com/idp/connect/token"

# OAuth2 Configuration (optional)
grant_type: "client_credentials"
auth_scope:
  - "hxp"

# HTTP Settings (optional)
timeout: 30.0
max_retries: 3
retry_backoff: 2.0

# Output preferences (optional)
default_output_format: "table"

# Audit settings (optional)
record_updates: false

# Pagination Configuration (optional)
pagination:
  max_filter_pages: 10

# UI Configuration (optional)
ui:
  data_provider: "cli"
  mock_data_dir: ""
```

## Testing Requirements

### Unit Tests (`tests/test_cli/test_configure.py`)

**Test scenarios**:
1. **Interactive mode - new config**
   - Prompt for all required fields
   - Accept defaults for optional fields
   - Create config file at specified location
   
2. **Interactive mode - update existing**
   - Load existing values as defaults
   - Update only changed fields
   - Preserve comments and formatting where possible

3. **Non-interactive mode**
   - All required options provided via CLI
   - Create valid config file
   - Error if required options missing

4. **Mixed mode**
   - Some options via CLI, prompt for others
   - CLI options override prompts

5. **Validation**
   - Invalid URLs rejected
   - Required fields enforced
   - Numeric values validated
   - Enum values validated (output_format, data_provider, etc.)

6. **File operations**
   - Create directory if doesn't exist
   - Confirm before overwriting (unless --force)
   - Handle permission errors gracefully

7. **Integration with check**
   - Option to run check after configuration
   - Proper error handling if check fails

### Integration Tests

1. **End-to-end configuration flow**
   - Run configure, create config, run check
   - Verify config is usable for API calls

2. **Config enforcement**
   - Commands fail without config (except allowed ones)
   - Helpful error messages displayed

### Manual Testing Checklist

- [ ] First-time setup with interactive mode
- [ ] Update existing config interactively
- [ ] Non-interactive mode with all options
- [ ] Mixed interactive/non-interactive mode
- [ ] Invalid input handling (bad URLs, out-of-range numbers)
- [ ] File permission errors
- [ ] Overwrite confirmation
- [ ] Integration with `ab check`
- [ ] Config enforcement for other commands
- [ ] Help text clarity

## Documentation Updates

### USAGE.md

Add new section:

```markdown
## Configuration

### Interactive Configuration Wizard

The easiest way to set up ab-cli is with the interactive configuration wizard:

```bash
# Create new configuration
ab configure

# Update existing configuration
ab configure -c config.yaml

# Specify output location
ab configure --output ~/.ab-cli/config.yaml
```

### Non-Interactive Configuration

For automation or scripts, you can provide all values via command-line options:

```bash
ab configure \
  --environment-id "your-env-id" \
  --client-id "your-client-id" \
  --client-secret "your-secret" \
  --api-endpoint "https://api.agentbuilder.experience.hyland.com/" \
  --auth-endpoint "https://auth.iam.experience.hyland.com/idp/connect/token" \
  --output config.yaml
```

### Configuration File Locations

ab-cli searches for configuration in this order:
1. File specified with `-c/--config` option
2. `config.yaml` in current directory
3. `ab-cli.yaml` in current directory
4. `~/.ab-cli/config.yaml`

The `configure` command defaults to creating `~/.ab-cli/config.yaml`.
```

### README.md

Update the "Getting Started" section:

```markdown
## Quick Start

1. **Install ab-cli** (see Installation section)

2. **Configure ab-cli**:
   ```bash
   ab configure
   ```
   Follow the interactive prompts to set up your API credentials.

3. **Test your configuration**:
   ```bash
   ab check
   ```

4. **List available agents**:
   ```bash
   ab agents list
   ```
```

## Success Criteria

- [ ] `ab configure` command creates valid configuration files
- [ ] Interactive mode guides users through all required fields
- [ ] Non-interactive mode accepts all options via CLI
- [ ] Existing configurations can be updated field-by-field
- [ ] Config validation catches common errors
- [ ] Commands requiring config show helpful error messages
- [ ] Integration with `ab check` works smoothly
- [ ] All tests pass
- [ ] `./lint.sh` passes without errors
- [ ] Documentation is clear and comprehensive
- [ ] User experience is smooth for first-time setup

## Implementation Phases

### Phase 1: Core configure Command
- Create `ab_cli/cli/configure.py`
- Implement interactive prompting for required fields
- Basic config file writing
- Unit tests for core functionality

### Phase 2: Enhanced Features
- Optional fields configuration
- Update existing config mode
- Non-interactive mode with CLI options
- Config validation and error handling

### Phase 3: Integration
- Modify main.py to enforce config requirement
- Integration with `ab check` command
- Improve error messages across CLI

### Phase 4: Polish & Documentation
- Add comprehensive tests
- Update USAGE.md and README.md
- Manual testing and refinement
- Run lint.sh and fix any issues

## Open Questions / Decisions

1. **Secret storage security**: Should we warn users about storing secrets in plain text? Consider suggesting environment variables for secrets in CI/CD scenarios.

2. **Backup on update**: When updating existing config, should we create a backup (config.yaml.backup)?

3. **Environment detection**: Should we add hints/warnings if URLs don't match common patterns (e.g., mixing dev/prod endpoints)?

4. **Config migration**: If config format changes in future versions, should configure command handle migration?

## Notes

- Use `rich.prompt` for enhanced user experience
- Follow existing CLI patterns (error messages, output formatting)
- Maintain backward compatibility with manual config files
- Consider adding `ab config show` as alias for viewing current config
- Ensure secrets are never logged or displayed in plain text (except during entry)
