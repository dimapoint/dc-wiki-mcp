#!/bin/bash
# Cloud sessions: uv new enough for Python 3.14.7, deps, the dump (from this repo's release) and data/dcdb.sqlite.
# Idempotent: each step is skipped when its result already exists.
set -euo pipefail
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
cd "$CLAUDE_PROJECT_DIR"

RELEASE=https://github.com/dimapoint/dc-wiki-mcp/releases/download/data-dump-2026-09-20/endcdatabase_pages_current.xml.7z
XML=data/raw/endcdatabase_pages_current.xml

# The preinstalled uv (0.8) doesn't know Python 3.14.7; pip's is newer and lives in /usr/local/bin.
if ! uv python install -q "$(cat .python-version)" 2>/dev/null; then
  pip install -q -U uv
  export PATH="/usr/local/bin:$PATH"
  echo 'export PATH="/usr/local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
  uv python install -q "$(cat .python-version)"
fi
uv sync -q

if [ ! -f data/dcdb.sqlite ]; then
  if [ ! -f "$XML" ]; then
    command -v 7z >/dev/null || apt-get install -y -qq 7zip >/dev/null
    mkdir -p data/raw
    curl -sSfL -o data/raw/dump.xml.7z "$RELEASE"
    7z e -y -odata/raw data/raw/dump.xml.7z >/dev/null
    rm data/raw/dump.xml.7z
  fi
  uv run python -m dcdb.ingest >&2
fi
