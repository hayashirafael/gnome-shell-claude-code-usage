#!/usr/bin/env python3
"""
Automatic Session Token Extractor for Claude Usage Indicator

This script extracts your sessionKey and organization ID from claude.ai
to enable the extension to fetch accurate usage percentages.
"""

import os
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

CONFIG_DIR = os.path.expanduser("~/.config/claude")
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials.json")
PORT = 8765

# HTML page that extracts cookies
EXTRACTION_PAGE = """<!DOCTYPE html>
<html>
<head>
    <title>Claude Cookie Extractor</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        .status {
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            font-weight: 500;
        }
        .loading { background: #fff3cd; color: #856404; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .info { background: #d1ecf1; color: #0c5460; }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
        }
        button:hover { background: #0056b3; }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
            display: block;
            margin: 5px 0;
            overflow-wrap: break-word;
        }
        input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .manual-section { margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍪 Claude Cookie Extractor</h1>
        <div id="status" class="status loading">Initializing...</div>
        <div id="instructions"></div>
        <div id="manual-section" class="manual-section" style="display: none;">
            <h3>Manual Cookie Entry</h3>
            <p>If automatic extraction failed, paste your cookies here:</p>
            <label>sessionKey:</label>
            <input type="text" id="sessionKey" placeholder="sk-ant-sid01-...">
            <label>Organization ID:</label>
            <input type="text" id="orgId" placeholder="732b3b29-...">
            <label>cf_clearance (optional but recommended):</label>
            <input type="text" id="cfClearance" placeholder="8m2peJaQt1pH3xrGpz_...">
            <button onclick="saveManualCookies()">Save Credentials</button>
        </div>
    </div>

    <script>
        const statusDiv = document.getElementById('status');
        const instructionsDiv = document.getElementById('instructions');
        const manualSection = document.getElementById('manual-section');

        function updateStatus(message, type = 'loading') {
            statusDiv.className = 'status ' + type;
            statusDiv.textContent = message;
        }

        function sendCredentials(sessionKey, orgId, cfClearance) {
            fetch('http://localhost:""" + str(PORT) + """/save-credentials', {
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
                    updateStatus('✅ Credentials saved successfully! You can close this window.', 'success');
                    setTimeout(() => window.close(), 2000);
                } else {
                    updateStatus('❌ Error saving credentials: ' + data.error, 'error');
                }
            })
            .catch(err => {
                updateStatus('❌ Error: ' + err.message, 'error');
            });
        }

        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }

        function extractFromClaudeAi() {
            updateStatus('Checking if you are on claude.ai...', 'loading');

            // Check if we're on claude.ai domain
            if (window.location.hostname === 'claude.ai' || window.location.hostname.endsWith('.claude.ai')) {
                updateStatus('Found claude.ai! Extracting cookies...', 'loading');

                const sessionKey = getCookie('sessionKey');
                const orgId = getCookie('lastActiveOrg');
                const cfClearance = getCookie('cf_clearance');

                if (sessionKey && orgId) {
                    updateStatus('✅ Found credentials! Saving...', 'success');
                    sendCredentials(sessionKey, orgId, cfClearance);
                    return true;
                } else {
                    updateStatus('⚠️ Cookies not found. Please log in to claude.ai first.', 'error');
                    showManualInstructions();
                    return false;
                }
            } else {
                // Not on claude.ai, show instructions to open it
                showOpenClaudeInstructions();
                return false;
            }
        }

        function showOpenClaudeInstructions() {
            updateStatus('Please open claude.ai to continue', 'info');
            instructionsDiv.innerHTML = `
                <p><strong>Steps:</strong></p>
                <ol>
                    <li>Click the button below to open claude.ai in a new tab</li>
                    <li>Make sure you're logged in</li>
                    <li>Come back to this tab</li>
                    <li>Click "Extract Cookies" button</li>
                </ol>
                <button onclick="window.open('https://claude.ai/settings/usage', '_blank')">Open Claude.ai</button>
                <button onclick="location.reload()">I'm Logged In - Extract Cookies</button>
            `;
            manualSection.style.display = 'block';
        }

        function showManualInstructions() {
            instructionsDiv.innerHTML = `
                <p><strong>Manual Extraction Steps:</strong></p>
                <ol>
                    <li>Go to <a href="https://claude.ai" target="_blank">claude.ai</a> and log in</li>
                    <li>Press <code>F12</code> to open DevTools</li>
                    <li>Go to the <strong>Application</strong> tab</li>
                    <li>Under "Storage" → "Cookies" → "https://claude.ai"</li>
                    <li>Find and copy these values:
                        <ul>
                            <li><code>sessionKey</code> (starts with sk-ant-sid01-)</li>
                            <li><code>lastActiveOrg</code> (your organization ID)</li>
                        </ul>
                    </li>
                    <li>Paste them in the fields below</li>
                </ol>
            `;
            manualSection.style.display = 'block';
        }

        function saveManualCookies() {
            const sessionKey = document.getElementById('sessionKey').value.trim();
            const orgId = document.getElementById('orgId').value.trim();
            const cfClearance = document.getElementById('cfClearance').value.trim();

            if (!sessionKey || !orgId) {
                alert('Please fill in sessionKey and orgId');
                return;
            }

            if (!sessionKey.startsWith('sk-ant-sid')) {
                alert('sessionKey should start with sk-ant-sid01-');
                return;
            }

            sendCredentials(sessionKey, orgId, cfClearance);
        }

        // Auto-extract on load
        setTimeout(extractFromClaudeAi, 500);
    </script>
</body>
</html>
"""

