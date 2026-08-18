#!/usr/bin/env bash
# Install these skills as personal skills in ~/.claude/skills/.
#
# Only needed where /plugin is unavailable (e.g. the Claude Code desktop app).
# In a terminal session, `/plugin marketplace add lacasavita144-jpg/research-toolkit`
# is the better route and makes this script unnecessary.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$REPO/plugins/research-kit"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
LIB="$SRC/lib/zotero.py"

mkdir -p "$DEST"
for dir in "$SRC"/skills/*/; do
  name=$(basename "$dir")
  mkdir -p "$DEST/$name"
  for f in "$dir"*; do
    base=$(basename "$f")
    if [ "$base" = "SKILL.md" ]; then
      # Personal skills don't substitute ${CLAUDE_PLUGIN_ROOT}; point at this repo.
      sed "s|\${CLAUDE_PLUGIN_ROOT}/lib/zotero.py|$LIB|g" "$f" > "$DEST/$name/$base"
    else
      cp "$f" "$DEST/$name/$base"
    fi
  done
  echo "  synced /$name"
done
echo "Done. Start a new Claude Code session to load them."
