# Claude Code Usage Indicator - GNOME Shell Extension

## 🎯 MVP Objective
Create a GNOME Shell extension that displays Claude Code token usage in the top bar.

**Target:** Show icon + percentage (e.g., "Claude 30%") in the status bar

---

## 🏗️ Project Structure

```
claude-usage-indicator@hayashirafael/
├── extension.js              # Main logic (hybrid approach)
├── metadata.json             # Extension metadata
├── schemas/
│   └── org.gnome.shell.extensions.claude-usage-indicator.gschema.xml
└── stylesheet.css            # (Later - styling)
```

---

## 🚀 Implementation Plan - MVP

### Phase 1: Basic Structure ✅
- [x] Create task-claude-code-gnome.md
- [ ] Create metadata.json (GNOME Shell 46 support)
- [ ] Create basic extension.js skeleton
- [ ] Create GSettings schema

### Phase 2: Core Functionality 🔄
- [ ] Implement ccusage command execution
- [ ] Parse JSON output from ccusage
- [ ] Calculate token percentage
- [ ] Display in top bar (text only first)
- [ ] Auto-refresh every 3-5 minutes

### Phase 3: Hybrid Approach 🔄
- [ ] Check if ccusage is installed
- [ ] Fallback to API direct if ccusage fails
- [ ] Read credentials from ~/.config/claude/credentials.json
- [ ] Fetch usage from https://api.anthropic.com/api/oauth/usage
- [ ] Handle errors gracefully

### Phase 4: Testing ✅
- [ ] Install extension locally
- [ ] Test with GNOME Shell 46
- [ ] Verify token percentage display
- [ ] Test refresh mechanism

### Phase 5: Polish (After MVP Works) 🎨
- [ ] Add custom icon
- [ ] Color coding (green/yellow/red)
- [ ] Preferences UI (prefs.js)
- [ ] Notifications at thresholds
- [ ] Better error messages
- [ ] Tooltips with details

---

## 🔧 Technical Approach

### Data Sources (Hybrid)

**Primary: ccusage (local JSONL files)**
```bash
npx ccusage blocks --json
```
- Reads: `~/.config/claude/usage/*.jsonl`
- No authentication needed
- Faster, works offline

**Fallback: Anthropic API**
```bash
GET https://api.anthropic.com/api/oauth/usage
Authorization: Bearer <token>
```
- Reads token from: `~/.config/claude/credentials.json`
- Real-time data
- Requires internet

### Calculation Logic

```javascript
percentage = (tokens_used / tokens_limit) * 100
```

**Display Format (MVP):**
```
Claude: 30%        // Simple text
```

**Display Format (Final):**
```
[🔵] 2h 35m (30%)  // Icon + time + percentage
```

---

## 📋 MVP Requirements

### Must Have:
- ✅ Display token percentage in top bar
- ✅ Auto-refresh every 3-5 minutes
- ✅ Basic error handling
- ✅ Works with ccusage installed

### Nice to Have (Later):
- Icon
- Color coding
- Preferences UI
- Notifications
- Time remaining
- Tooltips

---

## 🧪 Testing Checklist

- [ ] Extension loads without errors
- [ ] Shows in top bar
- [ ] Displays correct percentage
- [ ] Refreshes automatically
- [ ] Works after GNOME Shell restart
- [ ] Handles ccusage not installed
- [ ] Handles no Claude Code authentication

---

## 📦 Installation Commands

```bash
# Compile schema
glib-compile-schemas schemas/

# Install extension
cp -r . ~/.local/share/gnome-shell/extensions/claude-usage-indicator@hayashirafael/

# Restart GNOME Shell (X11)
Alt+F2 → r → Enter

# Restart GNOME Shell (Wayland)
Log out and log back in

# Enable extension
gnome-extensions enable claude-usage-indicator@hayashirafael
```

---

## 🐛 Known Issues to Address

From reference extension (ccusage-indicator):
- ❌ Double command execution (JSON + tabular)
- ❌ Timeout not implemented
- ❌ Fragile regex parsing
- ❌ No cache mechanism

Our solutions:
- ✅ Single command execution
- ✅ Proper timeout implementation
- ✅ Robust JSON parsing
- ✅ Simple cache (avoid excessive calls)

---

## 📝 Notes

- GNOME Shell version: 46.0
- UUID: `claude-usage-indicator@hayashirafael`
- License: MIT
- Language: JavaScript (GJS)

---

## 🔄 Current Status

**Status:** In Development - MVP Phase
**Last Updated:** 2025-11-15
**Next Step:** Create metadata.json and basic extension structure
