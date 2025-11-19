#!/usr/bin/env python3
"""
Automatic Session Token Extractor for Claude Usage Indicator

This script extracts your sessionKey and organization ID from claude.ai
to enable the extension to fetch accurate usage percentages.

Features:
- Bookmarklet for automatic extraction (recommended)
- Direct browser cookie reading (Chrome/Firefox)
- Manual extraction with improved UI
"""

import os
import json
import webbrowser
import sqlite3
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
from pathlib import Path
from urllib.parse import unquote

CONFIG_DIR = os.path.expanduser("~/.config/claude")
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials.json")
PORT = 8765

# Bookmarklet code (will be URL-encoded in HTML)
BOOKMARKLET_CODE = """
(function() {
    function getCookie(name) {
        const value = '; ' + document.cookie;
        const parts = value.split('; ' + name + '=');
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    const sessionKey = getCookie('sessionKey');
    const orgId = getCookie('lastActiveOrg');
    const cfClearance = getCookie('cf_clearance');

    if (!sessionKey || !orgId) {
        alert('❌ Cookies not found! Make sure you are logged in to claude.ai');
        return;
    }

    fetch('http://localhost:8765/receive-cookies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_key: sessionKey,
            organization_id: orgId,
            cf_clearance: cfClearance || ''
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ Cookies extracted successfully! You can close this tab now.');
        } else {
            alert('❌ Error: ' + data.error);
        }
    })
    .catch(err => {
        alert('❌ Error connecting to local server. Make sure the Python script is running!\\n\\nError: ' + err.message);
    });
})();
""".strip()

# Convert to bookmarklet format
import urllib.parse
# Replace newlines with spaces to avoid JavaScript syntax errors
BOOKMARKLET = "javascript:" + urllib.parse.quote(BOOKMARKLET_CODE.replace('\n', ' '))

