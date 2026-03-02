# Spec 36: Agent Edit Command

## Problem Statement

Editing an agent currently requires multiple manual steps:

1. Get agent full definition and export as JSON:
   ```bash
   ab --profile staging agents get <agent-id> -f json
   ```

2. Manually edit the definition:
   - Extract the config object from the payload
   - Extract and increment the version number
   - Construct the right JSON structure

3. Create a new version of the agent with the modified config

This workflow is error-prone, requires understanding of the JSON structure, and involves multiple manual transformations.

## Goals

Create an `ab agents edit` command that:
- Streamlines the agent editing workflow
- Fetches the full agent definition automatically
- Extracts config and version data
- Opens a text editor with a prepared JSON file
- Auto-increments the version label (minor version)
- Prompts for confirmation before pushing changes
- Creates a new agent version using the existing API

## Implementation Plan

### Phase 1: Configuration Support

**File**: `ab_cli/config/settings.py`

Add editor configuration parameter to `ABSettings`:
- `editor`: Optional text editor path/command
- Default: Use same logic as git (`$VISUAL`, `$EDITOR`, platform defaults)
- Fallback order:
  1. Config file `editor` setting
  2. `$VISUAL` environment variable
  3. `$EDITOR` environment variable  
  4. Platform default (`vi` for Unix, `notepad.exe` for Windows)

**File**: `config.example.yaml`

Add editor configuration example:
```yaml
# Optional: Text editor for interactive editing
# editor: vim
# editor: code --wait
# editor: nano
```

### Phase 2: Version Helper Utility

**File**: `ab_cli/utils/version.py` (new)

**Move existing `increment_version` function** from `ab_cli/abui/views/edit_agent.py` to this new utility module:
- `increment_version(version: str) -> str`: Increment the last numeric component
- Already handles various formats: "v1.0" → "v1.1", "1.2.3" → "1.2.4", "release-5" → "release-6"
- Uses regex to find and increment the last number in the string
- If no number found, appends ".1"

**File**: `ab_cli/abui/views/edit_agent.py` (modify)

Update to import `increment_version` from utils:
```python
from ab_cli.utils.version import increment_version
```

Remove the local `increment_version` function definition.

**File**: `ab_cli/utils/__init__.py` (modify)

Export the version utility:
```python
from ab_cli.utils.version import increment_version
```

### Phase 3: Agent Edit Command

**File**: `ab_cli/cli/agents.py`

Add `edit` subcommand:

```python
@agents.command()
@click.argument('agent_id')
@click.option('--editor', help='Override editor selection')
@click.option('--keep-temp', is_flag=True, help='Keep temporary file after completion')
@click.pass_context
def edit(ctx, agent_id: str, editor: str | None, keep_temp: bool):
    """Edit an agent configuration interactively.
    
    Opens the agent config in your default editor, auto-increments
    the version label, and creates a new agent version with your changes.
    """
```

**Workflow**:
1. Fetch agent definition using existing `get_agent()` API
2. Extract current `config` object
3. Extract current `versionLabel` and auto-increment minor version
4. Create temp JSON file with structure:
   ```json
   {
     "versionLabel": "1.2.0",
     "config": {
       // agent config
     }
   }
   ```
5. Open editor with temp file path
6. Wait for editor to close
7. Read and validate modified JSON
8. Prompt user: "Create new version with these changes? (y/N)"
9. If yes: call version creation API
10. Clean up temp file (unless `--keep-temp`)

### Phase 4: Editor Management

**File**: `ab_cli/utils/editor.py` (new)

Create editor management utilities:
- `get_editor(config: ABSettings, override: str | None) -> str`: Determine which editor to use
- `open_editor(file_path: str, editor_cmd: str) -> int`: Open editor and wait for completion
- Handle cross-platform differences (Windows vs Unix)
- Handle editors that require special flags (e.g., VS Code needs `--wait`)

### Phase 5: Temp File Management

**File**: `ab_cli/utils/tempfile_manager.py` (new)

Create temp file utilities:
- Use `tempfile.NamedTemporaryFile` with `delete=False`
- Create in system temp directory
- Naming pattern: `ab-agent-edit-{agent_id}-{timestamp}.json`
- Cleanup function with error handling
- Option to preserve for debugging (`--keep-temp`)

