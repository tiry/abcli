# 1. Configuration
$AppName = "ab_cli"
$InstallDir = "C:\Program Files\$AppName"
$SourceDist = ".\dist\$AppName"

# 2. Check for Admin Rights (Equivalent to sudo)
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Please run this script as Administrator (Right-click PowerShell > Run as Administrator)."
    exit
}

Write-Host "🚀 Starting installation of $AppName..." -ForegroundColor Cyan

# 3. Check if build exists
if (-not (Test-Path $SourceDist)) {
    Write-Error "❌ Error: Build directory $SourceDist not found. Run PyInstaller first."
    exit
}

# 4. Clean up previous installation
if (Test-Path $InstallDir) {
    Write-Host "Removing old installation at $InstallDir..."
    Remove-Item -Recurse -Force $InstallDir
}

# 5. Copy the folder to Program Files
Write-Host "Copying application to $InstallDir..."
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path "$SourceDist\*" -Destination $InstallDir -Recurse -Force

# 6. Add to PATH (Machine level)
# This allows 'ab_cli' to be run from any terminal
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($CurrentPath -notlike "*$InstallDir*") {
    Write-Host "Adding $InstallDir to System PATH..."
    $NewPath = "$CurrentPath;$InstallDir"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "Machine")
}

# 7. Create an 'ab' alias/symlink
# Windows 'mklink' requires full paths. This creates 'ab.exe' as a link to 'ab_cli.exe'
$AliasPath = Join-Path $InstallDir "ab.exe"
$TargetExe = Join-Path $InstallDir "$AppName.exe"
if (-not (Test-Path $AliasPath)) {
    Write-Host "Creating alias 'ab'..."
    cmd /c mklink "$AliasPath" "$TargetExe"
}

Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host "You may need to restart your terminal (PowerShell/CMD) for the PATH changes to take effect."