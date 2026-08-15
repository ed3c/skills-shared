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

require_literal "$skill" "Three-failure escalation law"
require_literal "$skill" "qualifying failed attempt"
require_literal "$skill" "GitHub Actions or"
require_literal "$skill" "forgejo-delivery-loop"
require_literal "$skill" "new ChatGPT Desktop question/session"
require_literal "$skill" "new isolated worktree/branch"

require_literal "$contract" "After **three consecutive qualifying failures**"
require_literal "$contract" "A fourth speculative patch in the same repair context is"
require_literal "$contract" "FRESH_DIAGNOSIS_HANDOFF_REQUIRED"
require_literal "$contract" "Forgejo issue"
require_literal "$contract" "GitHub Actions exception"
require_literal "$contract" "COMMIT_ELIGIBLE"
require_literal "$contract" "HUMAN_MERGE_BOUNDARY"
require_literal "$contract" "Neither action sends the prompt"
require_literal "$contract" "The submitted prompt must explicitly:"
require_literal "$contract" 'exact `owner/repo`'
require_literal "$contract" "installed GitHub plugin/connector"
require_literal "$contract" 'codex -C <existing-worktree-path>'
require_literal "$contract" "only after standard Git worktree path/HEAD verification"
require_literal "$contract" "Send / Submit was explicitly invoked"
require_literal "$contract" "the prompt appears in the conversation timeline, not the composer"
require_literal "$contract" "the assistant has started responding"
require_literal "$contract" "thread identity plus screenshot or equivalent UI observation is retained"
require_literal "$contract" "a populated input box must never be reported as dispatched"

require_literal "$overlay" "do not make a fourth speculative"
require_literal "$overlay" "GitHub issue with workflow/run/job/head evidence"
require_literal "$overlay" "new ChatGPT Desktop question/session"
require_literal "$overlay" "owning oracle = PASS on exact repair subject"
require_literal "$overlay" "A green repair does not create merge authority"
require_literal "$overlay" "do not send the prompt"
require_literal "$overlay" 'exact `owner/repo`'
require_literal "$overlay" "installed GitHub"
require_literal "$overlay" 'codex -C <existing-worktree-path>'
require_literal "$overlay" "Desktop submission requires a UI receipt"
require_literal "$overlay" "prefill alone is"

if grep -Fq "three errors" "$skill"; then
  echo "FAIL retry trigger weakened from qualifying failures to arbitrary errors" >&2
  exit 2
fi

if grep -Fq "automatic merge to main" "$overlay"; then
  echo "FAIL recovery overlay silently grants merge authority" >&2
  exit 2
fi

semantic_contract() {
  local candidate="$1"
  grep -Fq "The submitted prompt must explicitly:" "$candidate" || return 1
  grep -Fq "only after standard Git worktree path/HEAD verification" "$candidate" || return 1
  grep -Fq "Send / Submit was explicitly invoked" "$candidate" || return 1
  if grep -Fq "The submitted prompt may optionally:" "$candidate"; then
    return 1
  fi
  if grep -Fq "even without standard Git worktree path/HEAD verification" "$candidate"; then
    return 1
  fi
}

tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT
cp "$contract" "${tmp}/optional-prompt.md"
perl -0pi -e 's/The submitted prompt must explicitly:/The submitted prompt may optionally:/' "${tmp}/optional-prompt.md"
if semantic_contract "${tmp}/optional-prompt.md"; then
  echo "FAIL optional Desktop context mutation stayed green" >&2
  exit 2
fi
cp "$contract" "${tmp}/unproved-worktree.md"
perl -0pi -e 's/only after standard Git worktree path\/HEAD verification/even without standard Git worktree path\/HEAD verification/' "${tmp}/unproved-worktree.md"
if semantic_contract "${tmp}/unproved-worktree.md"; then
  echo "FAIL unproved CLI worktree mutation stayed green" >&2
  exit 2
fi
cp "$contract" "${tmp}/prefill-is-dispatch.md"
perl -0pi -e 's/Send \/ Submit was explicitly invoked/Composer prefill is sufficient/' "${tmp}/prefill-is-dispatch.md"
if semantic_contract "${tmp}/prefill-is-dispatch.md"; then
  echo "FAIL prefill-as-dispatch mutation stayed green" >&2
  exit 2
fi

echo "RECOVERY ESCALATION GREEN: three-failure, forge routing, submitted Desktop diagnosis, worktree, verification, merge boundaries, and 3 semantic mutations are present"
