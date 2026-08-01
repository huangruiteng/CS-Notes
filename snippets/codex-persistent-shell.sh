#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: codex-persistent-shell.sh [--quiet]

Start a dedicated interactive zsh session that loads ~/.zshrc exactly once.
Use this only for a stateful command block that needs shared cwd, env vars,
aliases, shell functions, virtualenv/conda state, or other in-shell context.

Do not use this as the default for unrelated or parallel read-only commands.
Those should continue to use isolated shell invocations.
USAGE
}

quiet=0
case "${1:-}" in
  "")
    ;;
  --quiet)
    quiet=1
    shift
    ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    echo "Unknown argument: $1" >&2
    usage >&2
    exit 1
    ;;
esac

if [[ $# -ne 0 ]]; then
  usage >&2
  exit 1
fi

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/codex-persistent-zsh.XXXXXX")"
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT INT TERM

cat > "$tmpdir/.zshrc" <<'ZSHRC'
export ZDOTDIR="$HOME"

if [[ -z "${CODEX_PERSISTENT_SHELL_READY:-}" ]]; then
  export CODEX_PERSISTENT_SHELL_READY=1
  export CODEX_PERSISTENT_SHELL_INIT_PID="$$"
  export CODEX_PERSISTENT_SHELL_INIT_TS="$(date +%s)"

  source ~/.zshrc

  if [[ "${CODEX_PERSISTENT_SHELL_QUIET:-0}" != "1" ]]; then
    print -r -- "[codex-persistent-shell] initialized pid=$$ ts=$CODEX_PERSISTENT_SHELL_INIT_TS cwd=$PWD"
  fi
fi
ZSHRC

if [[ "$quiet" -eq 1 ]]; then
  export CODEX_PERSISTENT_SHELL_QUIET=1
fi

ZDOTDIR="$tmpdir" zsh -i
