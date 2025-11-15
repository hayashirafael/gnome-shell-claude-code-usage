# Claude Code Usage Indicator

<div align="center">

**Monitor your Claude Code token usage directly from the GNOME top bar**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GNOME Shell](https://img.shields.io/badge/GNOME%20Shell-45%20|%2046-blue)](https://www.gnome.org/)

</div>

---

## 📖 Overview

A GNOME Shell extension that displays your Claude Code token usage in real-time on the top bar. Stay informed about your daily usage limits without switching contexts.

### Features

- 🔍 **Real-time monitoring** - Track token consumption as you work
- 📊 **Percentage display** - See your usage as a percentage of daily limit
- 🔄 **Auto-refresh** - Configurable update intervals (1-60 minutes)
- 🎯 **Hybrid approach** - Uses `ccusage` with API fallback (when libsoup is available)
- ⚡ **Lightweight** - Minimal resource footprint
- 🛠️ **Configurable** - Customize refresh intervals and display options

---

## 📋 Prerequisites

### Required

1. **GNOME Shell 45+** (tested on 46)
2. **Claude Code** authenticated:
   ```bash
   claude login
   ```
3. **ccusage** installed:
   ```bash
   npm install -g ccusage
   ```

### Optional

- **libsoup** for API fallback:
  ```bash
  sudo apt install gir1.2-soup-3.0
  ```

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

1. **Restart GNOME Shell:**
   - **X11:** Press `Alt+F2`, type `r`, press Enter
   - **Wayland:** Log out and log back in

2. **Enable the extension:**
   ```bash
   gnome-extensions enable claude-usage-indicator@hayashirafael
   ```

---

## 🎯 Usage

Once enabled, look at your **top bar** (right side):

```
Claude: 30.5%
```

The extension will automatically refresh based on your configured interval (default: 3 minutes).

---

## ⚙️ Configuration

Adjust settings using `gsettings`:

```bash
# Change refresh interval (in minutes)
gsettings set org.gnome.shell.extensions.claude-usage-indicator refresh-interval 5

# Change command timeout (in seconds)
gsettings set org.gnome.shell.extensions.claude-usage-indicator command-timeout 30

# Toggle percentage display
gsettings set org.gnome.shell.extensions.claude-usage-indicator show-percentage true

# Toggle API fallback (requires libsoup)
gsettings set org.gnome.shell.extensions.claude-usage-indicator use-api-fallback true
```

---

## 📁 Project Structure

```
gnome-shell-claude-code-usage/
├── README.md                  # This file
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
