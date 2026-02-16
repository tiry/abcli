# Spec 19: Improved List Pagination and Display

**Status:** ✅ COMPLETED

## Problem Statement

The `ab agents list` command had poor pagination support:
- No clear indication of page size, current position, or total count
- Navigation between pages required manual offset calculation
- Client-side filtering (--type, --name) broke pagination expectations
- No easy way to navigate forward through results

## Implementation Summary

### New Features
1. **--page option**: Jump directly to a specific page (conflicts with --offset and filters)
2. **--more option**: Interactive pagination mode (press SPACE for next page, 'q' to quit)
3. **Enhanced filtering**: Fetches multiple server pages to collect enough filtered results
4. **Improved display**: Shows clear pagination info and next page commands
5. **Configuration**: New `max_filter_pages` setting (default 10, range 1-100)

### Architecture

Proper separation of concerns to avoid circular dependencies:

```
┌─────────────┐
│   CLI       │  Simple: handles options, calls API module, displays results
│  agents.py  │
└──────┬──────┘
       │
       ↓
┌─────────────────┐
│  API Pagination │  Complex: API calls, filtering, multi-page logic
│  pagination.py  │
└──────┬──────────┘
       │
       ↓
┌─────────────┐
│ API Client  │  Low-level: HTTP calls
│  client.py  │
└─────────────┘
```

### Files Created/Modified

1. **`ab_cli/api/pagination.py`** (NEW)
   - `PaginatedResult` dataclass - holds paginated results and metadata
   - `fetch_agents_paginated()` - handles API calls, filtering, multi-page fetching
   - `_matches_filters()` - applies client-side filters

2. **`ab_cli/cli/pagination_utils.py`** (NEW)
   - `get_single_keypress()` - For interactive mode (uses termios/tty)
   - `show_pagination_info()` - Display pagination below tables
   - `show_next_page_command()` - Show command for next page

3. **`ab_cli/config/settings.py`** (MODIFIED)
   - Added `PaginationSettings` class with `max_filter_pages` field

4. **`config.example.yaml`** (MODIFIED)
   - Added pagination configuration section

5. **`ab_cli/cli/agents.py`** (MODIFIED)
   - Refactored `list_agents()` to use new pagination architecture
   - Added `--page` and `--more` options
   - Added validation for conflicting options

6. **`tests/test_cli/test_agents.py`** (MODIFIED)
   - Updated test expectations to match new output format

7. **`USAGE.md`** (MODIFIED)
   - Added comprehensive pagination documentation with examples

## Command Line Options

```bash
ab agents list
  --limit, -l INTEGER       # Page size (default: 50)
  --offset, -o INTEGER      # Start from row N (default: 0)
  --page, -p INTEGER        # Jump to page N (conflicts with --offset, filters)
  --more                    # Interactive pagination mode
  --type, -t TEXT           # Filter by type (disables --page)
  --name, -n TEXT           # Filter by name (disables --page)
```

### Option Conflicts
- `--page` and `--offset` are **mutually exclusive**
- `--page` cannot be used with filters (--type or --name)
- Page numbers must be >= 1

## Display Examples

### Without Filters (Server-Side Pagination)
```
                            35 agents of 150 total
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┓
┃ ID                              ┃ Name         ┃ Type ┃ Status  ┃ Created   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━┩
│ 8f6c2178-4f0a-43fb-88d7-f3d8... │ Calculator   │ tool │ CREATED │ 2026-02-… │
│ d9ce3525-0899-48b1-869f-ff9a... │ Document RAG │ rag  │ CREATED │ 2026-02-… │
└───────────────────────────────┴──────────────┴──────┴─────────┴───────────┘

Page: 1/3 | Showing: 1-50 of 150 | Page size: 50

Next page: ab agents list --offset 50 -l 50
```

### With Filters (Client-Side Pagination)
```
                            15 agents
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┓
┃ ID                              ┃ Name         ┃ Type ┃ Status  ┃ Created   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━┩
│ 8f6c2178-4f0a-43fb-88d7-f3d8... │ Calculator   │ tool │ CREATED │ 2026-02-… │
│ 3a5f891c-29b7-4e12-a094-c7f2... │ Math Helper  │ tool │ CREATED │ 2026-02-… │
└───────────────────────────────┴──────────────┴──────┴─────────┴───────────┘

Showing: 1-15 of ??? (filtered by type: tool) | Page size: 50
(End of results)
```

### Interactive Mode
```bash
$ ab agents list --more -l 10

                            10 agents of 150 total
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┓
┃ ID                              ┃ Name         ┃ Type ┃ Status  ┃ Created   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┻━━━━━━┻━━━━━━━━━┻━━━━━━━━━━━┛

Page: 1/15 | Showing: 1-10 of 150 | Page size: 10

Press SPACE for next page, 'q' to quit: 
```

## Configuration

Added to `config.yaml`:
```yaml
pagination:
  max_filter_pages: 10  # Max server pages to fetch when filtering (1-100)
```

## Testing Results

✅ All 22 unit tests pass  
✅ Linting passes (ruff format + lint + mypy)  
✅ Proper separation of concerns maintained  
✅ No circular dependencies  

### Test Coverage
- Basic page navigation (`--page`)
- Interactive mode (`--more`)
- Client-side filtering with pagination
- Option conflict detection
- End of results detection
- Configuration settings

## Usage Examples

```bash
# Jump to page 2
ab agents list --page 2 -l 25

# Interactive pagination
ab agents list --more -l 20

# Filter with pagination
ab agents list --type rag -l 20

# Combine filters
ab agents list --type tool --name calc

# Error: conflicting options
ab agents list --page 2 --offset 100  # ❌ Error
ab agents list --page 2 --type rag    # ❌ Error
```

## Success Criteria

✅ Pagination info displayed below table  
✅ --page option works for quick navigation  
✅ --more provides interactive pagination  
✅ --page and --offset are mutually exclusive  
✅ Filters disable --page, use --offset only  
✅ Client-side filtering fetches multiple pages as needed  
✅ max_filter_pages configurable and respected  
✅ Clear "Next page:" commands shown  
✅ End of results detected correctly  
✅ All existing tests continue to pass  
✅ New tests cover pagination scenarios  
✅ Documentation updated (USAGE.md)

## Backward Compatibility

✅ Existing --limit and --offset options unchanged  
✅ No breaking changes to CLI interface  
✅ Default behavior unchanged  
✅ New options are additive only
