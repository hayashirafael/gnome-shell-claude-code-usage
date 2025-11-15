# Claude Code Usage Indicator - GNOME Shell Extension

## Project Overview

This is a GNOME Shell extension that displays real-time Claude Code token usage in the top bar. It helps developers monitor their daily Claude Code usage limits without switching contexts.

### Key Features
- Real-time token usage monitoring in the top bar
- Hybrid data collection (ccusage CLI + Anthropic API fallback)
- Auto-refresh with configurable intervals
- Minimal resource footprint
- Development-friendly workflow with hot-reload scripts

---

## Technology Stack

- **Language**: JavaScript (GJS - GNOME JavaScript bindings)
- **Platform**: GNOME Shell 45+ (tested on 46)
- **APIs Used**:
  - `GObject` - Object system
  - `St` (Shell Toolkit) - UI components
  - `Gio` - I/O operations, subprocess execution
  - `GLib` - Main loop, timers, file operations
  - `Clutter` - Layout and positioning
  - `Soup` (optional) - HTTP requests for API fallback

### External Dependencies
- **ccusage** - npm package for reading Claude Code usage from local JSONL files
- **libsoup** (optional) - For direct API communication when ccusage is unavailable

---

## Architecture

### Data Flow

```
┌─────────────────────┐
│  Extension Starts   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Try ccusage (Primary Method)  │
│  Executes: npx ccusage blocks  │
│  --json                         │
└──────────┬──────────────────────┘
           │
           ├──Success──▶ Parse JSON ──▶ Calculate % ──▶ Display
           │
           └──Fail────▶ Try API Fallback (if libsoup available)
                       │
                       ├──Success──▶ Parse Response ──▶ Display
                       │
                       └──Fail────▶ Show "Error"
```

### How Usage Data is Obtained

**Primary Method - ccusage (Local JSONL Files):**
- Claude Code automatically writes usage data to `~/.config/claude/usage/*.jsonl`
- ccusage reads these files locally (no API calls needed)
- Faster, works offline, no authentication required beyond Claude Code login
- Returns active session data including tokens consumed and limits

**Fallback Method - Anthropic API (Currently Disabled):**
- Reads OAuth token from `~/.config/claude/credentials.json`
- Makes GET request to `https://api.anthropic.com/api/oauth/usage`
- Requires libsoup library (gir1.2-soup-3.0)
- Currently commented out due to missing libsoup dependency

### Calculation Logic

```javascript
percentage = (tokensUsed / tokensLimit) * 100

Example:
- Tokens used: 45,231
- Token limit: 150,000 (5-hour rolling window)
- Percentage: 30.15%
```

---

## Project Structure

```
gnome-shell-claude-code-usage/
├── README.md                  # User-facing documentation
├── CLAUDE.md                  # This file - Claude Code context
├── LICENSE                    # MIT License
├── .gitignore                 # Git ignore rules
│
├── docs/
│   ├── planning.md            # Development roadmap and planning
│   └── development.md         # Development setup guide
│
├── extension/                 # Extension source code
│   ├── extension.js           # Main logic (280+ lines)
│   ├── metadata.json          # Extension metadata (name, version, UUID)
│   ├── stylesheet.css         # UI styles (basic, planned enhancements)
│   └── schemas/
│       └── org.gnome.shell.extensions.claude-usage-indicator.gschema.xml
│
└── scripts/                   # Helper scripts
    ├── install.sh             # Production installation
    ├── install-dev.sh         # Development mode (symlink)
    └── dev-reload.sh          # Quick reload during development
```

---

## Code Organization

### extension/extension.js

**Main Classes:**

1. **`ClaudeUsageIndicator` (extends `PanelMenu.Button`)**
   - UI component displayed in the top bar
   - Manages refresh timers and state
   - Coordinates data fetching and display

**Key Methods:**

- `_init(settings)` - Initialize panel button, label, and timer
- `_setupTimer()` - Configure auto-refresh interval
- `_updateUsageInfo()` - Main update loop (tries ccusage → API fallback)
- `_tryGetUsageFromCcusage()` - Execute ccusage command and parse JSON
- `_tryGetUsageFromAPI()` - Fetch usage from Anthropic API (currently disabled)
- `_executeCommand(args, timeout)` - Run subprocess with timeout handling
- `_displayUsage(data)` - Update panel label with percentage
- `destroy()` - Cleanup timers and resources

2. **`ClaudeUsageExtension` (extends `Extension`)**
   - Extension lifecycle management
   - `enable()` - Create indicator and add to panel
   - `disable()` - Remove indicator and cleanup

### GSettings Schema

Configuration options stored in `extension/schemas/*.gschema.xml`:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `refresh-interval` | int | 3 | Minutes between updates (1-60) |
| `command-timeout` | int | 30 | Subprocess timeout in seconds (5-120) |
| `ccusage-command` | string | 'npx ccusage' | Command to execute |
| `show-percentage` | bool | true | Display percentage vs raw tokens |
| `use-api-fallback` | bool | true | Enable API fallback (needs libsoup) |

