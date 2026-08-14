#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
skill="$root/skills/dual-forge-repository-loop"
script="$skill/scripts/sync_instruction_projections.py"
module="$skill/references/instruction-projection.json"
commit="1111111111111111111111111111111111111111"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
repo="$tmp/repo"
home="$tmp/home"
mkdir -p "$repo" "$home/.claude"
printf '# Repo-specific rules\n\nKEEP_ME\n' > "$repo/AGENTS.md"
printf '# Claude adapter\n\nKEEP_CLAUDE_RULE\n' > "$repo/CLAUDE.md"
printf '# Global Claude\n\nKEEP_GLOBAL_RULE\n' > "$home/.claude/CLAUDE.md"

python3 "$script" --module "$module" --canonical-commit "$commit" --mode write --repo-root "$repo" --include-global --global-claude "$home/.claude/CLAUDE.md"
python3 "$script" --module "$module" --canonical-commit "$commit" --mode check --repo-root "$repo" --include-global --global-claude "$home/.claude/CLAUDE.md"

grep -q KEEP_ME "$repo/AGENTS.md"
grep -q KEEP_CLAUDE_RULE "$repo/CLAUDE.md"
grep -q KEEP_GLOBAL_RULE "$home/.claude/CLAUDE.md"
test -f "$repo/.skill-bindings/instruction-projection.json"
test -f "$home/.claude/.skills-shared-projection-receipt.json"

# Managed content drift must fail closed.
python3 - "$repo/AGENTS.md" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
p.write_text(s.replace('One mutable branch has one active writer', 'One mutable branch MAY have many writers', 1))
PY
if python3 "$script" --module "$module" --canonical-commit "$commit" --mode check --repo-root "$repo" >/dev/null 2>&1; then
  echo 'FAIL mutated AGENTS projection was accepted' >&2
  exit 1
fi

# Re-sync repairs only the managed block and preserves repo-owned text.
python3 "$script" --module "$module" --canonical-commit "$commit" --mode write --repo-root "$repo" >/dev/null
python3 "$script" --module "$module" --canonical-commit "$commit" --mode check --repo-root "$repo" >/dev/null
grep -q KEEP_ME "$repo/AGENTS.md"

# Stale canonical commit must fail.
if python3 "$script" --module "$module" --canonical-commit "2222222222222222222222222222222222222222" --mode check --repo-root "$repo" >/dev/null 2>&1; then
  echo 'FAIL stale canonical commit was accepted' >&2
  exit 1
fi

# Cloud-style repo check must not require or claim global home state.
rm -f "$home/.claude/CLAUDE.md" "$home/.claude/.skills-shared-projection-receipt.json"
python3 "$script" --module "$module" --canonical-commit "$commit" --mode check --repo-root "$repo" >/dev/null

echo 'PASS instruction projection positive + drift + preservation + cloud/local separation controls'
