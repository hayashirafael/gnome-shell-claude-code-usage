#!/bin/bash

EXTENSION_DIR="$HOME/.local/share/gnome-shell/extensions/claude-usage-indicator@hayashirafael"

echo "Installing Claude Usage Indicator extension..."

# Create extension directory if it doesn't exist
mkdir -p "$EXTENSION_DIR"

# Copy files
echo "Copying files..."
cp -r ./* "$EXTENSION_DIR/"

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
echo "   gnome-extensions enable claude-usage-indicator@hayashirafael"
echo ""
echo "3. Check if it's working:"
echo "   gnome-extensions info claude-usage-indicator@hayashirafael"
echo ""
