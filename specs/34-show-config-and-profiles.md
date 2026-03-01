# Spec 34: Show Profile Information in `ab validate --show-config`

## Problem Statement

The command `ab validate --show-config` displays the configuration values but does not show any information related to available profiles and the selected profile. This makes it difficult for users to understand:
- Which profile is currently active (if any)
- What profiles are available in the config file
- Whether they're using base configuration or a profile override

## Goals

1. Add profile information to `ab validate --show-config` output
2. Display active profile name (or "none" for base config)
3. List all available profiles from the config file
4. Keep config values display simple (no per-value profile markers)
5. Maintain backward compatibility

## Desired Behavior

### Without Profile (Base Config)

```bash
$ ab validate --show-config
✅ Configuration is valid
Config file: /path/to/config.yaml

Profile Information:
  Active Profile: none (using base configuration)
  Available Profiles: dev, staging, prod

Configuration Values:
  client_id: xxx
  client_secret: ***
  ...
```

### With Profile Selected

```bash
$ ab --profile dev validate --show-config
✅ Configuration is valid
Config file: /path/to/config.yaml

Profile Information:
  Active Profile: dev
  Available Profiles: dev, staging, prod

Configuration Values:
  client_id: dev-xxx
  ...
```

### No Profiles Defined in Config

```bash
$ ab validate --show-config
Profile Information:
  Active Profile: none
  Available Profiles: none
```

## Implementation Plan

### Phase 1: Add Profile Summary Function
- **File**: `ab_cli/config/settings.py`
- Create `get_profile_summary(config_data, active_profile)` function
- Returns list of (key, value) tuples for display
- Handles cases: active profile, no profile, no profiles in config

### Phase 2: Update Validate Command
- **File**: `ab_cli/cli/main.py`
- Get active profile from Click context
- Load raw config YAML to extract available profiles
- Display "Profile Information:" section before "Configuration Values:"
- Use Rich console for consistent formatting

### Phase 3: Add Tests
- Unit tests for `get_profile_summary()` 
- CLI tests for validate with/without profiles
- Test edge cases (no profiles defined)

### Phase 4: Update Documentation
- **File**: `doc/USAGE.md`
- Update `ab validate` section with new output format

## Technical Notes

- Active profile accessed via Click context (`ctx.obj["profile"]`)
- Available profiles from raw YAML config (`profiles` key)
- Profile section displayed before config values for better context
- Edge case: empty or missing profiles section shows "Available Profiles: none"

## Success Criteria

- [x] Profile information displayed in `ab validate --show-config`
- [x] Active profile clearly indicated
- [x] Available profiles listed
- [x] Works with and without `--profile` option
- [x] All tests pass
- [x] Documentation updated
