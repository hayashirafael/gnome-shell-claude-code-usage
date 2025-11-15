#!/bin/bash

EXTENSION_UUID="claude-usage-indicator@hayashirafael"
EXTENSION_DIR="$HOME/.local/share/gnome-shell/extensions/$EXTENSION_UUID"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR="$PROJECT_ROOT/extension"

echo "Installing Claude Usage Indicator extension..."

# Create extension directory if it doesn't exist
mkdir -p "$EXTENSION_DIR"

# Copy files
echo "Copying files..."
cp "$SOURCE_DIR/extension.js" "$EXTENSION_DIR/"
cp "$SOURCE_DIR/metadata.json" "$EXTENSION_DIR/"
cp "$SOURCE_DIR/stylesheet.css" "$EXTENSION_DIR/"
cp -r "$SOURCE_DIR/schemas" "$EXTENSION_DIR/"

# Compile schema
echo "Compiling GSettings schema..."
glib-compile-schemas "$EXTENSION_DIR/schemas/"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Restart GNOME Shell:"
echo "   - X11: Press Alt+F2, type 'r', press Enter"
echo "   - Wayland: Log out and log back in"
echo ""
echo "2. Enable the extension:"
echo "   gnome-extensions enable $EXTENSION_UUID"
echo ""
echo "3. Check if it's working:"
echo "   gnome-extensions info $EXTENSION_UUID"
echo ""
