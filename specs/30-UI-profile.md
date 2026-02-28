# Spec 30: UI Profile Display Support

## Overview

**DECISION**: Profile selection is intentionally CLI-only to prevent accidental environment changes in the UI. Users must restart the UI with a different `--profile` parameter to change profiles.

Add profile display capability to the Agent Builder UI, showing users which profile is currently active. Profile selection must be done via CLI parameters only.

## Goals

1. ✅ Display the current active profile in the UI sidebar (READ-ONLY)
2. ~~Provide a profile selector dropdown for switching profiles~~ **REMOVED** - CLI-only selection to prevent accidents
3. ~~Automatically reinitialize connections when profile changes~~ **NOT NEEDED** - no dynamic switching
4. ~~Clear all caches and refresh the UI on profile switch~~ **NOT NEEDED** - no dynamic switching
5. ✅ Support launching UI with a specific profile via CLI

## User Requirements

### Profile Display (Read-Only) ✅ IMPLEMENTED

- **Location**: Sidebar, above the "API Status" section
- **Display**: Show current profile name using `st.sidebar.info()` with emoji
- **Format**: `📋 Profile: **{profile_name}**` or `📋 Profile: **default**`
- **Visibility**: Always visible (shows which profile is active)

### Profile Initialization ✅ IMPLEMENTED

- When UI is launched with `ab ui --profile staging`, the "staging" profile:
  - Is automatically loaded at startup
  - Used to initialize the API client
  - Stored in session state as `current_profile`
  - Displayed in the sidebar

### Profile Selection - CLI ONLY

**To change profiles, users must:**
1. Stop the UI (Ctrl+C)
2. Restart with new profile: `ab ui --profile prod`

**Rationale**: Prevents accidental environment changes that could cause:
- Data loss (cleared caches)
- API calls to wrong environment  
- Confusion about which environment is active

## Technical Requirements

### 1. Command Line Support (Already Implemented ✓)

The `ab ui` command already supports `--profile` parameter:
```bash
ab ui --profile staging --direct
ab ui --profile prod
```

### 2. App Initialization Updates

**File**: `ab_cli/abui/app.py`

**Changes Needed**:
- Add `--profile` argument parsing
- Store profile name in session state
- Pass profile to config loader
- Support profile from command line args

**New Session State Keys**:
- `current_profile`: str | None - Name of active profile
- `available_profiles`: list[str] - List of profile names from config
- `data_provider`: DataProvider - Reference to data provider for cache clearing

### 3. Profile Detection and Loading

**Existing Functions** (in `ab_cli/config/loader.py`):
- `get_available_profiles(config_path)` - Extracts list of profile names from config
- `load_config_with_profile(config_path, profile)` - Loads config with profile applied

These existing functions will be reused - no new utilities needed.

### 4. Profile Switcher Component

**Location**: `ab_cli/abui/app.py` sidebar, before API Status section

**Key Elements**:
- Only show for non-mock providers (`provider_type != "mock"`)
- Profile selector using `st.sidebar.selectbox`
- Options: `["default"] + available_profiles`
- Show "(no profile defined)" if no profiles exist
- Call `handle_profile_change()` when selection changes

### 5. Profile Change Handler

**New Function**: `handle_profile_change(profile_name: str)` in `app.py`

**Logic**:
1. Update `current_profile` in session state
2. Reload configuration using `load_config_with_profile()` 
3. Reinitialize API client with new settings
4. Clear session state caches (agents, selected_agent, conversation)
5. Clear data provider cache via `clear_cache()` method
6. Show success/error message
7. Force rerun with `st.rerun()`

### 6. Data Provider Updates

**File**: `ab_cli/abui/providers/direct_data_provider.py`

**Changes**:
- Add profile support in initialization
- Implement proper `clear_cache()` if caching is added in future

**File**: `ab_cli/abui/providers/cli_data_provider.py`

**Changes**:
- Pass profile to CLI commands via `--profile` flag
- Ensure `clear_cache()` clears the command cache properly

## Implementation Steps

