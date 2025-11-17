#!/bin/bash
# OAuth Authentication Setup for Claude Usage Indicator
# This script helps you authenticate with Anthropic and obtain an OAuth token

set -e

CONFIG_DIR="$HOME/.config/claude"
CREDENTIALS_FILE="$CONFIG_DIR/credentials.json"

echo "================================================"
echo "Claude Usage Indicator - OAuth Setup"
echo "================================================"
echo ""

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

echo "This script will help you obtain an OAuth token from Anthropic."
echo ""
echo "Option 1: Extract from Claude.ai (Recommended)"
echo "Option 2: Manual OAuth flow"
echo ""
read -p "Choose option (1 or 2): " option

if [ "$option" = "1" ]; then
    echo ""
    echo "Follow these steps:"
    echo ""
    echo "1. Open https://claude.ai in your browser"
    echo "2. Make sure you're logged in"
    echo "3. Open Developer Tools (F12 or Ctrl+Shift+I)"
    echo "4. Go to the 'Application' or 'Storage' tab"
    echo "5. Under 'Local Storage', click on 'https://claude.ai'"
    echo "6. Look for a key like 'sessionKey' or similar"
    echo "7. Copy the access token value"
    echo ""
    echo "Alternatively, you can:"
    echo "1. Go to the 'Network' tab in DevTools"
    echo "2. Refresh the page"
    echo "3. Look for requests to 'api.anthropic.com'"
    echo "4. Check the 'Authorization' header"
    echo "5. Copy the Bearer token (everything after 'Bearer ')"
    echo ""

    read -p "Opening claude.ai in your browser. Press Enter when ready..."
    xdg-open "https://claude.ai/settings/account" 2>/dev/null || open "https://claude.ai/settings/account" 2>/dev/null || echo "Please open https://claude.ai/settings/account manually"

    echo ""
    read -p "Paste your access token here: " access_token

    if [ -z "$access_token" ]; then
        echo "Error: No token provided"
        exit 1
    fi

    # Save credentials
    cat > "$CREDENTIALS_FILE" <<EOF
{
  "access_token": "$access_token"
}
EOF

    chmod 600 "$CREDENTIALS_FILE"

    echo ""
    echo "✅ Credentials saved to $CREDENTIALS_FILE"
    echo ""

    # Test the token
    echo "Testing token..."
    response=$(curl -s -w "\n%{http_code}" -H "x-api-key: $access_token" https://api.anthropic.com/v1/messages 2>&1 | tail -1)

    if [ "$response" = "401" ] || [ "$response" = "403" ]; then
        echo "⚠️  Warning: Token may be invalid or expired. HTTP status: $response"
        echo "Please try again or use a different method."
    else
        echo "✅ Token appears to be valid!"
    fi

elif [ "$option" = "2" ]; then
    echo ""
    echo "Manual OAuth Flow:"
    echo ""
    echo "Unfortunately, Anthropic's OAuth flow requires a registered application."
    echo "Please use Option 1 to extract the token from your browser session."
    echo ""
    exit 1
else
    echo "Invalid option"
    exit 1
fi

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Now enable the API in the extension:"
echo ""
echo "  gsettings set org.gnome.shell.extensions.claude-usage-indicator use-api-fallback true"
echo ""
echo "Then reload the extension:"
echo "  cd scripts && ./dev-reload.sh"
echo ""
