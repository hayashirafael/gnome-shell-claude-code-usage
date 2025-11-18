# Quick Start Guide

## ✅ Good News: Soup Works!

The Soup-based API integration **successfully bypassed Cloudflare**! 🎉

Test result:
```
✅ API call successful!
📊 Usage Data:
   Percentage: 3%
   Resets at: 2025-11-18T07:59:59.581309+00:00
   Time remaining: 4h 0m
```

---

## Quick Setup (3 Steps)

### 1. Enable API
```bash
cd /home/user/gnome-shell-claude-code-usage/scripts
./settings.sh enable-api
```

### 2. Reload Extension
```bash
./dev-reload.sh
```

### 3. Check Panel
Look at your GNOME Shell top panel (top-right area).

**Expected:** `Claude: 4h 0m | 3%`

---

## Settings Management

```bash
cd scripts

# See all settings
./settings.sh list

# Change refresh interval (minutes)
./settings.sh set refresh-interval 2

# Enable/disable features
./settings.sh enable-api      # Use claude.ai API (recommended)
./settings.sh disable-api     # Use ccusage only (no percentage)

# Always reload after changing settings
./dev-reload.sh
```

---

## Troubleshooting

### Panel shows "Claude: 4h 0m | --"

API call failed. Check logs:
```bash
journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude
```

Look for:
- `[Claude Usage] Fetching from API: https://claude.ai/...`
- `[Claude Usage] Response status: 200`
- `[Claude Usage] Extracted percentage: 3`

### Panel shows "Claude: Setup API"

API not enabled. Run:
```bash
cd scripts
./settings.sh enable-api
./dev-reload.sh
```

### Cookies expired

Re-extract fresh cookies:
```bash
python3 scripts/extract-token.py
```

Then immediately test:
```bash
gjs scripts/test-soup-api.js
```

---

## Testing Commands

```bash
# Test API directly (standalone)
gjs scripts/test-soup-api.js

# List extension settings
cd scripts && ./settings.sh list

# Watch extension logs in real-time
journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude

# Reload extension after changes
cd scripts && ./dev-reload.sh
```

---

## What to Expect

### Success ✅
```
Panel display: "Claude: 4h 0m | 3%"
                        ↑         ↑
                   time left   exact %
                              from API
```

### Logs (if working correctly)
```
[Claude Usage] Fetching from API: https://claude.ai/api/organizations/.../usage
[Claude Usage] Sending request with cookies: sessionKey=sk-ant-sid01-...
[Claude Usage] Response status: 200
[Claude Usage] Response length: 340
[Claude Usage] API response received successfully
[Claude Usage] five_hour data: {"utilization":3,"resets_at":"2025-11-18T07:59:59..."}
[Claude Usage] Extracted percentage: 3
```

---

## Files You Need to Know

| File | Purpose |
|------|---------|
| `scripts/settings.sh` | Manage extension settings |
| `scripts/dev-reload.sh` | Reload extension after changes |
| `scripts/extract-token.py` | Extract cookies from browser |
| `scripts/test-soup-api.js` | Test API without GNOME Shell |
| `~/.config/claude/credentials.json` | Stored cookies (auto-generated) |

---

## Summary

1. ✅ Soup HTTP library **successfully bypasses Cloudflare**
2. ✅ API returns exact percentage (3%)
3. ✅ Extension code ready
4. ✅ Settings configured (API enabled)
5. ⏳ Final step: Check your GNOME Shell panel

**The extension should now display: "Claude: 4h 0m | 3%"**

If you see this, everything is working perfectly! 🎉
