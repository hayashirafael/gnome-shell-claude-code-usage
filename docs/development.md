# Claude Code Usage Indicator - GNOME Shell Extension

Monitor your Claude Code token usage directly from the GNOME top bar.

## Features

- 🔍 Real-time token usage monitoring
- 📊 Percentage-based display
- 🔄 Auto-refresh (configurable)
- 🎯 Hybrid approach: uses ccusage with API fallback
- ⚡ Lightweight and efficient

## Prerequisites

1. **Claude Code** must be authenticated:
   ```bash
   claude login
   ```

2. **Option A - ccusage (Recommended):**
   ```bash
   npm install -g ccusage
   ```

3. **Option B - API Fallback:**
   - No additional installation needed
   - Extension will read credentials from `~/.config/claude/credentials.json`

## Installation

### Quick Install (Production)

```bash
cd claude-usage-indicator@hayashirafael
./install.sh
```

### Development Install (Recommended for Development)

```bash
cd claude-usage-indicator@hayashirafael
./install-dev.sh
```

This creates a symbolic link, so any changes you make to the source files are immediately reflected. After making changes, just run:

```bash
./dev-reload.sh
```

### Manual Install

1. Copy extension to GNOME extensions directory:
   ```bash
   mkdir -p ~/.local/share/gnome-shell/extensions/
   cp -r claude-usage-indicator@hayashirafael ~/.local/share/gnome-shell/extensions/
   ```

2. Compile the GSettings schema:
   ```bash
   glib-compile-schemas ~/.local/share/gnome-shell/extensions/claude-usage-indicator@hayashirafael/schemas/
   ```

3. Restart GNOME Shell:
   - **X11:** Press `Alt+F2`, type `r`, press Enter
   - **Wayland:** Log out and log back in

4. Enable the extension:
   ```bash
   gnome-extensions enable claude-usage-indicator@hayashirafael
   ```

## Usage

Once installed and enabled, you'll see "Claude: X%" in your top bar, where X is your current token usage percentage.

The extension will automatically refresh every 3 minutes (configurable).

## Configuration

Settings can be adjusted using dconf-editor or gsettings:

```bash
# Change refresh interval (in minutes)
gsettings set org.gnome.shell.extensions.claude-usage-indicator refresh-interval 5

# Change command timeout (in seconds)
gsettings set org.gnome.shell.extensions.claude-usage-indicator command-timeout 30

# Toggle percentage display
gsettings set org.gnome.shell.extensions.claude-usage-indicator show-percentage true

# Toggle API fallback
gsettings set org.gnome.shell.extensions.claude-usage-indicator use-api-fallback true
```

## Troubleshooting

### Extension doesn't appear in top bar

1. Check if extension is enabled:
   ```bash
   gnome-extensions list --enabled | grep claude-usage-indicator
   ```

2. Check extension logs:
   ```bash
   journalctl -f -o cat /usr/bin/gnome-shell
   ```

### Shows "Error" or "..."

1. Verify Claude Code is authenticated:
   ```bash
   claude --version
   ls ~/.config/claude/credentials.json
   ```

2. Test ccusage manually:
   ```bash
   npx ccusage blocks --json
   ```

3. Check extension logs for detailed errors:
   ```bash
   journalctl -f -o cat | grep "Claude Usage"
   ```

## Development

### Viewing Logs

```bash
# Real-time logs
journalctl -f -o cat /usr/bin/gnome-shell

# Or use GNOME Looking Glass (Alt+F2 → lg)
```

### Reloading Extension

```bash
gnome-extensions disable claude-usage-indicator@hayashirafael
gnome-extensions enable claude-usage-indicator@hayashirafael
```

## License

MIT

## Author

Rafael Hayashi
