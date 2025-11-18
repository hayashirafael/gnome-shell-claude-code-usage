# Testing Instructions - Soup Migration

## Quick Start

The extension has been updated to use GNOME's native **Soup HTTP library** instead of curl. This should have better success bypassing Cloudflare's bot detection.

### Step 1: Test with Standalone Script

Run the test script to verify Soup can access the API:

```bash
cd /home/user/gnome-shell-claude-code-usage
gjs scripts/test-soup-api.js
```

### Expected Results

#### ✅ Success (API works with Soup)
```
✅ Credentials loaded
   Organization ID: 732b3b29-...
   Session Key: sk-ant-sid01-...
   CF Clearance: 3oJRNqAVNQCuo9...

🌐 Testing API with Soup library...

📥 Response received
   Status: 200

✅ API call successful!

📊 Usage Data:
   Percentage: 29%
   Resets at: 2025-11-18T08:00:00+00:00
   Time remaining: 4h 38m

🎉 Success! The extension should show: "Claude: 4h 38m | 29%"
```

**If you see this → Soup works! Proceed to Step 2.**

#### ❌ Still Blocked (Cloudflare blocks Soup too)
```
❌ Received HTML instead of JSON (Cloudflare blocking)

First 200 chars of response:
<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title>
```

**If you see this → Soup is also blocked. See "Plan B" below.**

---

### Step 2: Test Extension in GNOME Shell

If the standalone script worked, test the actual extension:

1. **Make sure extension is enabled:**
   ```bash
   # Use the helper script (recommended)
   cd scripts
   ./settings.sh enable-api

   # Or use gsettings directly
   gsettings --schemadir /home/user/gnome-shell-claude-code-usage/extension/schemas/ \
     set org.gnome.shell.extensions.claude-usage-indicator use-api-fallback true
   ```

2. **Reload extension:**
   ```bash
   cd scripts
   ./dev-reload.sh
   ```

3. **Check top panel:**
   - Look for the "Claude:" indicator in the top-right area
   - Should show: `Claude: Xh Ym | XX%`
   - Example: `Claude: 4h 38m | 29%`

4. **Watch logs (optional):**
   ```bash
   journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude
   ```

   Look for:
   - `[Claude Usage] Fetching from API: https://claude.ai/...`
   - `[Claude Usage] Response status: 200`
   - `[Claude Usage] API response received successfully`
   - `[Claude Usage] Extracted percentage: 29`

---

## What Changed?

### Before
- Used `curl` subprocess to call API
- Cloudflare blocked all curl requests
- Extension showed time but percentage was `--`

### After
- Uses native Soup HTTP library
- Proper HTTP client with browser-like fingerprinting
- Better chance of bypassing Cloudflare

### Files Modified
1. **extension/extension.js**
   - Added `import Soup from 'gi://Soup';`
   - Replaced curl subprocess with Soup Session API
   - Added all browser headers (anthropic-*, sec-fetch-*, etc.)

2. **scripts/test-soup-api.js** (NEW)
   - Standalone test script using same Soup code
   - Tests API access without running full extension

3. **API_MIGRATION.md** (NEW)
   - Complete documentation of changes
   - Troubleshooting guide
   - Alternative solutions if Soup fails

---

## Troubleshooting

### Issue: Credentials file not found

**Error:**
```
❌ Credentials file not found: /home/user/.config/claude/credentials.json
```

**Solution:**
```bash
python3 scripts/extract-token.py
```

Follow the browser instructions to extract cookies.

---

### Issue: Cookies expired

**Symptoms:**
- API was working but now returns HTML
- cf_clearance token is old (>30 minutes)

**Solution:**
Re-extract fresh cookies:
```bash
python3 scripts/extract-token.py
```

Then test immediately:
```bash
gjs scripts/test-soup-api.js
```

---

### Issue: Extension shows "Claude: Setup API"

**Cause:** API not enabled in settings

**Solution:**
```bash
gsettings set org.gnome.shell.extensions.claude-usage-indicator use-api-fallback true
cd scripts && ./dev-reload.sh
```