---

## Development Workflow

### Initial Setup
```bash
cd scripts
./install-dev.sh  # Creates symlink to extension/
```

### Making Changes
1. Edit files in `extension/` directory
2. Run `scripts/dev-reload.sh` to reload extension
3. Check logs: `journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude`

### File Modification Impact
- **extension.js** - Requires reload (`dev-reload.sh`)
- **metadata.json** - Requires GNOME Shell restart
- **stylesheet.css** - Requires reload
- **gschema.xml** - Requires recompile + restart

---

## Important Context for AI Assistants

### Current State
- ✅ MVP is complete and functional with ccusage
- ✅ Project structure is organized and documented
- ❌ API fallback is disabled (missing libsoup dependency)
- ❌ Preferences UI (prefs.js) not yet implemented
- ❌ No visual enhancements (icons, colors) yet

### Known Limitations
1. **libsoup not available** - API fallback is commented out
2. **No error notifications** - Errors only show as "Error" in panel
3. **No preferences UI** - Must use gsettings for configuration
4. **No visual feedback** - No color coding or icons yet
5. **Limited testing** - Needs testing on actual GNOME Shell 46 installation

### Future Enhancements (Roadmap)
- [ ] Preferences UI (prefs.js)
- [ ] Notification system for threshold alerts (75%, 90%, 95%)
- [ ] Color coding (green/yellow/red based on usage)
- [ ] Custom icon support
- [ ] Time remaining display
- [ ] Context menu with detailed stats
- [ ] Multiple session tracking

### Security Considerations
- Extension reads local files only (JSONL usage data)
- OAuth token is read but NOT modified
- No external network calls without libsoup
- No credential storage or manipulation
- Subprocess execution is timeout-protected

### Testing Strategy
- Manual testing on GNOME Shell 46 (Ubuntu)
- Check GNOME Shell logs for errors
- Verify ccusage command works: `npx ccusage blocks --json`
- Monitor resource usage (CPU, memory)
- Test enable/disable cycles

---

## Common Development Tasks

### Adding a New Setting
1. Add to `extension/schemas/*.gschema.xml`
2. Recompile: `glib-compile-schemas extension/schemas/`
3. Access in code: `this._settings.get_*('setting-name')`

### Debugging
```bash
# Watch logs in real-time
journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude

# Test ccusage manually
npx ccusage blocks --json

# Check extension status
gnome-extensions info claude-usage-indicator@hayashirafael

# View all errors
journalctl -f -o cat /usr/bin/gnome-shell
```

### Common Issues
- **"Extension not found"** - Not installed or wrong directory
- **"Error" in panel** - ccusage failed, check if Claude Code is authenticated
- **No update** - Check refresh interval, verify timer is running
- **Import errors** - Missing GObject introspection libraries

---

## Code Patterns

### Async Subprocess Execution
```javascript
const proc = Gio.Subprocess.new(args, flags);
proc.communicate_utf8_async(null, null, (proc, result) => {
    const [, stdout, stderr] = proc.communicate_utf8_finish(result);
    // Handle output
});
```

### Timeout Pattern
```javascript
const timeoutId = GLib.timeout_add_seconds(
    GLib.PRIORITY_DEFAULT,
    seconds,
    () => {
        // Timeout action
        return GLib.SOURCE_REMOVE;
    }
);
```

### Settings Binding
```javascript
const settings = this.getSettings();
const interval = settings.get_int('refresh-interval');
settings.connect('changed::refresh-interval', () => {
    // React to setting change
});
```

---

## Git Workflow

- **Main development branch**: `claude/gnome-extension-usage-indicator-014xdi5zeVhSk46gN8Y82Lbq`
- **Target branch**: `main` (currently out of sync)
- **Commit style**: Conventional Commits (feat:, fix:, docs:, refactor:)
- **Language**: English for commits and code comments

---

## Contact & Contribution

- **Author**: Rafael Hayashi (@hayashirafael)
- **Repository**: https://github.com/hayashirafael/gnome-shell-claude-code-usage
- **License**: MIT
- **Inspired by**: ccusage-indicator by lordvcs

---

## Quick Reference

### Install Extension
```bash
cd scripts && ./install-dev.sh
gnome-extensions enable claude-usage-indicator@hayashirafael
```

### Reload After Changes
```bash
cd scripts && ./dev-reload.sh
```

### Check Logs
```bash
journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude
```

### View Usage Data
```bash
npx ccusage blocks --json
cat ~/.config/claude/usage/*.jsonl | tail -1
```

---

**Last Updated**: 2025-11-15
**Status**: MVP Complete, Ready for Testing
