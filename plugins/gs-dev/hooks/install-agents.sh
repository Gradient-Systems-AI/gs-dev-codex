#!/usr/bin/env bash
# gs-dev plugin — install specialist subagents into the user's Codex agents dir.
#
# Codex plugin manifests bundle skills, MCP, apps, and hooks — but NOT custom
# subagents. The gs-dev skills spawn named specialists (correctness-reviewer,
# clarity-reviewer, implementer, verify, ...), which must live in ~/.codex/agents/.
# This SessionStart hook syncs the plugin's bundled agents there once, idempotently.
#
# Self-locating: resolves its own directory so it works whether Codex runs it from
# the plugin cache or the repo, regardless of cwd.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/../agents"
DEST_DIR="${CODEX_HOME:-$HOME/.codex}/agents"

[ -d "$SRC_DIR" ] || { echo "gs-dev: no bundled agents dir at $SRC_DIR" >&2; exit 0; }
mkdir -p "$DEST_DIR"

installed=0
for f in "$SRC_DIR"/*.toml; do
  [ -e "$f" ] || continue
  name="$(basename "$f")"
  dest="$DEST_DIR/$name"
  # Copy only if missing or changed, so we don't clobber user edits every session.
  if [ ! -f "$dest" ] || ! cmp -s "$f" "$dest"; then
    cp "$f" "$dest"
    installed=$((installed + 1))
  fi
done

if [ "$installed" -gt 0 ]; then
  echo "gs-dev: installed/updated $installed specialist agent(s) into $DEST_DIR"
fi
exit 0
