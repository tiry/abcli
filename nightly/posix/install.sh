#!/bin/bash

# Configuration
APP_NAME="ab_cli"
INSTALL_DIR="/opt/${APP_NAME}_app"
BIN_DEST="/usr/local/bin"
SOURCE_DIST="./${APP_NAME}"

# 1. Check if the build exists
if [ ! -d "$SOURCE_DIST" ]; then
    echo "❌ Error: Build directory $SOURCE_DIST not found."
    exit 1
fi

# 2. Require sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)."
    exit 1
fi

echo "🚀 Starting installation of $APP_NAME..."

# 3. Ensure destination directories exist
# We create the parent /opt if it doesn't exist, but we handle the app dir in step 4
mkdir -p "$(dirname "$INSTALL_DIR")"
mkdir -p "$BIN_DEST"

# 4. Clean up and Copy
echo "Copying application to $INSTALL_DIR..."
rm -rf "$INSTALL_DIR" 

# FIX: Copy the source folder but force the destination name to match $INSTALL_DIR
cp -RP "$SOURCE_DIST" "$INSTALL_DIR"

# 5. Fix Permissions
# PyInstaller 'onedir' creates the binary with the same name as the folder
if [ -f "$INSTALL_DIR/$APP_NAME" ]; then
    chmod +x "$INSTALL_DIR/$APP_NAME"
else
    echo "⚠️  Warning: Binary not found at $INSTALL_DIR/$APP_NAME"
fi

# 6. Create Symlinks
echo "Creating symlinks in $BIN_DEST..."
ln -sf "$INSTALL_DIR/$APP_NAME" "$BIN_DEST/$APP_NAME"
ln -sf "$INSTALL_DIR/$APP_NAME" "$BIN_DEST/ab"

echo "✅ Installation complete!"
echo "You can now run '$APP_NAME' or 'ab' from any terminal."

# 7. macOS Gatekeeper Bypass
if [[ "$(uname)" == "Darwin" ]]; then
    echo "🔓 Removing macOS quarantine flag..."
    xattr -rd com.apple.quarantine "$INSTALL_DIR" 2>/dev/null || true
fi