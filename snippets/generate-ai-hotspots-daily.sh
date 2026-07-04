#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/Users/bytedance/CS-Notes}"
CODEX_BIN="${CODEX_BIN:-/Applications/Codex.app/Contents/Resources/codex}"
CODEX_TIMEOUT_SECONDS="${CODEX_TIMEOUT_SECONDS:-1200}"
AI_HOTSPOTS_NOTIFY="${AI_HOTSPOTS_NOTIFY:-1}"

REPORT_DIR="$REPO_ROOT/.local/ai-hotspots/reports"
LOG_DIR="$REPO_ROOT/.local/ai-hotspots/logs"
TODAY="$(date +%F)"
RUN_ID="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="$LOG_DIR/ai-hotspots-$RUN_ID.log"
SUMMARY_FILE="$REPORT_DIR/ai-daily-$TODAY.summary.md"
REPORT_FILE="$REPORT_DIR/ai-daily-$TODAY.html"
LOCK_DIR="$LOG_DIR/.generate-ai-hotspots.lock"
START_EPOCH="$(date +%s)"

mkdir -p "$REPORT_DIR" "$LOG_DIR"

exec >>"$LOG_FILE" 2>&1

notify() {
  if [[ "$AI_HOTSPOTS_NOTIFY" != "1" ]]; then
    return 0
  fi
  local title="$1"
  local message="$2"
  /usr/bin/osascript -e "display notification \"${message//\"/\\\"}\" with title \"${title//\"/\\\"}\"" >/dev/null 2>&1 || true
}

echo "[$(date '+%F %T')] start ai-hotspots daily generation"
echo "repo=$REPO_ROOT"
echo "codex=$CODEX_BIN"
echo "timeout_seconds=$CODEX_TIMEOUT_SECONDS"

if [[ ! -x "$CODEX_BIN" ]]; then
  echo "Codex binary not found or not executable: $CODEX_BIN"
  notify "AI 日报生成失败" "Codex binary 不可执行，查看日志：$LOG_FILE"
  exit 1
fi

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  LOCK_PID=""
  if [[ -f "$LOCK_DIR/pid" ]]; then
    LOCK_PID="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
  fi
  if [[ -n "$LOCK_PID" ]] && kill -0 "$LOCK_PID" 2>/dev/null; then
    echo "Another ai-hotspots generation is already running: $LOCK_DIR pid=$LOCK_PID"
    exit 0
  fi
  echo "Removing stale ai-hotspots lock: $LOCK_DIR"
  rm -rf "$LOCK_DIR"
  mkdir "$LOCK_DIR"
fi
echo "$$" > "$LOCK_DIR/pid"
trap 'rm -rf "$LOCK_DIR"' EXIT

cd "$REPO_ROOT"

if [[ "${FORCE_AI_HOTSPOTS:-0}" != "1" && -s "$REPORT_FILE" ]]; then
  REPORT_SIZE="$(wc -c < "$REPORT_FILE" | tr -d ' ')"
  if [[ "$REPORT_SIZE" -gt 1000 ]]; then
    echo "Fresh daily report already exists; skip generation: $REPORT_FILE"
    notify "AI 日报已存在" "今日 AI 日报已生成：$REPORT_FILE"
    exit 0
  fi
fi

PROMPT=$(cat <<'PROMPT'
Use $ai-hotspots to produce today's bilingual AI daily report in HTML.

Requirements:
- Browse current sources and pick the best 10 AI items.
- Save the report to .local/ai-hotspots/reports/ai-daily-YYYY-MM-DD.html.
- Keep any report, logs, and private material candidates under .local/.
- Do not modify public notes unless a material is clearly high-value and the existing skill instructions require it.
- This is an automated macOS launchd run; do not ask follow-up questions. Prefer a best-effort report with unread/access-blocked notes.
PROMPT
)

set +e
"$CODEX_BIN" exec \
  --cd "$REPO_ROOT" \
  --sandbox danger-full-access \
  -c approval_policy=\"never\" \
  --output-last-message "$SUMMARY_FILE" \
  "$PROMPT" &
CODEX_PID=$!

CODEX_STATUS=0
while kill -0 "$CODEX_PID" 2>/dev/null; do
  NOW_EPOCH="$(date +%s)"
  if (( NOW_EPOCH - START_EPOCH >= CODEX_TIMEOUT_SECONDS )); then
    echo "Codex run exceeded ${CODEX_TIMEOUT_SECONDS}s; terminating pid=$CODEX_PID"
    kill "$CODEX_PID" 2>/dev/null || true
    sleep 10
    if kill -0 "$CODEX_PID" 2>/dev/null; then
      echo "Codex pid still alive after SIGTERM; sending SIGKILL"
      kill -9 "$CODEX_PID" 2>/dev/null || true
    fi
    wait "$CODEX_PID" 2>/dev/null
    CODEX_STATUS=124
    break
  fi
  sleep 5
done

if [[ "$CODEX_STATUS" -eq 0 ]]; then
  wait "$CODEX_PID"
  CODEX_STATUS=$?
fi
set -e

REPORT_MTIME=0
if [[ -f "$REPORT_FILE" ]]; then
  REPORT_MTIME="$(stat -f %m "$REPORT_FILE" 2>/dev/null || echo 0)"
fi

if [[ "$CODEX_STATUS" -ne 0 ]]; then
  if [[ -s "$REPORT_FILE" && "$REPORT_MTIME" -ge "$START_EPOCH" ]]; then
    echo "Codex exited with status $CODEX_STATUS after writing report; treating as partial success"
    notify "AI 日报已生成" "报告已写入：$REPORT_FILE"
  else
    echo "Codex failed with status $CODEX_STATUS and no fresh report was written"
    notify "AI 日报生成失败" "未生成新报告，查看日志：$LOG_FILE"
    exit "$CODEX_STATUS"
  fi
fi

echo "[$(date '+%F %T')] finished ai-hotspots daily generation"
echo "report=$REPORT_FILE"
echo "summary=$SUMMARY_FILE"
notify "AI 日报已生成" "报告已写入：$REPORT_FILE"
