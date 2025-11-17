#!/usr/bin/env python3
"""
Automatic OAuth Token Extractor for Claude Usage Indicator

This script:
1. Starts a local web server
2. Opens Claude.ai in your browser
3. Extracts the session token automatically via JavaScript
4. Saves it to ~/.config/claude/credentials.json
"""

import os
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import time

CONFIG_DIR = os.path.expanduser("~/.config/claude")
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials.json")
PORT = 8765

# HTML page that extracts the token
EXTRACTION_PAGE = """<!DOCTYPE html>
<html>
<head>
    <title>Claude Token Extractor</title>
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
        }
        button:hover { background: #0056b3; }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Claude Token Extractor</h1>
        <div id="status" class="status loading">Initializing...</div>
        <div id="instructions"></div>
    </div>

    <script>
        const statusDiv = document.getElementById('status');
        const instructionsDiv = document.getElementById('instructions');

        function updateStatus(message, type = 'loading') {
            statusDiv.className = 'status ' + type;
            statusDiv.textContent = message;
        }

        function sendToken(token) {
            fetch('http://localhost:""" + str(PORT) + """/save-token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: token })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateStatus('✅ Token saved successfully! You can close this window.', 'success');
                    setTimeout(() => window.close(), 2000);
                } else {
                    updateStatus('❌ Error saving token: ' + data.error, 'error');
                }
            })
            .catch(err => {
                updateStatus('❌ Error: ' + err.message, 'error');
            });
        }

        // Try to extract token from current page
        function extractToken() {
            updateStatus('Attempting to extract token...', 'loading');

            // Method 1: Check localStorage
            try {
                const keys = Object.keys(localStorage);
                for (const key of keys) {
                    const value = localStorage.getItem(key);
                    if (value && value.includes('sk-ant-')) {
                        updateStatus('Found API key in localStorage!', 'success');
                        sendToken(value);
                        return;
                    }
                    // Try parsing as JSON
                    try {
                        const parsed = JSON.parse(value);
                        if (parsed.accessToken || parsed.access_token || parsed.sessionKey) {
                            const token = parsed.accessToken || parsed.access_token || parsed.sessionKey;
                            updateStatus('Found token in localStorage!', 'success');
                            sendToken(token);
                            return;
                        }
                    } catch (e) {}
                }
            } catch (e) {
                console.error('localStorage error:', e);
            }

            // Method 2: Check sessionStorage
            try {
                const keys = Object.keys(sessionStorage);
                for (const key of keys) {
                    const value = sessionStorage.getItem(key);
                    try {
                        const parsed = JSON.parse(value);
                        if (parsed.accessToken || parsed.access_token) {
                            const token = parsed.accessToken || parsed.access_token;
                            updateStatus('Found token in sessionStorage!', 'success');
                            sendToken(token);
                            return;
                        }
                    } catch (e) {}
                }
            } catch (e) {
                console.error('sessionStorage error:', e);
            }

            // Method 3: Manual extraction
            updateStatus('Automatic extraction failed. Please follow manual steps:', 'info');
            instructionsDiv.innerHTML = `
                <p><strong>Manual Steps:</strong></p>
                <ol>
                    <li>Open <a href="https://claude.ai" target="_blank">claude.ai</a> in a new tab</li>
                    <li>Make sure you're logged in</li>
                    <li>Press <code>F12</code> or <code>Ctrl+Shift+I</code> to open DevTools</li>
                    <li>Go to the <strong>Network</strong> tab</li>
                    <li>Refresh the page</li>
                    <li>Look for requests to <code>api.anthropic.com</code></li>
                    <li>Click on any request and check the <strong>Headers</strong></li>
                    <li>Copy the value from the <code>x-api-key</code> or <code>Authorization</code> header</li>
                    <li>Paste it below and click Save</li>
                </ol>
                <input type="text" id="manualToken" placeholder="Paste token here" style="width: 100%; padding: 10px; margin: 10px 0;">
                <button onclick="saveManualToken()">Save Token</button>
            `;
        }

        function saveManualToken() {
            const token = document.getElementById('manualToken').value.trim();
            if (!token) {
                alert('Please paste a token');
                return;
            }
            // Remove "Bearer " prefix if present
            const cleanToken = token.replace(/^Bearer\\s+/i, '');
            sendToken(cleanToken);
        }

        // Wait a bit for page to load, then try extraction
        setTimeout(extractToken, 1000);
    </script>
</body>
</html>
"""

class TokenHandler(BaseHTTPRequestHandler):
    token_received = False

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
        if self.path == '/save-token':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode())
                token = data.get('token', '').strip()

                if not token:
                    self.send_json_response({'success': False, 'error': 'No token provided'})
                    return

                # Save token
                os.makedirs(CONFIG_DIR, exist_ok=True)
                credentials = {'access_token': token}

                with open(CREDENTIALS_FILE, 'w') as f:
                    json.dump(credentials, f, indent=2)

                os.chmod(CREDENTIALS_FILE, 0o600)

                print(f"\n✅ Token saved to {CREDENTIALS_FILE}")
                TokenHandler.token_received = True

                self.send_json_response({'success': True})

            except Exception as e:
                print(f"\n❌ Error saving token: {e}")
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
    print("Claude Usage Indicator - Automatic Token Extractor")
    print("=" * 60)
    print()

    # Start server
    server = HTTPServer(('localhost', PORT), TokenHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    print(f"📡 Local server started on http://localhost:{PORT}")
    print()
    print("Opening browser...")

    # Open browser
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}')

    print()
    print("Follow the instructions in your browser to extract the token.")
    print("Press Ctrl+C to cancel.")
    print()

    # Wait for token
    try:
        while not TokenHandler.token_received:
            time.sleep(0.5)

        print()
        print("=" * 60)
        print("Setup Complete!")
        print("=" * 60)
        print()
        print("Now enable the API in the extension:")
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
