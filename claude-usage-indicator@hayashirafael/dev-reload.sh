#!/bin/bash

EXTENSION_DIR="$HOME/.local/share/gnome-shell/extensions/claude-usage-indicator@hayashirafael"

echo "🔄 Reloading extension..."

# Copy updated files
echo "📁 Copying files..."
cp extension.js "$EXTENSION_DIR/"
cp metadata.json "$EXTENSION_DIR/"
cp stylesheet.css "$EXTENSION_DIR/"

# Recompile schema if changed
if [ schemas/org.gnome.shell.extensions.claude-usage-indicator.gschema.xml -nt "$EXTENSION_DIR/schemas/gschemas.compiled" ]; then
    echo "🔧 Recompiling schema..."
    glib-compile-schemas "$EXTENSION_DIR/schemas/"
fi

echo "♻️ Reloading extension..."
gnome-extensions disable claude-usage-indicator@hayashirafael 2>/dev/null
sleep 0.5
gnome-extensions enable claude-usage-indicator@hayashirafael

echo ""
echo "✅ Extension reloaded!"
echo ""
echo "💡 Tips:"
echo "   - Check logs: journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude"
echo "   - Restart GNOME Shell: Alt+F2 → r (X11) or logout/login (Wayland)"
echo ""
