# Claude Code Usage Indicator

<div align="center">

**Monitor your Claude Code token usage directly from the GNOME top bar**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GNOME Shell](https://img.shields.io/badge/GNOME%20Shell-45%20|%2046-blue)](https://www.gnome.org/)

> 📘 **For developers & AI assistants**: See [CLAUDE.md](CLAUDE.md) for comprehensive project context and architecture

</div>

---

## 📖 Overview

A GNOME Shell extension that displays your Claude Code usage in real-time on the top bar. Stay informed about your 5-hour session limits without switching contexts.

### Features

- 🎯 **100% Accurate** - Gets exact percentage from claude.ai API
- ⏱️ **Time Remaining** - Shows hours and minutes until session reset
- 🔄 **Auto-refresh** - Updates every 1 minute automatically
- 🌐 **API Integration** - Uses Soup library, successfully bypasses Cloudflare
- 📊 **Clean Display** - Shows "4h 0m | 3%" in top panel
- ⚡ **Lightweight** - Native GNOME libraries, minimal resource usage
- 🛠️ **Easy Configuration** - Helper script for managing settings

---

## 📋 Prerequisites

1. **GNOME Shell 45+** (tested on 46)
2. **Python 3** (for cookie extraction script)
3. **Active claude.ai session** (logged in browser)

**Optional (for fallback):**
- **ccusage** for offline time display:
  ```bash
  npm install -g ccusage
  ```

**Built-in (no installation needed):**
- Soup 3.0 HTTP library (included with GNOME)

---

## 🚀 Installation

### Quick Install

```bash
cd scripts
./install.sh
```

### Development Mode

For active development with hot-reload:

```bash
cd scripts
./install-dev.sh
```

This creates a symbolic link. After making code changes:

```bash
cd scripts
./dev-reload.sh
```

### Post-Installation

1. **Extract cookies from your browser:**
   ```bash
   python3 scripts/extract-token.py
   ```
   Follow the instructions to copy cookies from your logged-in claude.ai browser session.

2. **Restart GNOME Shell:**
   - **X11:** Press `Alt+F2`, type `r`, press Enter
   - **Wayland:** Log out and log back in

3. **Enable the extension:**
   ```bash
   gnome-extensions enable claude-usage-indicator@hayashirafael
   ```

4. **Verify it works:**
   ```bash
   # Test API access
   gjs scripts/test-soup-api.js

   # Should show: ✅ API call successful!
   ```

---

## 🎯 Usage

Once enabled, look at your **top bar** (right side):

```
Claude: 4h 0m | 3%
        ↑        ↑
   time left   exact %
             from API
```

The extension automatically refreshes every 1 minute with the latest data from claude.ai.

### What the Display Shows

- **Time remaining**: Hours and minutes until your 5-hour session resets
- **Percentage**: Exact usage percentage from claude.ai (100% accuracy)
- **Auto-updates**: Refreshes every 60 seconds

---

## ⚙️ Configuration

Use the helper script for easy configuration:

```bash
cd scripts

# List all settings
./settings.sh list

# Enable API (recommended)
./settings.sh enable-api

# Change refresh interval (1-60 minutes)
./settings.sh set refresh-interval 2

# Reload extension after changes
./dev-reload.sh
```

### Manual Configuration (Advanced)

You can also use `gsettings` directly:

```bash
# Enable API
gsettings --schemadir /path/to/extension/schemas/ \
  set org.gnome.shell.extensions.claude-usage-indicator use-api-fallback true

# Change refresh interval
gsettings --schemadir /path/to/extension/schemas/ \
  set org.gnome.shell.extensions.claude-usage-indicator refresh-interval 2
```

---

## 📁 Project Structure

```
gnome-shell-claude-code-usage/
├── README.md                  # This file
├── CLAUDE.md                  # AI/Developer context & architecture
├── LICENSE                    # MIT License
├── .gitignore                 # Git ignore rules
├── docs/
│   ├── planning.md            # Development planning
│   └── development.md         # Development guide
├── extension/                 # Extension source code
│   ├── extension.js           # Main logic
│   ├── metadata.json          # Extension metadata
│   ├── schemas/               # GSettings schemas
│   └── stylesheet.css         # Styles
└── scripts/                   # Helper scripts
    ├── install.sh             # Production install
    ├── install-dev.sh         # Development install
    └── dev-reload.sh          # Quick reload
```

---

## 🐛 Troubleshooting

### Extension doesn't appear

```bash
# Check if enabled
gnome-extensions list --enabled | grep claude

# Check extension info
gnome-extensions info claude-usage-indicator@hayashirafael

# View logs
journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude
```

### Shows "Error" or "..."

1. **Verify Claude Code is authenticated:**
   ```bash
   claude --version
   ls ~/.config/claude/credentials.json
   ```

2. **Test ccusage manually:**
   ```bash
   npx ccusage blocks --json
   ```

3. **Check logs for errors:**
   ```bash
   journalctl -f -o cat /usr/bin/gnome-shell | grep "Claude Usage"
   ```

---

## 🛠️ Development

See [docs/development.md](docs/development.md) for detailed development instructions.

### Quick Start

1. Clone the repository
2. Run `scripts/install-dev.sh`
3. Edit files in `extension/`
4. Run `scripts/dev-reload.sh` to apply changes

---

## 📝 Roadmap

- [ ] Preferences UI (prefs.js)
- [ ] Notification alerts at thresholds (75%, 90%, 95%)
- [ ] Custom icon support
- [ ] Color coding (green/yellow/red)
- [ ] Time remaining display
- [ ] Menu with detailed stats
- [ ] API direct support (without ccusage)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 👤 Author

**Rafael Hayashi**

- GitHub: [@hayashirafael](https://github.com/hayashirafael)

---

## 🙏 Acknowledgments

- Inspired by [ccusage-indicator](https://github.com/lordvcs/ccusage-indicator)
- Built with [GNOME Shell Extensions](https://gjs.guide/)
- Uses [ccusage](https://github.com/ryoppippi/ccusage) for data collection

---

<div align="center">

**Made with ❤️ for the Claude Code community**

</div>