### Phase 6: Error Handling

Handle common error scenarios:
- Editor not found or fails to launch
- User cancels edit (no changes made)
- Invalid JSON after edit
- Missing required fields (versionLabel, config)
- API errors during version creation
- Permission errors for temp file

Display clear error messages and cleanup properly in all cases.

### Phase 7: Service Layer Integration

**File**: `ab_cli/services/agent_service.py`

Add helper method if needed:
- `prepare_edit_payload(agent_data: dict) -> dict`: Extract and prepare config for editing
- `validate_edit_payload(edited_data: dict) -> bool`: Validate edited JSON structure

## Files to Create/Modify

### New Files:
1. `ab_cli/utils/version.py` - Version manipulation utilities
2. `ab_cli/utils/editor.py` - Editor selection and management
3. `ab_cli/utils/tempfile_manager.py` - Temp file handling

### Modified Files:
1. `ab_cli/config/settings.py` - Add `editor` configuration parameter
2. `ab_cli/cli/agents.py` - Add `edit` subcommand
3. `ab_cli/services/agent_service.py` - Add helper methods if needed
4. `config.example.yaml` - Add editor configuration example
5. `ab_cli/config/__init__.py` - Export updated settings

### Test Files:
1. `tests/test_utils/test_version.py` - Test version utilities
2. `tests/test_utils/test_editor.py` - Test editor selection logic
3. `tests/test_cli/test_agents_edit.py` - Test edit command
4. `tests/test_config/test_settings.py` - Test editor config

## Usage Examples

### Basic usage:
```bash
# Edit an agent (uses default editor)
ab agents edit <agent-id>

# Edit with specific editor
ab agents edit <agent-id> --editor vim

# Edit and keep temp file for debugging
ab agents edit <agent-id> --keep-temp

# With profile
ab --profile staging agents edit cacb7f8e-475a-48e5-96db-6b97f7a9b0db
```

### Configuration:
```yaml
# In config.yaml
editor: code --wait  # VS Code with wait flag
```

### Interactive Flow:
```
$ ab agents edit abc-123

Fetching agent definition...
Current version: 1.1.5
Preparing editor with version: 1.1.6

Opening editor: /usr/bin/vim
[Editor opens, user makes changes, saves and exits]

Changes detected.
New version label: 1.2.0

Create new agent version with these changes? (y/N): y

Creating version 1.2.0...
✓ Version created successfully
Agent ID: abc-123
Version: 1.2.0
```

## Technical Notes

### Version Increment Logic:
- Parse current version (e.g., "1.1.5")
- Increment minor version: "1.2.0"
- User can edit to different value if needed
- Handle non-semantic versions gracefully

### Editor Selection Priority:
1. `--editor` command flag
2. `editor` in config.yaml
3. `$VISUAL` environment variable
4. `$EDITOR` environment variable
5. Platform default

### Temp File Structure:
The temp JSON file presented to the user contains only what's needed:
```json
{
  "versionLabel": "1.2.0",
  "config": {
    "name": "My Agent",
    "description": "Agent description",
    "model": "gpt-4",
    // ... rest of config
  }
}
```

This is simpler than the full agent definition returned by the API.

### API Integration:
After editing, the command uses the existing agent version creation endpoint with the edited `versionLabel` and `config`.

## Success Criteria

- [ ] Configuration parameter for editor added
- [ ] Version manipulation utilities implemented
- [ ] `ab agents edit` command implemented
- [ ] Editor opens with prepared JSON
- [ ] Version auto-increments correctly
- [ ] User confirmation prompt works
- [ ] New version created successfully via API
- [ ] Temp files cleaned up properly
- [ ] `--editor` and `--keep-temp` flags work
- [ ] Error handling covers common scenarios
- [ ] Cross-platform support (Windows, macOS, Linux)
- [ ] Unit tests for all utilities
- [ ] CLI command tests
- [ ] Documentation updated

## Future Enhancements (Not in this spec)

- `--no-confirm` flag to skip confirmation prompt
- `--version-label <label>` to specify version instead of auto-increment
- Diff display showing changes before confirmation
- Support for editing multiple agents in sequence
- Template-based editing for bulk operations