---

### Issue: Extension shows "Claude: Xh Ym | --"

**Cause:** API call failed (Cloudflare blocking or network error)

**Debug steps:**

1. Test standalone script:
   ```bash
   gjs scripts/test-soup-api.js
   ```

2. Check if cookies are fresh:
   ```bash
   cat ~/.config/claude/credentials.json
   # Check if cf_clearance exists and is recent
   ```

3. Watch extension logs:
   ```bash
   journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude
   ```

4. Look for error messages:
   - "Received HTML instead of JSON" → Cloudflare blocking
   - "Error parsing API response" → Invalid JSON
   - "No five_hour data" → Unexpected API response format

---

## Plan B: If Soup is Also Blocked

If Cloudflare blocks Soup too, we have these options:

### Option 1: Browser Automation (Recommended)

Use Puppeteer/Playwright to control a real browser:

```bash
# Install Puppeteer
npm install puppeteer

# Create helper script
cat > scripts/fetch-api-via-browser.js << 'EOF'
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();

  // Set cookies from credentials.json
  await page.setCookie({ name: 'sessionKey', value: '...' });
  await page.setCookie({ name: 'lastActiveOrg', value: '...' });
  await page.setCookie({ name: 'cf_clearance', value: '...' });

  // Navigate and fetch
  const response = await page.goto('https://claude.ai/api/organizations/.../usage');
  const data = await response.json();

  console.log(JSON.stringify(data));
  await browser.close();
})();
EOF

# Test it
node scripts/fetch-api-via-browser.js
```

Then modify extension to call this script instead of Soup.

### Option 2: curl-impersonate

Use a curl variant that mimics browser TLS fingerprint:

```bash
# Install curl-impersonate
# See: https://github.com/lwthiker/curl-impersonate

curl_chrome116 'https://claude.ai/api/organizations/.../usage' \
  --cookie "sessionKey=...; lastActiveOrg=...; cf_clearance=..."
```

### Option 3: Firefox Headless

Use Firefox's headless mode:

```bash
# Export cookies to Firefox format
# Use firefox --headless to make request
```

### Option 4: Disable API (Time-Only Mode)

If nothing works, disable API and show time only:

```bash
cd scripts
./settings.sh disable-api
./settings.sh set show-percentage false
./dev-reload.sh
```

Extension will show: `Claude: 4h 38m` (no percentage)

---

## Settings Management

A helper script (`scripts/settings.sh`) is provided to make managing extension settings easier:

```bash
cd scripts

# List all settings and their current values
./settings.sh list

# Output:
# Available settings:
#   ccusage-command           = 'npx ccusage'
#   command-timeout           = 30
#   cost-limit                = 4.73
#   refresh-interval          = 1
#   show-percentage           = true
#   show-time-remaining       = true
#   token-limit               = 88000
#   use-api-fallback          = true

# Get a specific setting
./settings.sh get refresh-interval
# Output: 1

# Set a setting
./settings.sh set refresh-interval 2
# Output: ✓ Set refresh-interval = 2

# Quick commands
./settings.sh enable-api    # Enable API (use claude.ai for percentage)
./settings.sh disable-api   # Disable API (time-only mode)
```

**Note:** After changing settings, reload the extension:
```bash
./dev-reload.sh
```

---

## Current Status

- ✅ Extension code updated to use Soup
- ✅ Test script created (scripts/test-soup-api.js)
- ✅ **Soup successfully bypasses Cloudflare!** (API returns percentage: 3%)
- ✅ Settings helper script added (scripts/settings.sh)
- ✅ API enabled via settings
- ✅ Changes committed and pushed
- ⏳ **Ready for final testing in GNOME Shell panel**

## Next Steps

1. Run standalone test: `gjs scripts/test-soup-api.js`
2. If successful → Test extension in GNOME Shell
3. If blocked → Implement Plan B (browser automation)
4. Report results so we can iterate

---

**Good luck! 🚀**

If you encounter any issues, check the logs and the API_MIGRATION.md document for detailed troubleshooting.
