# Agent Builder CLI - Source Installation Script (Windows)
# This script automates the installation from source

param(
    [switch]$Update,
    [switch]$Help
)

# Configuration
$VenvDir = "venv"
$MinPythonVersion = [version]"3.10"
$ErrorActionPreference = "Stop"

# Show help
if ($Help) {
    Write-Host "Usage: .\install.ps1 [-Update] [-Help]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Update    Update existing installation (git pull + reinstall)"
    Write-Host "  -Help      Show this help message"
    exit 0
}

# Print colored message
function Write-ColorMessage {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Check Python version
function Test-PythonVersion {
    Write-ColorMessage "Checking Python version..." "Cyan"
    
    try {
        $pythonCmd = Get-Command python -ErrorAction Stop
        $pythonVersion = & python --version 2>&1
        
        if ($pythonVersion -match "Python (\d+\.\d+)") {
            $version = [version]$matches[1]
            Write-ColorMessage "Found Python $version" "Green"
            
            if ($version -lt $MinPythonVersion) {
                Write-ColorMessage "⚠️  Warning: Python $version is older than recommended $MinPythonVersion" "Yellow"
                Write-ColorMessage "Installation will proceed but may encounter issues" "Yellow"
            }
        }
    }
    catch {
        Write-ColorMessage "❌ Error: python is not installed or not in PATH" "Red"
        Write-ColorMessage "Please install Python 3.10 or higher" "Yellow"
        exit 1
    }
}

# Handle update mode
function Invoke-UpdateMode {
    if ($Update) {
        Write-ColorMessage "🔄 Update mode activated" "Cyan"
        
        # Check if git is available
        try {
            $gitCmd = Get-Command git -ErrorAction Stop
            Write-ColorMessage "Pulling latest changes from git..." "Cyan"
            
            try {
                git pull
                Write-ColorMessage "✓ Git pull successful" "Green"
            }
            catch {
                Write-ColorMessage "⚠️  Warning: git pull failed, continuing with current code" "Yellow"
            }
        }
        catch {
            Write-ColorMessage "⚠️  Warning: git is not installed, skipping git pull" "Yellow"
        }
    }
}

# Setup virtual environment
function Initialize-VirtualEnvironment {
    if (Test-Path $VenvDir) {
        if ($Update) {
            Write-ColorMessage "Using existing virtual environment" "Cyan"
        }
        else {
            Write-ColorMessage "Virtual environment already exists at $VenvDir" "Yellow"
            $response = Read-Host "Do you want to overwrite it? (y/N)"
            
            if ($response -notmatch '^[Yy]$') {
                Write-ColorMessage "❌ Installation aborted" "Red"
                exit 1
            }
            
            Write-ColorMessage "Removing existing virtual environment..." "Cyan"
            Remove-Item -Recurse -Force $VenvDir
        }
    }
    
    if (-not (Test-Path $VenvDir)) {
        Write-ColorMessage "Creating virtual environment..." "Cyan"
        python -m venv $VenvDir
        Write-ColorMessage "✓ Virtual environment created" "Green"
    }
}

# Install package
function Install-Package {
    Write-ColorMessage "Activating virtual environment..." "Cyan"
    
    # Activate venv
    $activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
    }
    else {
        Write-ColorMessage "❌ Error: Failed to find activation script" "Red"
        exit 1
    }
    
    Write-ColorMessage "Upgrading pip..." "Cyan"
    python -m pip install --quiet --upgrade pip
    
    Write-ColorMessage "Installing ab-cli with development dependencies..." "Cyan"
    
    try {
        python -m pip install -e ".[dev]"
        Write-ColorMessage "✓ Installation successful" "Green"
    }
    catch {
        Write-ColorMessage "❌ Installation failed" "Red"
        Write-ColorMessage "Please check the error messages above" "Red"
        exit 1
    }
}

# Post-installation guidance
function Show-PostInstall {
    Write-Host ""
    Write-ColorMessage "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Green"
    Write-ColorMessage "✅ Installation Complete!" "Green"
    Write-ColorMessage "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Green"
    Write-Host ""
    
    Write-ColorMessage "📋 Next Steps:" "Cyan"
    Write-Host ""
    Write-Host "  1. Activate the virtual environment:"
    Write-ColorMessage "     .\$VenvDir\Scripts\Activate.ps1" "Yellow"
    Write-Host ""
    Write-Host "  2. (Optional) Verify the installation:"
    Write-ColorMessage "     ab --version" "Yellow"
    Write-Host ""
    Write-Host "  3. Configure your API credentials:"
    Write-ColorMessage "     ab configure init" "Yellow"
    Write-Host ""
    Write-Host "  4. Validate your configuration:"
    Write-ColorMessage "     ab validate" "Yellow"
    Write-Host ""
    
    Write-ColorMessage "💡 Tip: You need to activate the virtual environment" "Cyan"
    Write-ColorMessage "   (step 1) each time you open a new PowerShell session." "Cyan"
    Write-Host ""
}

# Main execution
function Main {
    Write-ColorMessage "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
    Write-ColorMessage "🚀 Agent Builder CLI - Source Installation" "Cyan"
    Write-ColorMessage "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "Cyan"
    Write-Host ""
    
    Test-PythonVersion
    Invoke-UpdateMode
    Initialize-VirtualEnvironment
    Install-Package
    Show-PostInstall
}

# Run main function
try {
    Main
}
catch {
    Write-ColorMessage "❌ An error occurred: $_" "Red"
    exit 1
}
