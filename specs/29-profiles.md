
# Spec 29: Multi-Environment Profile Support

## Objective
Add profile support to enable working with multiple environments (dev, staging, prod) from a single configuration file.

## Requirements

### Configuration Structure
- Add optional `profiles` section to config file
- Top-level config = "default" profile
- Each profile can override default values
- Profiles cannot contain nested `profiles` section

### CLI Integration
- Add global `-p/--profile` flag to all commands
- Profile selection: CLI flag → Profile config → Env vars → Default
- Error on invalid/non-existent profile
- Default profile used when no flag specified

### Profiles Command
New `ab profiles` command with subcommands:
- `ab profiles list` - Show all available profiles
- `ab profiles show [profile_name]` - Display merged config (redact secrets)
  - If no name given, show default profile

## Implementation Plan

### 1. Configuration Layer (`ab_cli/config/`)
**File: `settings.py`**
- Add `profiles: Optional[Dict[str, Dict[str, Any]]]` to ABSettings
- Add `apply_profile(profile_name: str) -> ABSettings` method
  - Merge profile overrides into base settings
  - Validate profile exists
  - Return new settings instance with merged values

**File: `loader.py`**
- Add `load_config_with_profile(config_path, profile: Optional[str])` function
- Add `get_available_profiles(config_path) -> List[str]` function
- Add `merge_profile_settings(base_dict, profile_dict) -> dict` helper
  - Deep merge profile values over base
  - Handle all config types (strings, ints, dicts, lists)

### 2. CLI Layer (`ab_cli/cli/`)
**File: `main.py`**
- Add `--profile/-p` as global option in main CLI group
- Pass profile to all command functions via context
- Store profile in click context for child commands

**File: `profiles.py`** (NEW)
- `profiles_group()` - Main command group
- `list_profiles()` - List all profiles from config
- `show_profile(profile_name: Optional[str])` - Display merged config
  - Use `get_config_summary()` for secret redaction
  - Show which values are overridden

**File: `client_utils.py`**
- Update `get_client_with_error_handling()` to accept profile parameter
- Apply profile before creating client

### 3. Testing (`tests/`)
**Directory: `tests/data/profiles/`** (NEW)
- `config-with-profiles.yaml` - Sample config with dev/staging profiles
- `config-no-profiles.yaml` - Config without profiles section
- `config-invalid-profile.yaml` - Config with malformed profiles

**File: `tests/test_config/test_profiles.py`** (NEW)
- `test_load_profile_success()` - Profile merging works
- `test_load_default_profile()` - No profile specified
- `test_load_invalid_profile()` - Error on non-existent profile
- `test_profile_overrides_base()` - Profile values override defaults
- `test_profile_partial_override()` - Unspecified values use defaults
- `test_nested_config_merge()` - Deep merge for nested dicts
- `test_list_profiles()` - Get all profile names
- `test_profile_precedence()` - Profile > env vars

**File: `tests/test_cli/test_profiles.py`** (NEW)
- `test_profiles_list_command()` - List profiles CLI
- `test_profiles_show_command()` - Show profile with redaction
- `test_profiles_show_default()` - Show without name argument
- `test_global_profile_flag()` - Profile flag works on commands

### 4. Documentation
**File: `CONFIG.md`**
- Add "Profiles" section
- Document profiles structure
- Show example multi-environment config
- Explain merge behavior and precedence

**File: `USAGE.md`**
- Add `ab profiles` command documentation
- Show `--profile` flag usage examples
- Add multi-environment workflow examples

**File: `config.example.yaml`**
- Add commented example profiles section

## Order of Precedence
1. Profile-specific values (from selected profile)
2. Environment variables (AB_* prefixed)
3. Top-level config (default profile)

## Example Usage
```bash
# List available profiles
ab profiles list

# Show merged config for dev profile
ab profiles show dev

# Use dev profile for commands
ab --profile dev agents list
ab -p staging invoke <agent-id> --message "test"

# Default profile (no flag)
ab agents list
```

## Testing Checklist
- [ ] Config loading with profiles
- [ ] Profile merging logic
- [ ] Invalid profile handling
- [ ] CLI global flag integration
- [ ] Profiles command (list/show)
- [ ] Secret redaction in show command
- [ ] All existing tests still pass
- [ ] Linting passes (ruff, mypy)

## Implementation Steps
1. Add profile support to settings/loader (with tests)
2. Implement `ab profiles` command
3. Add global `--profile` flag to main CLI
4. Update all command functions to use profile
5. Create test data files
6. Write comprehensive unit tests
7. Update documentation (CONFIG.md, USAGE.md)
8. Run full test suite and linting

