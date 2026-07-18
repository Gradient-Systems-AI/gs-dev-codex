#!/usr/bin/env bash
# gs-dev plugin — install specialist subagents into the user's Codex agents dir,
# with each agent's MODEL chosen per its tier (L/M/S) from the models this Codex
# actually has. See resolve-models.py.
#
# Codex plugin manifests bundle skills/MCP/apps/hooks — but NOT custom subagents,
# so the gs-dev skills' named specialists (correctness-reviewer, implementer-l,
# verify, ...) must be placed in ~/.codex/agents/. This SessionStart hook does that
# once, idempotently, and is self-locating so it works from the plugin cache.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/../agents"
CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
DEST_DIR="$CODEX_DIR/agents"
CACHE="$CODEX_DIR/models_cache.json"

[ -d "$SRC_DIR" ] || { echo "gs-dev: no bundled agents dir at $SRC_DIR" >&2; exit 0; }
mkdir -p "$DEST_DIR"

# Preferred path: resolve per-tier models from the machine's model list.
if command -v python3 >/dev/null 2>&1 && [ -f "$CACHE" ]; then
  python3 "$SCRIPT_DIR/resolve-models.py" "$SRC_DIR" "$DEST_DIR" "$CACHE"
  exit 0
fi

# Fallback (no python3 or no model cache): plain copy. Agents keep their tier +
# reasoning effort and inherit the session model — still fully functional.
installed=0
for f in "$SRC_DIR"/*.toml; do
  [ -e "$f" ] || continue
  dest="$DEST_DIR/$(basename "$f")"
  if [ ! -f "$dest" ] || ! cmp -s "$f" "$dest"; then
    cp "$f" "$dest"; installed=$((installed + 1))
  fi
done
echo "gs-dev: installed/updated $installed agent(s) into $DEST_DIR (model inherits session — python3/models_cache not found for per-tier selection)"
exit 0