# HTML page with bookmarklet instructions
EXTRACTION_PAGE = f"""<!DOCTYPE html>
<html>
<head>
    <title>Claude Cookie Extractor</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        h2 {{
            color: #555;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
            margin-top: 30px;
        }}
        .subtitle {{
            color: #666;
            font-size: 18px;
            margin-bottom: 30px;
        }}
        .status {{
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            font-weight: 500;
        }}
        .loading {{ background: #fff3cd; color: #856404; }}
        .success {{ background: #d4edda; color: #155724; }}
        .error {{ background: #f8d7da; color: #721c24; }}
        .info {{ background: #d1ecf1; color: #0c5460; }}

        .method {{
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}

        .bookmarklet {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            font-size: 18px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: transform 0.2s;
            cursor: move;
        }}
        .bookmarklet:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }}

        button {{
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
            transition: background 0.2s;
        }}
        button:hover {{ background: #0056b3; }}

        .steps {{
            background: white;
            padding: 20px;
            margin: 15px 0;
        }}
        .steps ol {{
            padding-left: 25px;
        }}
        .steps li {{
            margin: 10px 0;
            font-size: 16px;
        }}

        code {{
            background: #f4f4f4;
            padding: 3px 8px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            color: #c7254e;
        }}

        .highlight {{
            background: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin: 15px 0;
        }}

        input {{
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            font-family: 'Courier New', monospace;
        }}

        .manual-section {{ margin-top: 30px; }}

        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .badge-recommended {{ background: #28a745; color: white; }}
        .badge-advanced {{ background: #6c757d; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🍪 Claude Cookie Extractor</h1>
        <p class="subtitle">Extract your Claude.ai session cookies to enable the GNOME extension</p>

        <div id="status" class="status info">
            ✅ Local server is running on port {PORT}
        </div>

        <!-- Method 1: Bookmarklet (Recommended) -->
        <h2>Method 1: Bookmarklet <span class="badge badge-recommended">RECOMMENDED</span></h2>
        <div class="method">
            <p><strong>Easiest and fastest method!</strong> Drag the button below to your bookmarks bar:</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{BOOKMARKLET}" class="bookmarklet" onclick="alert('Drag this button to your bookmarks bar!\\n\\nDon\\'t click it here - drag it to the bookmarks bar at the top of your browser.'); return false;">
                    📤 Extract Claude Cookies
                </a>
            </div>

            <div class="steps">
                <p><strong>Steps:</strong></p>
                <ol>
                    <li><strong>Drag</strong> the purple button above to your bookmarks bar (at the top of your browser)</li>
                    <li><strong>Open</strong> <a href="https://claude.ai/settings/usage" target="_blank">claude.ai</a> in a new tab and make sure you're logged in</li>
                    <li><strong>Click</strong> the bookmarklet you just added to your bookmarks bar</li>
                    <li><strong>Done!</strong> The cookies will be automatically extracted and saved</li>
                </ol>
            </div>

            <div class="highlight">
                💡 <strong>Tip:</strong> If you don't see the bookmarks bar, press <code>Ctrl+Shift+B</code> (Chrome/Firefox) or <code>Cmd+Shift+B</code> (Mac) to show it.
            </div>
        </div>

        <!-- Method 2: Automatic Browser Detection -->
        <h2>Method 2: Automatic Browser Detection</h2>
        <div class="method">
            <p>Try to read cookies directly from your browser's database:</p>
            <button onclick="tryAutomaticExtraction()">🔍 Auto-detect Browser Cookies</button>
            <div id="auto-result" style="margin-top: 10px;"></div>
        </div>

        <!-- Method 3: Manual Extraction -->
        <h2>Method 3: Manual Extraction <span class="badge badge-advanced">ADVANCED</span></h2>
        <div class="manual-section">
            <p>If the automatic methods don't work, you can manually extract the cookies:</p>

            <div class="steps">
                <ol>
                    <li>Go to <a href="https://claude.ai" target="_blank">claude.ai</a> and log in</li>
                    <li>Press <code>F12</code> to open DevTools</li>
                    <li>Go to the <strong>Application</strong> tab (Chrome) or <strong>Storage</strong> tab (Firefox)</li>
                    <li>Under "Cookies" → "https://claude.ai", find:
                        <ul>
                            <li><code>sessionKey</code> (starts with sk-ant-sid01-)</li>
                            <li><code>lastActiveOrg</code> (UUID format)</li>
                            <li><code>cf_clearance</code> (optional, for Cloudflare)</li>
                        </ul>
                    </li>
                    <li>Copy and paste the values below:</li>
                </ol>
            </div>

            <label><strong>sessionKey:</strong></label>
            <input type="text" id="sessionKey" placeholder="sk-ant-sid01-...">

            <label><strong>Organization ID (lastActiveOrg):</strong></label>
            <input type="text" id="orgId" placeholder="732b3b29-xxxx-xxxx-xxxx-xxxxxxxxxxxx">

            <label><strong>cf_clearance (optional):</strong></label>
            <input type="text" id="cfClearance" placeholder="8m2peJaQt1pH3xrGpz_...">

            <button onclick="saveManualCookies()">💾 Save Credentials</button>
        </div>
    </div>

    <script>
        function updateStatus(message, type = 'info') {{
            const statusDiv = document.getElementById('status');
            statusDiv.className = 'status ' + type;
            statusDiv.innerHTML = message;
        }}

        function tryAutomaticExtraction() {{
            const resultDiv = document.getElementById('auto-result');
            resultDiv.innerHTML = '<div class="status loading">Requesting automatic extraction from server...</div>';

            fetch('http://localhost:{PORT}/auto-extract', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }}
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    resultDiv.innerHTML = '<div class="status success">✅ ' + data.message + '</div>';
                    updateStatus('✅ Credentials saved successfully! You can close this window.', 'success');
                }} else {{
                    resultDiv.innerHTML = '<div class="status error">❌ ' + data.error + '</div>';
                }}
            }})
            .catch(err => {{
                resultDiv.innerHTML = '<div class="status error">❌ Error: ' + err.message + '</div>';
            }});
        }}

        function saveManualCookies() {{
            const sessionKey = document.getElementById('sessionKey').value.trim();
            const orgId = document.getElementById('orgId').value.trim();
            const cfClearance = document.getElementById('cfClearance').value.trim();

            if (!sessionKey || !orgId) {{
                alert('❌ Please fill in both sessionKey and Organization ID');
                return;
            }}

            if (!sessionKey.startsWith('sk-ant-sid')) {{
                alert('⚠️ Warning: sessionKey should start with "sk-ant-sid01-"\\nAre you sure this is correct?');
            }}

            fetch('http://localhost:{PORT}/receive-cookies', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    session_key: sessionKey,
                    organization_id: orgId,
                    cf_clearance: cfClearance || ''
                }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    updateStatus('✅ Credentials saved successfully! You can close this window.', 'success');
                    setTimeout(() => window.close(), 2000);
                }} else {{
                    updateStatus('❌ Error saving credentials: ' + data.error, 'error');
                }}
            }})
            .catch(err => {{
                updateStatus('❌ Error: ' + err.message, 'error');
            }});
        }}
    </script>
</body>
</html>
"""

