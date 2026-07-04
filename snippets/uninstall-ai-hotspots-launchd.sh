#!/usr/bin/env bash
set -euo pipefail

LABEL="com.huangrt.csnotes.ai-hotspots"
DST_PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
  launchctl bootout "$DOMAIN/$LABEL" >/dev/null 2>&1 || true
fi

rm -f "$DST_PLIST"

echo "Uninstalled $LABEL"
