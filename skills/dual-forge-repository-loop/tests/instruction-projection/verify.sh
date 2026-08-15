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
grep -Fq 'codex app <workspace-path>' "$repo/AGENTS.md"
grep -Fq 'deep-link composer text remains pending until the operator sends it' "$repo/AGENTS.md"
grep -Fq 'installed GitHub plugin or connector' "$repo/AGENTS.md"
grep -Fq 'cross-family models are reviewers rather than official truth authorities' "$repo/AGENTS.md"
test -f "$repo/.skill-bindings/instruction-projection.json"
test -f "$home/.claude/.skills-shared-projection-receipt.json"

# Repository projections must never inherit host home locators.
for path in \
  "$repo/AGENTS.md" \
  "$repo/CLAUDE.md" \
  "$repo/.skill-bindings/instruction-projection.json"
do
  if grep -Eq '(^|[^A-Za-z0-9_.-])~/|/Users/|/home/' "$path"; then
    echo "FAIL repository projection contains a host home locator: $path" >&2
    exit 1
  fi
done

# A source mutation that reintroduces a host path must turn the generator red.
mutated="$tmp/instruction-projection-mutated.json"
python3 - "$module" "$mutated" <<'PY'
from pathlib import Path
import json
import sys
source = Path(sys.argv[1])
target = Path(sys.argv[2])
data = json.loads(source.read_text(encoding="utf-8"))
data["hard_laws"].append(
    "A repository Agent must read global ~/.claude/CLAUDE.md before work."
)
target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
if python3 "$script" --module "$mutated" --canonical-commit "$commit" --mode write --repo-root "$tmp/mutated-repo" >/dev/null 2>&1; then
  echo 'FAIL source mutation with a host home locator was accepted' >&2
  exit 1
fi

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

echo 'PASS instruction projection positive + path hygiene + mutation + drift + preservation + cloud/local separation controls'
