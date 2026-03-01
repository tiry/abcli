# Spec 31: Batch Collection Command

## Overview

Add a `collect` subcommand to `ab invoke` for running batch invocations and collecting results. This enables testing, benchmarking, and data collection workflows.

## Command Syntax

```bash
ab invoke collect [OPTIONS] AGENT_ID [VERSION_ID]
```

### Required Arguments
- `AGENT_ID`: The target agent to invoke
- `VERSION_ID`: (Optional) Specific agent version, defaults to latest

### Input Options (Mutually Exclusive)

Must provide exactly ONE of:
- `--tasks <file.jsonl>`: JSONL file with task invocations
- `--chats <file.csv>`: CSV file with chat messages

### Output Options

- `--out <file.jsonl>`: Output file path
  - **Default**: `./collections/{agent_id}_{timestamp}.jsonl`
  - Automatically creates `collections/` directory if needed
  - Timestamp format: `YYYYMMDD_HHMMSS`

### Standard Options

All standard invoke options apply:
- `--config`: Config file path
- `--profile`: Profile name
- `--verbose`: Verbose output
- etc.

## Input File Formats

### Task Input (JSONL)

Each line is a complete JSON object matching the agent's `inputSchema`:

```jsonl
{"field1": "value1", "field2": "value2"}
{"field1": "value3", "field2": "value4"}
```

- One task per line
- Must conform to agent's inputSchema
- No blank lines

### Chat Input (CSV)

Simple CSV format with auto-detection:

**Single Column (message only):**
```csv
What is the weather?
Tell me a joke
Explain quantum physics
```

**Two Columns (message_id, message):**
```csv
msg_001,What is the weather?
msg_002,Tell me a joke
msg_003,Explain quantum physics
```

**With Header Detection:**
```csv
message_id,message
msg_001,What is the weather?
msg_002,Tell me a joke
```

**Rules:**
- Comma delimiter
- Header auto-detection: if first row contains "message", treat as header
- If 1 column: all values are messages, message_id = row index (0, 1, 2...)
- If 2 columns: first = message_id, second = message
- No extra metadata columns needed

## Output Format (JSONL)

