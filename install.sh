#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/clong202603-star/bixia-shangchao.git"
SOURCE="${BASH_SOURCE[0]:-}"

if [[ -n "$SOURCE" && -f "$SOURCE" ]]; then
  ROOT="$(cd "$(dirname "$SOURCE")" && pwd)"
  exec python3 "$ROOT/install.py"
fi

TMP="$(mktemp -d)"
git clone --depth 1 "$REPO" "$TMP/repo"
exec python3 "$TMP/repo/install.py"