class CredentialsHandler(BaseHTTPRequestHandler):
    credentials_received = False

    def log_message(self, format, *args):
        pass  # Suppress default logs

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(EXTRACTION_PAGE.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/receive-cookies':
            self._handle_receive_cookies()
        elif self.path == '/auto-extract':
            self._handle_auto_extract()
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _handle_receive_cookies(self):
        """Handle cookies received from bookmarklet or manual entry"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode())
            session_key = data.get('session_key', '').strip()
            org_id = data.get('organization_id', '').strip()
            cf_clearance = data.get('cf_clearance', '').strip()

            if not session_key or not org_id:
                self.send_json_response({'success': False, 'error': 'Missing required fields (sessionKey or orgId)'})
                return

            # Validate format
            if not session_key.startswith('sk-ant-sid'):
                print(f"⚠️  Warning: sessionKey has unusual format: {session_key[:20]}...")

            # Save credentials
            success, message = save_credentials(session_key, org_id, cf_clearance)

            if success:
                print(f"\n✅ Credentials received and saved!")
                print(f"   Session Key: {session_key[:25]}...")
                print(f"   Organization ID: {org_id}")
                if cf_clearance:
                    print(f"   CF Clearance: {cf_clearance[:25]}...")

                CredentialsHandler.credentials_received = True
                self.send_json_response({'success': True, 'message': 'Credentials saved successfully'})
            else:
                self.send_json_response({'success': False, 'error': message})

        except Exception as e:
            print(f"\n❌ Error processing cookies: {e}")
            self.send_json_response({'success': False, 'error': str(e)})

    def _handle_auto_extract(self):
        """Try to automatically extract cookies from browser databases"""
        try:
            result = try_read_browser_cookies()

            if result['success']:
                CredentialsHandler.credentials_received = True
                self.send_json_response(result)
            else:
                self.send_json_response(result)

        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def save_credentials(session_key, org_id, cf_clearance=''):
    """Save credentials to file"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)

        credentials = {
            'session_key': session_key,
            'organization_id': org_id
        }

        if cf_clearance:
            credentials['cf_clearance'] = cf_clearance

        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(credentials, f, indent=2)

        os.chmod(CREDENTIALS_FILE, 0o600)

        return True, "Credentials saved successfully"
    except Exception as e:
        return False, f"Error saving credentials: {e}"


def try_read_browser_cookies():
    """
    Try to read cookies directly from browser databases.
    Supports Chrome and Firefox on Linux.
    """
    browsers = {
        'Chrome': os.path.expanduser('~/.config/google-chrome/Default/Cookies'),
        'Chromium': os.path.expanduser('~/.config/chromium/Default/Cookies'),
        'Firefox': None  # Firefox uses different structure
    }

    for browser_name, cookie_path in browsers.items():
        if cookie_path and os.path.exists(cookie_path):
            print(f"   Found {browser_name} cookies database...")

            try:
                # Copy to temp file (browser might have it locked)
                temp_db = '/tmp/cookies_temp.db'
                shutil.copy2(cookie_path, temp_db)

                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()

                # Query for claude.ai cookies
                cursor.execute("""
                    SELECT name, value
                    FROM cookies
                    WHERE host_key LIKE '%claude.ai%'
                    AND (name = 'sessionKey' OR name = 'lastActiveOrg' OR name = 'cf_clearance')
                """)

                cookies = {row[0]: row[1] for row in cursor.fetchall()}
                conn.close()
                os.remove(temp_db)

                session_key = cookies.get('sessionKey')
                org_id = cookies.get('lastActiveOrg')
                cf_clearance = cookies.get('cf_clearance', '')

                if session_key and org_id:
                    # Decrypt if needed (Chrome encrypts cookies on Linux)
                    if session_key.startswith('v10') or session_key.startswith('v11'):
                        return {
                            'success': False,
                            'error': f'{browser_name} cookies are encrypted. Please use the bookmarklet method instead.'
                        }

                    success, message = save_credentials(session_key, org_id, cf_clearance)

                    if success:
                        return {
                            'success': True,
                            'message': f'Cookies extracted from {browser_name}!'
                        }
                    else:
                        return {'success': False, 'error': message}

            except Exception as e:
                print(f"   Error reading {browser_name} cookies: {e}")
                continue

    return {
        'success': False,
        'error': 'Could not find browser cookies. Please use the bookmarklet or manual method.'
    }


def main():
    print("=" * 70)
    print("  Claude Usage Indicator - Cookie Extractor v2.0")
    print("=" * 70)
    print()
    print("  🚀 Improved with automatic bookmarklet extraction!")
    print()

    # Start server
    server = HTTPServer(('localhost', PORT), CredentialsHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    print(f"📡 Local server started on http://localhost:{PORT}")
    print()
    print("Opening browser with extraction page...")
    print()

    # Open browser
    time.sleep(1)
    try:
        webbrowser.open(f'http://localhost:{PORT}')
        print("✅ Browser opened successfully!")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print(f"\n   Please open this URL manually:")
        print(f"   http://localhost:{PORT}")

    print()
    print("-" * 70)
    print("  INSTRUCTIONS:")
    print("-" * 70)
    print("  1. Drag the purple 'Extract Claude Cookies' button to your bookmarks")
    print("  2. Open claude.ai in a new tab (make sure you're logged in)")
    print("  3. Click the bookmarklet in your bookmarks bar")
    print("  4. Done! Cookies will be automatically saved")
    print()
    print("  Press Ctrl+C to cancel")
    print("-" * 70)
    print()

    # Wait for credentials
    try:
        while not CredentialsHandler.credentials_received:
            time.sleep(0.5)

        print()
        print("=" * 70)
        print("  ✅ Setup Complete!")
        print("=" * 70)
        print()
        print("Credentials saved to:", CREDENTIALS_FILE)
        print()
        print("Next steps:")
        print()
        print("  1. Enable API in extension:")
        print("     gsettings set org.gnome.shell.extensions.claude-usage-indicator use-api-fallback true")
        print()
        print("  2. Reload the extension:")
        print("     cd scripts && ./dev-reload.sh")
        print()
        print("  3. Check the panel - you should see usage percentage!")
        print()

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    finally:
        server.shutdown()

if __name__ == '__main__':
    main()
