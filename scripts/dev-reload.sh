#!/bin/bash

EXTENSION_UUID="claude-usage-indicator@hayashirafael"
EXTENSION_DIR="$HOME/.local/share/gnome-shell/extensions/$EXTENSION_UUID"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR="$PROJECT_ROOT/extension"

echo "🔄 Reloading extension..."

# Copy updated files (if not using symlink)
if [ ! -L "$EXTENSION_DIR" ]; then
    echo "📁 Copying files..."
    cp "$SOURCE_DIR/extension.js" "$EXTENSION_DIR/"
    cp "$SOURCE_DIR/metadata.json" "$EXTENSION_DIR/"
    cp "$SOURCE_DIR/stylesheet.css" "$EXTENSION_DIR/"
fi

# Recompile schema if changed
if [ "$SOURCE_DIR/schemas/org.gnome.shell.extensions.claude-usage-indicator.gschema.xml" -nt "$EXTENSION_DIR/schemas/gschemas.compiled" ]; then
    echo "🔧 Recompiling schema..."
    glib-compile-schemas "$EXTENSION_DIR/schemas/" || glib-compile-schemas "$SOURCE_DIR/schemas/"
fi

echo "♻️  Reloading extension..."
gnome-extensions disable "$EXTENSION_UUID" 2>/dev/null
sleep 0.5
gnome-extensions enable "$EXTENSION_UUID"

echo ""
echo "✅ Extension reloaded!"
echo ""
echo "💡 Tips:"
echo "   - Check logs: journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude"
echo "   - Restart GNOME Shell: Alt+F2 → r (X11) or logout/login (Wayland)"
echo ""
