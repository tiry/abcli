#!/bin/bash

# Configuration
APP_NAME="ab_cli"
INSTALL_DIR="/opt/${APP_NAME}_app"
BIN_DEST="/usr/local/bin"
SOURCE_DIST="./dist/${APP_NAME}"

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

# 3. Ensure destination directories exist (Crucial for Linux)
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DEST"

# 4. Clean up and Copy
# Using -a (archive) on Linux is safer; -R is fine for macOS.
echo "Copying application to $INSTALL_DIR..."
rm -rf "$INSTALL_DIR" 
cp -RP "$SOURCE_DIST" "$(dirname "$INSTALL_DIR")" # Copy folder to /opt/

# 5. Fix Permissions
chmod +x "$INSTALL_DIR/$APP_NAME"

# 6. Create Symlinks
echo "Creating symlinks in $BIN_DEST..."
ln -sf "$INSTALL_DIR/$APP_NAME" "$BIN_DEST/$APP_NAME"
ln -sf "$INSTALL_DIR/$APP_NAME" "$BIN_DEST/ab"

echo "✅ Installation complete!"
echo "You can now run '$APP_NAME' or 'ab' from any terminal."
