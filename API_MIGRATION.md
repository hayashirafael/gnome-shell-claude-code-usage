# API Migration: From curl to Soup

## Summary of Changes

We've migrated the Claude.ai API integration from using `curl` subprocess to using GNOME's native **Soup** HTTP library. This change aims to bypass Cloudflare's bot detection, which was blocking curl requests even with correct cookies and headers.

## What Changed

### Before (curl-based approach)
```javascript
// Spawned subprocess: curl -s -H "Cookie: ..." https://claude.ai/api/...
const args = ['curl', '-s', '-H', `Cookie: ${cookieString}`, ...];
const result = await this._executeCommand(args, timeout);
```

**Problems:**
- ❌ Cloudflare detected curl as a bot
- ❌ Returned HTML challenge page instead of JSON
- ❌ No amount of headers/cookies could bypass detection
- ❌ Extension showed "--" for percentage

### After (Soup-based approach)
```javascript
// Uses native GNOME HTTP library
const session = new Soup.Session({ user_agent: '...' });
const message = Soup.Message.new('GET', url);
headers.append('Cookie', cookieString);
session.send_and_read_async(message, ...);
```

**Benefits:**
- ✅ Proper HTTP library (not CLI tool)
- ✅ Better browser-like behavior
- ✅ Native to GNOME ecosystem
- ✅ More efficient (no subprocess spawning)
- ✅ May bypass Cloudflare detection

## Files Modified

1. **extension/extension.js**
   - Added: `import Soup from 'gi://Soup';`
   - Replaced: `_fetchFromAPIWithCurl()` → `_fetchFromAPIWithSoup()`
   - Changed: All API calls now use Soup Session + Message APIs

## Testing

### Method 1: Test Script (Standalone)

Run the standalone test script to verify Soup can access the API:

```bash
cd /home/user/gnome-shell-claude-code-usage
gjs scripts/test-soup-api.js
```

**Expected output if working:**
```
✅ Credentials loaded
   Organization ID: 732b3b29-...
   Session Key: sk-ant-sid01-...
   CF Clearance: 3oJRNqAVNQCuo9...

🌐 Testing API with Soup library...
   URL: https://claude.ai/api/organizations/.../usage

📤 Sending request...

📥 Response received
   Status: 200
   Length: 450 bytes

✅ API call successful!

📊 Usage Data:
   Percentage: 29%
   Resets at: 2025-11-18T08:00:00+00:00
   Time remaining: 4h 38m

🎉 Success! The extension should show: "Claude: 4h 38m | 29%"
```

**If still blocked by Cloudflare:**
```
❌ Received HTML instead of JSON (Cloudflare blocking)

First 200 chars of response:
<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title>
```

### Method 2: Extension Testing

1. **Reload the extension:**
   ```bash
   cd scripts
   ./dev-reload.sh
   ```

2. **Check the top panel:**
   - Should show: `Claude: Xh Ym | XX%`
   - If shows `Claude: Xh Ym | --` → API still blocked

3. **Watch logs for debugging:**
   ```bash
   journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude
   ```

   Look for these log messages:
   - `[Claude Usage] Fetching from API: https://claude.ai/...`
   - `[Claude Usage] Response status: 200`
   - `[Claude Usage] API response received successfully`
   - `[Claude Usage] Extracted percentage: 29`

## Troubleshooting

### If Soup is also blocked by Cloudflare

If Soup library also gets blocked (returns HTML instead of JSON), we have these options:

**Option 1: Browser Automation**
Use Puppeteer/Playwright via Node.js helper script:
```javascript
// scripts/fetch-api-via-browser.js
const puppeteer = require('puppeteer');
// Launch headless browser, extract data, return JSON
```

**Option 2: curl-impersonate**
Use a tool that mimics browser TLS fingerprint:
```bash
curl_chrome116 'https://claude.ai/api/...' --cookie "..."
```

**Option 3: Firefox Profile**
Extract cookies from Firefox and use `firefox --headless` to make request.

**Option 4: Give up on API**
Fallback to ccusage-only mode (shows time but no percentage).

### Verifying Cookies are Fresh

Cookies expire! If API was working but stopped:

1. **Check cookie age:**
   ```bash
   cat ~/.config/claude/credentials.json
   # cf_clearance tokens typically expire after 30 minutes
   ```

2. **Re-extract cookies:**
   ```bash
   python3 scripts/extract-token.py
   ```

3. **Test immediately:**
   ```bash
   gjs scripts/test-soup-api.js
   ```

### Enable/Disable API

```bash
# Enable API usage
gsettings set org.gnome.shell.extensions.claude-usage-indicator use-api-fallback true

# Disable API usage (time-only mode)
gsettings set org.gnome.shell.extensions.claude-usage-indicator use-api-fallback false
```

## Technical Details

### Soup vs curl: Why Soup might work better

| Aspect | curl | Soup |
|--------|------|------|
| **TLS Fingerprint** | OpenSSL/BoringSSL (CLI) | GnuTLS/OpenSSL (library) |
| **HTTP/2** | Supported but different implementation | Native library support |
| **Request Timing** | Subprocess spawn overhead | Direct async calls |
| **Connection Reuse** | One-shot per invocation | Session with connection pooling |
| **User-Agent** | Identifies as curl by default | Configurable, looks more like app |

### Why Cloudflare Blocks Automated Requests

Cloudflare uses multiple signals:
1. **TLS Fingerprint** - TLS handshake characteristics (cipher suites, extensions order)
2. **HTTP/2 Fingerprint** - SETTINGS frame, header compression (HPACK)
3. **Timing Patterns** - Request intervals, connection behavior
4. **JavaScript Challenge** - Executes JS, validates browser environment
5. **Behavioral Analysis** - Mouse movements, scroll patterns (N/A for API)

### Headers Sent by Soup

The extension sends these headers (mimicking browser):

```
GET /api/organizations/{org_id}/usage HTTP/1.1
Host: claude.ai
Accept: */*
Accept-Language: pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7
anthropic-client-platform: web_claude_ai
anthropic-client-sha: 32e70e953567275b457146991c741b2f86f4a0f0
anthropic-client-version: 1.0.0
cache-control: no-cache
pragma: no-cache
Referer: https://claude.ai/settings/usage
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-origin
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36...
Cookie: sessionKey=sk-ant-sid01-...; lastActiveOrg=...; cf_clearance=...
```

## Next Steps

1. **Test the new Soup implementation**
   ```bash
   gjs scripts/test-soup-api.js
   ```

2. **If successful**, verify extension shows percentage:
   ```bash
   # Should show in top panel: "Claude: 4h 38m | 29%"
   ```

3. **If still blocked**, we'll need to implement browser automation (Option 1 above)

4. **Document the final solution** in CLAUDE.md and README.md

## Commit Message

```
feat: migrate API calls from curl to Soup library

- Replace subprocess curl calls with native Soup HTTP library
- Add comprehensive browser-like headers to mimic real requests
- Improve efficiency by avoiding subprocess spawning
- Better Cloudflare compatibility with proper HTTP client
- Add standalone test script (scripts/test-soup-api.js)

This change addresses Cloudflare blocking curl requests even with
correct cookies and headers. Soup provides a more browser-like HTTP
client that may bypass bot detection.

Ref: claude.ai API integration for accurate percentage display
```

---

**Status**: Implementation complete, awaiting testing in GNOME Shell environment.
**Date**: 2025-11-18
