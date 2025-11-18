#!/bin/bash
# Helper script for managing extension settings
# Usage: ./settings.sh [get|set|list] [key] [value]

SCHEMA_DIR="/home/user/gnome-shell-claude-code-usage/extension/schemas/"
SCHEMA_NAME="org.gnome.shell.extensions.claude-usage-indicator"

case "$1" in
    list)
        echo "Available settings:"
        gsettings --schemadir "$SCHEMA_DIR" list-keys "$SCHEMA_NAME" | while read key; do
            value=$(gsettings --schemadir "$SCHEMA_DIR" get "$SCHEMA_NAME" "$key")
            printf "  %-25s = %s\n" "$key" "$value"
        done
        ;;
    get)
        if [ -z "$2" ]; then
            echo "Usage: $0 get <key>"
            exit 1
        fi
        gsettings --schemadir "$SCHEMA_DIR" get "$SCHEMA_NAME" "$2"
        ;;
    set)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 set <key> <value>"
            exit 1
        fi
        gsettings --schemadir "$SCHEMA_DIR" set "$SCHEMA_NAME" "$2" "$3"
        echo "✓ Set $2 = $3"
        ;;
    enable-api)
        gsettings --schemadir "$SCHEMA_DIR" set "$SCHEMA_NAME" use-api-fallback true
        echo "✓ API enabled"
        ;;
    disable-api)
        gsettings --schemadir "$SCHEMA_DIR" set "$SCHEMA_NAME" use-api-fallback false
        echo "✓ API disabled"
        ;;
    *)
        echo "Claude Usage Indicator - Settings Manager"
        echo ""
        echo "Usage: $0 <command> [arguments]"
        echo ""
        echo "Commands:"
        echo "  list              List all settings and current values"
        echo "  get <key>         Get value of a setting"
        echo "  set <key> <val>   Set value of a setting"
        echo "  enable-api        Enable API usage (recommended)"
        echo "  disable-api       Disable API usage (time-only mode)"
        echo ""
        echo "Examples:"
        echo "  $0 list"
        echo "  $0 get use-api-fallback"
        echo "  $0 set refresh-interval 1"
        echo "  $0 enable-api"
        echo ""
        exit 1
        ;;
esac
