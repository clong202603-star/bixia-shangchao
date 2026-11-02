#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/clong202603-star/ai-task-done.git"
SOURCE="${BASH_SOURCE[0]:-}"

if [[ -n "$SOURCE" && -f "$SOURCE" ]]; then
  ROOT="$(cd "$(dirname "$SOURCE")" && pwd)"
  exec python3 "$ROOT/install.py"
fi

TMP="$(mktemp -d)"
git clone --depth 1 "$REPO" "$TMP/ai-task-done"
exec python3 "$TMP/ai-task-done/install.py"
