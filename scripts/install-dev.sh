#!/bin/bash

EXTENSION_UUID="claude-usage-indicator@hayashirafael"
EXTENSIONS_DIR="$HOME/.local/share/gnome-shell/extensions"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR="$PROJECT_ROOT/extension"

echo "🔧 Installing extension in development mode..."

# Remove existing installation
if [ -d "$EXTENSIONS_DIR/$EXTENSION_UUID" ]; then
    echo "🗑️  Removing existing installation..."
    rm -rf "$EXTENSIONS_DIR/$EXTENSION_UUID"
fi

# Create symlink
echo "🔗 Creating symbolic link..."
mkdir -p "$EXTENSIONS_DIR"
ln -s "$SOURCE_DIR" "$EXTENSIONS_DIR/$EXTENSION_UUID"

# Compile schema
echo "📦 Compiling schema..."
glib-compile-schemas "$SOURCE_DIR/schemas/"

echo ""
echo "✅ Development installation complete!"
echo ""
echo "📝 Now you can:"
echo "   1. Edit files directly in: $SOURCE_DIR"
echo "   2. Changes will be reflected automatically!"
echo "   3. Just reload the extension: $SCRIPT_DIR/dev-reload.sh"
echo ""
echo "⚠️  Remember to restart GNOME Shell or run dev-reload.sh after changes"
echo ""