### Phase 1: Profile Integration
1. Import existing profile functions from `ab_cli.config.loader`
2. Verify profile functions work correctly with UI context

### Phase 2: App Initialization
1. Update `app.py` argument parsing to capture `--profile`
2. Store profile in session state on startup
3. Load available profiles from config
4. Initialize with profile if specified

### Phase 3: Profile Switcher UI
1. Add profile selector component to sidebar (above API Status)
2. Only show for CLI and Direct providers (hide in Mock mode)
3. Display current profile in dropdown
4. Show "(no profile defined)" if no profiles exist

### Phase 4: Profile Change Logic
1. Implement `handle_profile_change()` function
2. Reload configuration with new profile
3. Reinitialize API client
4. Clear all caches (session state + data provider)
5. Rerun health check
6. Force UI refresh

### Phase 5: Data Provider Integration
1. Update CLI data provider to support profile in commands
2. Ensure DirectDataProvider handles profile properly
3. Verify cache clearing works correctly

### Phase 6: Testing
1. UI tests for profile switching
3. Integration tests for cache clearing
4. Test with mock data provider (no profile selector)
5. Test with CLI and Direct providers

### Phase 7: Documentation
1. Update UI.md with profile switcher information
2. Update USAGE.md with profile examples for UI
3. Add screenshots showing profile selector

## Files to Modify

### New Files
- `tests/test_abui/test_profile_switcher.py` - Tests for profile switching

### Modified Files
- `ab_cli/config/loader.py` - Already has required functions (no changes needed)
- `ab_cli/abui/app.py` - Add profile selector UI and change handler
- `ab_cli/abui/providers/cli_data_provider.py` - Add profile support to CLI commands
- `ab_cli/abui/providers/direct_data_provider.py` - Add profile support to initialization
- `UI.md` - Document profile switcher feature
- `USAGE.md` - Add profile examples for UI command

## UI Mockup

```
┌─────────────────────────────┐
│ [Logo]                      │
│                             │
│ Navigation                  │
│ ┌─────────┬─────────┐       │
│ │ Agents  │  Chat   │       │
│ └─────────┴─────────┘       │
│                             │
│ ─────────────────────────   │
│                             │
│ **Profile:**                │
│ ┌─────────────────────────┐ │
│ │ staging            ▼    │ │ <- st.selectbox
│ └─────────────────────────┘ │
│   (default, dev, staging,   │
│    prod options)            │
│                             │
│ ─────────────────────────   │
│                             │
│ API Status:                 │
│ ✅ Connected to AB API      │
│ 🚀 Direct API               │
└─────────────────────────────┘
```

## Success Criteria

1. ✅ Profile selector appears in sidebar (CLI/Direct modes only)
2. ✅ Current profile is correctly displayed in dropdown
3. ✅ Profile passed via CLI (`--profile staging`) is auto-selected
4. ✅ Profile switching triggers config reload
5. ✅ API client is reinitialized on profile change
6. ✅ All caches (session state + provider) are cleared
7. ✅ Health check runs with new configuration
8. ✅ UI refreshes automatically after profile switch
9. ✅ Mock mode does not show profile selector
10. ✅ "(no profile defined)" shown when config has no profiles

## Testing Strategy

### Manual Testing
1. Launch UI with `ab ui --profile staging --direct`
2. Verify "staging" is selected in dropdown
3. Switch to "prod" profile
4. Verify API reconnects with prod settings
5. Verify agents list refreshes with prod data
6. Test with Mock mode - no profile selector shown

### Automated Testing
1. Unit tests for profile detection
2. Unit tests for config loading with profiles
3. UI component tests for profile selector
4. Integration tests for full profile switch flow
5. Test cache clearing mechanism

## Related Specs

- Spec 29: Profile Management (CLI-level profiles)
- Spec 28: UI Direct Data Provider
- Spec 10: UI Refactoring

## Notes

- Profile switching is a potentially disruptive operation (clears data)
- Consider adding a confirmation dialog for production use
- Health check should provide clear feedback if new profile fails
- Error handling is critical - bad profile should not crash UI