class CredentialsHandler(BaseHTTPRequestHandler):
    credentials_received = False

    def log_message(self, format, *args):
        pass  # Suppress logs

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(EXTRACTION_PAGE.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/save-credentials':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode())
                session_key = data.get('session_key', '').strip()
                org_id = data.get('organization_id', '').strip()
                cf_clearance = data.get('cf_clearance', '').strip()

                if not session_key or not org_id:
                    self.send_json_response({'success': False, 'error': 'Missing credentials'})
                    return

                # Save credentials
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

                print(f"\n✅ Credentials saved to {CREDENTIALS_FILE}")
                print(f"   Session Key: {session_key[:20]}...")
                print(f"   Organization ID: {org_id}")
                if cf_clearance:
                    print(f"   CF Clearance: {cf_clearance[:20]}...")

                CredentialsHandler.credentials_received = True

                self.send_json_response({'success': True})

            except Exception as e:
                print(f"\n❌ Error saving credentials: {e}")
                self.send_json_response({'success': False, 'error': str(e)})
        else:
            self.send_response(404)
            self.end_headers()

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def main():
    print("=" * 60)
    print("Claude Usage Indicator - Cookie Extractor")
    print("=" * 60)
    print()

    # Start server
    server = HTTPServer(('localhost', PORT), CredentialsHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    print(f"📡 Local server started on http://localhost:{PORT}")
    print()
    print("Opening browser...")
    print()
    print("If browser doesn't open automatically, visit:")
    print(f"  http://localhost:{PORT}")
    print()

    # Open browser
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}')

    print("Follow the instructions in your browser to extract cookies.")
    print("Press Ctrl+C to cancel.")
    print()

    # Wait for credentials
    try:
        while not CredentialsHandler.credentials_received:
            time.sleep(0.5)

        print()
        print("=" * 60)
        print("Setup Complete!")
        print("=" * 60)
        print()
        print("Credentials have been saved. Now enable the extension:")
        print()
        print("  gsettings set org.gnome.shell.extensions.claude-usage-indicator use-api-fallback true")
        print()
        print("Then reload the extension:")
        print("  cd scripts && ./dev-reload.sh")
        print()

    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    finally:
        server.shutdown()

if __name__ == '__main__':
    main()
