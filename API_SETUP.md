# API Setup Guide - Claude Usage Indicator

## Why API Authentication is Required

The Claude usage percentage calculation uses **proprietary dynamic algorithms** that cannot be accurately replicated locally. Previous attempts to reverse-engineer the formula showed persistent inaccuracies:

- Extension showed 31% when claude.ai showed 29% (2% error)
- Formula with dynamic factors still had variances

**Solution**: Use Anthropic's OAuth API directly to get the exact percentage shown on claude.ai/settings/usage.

---

## Setup Methods

### Method 1: Automatic Token Extraction (Recommended)

Run the Python script that extracts your session token automatically:

```bash
cd scripts
python3 extract-token.py
```

This will:
1. Start a local web server
2. Open your browser
3. Attempt to extract the Claude.ai session token automatically
4. Save it to `~/.config/claude/credentials.json`

If automatic extraction fails, follow the manual steps shown in the browser.

### Method 2: Manual Setup (Alternative)

```bash
cd scripts
./setup-oauth.sh
```

Follow the interactive prompts to extract your token from Claude.ai.

---

## Extracting Your Token Manually

If the automated scripts don't work, follow these steps:

1. **Open Claude.ai**
   - Go to https://claude.ai/settings/account
   - Make sure you're logged in

2. **Open Developer Tools**
   - Press `F12` or `Ctrl+Shift+I` (Linux/Windows)
   - Or `Cmd+Option+I` (Mac)

3. **Go to Network Tab**
   - Click on the "Network" tab
   - Refresh the page (`F5` or `Ctrl+R`)

4. **Find an API Request**
   - Look for requests to `api.anthropic.com`
   - Click on any request

5. **Copy the Token**
   - Look in the "Headers" section
   - Find either:
     - `x-api-key:` header, OR
     - `Authorization: Bearer` header
   - Copy the token value (the long string after the header name)

6. **Save Credentials**
   ```bash
   mkdir -p ~/.config/claude
   echo '{"access_token":"YOUR_TOKEN_HERE"}' > ~/.config/claude/credentials.json
   chmod 600 ~/.config/claude/credentials.json
   ```

---

## Verifying Setup

After setting up credentials:

1. **Check if file exists:**
   ```bash
   ls -la ~/.config/claude/credentials.json
   ```

2. **Make sure API is enabled:**
   ```bash
   gsettings get org.gnome.shell.extensions.claude-usage-indicator use-api-fallback
   ```
   Should return `true`

3. **Reload the extension:**
   ```bash
   cd scripts
   ./dev-reload.sh
   ```

4. **Check the panel:**
   - You should see: "Claude: 2h 15m | 29%"
   - If you see "API Required" or "Setup API", check logs:
     ```bash
     journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude
     ```

---

## Troubleshooting

### "Credentials file not found"
- Make sure the file exists at `~/.config/claude/credentials.json`
- Check file permissions: should be `600` (read/write for owner only)

### "API Required" showing in panel
- API might be disabled. Enable it:
  ```bash
  gsettings set org.gnome.shell.extensions.claude-usage-indicator use-api-fallback true
  ```

### Token appears invalid
- Your session may have expired
- Extract a fresh token from Claude.ai
- Make sure you copied the complete token (no spaces or quotes)

### Still showing "--" for percentage
- Check GNOME Shell logs for errors:
  ```bash
  journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude
  ```
- Try running the curl command manually:
  ```bash
  TOKEN="your_token_here"
  curl -s -H "x-api-key: $TOKEN" https://api.anthropic.com/api/oauth/usage | jq
  ```

### Wrong API endpoint or headers
The extension tries:
- Endpoint: `https://api.anthropic.com/api/oauth/usage`
- Header: `x-api-key: YOUR_TOKEN`

If this doesn't work, you may need to:
1. Check Claude.ai's actual API calls in DevTools
2. Update the endpoint/headers in `extension/extension.js` (line 289-296)

---

## Security Notes

- ⚠️ **Your OAuth token is sensitive** - treat it like a password
- ✅ File permissions are set to `600` (only you can read it)
- ✅ Extension only reads the token, never modifies it
- ✅ Token is only used for API calls to Anthropic's servers
- ⚠️ Never commit credentials.json to git (it's in .gitignore)
- ⚠️ Token may expire - you'll need to refresh it periodically

---

## What the Extension Does

**With API configured:**
1. Every 1 minute, fetches usage from Anthropic API
2. Displays exact percentage from claude.ai
3. Falls back to showing time + cost if API fails

**Without API:**
1. Shows time remaining from ccusage
2. Shows "API Required" for percentage
3. Works for time tracking, but no percentage

---

## Alternative: Disable Percentage Display

If you don't want to set up the API:

```bash
# Disable percentage, show only time
gsettings set org.gnome.shell.extensions.claude-usage-indicator show-percentage false

# Disable API
gsettings set org.gnome.shell.extensions.claude-usage-indicator use-api-fallback false
```

The extension will show: "Claude: 2h 15m" (no percentage)

---

## Questions?

- Check logs: `journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude`
- See DEVELOPMENT.md for code details
- See CLAUDE.md for architecture overview
- Open an issue on GitHub

---

**Last Updated**: 2025-11-16
**Status**: API authentication required for accurate percentage display
