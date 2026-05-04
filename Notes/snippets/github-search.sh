#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  Notes/snippets/github-search.sh status
  Notes/snippets/github-search.sh repos "agent memory llm" [limit]
  Notes/snippets/github-search.sh code "memory router" owner/repo [limit]
  Notes/snippets/github-search.sh issues "memory" owner/repo [limit]
  Notes/snippets/github-search.sh prs "eval" owner/repo [limit]

Requires:
  gh auth login

Output:
  JSON from GitHub CLI, suitable for Codex parsing.
EOF
}

find_gh() {
  if command -v gh >/dev/null 2>&1; then
    command -v gh
    return 0
  fi

  for candidate in /opt/homebrew/bin/gh /usr/local/bin/gh "$HOME/.local/bin/gh"; do
    if [[ -x "$candidate" ]]; then
      echo "$candidate"
      return 0
    fi
  done

  return 1
}

GH_BIN="$(find_gh || true)"

if [[ -z "$GH_BIN" ]]; then
  echo "gh is not installed. Install with: brew install gh" >&2
  exit 127
fi

if [[ "${1:-}" == "status" ]]; then
  "$GH_BIN" --version
  "$GH_BIN" auth status
  exit $?
fi

if ! "$GH_BIN" auth status >/dev/null 2>&1; then
  cat >&2 <<'EOF'
gh is installed but not authenticated.

Run:
  gh auth login

Recommended choices:
  GitHub.com
  HTTPS
  Login with a web browser

After login, test with:
  gh auth status
EOF
  exit 78
fi

kind="${1:-}"
query="${2:-}"

if [[ -z "$kind" || -z "$query" ]]; then
  usage >&2
  exit 2
fi

case "$kind" in
  repos)
    limit="${3:-20}"
    "$GH_BIN" search repos "$query" \
      --limit "$limit" \
      --json fullName,description,url,stargazersCount,language,updatedAt \
      --jq '.'
    ;;
  code)
    repo="${3:-}"
    limit="${4:-20}"
    if [[ -z "$repo" ]]; then
      echo "code search requires owner/repo." >&2
      usage >&2
      exit 2
    fi
    "$GH_BIN" search code "$query" \
      --repo "$repo" \
      --limit "$limit" \
      --json path,repository,url,textMatches \
      --jq '.'
    ;;
  issues)
    repo="${3:-}"
    limit="${4:-20}"
    if [[ -z "$repo" ]]; then
      echo "issue search requires owner/repo." >&2
      usage >&2
      exit 2
    fi
    "$GH_BIN" search issues "$query" \
      --repo "$repo" \
      --limit "$limit" \
      --json title,url,state,author,createdAt,updatedAt,labels \
      --jq '.'
    ;;
  prs)
    repo="${3:-}"
    limit="${4:-20}"
    if [[ -z "$repo" ]]; then
      echo "PR search requires owner/repo." >&2
      usage >&2
      exit 2
    fi
    "$GH_BIN" search prs "$query" \
      --repo "$repo" \
      --limit "$limit" \
      --json title,url,state,author,createdAt,updatedAt,labels \
      --jq '.'
    ;;
  *)
    echo "Unknown search kind: $kind" >&2
    usage >&2
    exit 2
    ;;
esac
