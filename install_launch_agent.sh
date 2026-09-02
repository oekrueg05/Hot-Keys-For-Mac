#!/bin/bash
# Installs the Hot-Keys menu bar app as a launchd agent that starts at login.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="com.hotkeys.menubar"
PLIST_DEST="$HOME/Library/LaunchAgents/${LABEL}.plist"
ENTRY_SCRIPT="${1:-menubar.py}"

if [ -x "$SCRIPT_DIR/venv/bin/python3" ]; then
    PYTHON_BIN="$SCRIPT_DIR/venv/bin/python3"
else
    PYTHON_BIN="$(command -v python3)"
fi

if [ ! -f "$SCRIPT_DIR/$ENTRY_SCRIPT" ]; then
    echo "Entry script not found: $SCRIPT_DIR/$ENTRY_SCRIPT" >&2
    exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents"

sed \
    -e "s|__LABEL__|${LABEL}|g" \
    -e "s|__PYTHON__|${PYTHON_BIN}|g" \
    -e "s|__SCRIPT__|${SCRIPT_DIR}/${ENTRY_SCRIPT}|g" \
    -e "s|__WORKDIR__|${SCRIPT_DIR}|g" \
    "$SCRIPT_DIR/com.hotkeys.menubar.plist.template" > "$PLIST_DEST"

echo "Wrote $PLIST_DEST"
echo "Using Python: $PYTHON_BIN"
echo "Using entry script: $SCRIPT_DIR/$ENTRY_SCRIPT"

launchctl unload "$PLIST_DEST" >/dev/null 2>&1 || true
launchctl load "$PLIST_DEST"

echo "Loaded. It will now also start automatically at login."
echo "To remove: launchctl unload $PLIST_DEST && rm $PLIST_DEST"
