# Spec 15: Task Invocation CLI Consistency

## Background

Currently, the CLI has inconsistent parameter naming between chat and task agent invocations:

- **Chat agents** use `--message` and `--message-file` for input
- **Task agents** use `--input` for file-based input only

This inconsistency makes the CLI harder to learn and use. Additionally, task agents don't support inline JSON input, requiring users to create temporary files even for simple invocations.

## Current Behavior

### Chat Invocation (Consistent)
```bash
# Inline message
ab invoke chat <agent-id> --message "Hello"

# Message from file
ab invoke chat <agent-id> --message-file message.txt
```

### Task Invocation (Inconsistent)
```bash
# Only file-based input is supported
ab invoke task <agent-id> --input task.json
```

**Limitations:**
- No support for inline JSON task data
- Different parameter naming convention from chat
- Requires creating a file even for simple one-line JSON

## Proposed Changes

### New Task Invocation Interface
```bash
# Inline task data (NEW)
ab invoke task <agent-id> --task '{"claim_id": "01", "policy_number": "01"}'

# Task data from file
ab invoke task <agent-id> --task-file task.json
```

### Changes Required

1. **Remove `--input` option** (breaking change, but acceptable at this stage)
2. **Add `--task` option** for inline JSON string input
3. **Add `--task-file` option** for file-based JSON input
4. **Implement mutual exclusivity** between `--task` and `--task-file`
5. **Add JSON validation** for `--task` parameter with helpful error messages
6. **Update all documentation** to reflect new parameters
7. **Update all tests** to use new parameters

## Implementation Details

### Parameter Validation

1. **Mutual Exclusivity**
   - User must specify either `--task` OR `--task-file`, but not both
   - Error if both are specified
   - Error if neither is specified

2. **JSON Validation for `--task`**
   - Parse the string as JSON
   - Provide clear error message if invalid JSON
   - Example: "Invalid JSON in --task parameter: Expecting property name enclosed in double quotes"

3. **File Handling for `--task-file`**
   - Check file exists before reading
   - Parse JSON content with error handling
   - Provide clear error message if file doesn't exist or contains invalid JSON

### Code Changes

**File: `ab_cli/cli/invoke.py`**

```python
# Remove this:
@click.option("--input", type=click.Path(exists=True), help="Path to input file")

# Add these:
@click.option("--task", "-t", help="Task data as JSON string")
@click.option("--task-file", type=click.Path(exists=True), help="Path to task data file")

# Add validation in function:
def invoke_task(..., task: str | None, task_file: Path | None):
    # Validate mutual exclusivity
    if task and task_file:
        raise click.UsageError("Cannot specify both --task and --task-file")
    
    if not task and not task_file:
        raise click.UsageError("Must specify either --task or --task-file")
    
    # Parse task data
    if task:
        try:
            task_data = json.loads(task)
        except json.JSONDecodeError as e:
            raise click.UsageError(f"Invalid JSON in --task parameter: {e}")
    else:
        with open(task_file, 'r') as f:
            try:
                task_data = json.load(f)
            except json.JSONDecodeError as e:
                raise click.UsageError(f"Invalid JSON in file {task_file}: {e}")
```

### Documentation Updates

**File: `USAGE.md`**

Update task invocation section:

```markdown
### Task Agent Invocation

Invoke a task agent with task data:

```bash
# Inline task data
ab invoke task <agent-id> --task '{"claim_id": "01", "policy_number": "POL001"}'

# Task data from file
ab invoke task <agent-id> --task-file task.json
```

With output formatting:

```bash
ab invoke task <agent-id> --task '{"claim_id": "01"}' --format json
ab invoke task <agent-id> --task-file task.json --format yaml
```
```

### Test Updates

**File: `tests/test_cli/test_invoke.py`**

Update existing tests and add new ones:

1. **Update existing tests** to use `--task-file` instead of `--input`
2. **Add test for inline task data:**
   ```python
   def test_invoke_task_with_inline_data(self, runner, mock_client):
       """Test task invocation with inline JSON."""
       task_data = '{"claim_id": "01", "policy_number": "POL001"}'
       result = runner.invoke(invoke, ["task", "agent-id", "--task", task_data])
       assert result.exit_code == 0
   ```

3. **Add test for mutual exclusivity:**
   ```python
   def test_invoke_task_both_options_error(self, runner):
       """Test error when both --task and --task-file are specified."""
       result = runner.invoke(invoke, [
           "task", "agent-id", 
           "--task", '{"id": "01"}',
           "--task-file", "task.json"
       ])
       assert result.exit_code != 0
       assert "Cannot specify both" in result.output
   ```

4. **Add test for missing options:**
   ```python
   def test_invoke_task_no_options_error(self, runner):
       """Test error when neither option is specified."""
       result = runner.invoke(invoke, ["task", "agent-id"])
       assert result.exit_code != 0
       assert "Must specify either" in result.output
   ```

5. **Add test for invalid JSON:**
   ```python
   def test_invoke_task_invalid_json(self, runner):
       """Test error with invalid JSON in --task."""
       result = runner.invoke(invoke, ["task", "agent-id", "--task", "{invalid}"])
       assert result.exit_code != 0
       assert "Invalid JSON" in result.output
   ```

## Examples

### Before (Current)
```bash
# Create a file (only option)
echo '{"claim_id": "01"}' > task.json
ab invoke task 10238ef8-1882-430c-8cbb-349852379c46 --input task.json --format json
rm task.json  # cleanup
```

### After (Proposed)
```bash
# Inline data (simple and direct)
ab invoke task 10238ef8-1882-430c-8cbb-349852379c46 \
  --task '{"claim_id": "01", "policy_number": "POL001", "claim_description": "Damage"}' \
  --format json

# Or use a file for complex data
ab invoke task 10238ef8-1882-430c-8cbb-349852379c46 --task-file task.json --format json
```

## Benefits

1. **Consistency**: Task invocation now matches chat invocation pattern
2. **Convenience**: No need to create files for simple JSON inputs
3. **Better UX**: Clear, descriptive parameter names (`--task` vs `--input`)
4. **Flexibility**: Support both inline and file-based workflows

## Breaking Changes

- **`--input` parameter is removed** and replaced with `--task-file`
- Users with existing scripts will need to update them
- Since this is early in the project lifecycle, the impact is minimal

## Success Criteria

- [ ] `--input` parameter removed from task invocation
- [ ] `--task` parameter accepts inline JSON strings
- [ ] `--task-file` parameter accepts file paths
- [ ] Mutual exclusivity enforced with clear error messages
- [ ] JSON validation provides helpful error messages
- [ ] All tests updated and passing
- [ ] Documentation updated with new examples
- [ ] CLI help text updated