# Claude Code Usage Indicator - GNOME Shell Extension

## Project Overview

This is a GNOME Shell extension that displays real-time Claude Code usage in the top bar. It helps developers monitor their 5-hour session usage limits without switching contexts, allowing them to plan work accordingly and avoid hitting 100% limit unexpectedly.

### Key Features
- **Real-time percentage display** matching claude.ai/settings/usage (~1% accuracy)
- **Session time remaining** in top bar (e.g., "3h 28m | 16%")
- **Dynamic calculation** using discovered formula - works for all plans (Pro/Max5/Max20)
- **Hybrid data sources** (Anthropic OAuth API → ccusage CLI → static config)
- **Auto-refresh every 1 minute** with configurable intervals
- **Zero hardcoded limits** - adapts to any plan automatically
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
- **curl** - Used for Anthropic OAuth API requests (no libsoup needed!)

---

## Architecture

### Data Flow

```
┌─────────────────────────────────────────┐
│  Extension Starts (Every 1 minute)      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Try Anthropic OAuth API (if enabled)   │
│  GET api.anthropic.com/api/oauth/usage  │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴────────────┐
    │                       │
    ▼                       ▼
 Success              No API / Failed
 Return %                   │
    │                       ▼
    │          ┌────────────────────────────┐
    │          │  Try ccusage (Primary)     │
    │          │  npx ccusage blocks        │
    │          │  --active --json           │
    │          └──────────┬─────────────────┘
    │                     │
    │          ┌──────────┴────────────┐
    │          │                       │
    │          ▼                       ▼
    │      Success                  Failed
    │      Calculate %                │
    │      (formula)                  │
    │          │                      │
    └──────────┴──────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Display in Panel    │
    │  "3h 28m | 16%"     │
    └──────────────────────┘
```

### How Usage Data is Obtained

**Method 1 - Anthropic OAuth API (Most Accurate):**
- **Endpoint**: `https://api.anthropic.com/api/oauth/usage`
- **Returns**: Exact percentage from Claude's servers
- **Authentication**: OAuth token from `~/.config/claude/credentials.json`
- **Status**: Available via curl (disabled by default - enable with gsettings)
- **Accuracy**: 100% - matches claude.ai exactly

**Method 2 - ccusage CLI (Primary, Always Used):**
- **Source**: Reads local JSONL files from `~/.config/claude/usage/*.jsonl`
- **Command**: `npx ccusage blocks --active --json`
- **Returns**: Cost, projected cost, tokens, time remaining
- **Calculation**: Uses discovered formula (see below)
- **Accuracy**: ~1% difference from claude.ai
- **Benefits**: Works offline, no API key needed, fast

**Method 3 - Static Configuration (Fallback):**
- Uses `cost-limit` setting from gsettings
- Least accurate but always available
- Requires manual configuration per plan

### The Magic Formula 🎯

After extensive testing and reverse engineering, we discovered Claude Code calculates usage as:

```javascript
percentage = (current_cost / (projected_cost × 2)) × 100
```

**Why This Works:**
- Claude Code adjusts limits **dynamically** based on burn rate
- The `projected_cost` is what you'd spend if current rate continues
- Multiplying by **2** gives the effective session limit
- This works for **all plans** (Pro/Max5/Max20) without hardcoded limits

**Real Example:**
```
Current cost:     $4.21
Projected cost:   $12.28
Dynamic limit:    $12.28 × 2 = $24.56
Percentage:       ($4.21 / $24.56) × 100 = 17%
Site shows:       16%
Accuracy:         ~1% ✓
```

**Token Calculation:**
Only these tokens count towards limits:
```javascript
tokensUsed = inputTokens + outputTokens + cacheCreationInputTokens
// cacheReadInputTokens are NOT counted (90% discount)
```

---

## Project Structure

