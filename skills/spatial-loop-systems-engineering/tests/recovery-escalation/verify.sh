#!/usr/bin/env bash
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_root="$(cd "${here}/../.." && pwd)"
skill="${skill_root}/SKILL.md"
contract="${skill_root}/references/three-failure-escalation.md"
overlay="${skill_root}/references/system-prompt-recovery-overlay.md"

require_literal() {
  local file="$1"
  local literal="$2"
  grep -Fq -- "$literal" "$file" || {
    echo "FAIL missing required recovery contract text: $literal in ${file#"${skill_root}/"}" >&2
    exit 2
  }
}

# The universal entrypoint owns the escalation trigger and mandatory delegation.
# Forge/provider/Desktop implementation details remain decoupled in the recovery
# contract/overlay below rather than being duplicated in SKILL.md.
require_literal "$skill" "After three consecutive qualifying failures"
require_literal "$skill" "do not make a fourth blind patch"
require_literal "$skill" "references/three-failure-escalation.md"
require_literal "$skill" "forgejo-delivery-loop"
require_literal "$skill" "github-delivery-loop"
require_literal "$skill" "new isolated worktree"

# The dedicated recovery contract remains authoritative for the complete hard
# laws and routing semantics.
require_literal "$contract" "After **three consecutive qualifying failures**"
require_literal "$contract" "A fourth speculative patch in the same repair context is"
require_literal "$contract" "FRESH_DIAGNOSIS_HANDOFF_REQUIRED"
require_literal "$contract" "Forgejo issue"
require_literal "$contract" "GitHub Actions exception"
require_literal "$contract" "COMMIT_ELIGIBLE"
require_literal "$contract" "HUMAN_MERGE_BOUNDARY"

require_literal "$overlay" "do not make a fourth speculative"
require_literal "$overlay" "GitHub issue with workflow/run/job/head evidence"
require_literal "$overlay" "new ChatGPT Desktop question/session"
require_literal "$overlay" "owning oracle = PASS on exact repair subject"
require_literal "$overlay" "A green repair does not create merge authority"

if grep -Fq "three errors" "$skill"; then
  echo "FAIL retry trigger weakened from qualifying failures to arbitrary errors" >&2
  exit 2
fi

if grep -Fq "automatic merge to main" "$overlay"; then
  echo "FAIL recovery overlay silently grants merge authority" >&2
  exit 2
fi

echo "RECOVERY ESCALATION GREEN: universal trigger delegates to the decoupled recovery contract; forge routing, fresh diagnosis, worktree, verification, and merge boundaries are present"
