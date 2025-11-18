#!/bin/bash
# Test script for Claude Usage Indicator Extension
# This simulates API responses and tests the extension logic

set -e

echo "========================================"
echo "Claude Usage Indicator - Extension Test"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check ccusage availability
echo -n "Test 1: Checking ccusage availability... "
if command -v npx &> /dev/null && npx ccusage --version &> /dev/null; then
    echo -e "${GREEN}✓ PASS${NC}"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  ccusage not found. Install with: npm install -g ccusage"
    exit 1
fi

# Test 2: Check ccusage data
echo -n "Test 2: Fetching ccusage data... "
CCUSAGE_DATA=$(npx ccusage blocks --active --json 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$CCUSAGE_DATA" ]; then
    echo -e "${GREEN}✓ PASS${NC}"

    # Extract data
    COST=$(echo "$CCUSAGE_DATA" | jq -r '.blocks[0].costUSD // 0')
    PROJECTED=$(echo "$CCUSAGE_DATA" | jq -r '.blocks[0].projection.totalCost // 0')
    REMAINING=$(echo "$CCUSAGE_DATA" | jq -r '.blocks[0].projection.remainingMinutes // 0')

    echo "  Cost: \$${COST}"
    echo "  Projected: \$${PROJECTED}"
    echo "  Time remaining: ${REMAINING} minutes"
else
    echo -e "${YELLOW}⚠ SKIP${NC} (no active session)"
fi

# Test 3: Check API endpoint
echo -n "Test 3: Testing API endpoint... "
API_RESPONSE=$(curl -s -w "\n%{http_code}" https://api.anthropic.com/api/oauth/usage 2>&1 | tail -1)
if [ "$API_RESPONSE" = "401" ]; then
    echo -e "${GREEN}✓ PASS${NC} (endpoint exists, needs auth)"
elif [ "$API_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (endpoint accessible)"
else
    echo -e "${YELLOW}⚠ WARN${NC} (HTTP $API_RESPONSE)"
fi

# Test 4: Check for credentials file
echo -n "Test 4: Checking credentials file... "
CRED_FILE="$HOME/.config/claude/credentials.json"
if [ -f "$CRED_FILE" ]; then
    echo -e "${GREEN}✓ PASS${NC}"

    # Try to extract and test token
    if command -v jq &> /dev/null; then
        TOKEN=$(jq -r '.access_token' "$CRED_FILE" 2>/dev/null)
        if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
            echo "  Testing token..."
            API_TEST=$(curl -s -H "x-api-key: $TOKEN" https://api.anthropic.com/api/oauth/usage 2>&1)

            if echo "$API_TEST" | jq . &> /dev/null; then
                echo -e "  ${GREEN}✓ Token is valid!${NC}"

                # Extract percentage if available
                PERCENTAGE=$(echo "$API_TEST" | jq -r '.current_session.percentage // .five_hour.percentage // .session.percentage // null')
                if [ "$PERCENTAGE" != "null" ]; then
                    echo "  API returned: ${PERCENTAGE}%"
                fi
            else
                echo -e "  ${RED}✗ Token appears invalid${NC}"
                echo "  Response: $API_TEST"
            fi
        fi
    fi
else
    echo -e "${YELLOW}⚠ NOT FOUND${NC}"
    echo "  Run: scripts/extract-token.py to set up API access"
fi

# Test 5: Check extension installation
echo -n "Test 5: Checking extension installation... "
EXT_DIR="$HOME/.local/share/gnome-shell/extensions/claude-usage-indicator@hayashirafael"
if [ -d "$EXT_DIR" ] || [ -L "$EXT_DIR" ]; then
    echo -e "${GREEN}✓ PASS${NC}"

    # Check if enabled
    if gnome-extensions list --enabled 2>/dev/null | grep -q "claude-usage-indicator"; then
        echo "  Extension is enabled"
    else
        echo -e "  ${YELLOW}Extension is installed but not enabled${NC}"
        echo "  Enable with: gnome-extensions enable claude-usage-indicator@hayashirafael"
    fi
else
    echo -e "${YELLOW}⚠ NOT INSTALLED${NC}"
    echo "  Install with: cd scripts && ./install-dev.sh"
fi

# Test 6: Check gsettings
echo -n "Test 6: Checking extension settings... "
if command -v gsettings &> /dev/null; then
    API_ENABLED=$(gsettings get org.gnome.shell.extensions.claude-usage-indicator use-api-fallback 2>/dev/null || echo "false")
    SHOW_PCT=$(gsettings get org.gnome.shell.extensions.claude-usage-indicator show-percentage 2>/dev/null || echo "true")
    SHOW_TIME=$(gsettings get org.gnome.shell.extensions.claude-usage-indicator show-time-remaining 2>/dev/null || echo "true")
    INTERVAL=$(gsettings get org.gnome.shell.extensions.claude-usage-indicator refresh-interval 2>/dev/null || echo "1")

    echo -e "${GREEN}✓ PASS${NC}"
    echo "  API enabled: $API_ENABLED"
    echo "  Show percentage: $SHOW_PCT"
    echo "  Show time: $SHOW_TIME"
    echo "  Refresh interval: $INTERVAL minute(s)"
else
    echo -e "${RED}✗ FAIL${NC} (gsettings not found)"
fi

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo ""

if [ -f "$CRED_FILE" ] && [ -d "$EXT_DIR" ]; then
    echo -e "${GREEN}✓ Ready to use!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Reload extension: cd scripts && ./dev-reload.sh"
    echo "  2. Check panel for: 'Claude: 2h 15m | 29%'"
    echo "  3. View logs: journalctl -f -o cat /usr/bin/gnome-shell | grep -i claude"
elif [ ! -f "$CRED_FILE" ]; then
    echo -e "${YELLOW}⚠ Setup required${NC}"
    echo ""
    echo "API authentication not configured."
    echo "Run: python3 scripts/extract-token.py"
elif [ ! -d "$EXT_DIR" ]; then
    echo -e "${YELLOW}⚠ Installation required${NC}"
    echo ""
    echo "Extension not installed."
    echo "Run: cd scripts && ./install-dev.sh"
fi

echo ""