```
gnome-shell-claude-code-usage/
├── README.md                  # User-facing documentation
├── CLAUDE.md                  # This file - Claude Code context
├── DEVELOPMENT.md             # Developer guide with formula explanation
├── LICENSE                    # MIT License
├── .gitignore                 # Git ignore rules
│
├── extension/                 # Extension source code
│   ├── extension.js           # Main logic (470+ lines, fully documented)
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
- `_setupTimer()` - Configure auto-refresh interval (default: 1 minute)
- `_updateUsageInfo()` - Main update loop (tries API → ccusage → fallback)
- `_tryGetUsageFromAPI()` - Fetch exact percentage from Anthropic OAuth API
- `_fetchFromAPIWithCurl(token)` - Execute API request using curl
- `_tryGetUsageFromCcusage()` - Execute ccusage command, parse JSON, calculate %
- `_executeCommand(args, timeout)` - Run subprocess with timeout handling
- `_displayUsage(data)` - Calculate percentage (3-tier priority) and update panel
- `destroy()` - Cleanup timers and resources

**Percentage Calculation Priority (in _displayUsage):**
1. Use `apiPercentage` if available (from OAuth API)
2. Calculate using `dynamicLimit` formula: `(cost / (projected × 2)) × 100`
3. Fallback to static `cost-limit` configuration

2. **`ClaudeUsageExtension` (extends `Extension`)**
   - Extension lifecycle management
   - `enable()` - Create indicator and add to panel
   - `disable()` - Remove indicator and cleanup

### GSettings Schema

Configuration options stored in `extension/schemas/*.gschema.xml`:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `refresh-interval` | int | 1 | Minutes between updates (1-60) |
| `command-timeout` | int | 30 | Subprocess timeout in seconds (5-120) |
| `ccusage-command` | string | 'npx ccusage' | Command to execute |
| `show-percentage` | bool | true | Display percentage vs raw cost |
| `show-time-remaining` | bool | true | Display session time remaining |
| `use-api-fallback` | bool | false | Enable OAuth API (needs credentials) |
| `token-limit` | int | 88000 | Token limit (unused, kept for future use) |
| `cost-limit` | double | 4.73 | Static cost limit for Pro plan (~$4.73) |

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
- ✅ **Core functionality complete and working** (~1% accuracy vs claude.ai)
- ✅ **Dynamic formula discovered** - works for all plans without hardcoding
- ✅ **Time remaining display** - shows hours and minutes until session reset
- ✅ **Fully documented code** - JSDoc comments and DEVELOPMENT.md guide
- ✅ **API support via curl** - no libsoup dependency needed
- ✅ **Auto-refresh every 1 minute** - stays up-to-date
- ⚠️ **API disabled by default** - requires credentials file to enable
- ❌ **No preferences UI** - must use gsettings for configuration
- ❌ **No visual enhancements** - no colors, icons, or notifications yet

### Known Limitations
1. **No preferences UI (prefs.js)** - Configuration via gsettings only
2. **No error notifications** - Errors only show as "Error" in panel
3. **No visual feedback** - No color coding (green/yellow/red) or icons
4. **API requires setup** - Needs `~/.config/claude/credentials.json` to work
5. **Small percentage variance** - Dynamic calculation ~1% different from site (acceptable)

### Future Enhancements (Roadmap)
- [ ] Preferences UI (prefs.js) for easy configuration
- [ ] Notification system for threshold alerts (75%, 90%, 95%)
- [ ] Color coding (green/yellow/red based on usage percentage)
- [ ] Custom icon support with different states
- [ ] Click-to-expand popup with detailed stats
- [ ] Historical usage graph (last 24h)
- [ ] Multiple session tracking across different time windows
- [ ] Export usage data to CSV/JSON

### Security Considerations
- Extension reads local files only (JSONL usage data from ccusage)
- OAuth token is read from credentials file but NOT modified
- External API calls only via curl (user-controlled, optional)
- No credential storage or manipulation by extension
- Subprocess execution is timeout-protected
- All API communication uses HTTPS
- No sensitive data logging

### Testing Strategy
- Manual testing on GNOME Shell 46 (Ubuntu)
- Verify formula accuracy: compare with claude.ai/settings/usage
- Check GNOME Shell logs for errors: `journalctl -f -o cat /usr/bin/gnome-shell`
- Test ccusage command: `npx ccusage blocks --active --json`
- Monitor resource usage (CPU, memory) - should be minimal
- Test enable/disable cycles
- Verify percentage calculation with different burn rates

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
npx ccusage blocks --active --json

# Test formula calculation
npx ccusage blocks --active --json | jq -r '
  .blocks[0] |
  "Cost: $\(.costUSD)
   Projected: $\(.projection.totalCost)
   Limit: $\(.projection.totalCost * 2)
   Calculated %: \((.costUSD / (.projection.totalCost * 2)) * 100 | floor)"
'

# Check extension status
gnome-extensions info claude-usage-indicator@hayashirafael

# View all errors
journalctl -f -o cat /usr/bin/gnome-shell
```

### Common Issues
- **"Extension not found"** - Not installed or wrong directory
- **"Error" in panel** - ccusage failed, check if Claude Code is authenticated
- **"Credentials file not found"** - API fallback enabled but no credentials (disable it)
- **Percentage doesn't match** - Small variance (<2%) is normal, timing differences
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
# View active session data
npx ccusage blocks --active --json

# See formula in action
npx ccusage blocks --active --json | jq '.blocks[0] | {
  cost: .costUSD,
  projected: .projection.totalCost,
  limit: (.projection.totalCost * 2),
  percentage: ((.costUSD / (.projection.totalCost * 2)) * 100 | floor)
}'

# View raw usage files
cat ~/.config/claude/usage/*.jsonl | tail -5
```

---

## Additional Resources

- **DEVELOPMENT.md** - Complete developer guide with formula explanation
- **README.md** - User installation and usage guide
- **extension/extension.js** - Fully documented source code with JSDoc comments

---

**Last Updated**: 2025-11-16
**Status**: ✅ Production Ready - Formula discovered, fully functional, ~1% accuracy
