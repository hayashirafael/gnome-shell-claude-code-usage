# Development Guide - Claude Usage Indicator Extension

## Architecture Overview

### Data Sources (Priority Order)

1. **Anthropic OAuth API** (Primary - Most Accurate)
   - Endpoint: `https://api.anthropic.com/api/oauth/usage`
   - Returns exact percentage from Claude's servers
   - Requires: OAuth token from `~/.config/claude/credentials.json`
   - Status: Disabled by default (enable via gsettings)

2. **ccusage CLI Tool** (Secondary - Calculated)
   - Command: `npx ccusage blocks --active --json`
   - Reads local JSONL files from `~/.config/claude/usage/`
   - Calculates percentage using discovered formula
   - Always available when Claude Code is installed

3. **Static Configuration** (Fallback)
   - Uses `cost-limit` setting from gsettings
   - Least accurate but always works

---

## The Magic Formula 🎯

After extensive testing, we discovered Claude Code calculates usage as:

```javascript
percentage = (current_cost / (projected_cost × 2)) × 100
```

### Why This Works

- **Dynamic Adjustment**: The limit changes based on burn rate
- **Projection-Based**: Uses projected total cost if current rate continues
- **Factor of 2**: The "× 2" multiplier gives the effective session limit
- **Plan-Agnostic**: Works for Pro, Max5, and Max20 without hardcoded limits

### Real Example

```
Current cost:     $4.21
Projected cost:   $12.28
Dynamic limit:    $12.28 × 2 = $24.56
Percentage:       ($4.21 / $24.56) × 100 = 17%
Site shows:       16%
Accuracy:         ~1% difference ✓
```

---

## Code Flow

```
┌─────────────────────────────────────────┐
│  Extension Initialization               │
│  - Create panel button                  │
│  - Start refresh timer (default: 1 min) │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  _updateUsageInfo()                     │
│  - Set "Refreshing..." text             │
│  - Try API first, fallback to ccusage   │
└──────────────┬──────────────────────────┘
               │
         ┌─────┴─────┐
         ▼           ▼
    ┌────────┐  ┌────────────┐
    │  API   │  │  ccusage   │
    │(if en.)│  │ (primary)  │
    └────┬───┘  └─────┬──────┘
         │            │
         └─────┬──────┘
               ▼
    ┌──────────────────────┐
    │  _displayUsage()     │
    │  1. API %? Use it    │
    │  2. Calc dynamic %   │
    │  3. Fallback static  │
    │  4. Format & display │
    └──────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │  Panel Display       │
    │  "3h 28m | 16%"     │
    └──────────────────────┘
```

---

## Key Methods

### `_tryGetUsageFromAPI()`
- Fetches exact percentage from Anthropic servers
- Most accurate but requires credentials file
- Uses curl to avoid libsoup dependency

### `_tryGetUsageFromCcusage()`
- Parses local usage JSONL files
- Calculates dynamic limit: `projected_cost × 2`
- Returns cost, projection, and time data

### `_displayUsage(data)`
- 3-tier percentage calculation priority
- Formats time (hours/minutes)
- Builds display string

---

## Token Calculation

Only these tokens count towards rate limits:

```javascript
tokensUsed = inputTokens + outputTokens + cacheCreationInputTokens
```

**NOT counted:**
- `cacheReadInputTokens` (90% discount, doesn't count towards limits)

---

## Settings (GSettings)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `refresh-interval` | int | 1 | Update frequency in minutes |
| `command-timeout` | int | 30 | Subprocess timeout in seconds |
| `ccusage-command` | string | 'npx ccusage' | Command to execute |
| `show-percentage` | bool | true | Display percentage vs cost |
| `show-time-remaining` | bool | true | Show session time left |
| `use-api-fallback` | bool | false | Enable OAuth API (needs creds) |
| `cost-limit` | double | 4.73 | Static fallback limit (Pro plan) |
| `token-limit` | int | 88000 | Token limit (unused in current impl) |

---

## ccusage JSON Structure

```json
{
  "blocks": [
    {
      "id": "2025-11-16T16:00:00.000Z",
      "startTime": "2025-11-16T16:00:00.000Z",
      "endTime": "2025-11-16T21:00:00.000Z",
      "isActive": true,
      "costUSD": 4.21,
      "tokenCounts": {
        "inputTokens": 11143,
        "outputTokens": 1699,
        "cacheCreationInputTokens": 88092,
        "cacheReadInputTokens": 1274396
      },
      "totalTokens": 1375330,
      "projection": {
        "totalCost": 12.28,
        "remainingMinutes": 202
      }
    }
  ]
}
```

---

## Debugging

### Enable Logs
```bash
journalctl -f -o cat /usr/bin/gnome-shell | grep -i "claude usage"
```

### Test ccusage Manually
```bash
npx ccusage blocks --active --json | jq '.'
```

### Test Formula
```bash
npx ccusage blocks --active --json | jq -r '
  .blocks[0] |
  "Cost: $\(.costUSD)
   Projected: $\(.projection.totalCost)
   Limit: $\(.projection.totalCost * 2)
   Calculated %: \((.costUSD / (.projection.totalCost * 2)) * 100 | floor)"
'
```

### Common Issues

1. **"Credentials file not found"**
   - API fallback is enabled but no credentials
   - Disable: `gsettings set ... use-api-fallback false`

2. **Shows "Error"**
   - ccusage command failed
   - Check: `npx ccusage blocks --active --json`
   - Ensure Claude Code is authenticated

3. **Percentage doesn't match site**
   - Small differences (<2%) are normal
   - Timing differences between fetch and site view
   - Projection changes based on recent activity

---

## Development Workflow

### Quick Reload
```bash
cd scripts && ./dev-reload.sh
```

### Full Reinstall
```bash
cd scripts && ./install-dev.sh
```

### Schema Changes
After modifying `gschema.xml`:
```bash
glib-compile-schemas extension/schemas/
# Then reload extension
```

---

## Future Improvements

- [ ] Add notification at 75%, 90%, 95% usage
- [ ] Color-coded display (green/yellow/red)
- [ ] Click to show detailed stats popup
- [ ] Multiple session tracking
- [ ] Graph of usage over time
- [ ] Preferences UI (prefs.js)

---

## References

- [ccusage](https://github.com/ryoppippi/ccusage) - Usage analysis CLI
- [GNOME Shell Extension Guide](https://gjs.guide/extensions/)
- [Claude Code Docs](https://docs.claude.com/en/docs/claude-code)
