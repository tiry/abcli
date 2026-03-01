# Spec 33: Documentation Reorganization and Enhancement

## Overview

Reorganize the documentation structure by moving documentation files into a dedicated `doc/` folder and enhance the root README with a "Why Use ab-cli?" section to better communicate value to users.

## Goals

1. **Improve Documentation Organization**: Move documentation files to `doc/` folder for better structure
2. **Enhance Discoverability**: Create a documentation index (doc/README.md) with descriptions
3. **Communicate Value**: Add a "Why Use ab-cli?" section with concrete use cases and CLI examples
4. **Maintain Compatibility**: Update all links to reflect new structure

## Implementation Plan

### Phase 1: Move Documentation Files to doc/

Move the following 5 documentation files from root to `doc/`:

- `CONFIG.md` → `doc/CONFIG.md`
- `INSTALL.md` → `doc/INSTALL.md`  
- `TESTING.md` → `doc/TESTING.md`
- `UI.md` → `doc/UI.md`
- `USAGE.md` → `doc/USAGE.md`

**Files to keep at root:**
- `README.md` (will be updated)
- `config.example.yaml` (no changes - referenced in Quick Start)

### Phase 2: Create doc/README.md

Create a comprehensive documentation index at `doc/README.md` with:

**Structure:**
```markdown
# Agent Builder CLI Documentation

Welcome to the Agent Builder CLI documentation hub. This directory contains comprehensive guides for using and developing the CLI.

## Getting Started

- **[INSTALL.md](INSTALL.md)** - Installation instructions and system requirements
- **[USAGE.md](USAGE.md)** - Comprehensive command documentation with examples

## Configuration

- **[CONFIG.md](CONFIG.md)** - Configuration parameters, profiles, and environment setup

## User Interfaces

- **[UI.md](UI.md)** - Web-based user interface for visual agent management

## Development

- **[TESTING.md](TESTING.md)** - Testing practices, running tests, and CI/CD information

## Quick Links

- [Main README](../README.md) - Project overview and quick start
- [Example Configuration](../config.example.yaml) - Template configuration file
```

### Phase 3: Update Root README.md

#### 3.1 Add "Why Use ab-cli?" Section

Insert this new section **after the Overview section** and **before Quick Start**:

```markdown
## Why Use ab-cli?

The Agent Builder CLI is designed to streamline AI agent development and operations. Here are the key use cases:

### Introspect Agents

Quickly discover what agents are deployed and examine their configurations:

```bash
# List all deployed agents
ab agents list

# Get detailed information about a specific agent
ab agents get <agent-id>

# View agent versions
ab versions list <agent-id>
```

### Tweak and Test Agents

Rapidly iterate on agent configurations and validate changes:

```bash
# Update agent metadata
ab agents patch <agent-id> --name "New Name" --description "Updated description"

# Test agent behavior with chat
ab invoke chat <agent-id> --message "Test this change"

# Test with streaming
ab invoke chat <agent-id> --message "Analyze this" --stream

# Create new agent version
ab versions create <agent-id> --config updated-config.json
```

### Validate Access and Environment Configuration

Ensure your authentication and API access are correctly configured:

```bash
# Validate configuration and test API connectivity
ab validate --show-config

# Get authentication token and ready-to-use API commands
ab auth
ab auth --curl
ab auth --wget --post
```

### Multi-Environment Management

Use profiles to seamlessly work across development, staging, and production environments:

```bash
# Work with development environment
ab --profile dev agents list

# Switch to production
ab --profile prod agents list

# Compare configurations across environments
ab --profile dev agents get <agent-id>
ab --profile prod agents get <agent-id>
```

### Record and Analyze Datasets

Collect request/response pairs for testing, debugging, and model evaluation:

```bash
# Collect chat responses from CSV file
ab invoke collect <agent-id> --chats messages.csv

# Collect with custom output location
ab invoke collect <agent-id> --chats messages.csv --out results.jsonl

# Collect task agent responses
ab invoke collect <agent-id> --tasks tasks.jsonl
```

#### 3.2 Update All Documentation Links

Update all references to documentation files to point to `doc/` directory:

**In "Quick Start" section:**
- `[INSTALL.md](INSTALL.md)` → `[INSTALL.md](doc/INSTALL.md)`

**In "Configuration" section:**
- `[CONFIG.md](CONFIG.md)` → `[CONFIG.md](doc/CONFIG.md)`

**In "Basic Usage" section:**
- `[USAGE.md](USAGE.md)` → `[USAGE.md](doc/USAGE.md)`

**In "Documentation" section:**
- `[USAGE.md](USAGE.md)` → `[USAGE.md](doc/USAGE.md)`
- `[CONFIG.md](CONFIG.md)` → `[CONFIG.md](doc/CONFIG.md)`
- `[INSTALL.md](INSTALL.md)` → `[INSTALL.md](doc/INSTALL.md)`
- `[TESTING.md](TESTING.md)` → `[TESTING.md](doc/TESTING.md)`
- Add: `[UI.md](doc/UI.md)` if not already present

**In "Testing and CI" section:**
- `[TESTING.md](TESTING.md)` → `[TESTING.md](doc/TESTING.md)`

#### 3.3 Update Project Structure Section

Update the project structure tree to reflect the new documentation organization:

```markdown
## Project Structure

```
ab-cli/
├── ab_cli/                 # Core package directory
│   ├── __init__.py
│   ├── api/                # API client components
│   ├── cli/                # CLI commands and interfaces
│   ├── config/             # Configuration handling
│   ├── models/             # Data models
│   └── utils/              # Utility functions
├── doc/                    # Documentation files
│   ├── README.md           # Documentation index
│   ├── CONFIG.md           # Configuration guide
│   ├── INSTALL.md          # Installation instructions
│   ├── TESTING.md          # Testing guide
│   ├── UI.md               # UI documentation
│   ├── USAGE.md            # Command reference
│   └── pics/               # Documentation images
├── tests/                  # Test suite
├── specs/                  # Specification documents
├── config.example.yaml     # Example configuration
├── pyproject.toml          # Project dependencies
└── README.md               # Project overview
```
```

## Verification Checklist

After implementation, verify:

- [ ] All 5 documentation files moved to `doc/` directory
- [ ] `doc/README.md` created with comprehensive index
- [ ] "Why Use ab-cli?" section added to root README after Overview
- [ ] All documentation links in root README updated to `doc/` paths
- [ ] Project structure section updated
- [ ] Image link `doc/pics/CLI-List.png` still works
- [ ] All markdown files render correctly on GitHub
- [ ] No broken links in any documentation

## Success Criteria

1. **Clear Value Communication**: Users immediately understand why they should use ab-cli
2. **Better Organization**: Documentation is logically organized in dedicated folder
3. **Easy Navigation**: doc/README.md serves as effective documentation hub
4. **No Broken Links**: All internal links work correctly
5. **GitHub Compatibility**: All markdown renders correctly on GitHub

## Notes

- `config.example.yaml` stays at root (referenced in Quick Start section)
- The `doc/pics/` folder already exists and contains images
- Use concrete CLI examples (not placeholders) in "Why" section
- Keep descriptions in doc/README.md brief (1-2 sentences each)
