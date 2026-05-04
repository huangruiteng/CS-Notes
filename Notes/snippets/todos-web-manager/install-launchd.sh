#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/Users/bytedance/CS-Notes}"
LABEL="com.huangrt.csnotes.todos-web-manager"
SRC_PLIST="$REPO_ROOT/Notes/snippets/todos-web-manager/launchd/$LABEL.plist"
DST_PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

mkdir -p "$HOME/Library/LaunchAgents" "$REPO_ROOT/.local/todos-web-manager/logs"
chmod +x "$REPO_ROOT/Notes/snippets/todos-web-manager/start.sh"

if [[ ! -f "$SRC_PLIST" ]]; then
  echo "Missing source plist: $SRC_PLIST"
  exit 1
fi

cp "$SRC_PLIST" "$DST_PLIST"

if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
  launchctl bootout "$DOMAIN/$LABEL" >/dev/null 2>&1 || true
fi

launchctl bootstrap "$DOMAIN" "$DST_PLIST"
launchctl enable "$DOMAIN/$LABEL"

echo "Installed $LABEL"
echo "Plist: $DST_PLIST"
echo "URL: http://127.0.0.1:5000"
echo "Manual run: launchctl kickstart -k $DOMAIN/$LABEL"
echo "Status: launchctl print $DOMAIN/$LABEL"
