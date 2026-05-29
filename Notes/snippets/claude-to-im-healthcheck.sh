#!/usr/bin/env bash
set -euo pipefail

# Read-only health check for claude-to-im / Lark bridge.
# It summarizes local state without printing config values or full logs.

CTI_HOME="${CTI_HOME:-$HOME/.claude-to-im}"
CONFIG_FILE="$CTI_HOME/config.env"
PID_FILE="$CTI_HOME/runtime/bridge.pid"
STATUS_FILE="$CTI_HOME/runtime/status.json"

find_skill_dir() {
  local candidates=(
    "$HOME/.codex/skills/claude-to-im"
    "$HOME/.codex/skills/Claude-to-IM-skill"
    "$HOME/.claude/skills/claude-to-im"
    "$HOME/.claude/skills/Claude-to-IM-skill"
  )
  local dir
  for dir in "${candidates[@]}"; do
    if [ -f "$dir/scripts/daemon.sh" ] || [ -f "$dir/SKILL.md" ]; then
      printf '%s\n' "$dir"
      return 0
    fi
  done
  return 1
}

mask_sensitive() {
  sed -E \
    -e 's/((token|secret|password|key)(["'\'' ]?[=:]["'\'' ]?))[^ "]+/\1*****/gi' \
    -e 's/(Bearer )[A-Za-z0-9._~+\/=-]+/\1*****/g' \
    -e 's/(sk-[A-Za-z0-9_-]+)/sk-*****/g'
}

config_key_exists() {
  local key="$1"
  [ -f "$CONFIG_FILE" ] && grep -qE "^${key}=" "$CONFIG_FILE"
}

config_value_or_default() {
  local key="$1"
  local default="$2"
  if [ ! -f "$CONFIG_FILE" ]; then
    printf '%s\n' "$default"
    return
  fi
  local value
  value=$(grep -E "^${key}=" "$CONFIG_FILE" 2>/dev/null | head -1 | cut -d= -f2- | sed 's/^["'\'']//;s/["'\'']$//' || true)
  printf '%s\n' "${value:-$default}"
}

print_section() {
  printf '\n## %s\n' "$1"
}

print_kv() {
  printf -- '- %s: %s\n' "$1" "$2"
}

SKILL_DIR="$(find_skill_dir || true)"
DAEMON_SH="${SKILL_DIR:+$SKILL_DIR/scripts/daemon.sh}"
DOCTOR_SH="${SKILL_DIR:+$SKILL_DIR/scripts/doctor.sh}"

echo "# claude-to-im healthcheck"
print_kv "cti_home" "$CTI_HOME"
print_kv "skill_dir" "${SKILL_DIR:-missing}"
print_kv "mode" "read-only"

print_section "Config"
if [ -f "$CONFIG_FILE" ]; then
  print_kv "config" "exists"
  print_kv "runtime" "$(config_value_or_default CTI_RUNTIME claude | mask_sensitive)"
  channels=()
  config_key_exists "CTI_TELEGRAM_BOT_TOKEN" && channels+=("telegram")
  config_key_exists "CTI_DISCORD_BOT_TOKEN" && channels+=("discord")
  config_key_exists "CTI_FEISHU_APP_ID" && channels+=("feishu")
  config_key_exists "CTI_QQ_APP_ID" && channels+=("qq")
  config_key_exists "CTI_WEIXIN_MEDIA_ENABLED" && channels+=("weixin")
  if [ "${#channels[@]}" -gt 0 ]; then
    IFS=,
    print_kv "configured_channels" "${channels[*]}"
    unset IFS
  else
    print_kv "configured_channels" "unknown"
  fi
else
  print_kv "config" "missing"
  print_kv "next" "create config.env before attempting daemon start"
fi

print_section "Process"
pid=""
if [ -f "$PID_FILE" ]; then
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
fi
if [ -n "$pid" ]; then
  if kill -0 "$pid" 2>/dev/null; then
    print_kv "pid" "$pid alive"
    ps -p "$pid" -o pid,ppid,etime,command 2>/dev/null | tail -n +2 | mask_sensitive | sed 's/^/- ps: /'
  else
    print_kv "pid" "$pid stale_or_dead"
  fi
else
  print_kv "pid" "missing"
fi
if [ -f "$STATUS_FILE" ]; then
  if grep -q '"running"[[:space:]]*:[[:space:]]*true' "$STATUS_FILE" 2>/dev/null; then
    print_kv "status_json" "running=true"
  else
    print_kv "status_json" "running_not_true"
  fi
else
  print_kv "status_json" "missing"
fi

print_section "Daemon Status Summary"
if [ "$(uname -s)" = "Darwin" ] && command -v launchctl >/dev/null 2>&1; then
  launchctl list 2>/dev/null \
    | grep 'com.claude-to-im.bridge' \
    | mask_sensitive \
    | sed 's/^/- launchd: /' || print_kv "launchd" "not_registered_or_not_visible"
elif [ -n "$pid" ]; then
  if kill -0 "$pid" 2>/dev/null; then
    print_kv "process" "alive"
  else
    print_kv "process" "not_alive"
  fi
else
  print_kv "process" "no_pid"
fi

print_section "Doctor Summary"
if [ -n "${DOCTOR_SH:-}" ] && [ -f "$DOCTOR_SH" ]; then
  doctor_output="$(bash "$DOCTOR_SH" 2>&1 | mask_sensitive || true)"
  ok_count="$(printf '%s\n' "$doctor_output" | grep -c '^\[OK\]' || true)"
  fail_count="$(printf '%s\n' "$doctor_output" | grep -c '^\[FAIL\]' || true)"
  print_kv "ok" "$ok_count"
  print_kv "fail" "$fail_count"
  printf '%s\n' "$doctor_output" | grep '^\[FAIL\]' | head -12 | sed 's/^/- /' || true
else
  print_kv "doctor" "missing"
fi

print_section "Recent Error Keyword Counts"
if [ -n "${DAEMON_SH:-}" ] && [ -f "$DAEMON_SH" ]; then
  counts="$(
    bash "$DAEMON_SH" logs 300 2>/dev/null \
      | mask_sensitive \
      | grep -Eoi 'feishu|lark|message|event|callback|permission|websocket|error|fail|timeout|codex|claude|auth|working|stale|pid' \
      | tr '[:upper:]' '[:lower:]' \
      | sort \
      | uniq -c \
      | sort -nr \
      | head -20 || true
  )"
  if [ -n "$counts" ]; then
    printf '%s\n' "$counts" | sed -E 's/^[[:space:]]*([0-9]+)[[:space:]]+(.+)$/- \2: \1/'
  else
    print_kv "keywords" "none_in_last_300_log_lines"
  fi
else
  print_kv "keywords" "daemon_missing"
fi
