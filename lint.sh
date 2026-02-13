#!/bin/bash
# Script to run code quality tools on the ab-cli codebase
# Usage: ./lint.sh [directory]
# Example: ./lint.sh ab_cli/abui

set -e  # Exit on error

# Default directory to check
TARGET_DIR=${1:-ab_cli}
YELLOW='\033[1;33m'
GREEN='\033[1;32m'
RED='\033[1;31m'
NC='\033[0m' # No Color

# Check mode
CHECK_ONLY=${2:-false}

echo -e "${YELLOW}Running code quality checks on: ${TARGET_DIR}${NC}\n"

# Step 1: Format the code with ruff format
echo -e "${YELLOW}Step 1/3: Running ruff format...${NC}"
if [ "$CHECK_ONLY" = "true" ]; then
    # Check only mode - don't modify files (CI mode)
    if ruff format --check "$TARGET_DIR"; then
        echo -e "${GREEN}✓ Formatting check passed${NC}\n"
    else
        echo -e "${RED}✗ Formatting check failed${NC}\n"
        exit 1
    fi
else
    # Format mode - modify files (dev mode)
    if ruff format "$TARGET_DIR"; then
        echo -e "${GREEN}✓ Formatting successful${NC}\n"
    else
        echo -e "${RED}✗ Formatting failed${NC}\n"
        exit 1
    fi
fi

# Step 2: Run linting checks with ruff
echo -e "${YELLOW}Step 2/3: Running linting checks with ruff...${NC}"
if ruff check "$TARGET_DIR"; then
    echo -e "${GREEN}✓ Linting checks passed${NC}\n"
else
    echo -e "${RED}✗ Linting checks failed${NC}"
    
    # Only try to fix if we're not in check-only mode
    if [ "$CHECK_ONLY" = "false" ]; then
        echo -e "${YELLOW}Attempting to fix auto-fixable issues...${NC}"
        
        if ruff check --fix "$TARGET_DIR"; then
            echo -e "${GREEN}✓ Auto-fixes applied successfully${NC}\n"
        else
            echo -e "${RED}✗ Some issues could not be auto-fixed${NC}\n"
            exit 2
        fi
    else
        echo -e "${RED}✗ Linting checks failed in check-only mode${NC}\n"
        exit 2
    fi
fi

# Step 3: Run type checking with mypy
echo -e "${YELLOW}Step 3/3: Running type checking with mypy...${NC}"

# We want to match the CI workflow exactly
if [ "$CHECK_ONLY" = "true" ]; then
    # This is CI mode
    if [ "$TARGET_DIR" = "ab_cli" ]; then
        # When checking the entire project in CI mode, match the CI behavior exactly
        # CI workflow ignores errors in mypy
        echo -e "${YELLOW}Running type check in CI-compatible mode...${NC}"
        
        # Run mypy but don't let the exit code affect the script
        set +e  # Temporarily disable exit on error
        mypy "$TARGET_DIR" --ignore-missing-imports
        set -e  # Re-enable exit on error
        
        # In CI mode for the full codebase, we always succeed this step
        echo -e "${GREEN}✓ Type checking step completed in CI mode${NC}\n"
    else
        # When checking specific files/directories in CI mode, be strict
        if mypy "$TARGET_DIR" --ignore-missing-imports; then
            echo -e "${GREEN}✓ Type checking passed${NC}\n"
        else
            echo -e "${RED}✗ Type checking failed${NC}\n"
            exit 3
        fi
    fi
else
    # In development mode, be strict regardless of which files we're checking
    if mypy "$TARGET_DIR" --ignore-missing-imports; then
        echo -e "${GREEN}✓ Type checking passed${NC}\n"
    else
        echo -e "${RED}✗ Type checking failed${NC}\n"
        exit 3
    fi
fi

echo -e "${GREEN}All checks completed successfully!${NC}"
echo "✓ Code formatting"
echo "✓ Linting checks"
if [ "$CHECK_ONLY" = "true" ] && [ "$TARGET_DIR" = "ab_cli" ]; then
    echo "✓ Type checking (CI mode - warnings shown but not enforced)"
else
    echo "✓ Type checking"
fi

# Display CI-compatible usage
echo -e "\n${YELLOW}CI-Compatible Usage:${NC}"
echo "./lint.sh ab_cli/ true   # Check-only mode for CI"