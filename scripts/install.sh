#!/bin/bash
# Agent Builder CLI - Source Installation Script (POSIX)
# This script automates the installation from source

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VENV_DIR="venv"
MIN_PYTHON_VERSION="3.10"
UPDATE_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --update)
            UPDATE_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--update]"
            echo ""
            echo "Options:"
            echo "  --update    Update existing installation (git pull + reinstall)"
            echo "  --help      Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Print colored message
print_msg() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check Python version
check_python_version() {
    print_msg "$BLUE" "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        print_msg "$RED" "❌ Error: python3 is not installed"
        print_msg "$YELLOW" "Please install Python 3.10 or higher"
        exit 1
    fi
    
    local python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_msg "$GREEN" "Found Python $python_version"
    
    # Compare version (simple string comparison works for major.minor)
    if [[ "$(printf '%s\n' "$MIN_PYTHON_VERSION" "$python_version" | sort -V | head -n1)" != "$MIN_PYTHON_VERSION" ]]; then
        print_msg "$YELLOW" "⚠️  Warning: Python $python_version is older than recommended $MIN_PYTHON_VERSION"
        print_msg "$YELLOW" "Installation will proceed but may encounter issues"
    fi
}

# Handle update mode
handle_update() {
    if [ "$UPDATE_MODE" = true ]; then
        print_msg "$BLUE" "🔄 Update mode activated"
        
        # Check if git is available
        if ! command -v git &> /dev/null; then
            print_msg "$YELLOW" "⚠️  Warning: git is not installed, skipping git pull"
        else
            print_msg "$BLUE" "Pulling latest changes from git..."
            if git pull; then
                print_msg "$GREEN" "✓ Git pull successful"
            else
                print_msg "$YELLOW" "⚠️  Warning: git pull failed, continuing with current code"
            fi
        fi
    fi
}

# Setup virtual environment
setup_venv() {
    if [ -d "$VENV_DIR" ]; then
        if [ "$UPDATE_MODE" = true ]; then
            print_msg "$BLUE" "Using existing virtual environment"
        else
            print_msg "$YELLOW" "Virtual environment already exists at $VENV_DIR"
            read -p "Do you want to overwrite it? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_msg "$RED" "❌ Installation aborted"
                exit 1
            fi
            print_msg "$BLUE" "Removing existing virtual environment..."
            rm -rf "$VENV_DIR"
        fi
    fi
    
    if [ ! -d "$VENV_DIR" ]; then
        print_msg "$BLUE" "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        print_msg "$GREEN" "✓ Virtual environment created"
    fi
}

# Install package
install_package() {
    print_msg "$BLUE" "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    print_msg "$BLUE" "Upgrading pip..."
    pip install --quiet --upgrade pip
    
    print_msg "$BLUE" "Installing ab-cli with development dependencies..."
    if pip install -e ".[dev]"; then
        print_msg "$GREEN" "✓ Installation successful"
    else
        print_msg "$RED" "❌ Installation failed"
        print_msg "$RED" "Please check the error messages above"
        exit 1
    fi
}

# Post-installation guidance
show_post_install() {
    echo ""
    print_msg "$GREEN" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_msg "$GREEN" "✅ Installation Complete!"
    print_msg "$GREEN" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    print_msg "$BLUE" "📋 Next Steps:"
    echo ""
    echo "  1. Activate the virtual environment:"
    print_msg "$YELLOW" "     source $VENV_DIR/bin/activate"
    echo ""
    echo "  2. (Optional) Verify the installation:"
    print_msg "$YELLOW" "     ab --version"
    echo ""
    echo "  3. Configure your API credentials:"
    print_msg "$YELLOW" "     ab configure init"
    echo ""
    echo "  4. Validate your configuration:"
    print_msg "$YELLOW" "     ab validate"
    echo ""
    
    print_msg "$BLUE" "💡 Tip: You need to activate the virtual environment"
    print_msg "$BLUE" "   (step 1) each time you open a new terminal session."
    echo ""
}

# Main execution
main() {
    print_msg "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_msg "$BLUE" "🚀 Agent Builder CLI - Source Installation"
    print_msg "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    check_python_version
    handle_update
    setup_venv
    install_package
    show_post_install
}

# Run main function
main