Each invocation writes one JSON line immediately after completion:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "invocation_index": 0,
  "message_id": "msg_001",
  "agent": {
    "agent_id": "agent-123",
    "version_id": "v1.2.0"
  },
  "input": {
    "message": "What is the weather?"
  },
  "output": {
    "response": "The current weather is sunny, 72°F."
  },
  "metrics": {
    "success": true,
    "status_code": 200,
    "execution_time_ms": 1234,
    "retry_count": 0,
    "error_message": null
  }
}
```

### Output Schema

- **timestamp**: ISO 8601 timestamp when invocation completed
- **invocation_index**: Zero-based index in the batch (0, 1, 2...)
- **message_id**: From input (CSV) or index (tasks), or generated
- **agent**: Agent and version information
- **input**: The complete input sent to the agent (as JSON object)
- **output**: The complete response from the agent (as JSON object)
  - For failed invocations, this may be null
- **metrics**:
  - `success`: Boolean - true if invocation succeeded
  - `status_code`: HTTP status code from API
  - `execution_time_ms`: Response time in milliseconds
  - `retry_count`: Number of retries attempted (0, 1, or 2)
  - `error_message`: Error details if failed, null otherwise

## Processing Logic

### Workflow

1. **Validate inputs**
   - Check exactly one of --tasks or --chats provided
   - Verify input file exists and is readable
   - Validate agent exists (optional: fast-fail vs discover during processing)

2. **Setup output**
   - Create collections/ directory if needed
   - Determine output filename (provided or auto-generated)
   - Open output file for append

3. **Process each input sequentially**
   ```
   For each input (row/line):
     - Parse input
     - Display progress: "Processing 15/100..."
     - Invoke agent
     - On failure: Retry once after brief delay (1-2 seconds)
     - On second failure: Abort entire batch with error
     - Record result to output file (append JSONL line)
     - Flush to disk
   ```

4. **Completion summary**
   ```
   Collection complete!
   - Total: 100
   - Successful: 98
   - Failed (after retry): 2
   - Output: ./collections/agent-123_20240115_103045.jsonl
   ```

### Error Handling

**Retry Strategy:**
- On first failure: Wait 1-2 seconds, retry once
- On second failure: Abort entire batch
- Exit with error code 1
- Record both attempts in metrics (retry_count = 1)

**Error Messages:**
- Write to stderr: "ERROR: Invocation failed after retry (index 42): <error details>"
- Exit immediately, do not process remaining inputs
- Partial results already written to output file are preserved

### Progress Reporting

Display to stderr (doesn't interfere with potential stdout):
```
Processing invocation 1/100...
Processing invocation 2/100...
Processing invocation 15/100... (retry)
ERROR: Invocation failed after retry (index 15): Connection timeout
```

Progress format:
- `Processing invocation {current}/{total}...`
- Add `(retry)` suffix when retrying
- Update on same line if terminal supports it (optional enhancement)

## Implementation Notes

### File I/O

- **Input**: Read line-by-line or row-by-row (streaming, don't load entire file)
- **Output**: Append each result immediately, flush after each write
  - Ensures partial results saved even if process interrupted
  - Allows monitoring progress via `tail -f`

### JSON Encoding

- Properly escape newlines in JSON strings
- Use `json.dumps()` to ensure valid JSONL
- Each line must be complete, valid JSON

### CSV Parsing

- Use Python's `csv` module for robust parsing
- Handle quoted fields with commas
- Strip whitespace from fields
- Auto-detect header by checking if first row contains "message"

### Agent Invocation

- Reuse existing `ab_cli.services.invocation_service` or similar
- Pass same auth/config as normal invoke command
- Capture timing with `time.time()` or `time.perf_counter()`
- Extract status code from API response

## Testing Strategy

### Unit Tests

1. **Input parsing**:
   - Parse JSONL tasks correctly
   - Parse CSV with/without headers
   - Detect column count correctly
   - Handle edge cases (empty lines, quotes, commas in fields)

2. **Output generation**:
   - Generate correct JSONL format
   - Escape special characters properly
   - Include all required fields

3. **Error handling**:
   - Retry logic works correctly
   - Abort on second failure
   - Preserve partial results

### Integration Tests

1. **End-to-end with mock agent**:
   - Process small batch (5-10 items)
   - Verify output file created
   - Check all records present
   - Validate JSONL format

2. **Error scenarios**:
   - Simulate API failures
   - Verify retry behavior
   - Check error messages
   - Confirm abort on double-failure

### Test Data Files

Create in `tests/data/collect/`:
- `tasks_sample.jsonl` - Sample task inputs
- `chats_with_header.csv` - CSV with header row
- `chats_no_header.csv` - CSV without header
- `chats_single_column.csv` - Just messages
- `expected_output.jsonl` - Expected output format

## Usage Examples

### Example 1: Task Batch

```bash
# Run batch of tasks
ab invoke collect --tasks ./data/test_inputs.jsonl agent-123

# Output: ./collections/agent-123_20240115_153045.jsonl
```

### Example 2: Chat Messages

```bash
# Process chat messages from CSV
ab invoke collect --chats ./messages.csv agent-456 v2.1.0

# Output: ./collections/agent-456_20240115_153122.jsonl
```

### Example 3: Custom Output

```bash
# Specify output location
ab invoke collect \
  --tasks ./inputs.jsonl \
  --out ./results/experiment_1.jsonl \
  agent-789
```

### Example 4: With Profile

```bash
# Use staging environment
ab invoke collect \
  --profile staging \
  --chats ./qa_questions.csv \
  agent-qa-bot
```

## Future Enhancements (Not in Scope)

These are ideas for future iterations:

1. **Parallel execution**: `--concurrency N` to run N invocations in parallel
2. **Resume capability**: `--resume <file>` to continue interrupted batch
3. **Rate limiting**: `--rate-limit N` requests per second
4. **Flexible retry**: `--max-retries N` and `--retry-delay-ms N`
5. **Summary statistics**: `--summary` flag to show aggregate metrics
6. **Progress bar**: Visual progress indicator instead of text
7. **Filtering**: `--skip-errors` to continue on failure instead of aborting
8. **Batch metadata**: Add batch-level info (start time, user, git commit, etc.)

## Related Specs

- Spec 04: Agent Invocation Improvements (base invoke functionality)
- Spec 09: Invoke Command Enhancements (invoke options and patterns)
- Spec 29: Profiles (configuration profiles)

## Success Criteria

- ✅ Command accepts JSONL task files
- ✅ Command accepts CSV chat files (with auto-header detection)
- ✅ Generates properly formatted JSONL output
- ✅ Displays progress during processing
- ✅ Retries failed invocations once
- ✅ Aborts on double-failure
- ✅ Auto-generates output filename with agent_id and timestamp
- ✅ Creates collections/ directory automatically
- ✅ All standard invoke options work (config, profile, etc.)
- ✅ Comprehensive unit and integration tests
- ✅ Documentation in USAGE.md
