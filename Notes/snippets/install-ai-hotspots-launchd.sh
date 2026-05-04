#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/Users/bytedance/CS-Notes}"
LABEL="com.huangrt.csnotes.ai-hotspots"
SRC_PLIST="$REPO_ROOT/Notes/snippets/launchd/$LABEL.plist"
DST_PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

mkdir -p "$HOME/Library/LaunchAgents" "$REPO_ROOT/.local/ai-hotspots/logs" "$REPO_ROOT/.local/ai-hotspots/reports"
chmod +x "$REPO_ROOT/Notes/snippets/generate-ai-hotspots-daily.sh"

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
echo "Schedule: daily 08:30 local time"
echo "Manual run: launchctl kickstart -k $DOMAIN/$LABEL"
echo "Status: launchctl print $DOMAIN/$LABEL"
