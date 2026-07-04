#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/Users/bytedance/CS-Notes}"
WEB_MANAGER_HOST="${WEB_MANAGER_HOST:-127.0.0.1}"
WEB_MANAGER_PORT="${WEB_MANAGER_PORT:-5000}"
WEB_MANAGER_DEBUG="${WEB_MANAGER_DEBUG:-0}"

export REPO_ROOT WEB_MANAGER_HOST WEB_MANAGER_PORT WEB_MANAGER_DEBUG
export PYTHONUNBUFFERED=1
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

cd "$REPO_ROOT"
mkdir -p "$REPO_ROOT/.local/todos-web-manager/logs"

python3 - <<'PY'
import importlib.util
import sys

missing = [name for name in ("flask", "flask_cors") if importlib.util.find_spec(name) is None]
if missing:
    print(
        "Missing Python packages: "
        + ", ".join(missing)
        + "\nInstall with: python3 -m pip install -r .trae/web-manager/requirements.txt",
        file=sys.stderr,
    )
    raise SystemExit(78)
PY

exec python3 "$REPO_ROOT/.trae/web-manager/server.py"
