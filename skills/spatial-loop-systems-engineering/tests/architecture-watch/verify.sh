#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
skill="$root/SKILL.md"
watch="$root/references/architecture-watch-loop.md"
monitor="$root/modes/monitor.md"
precheck="$root/modes/precheck.md"
postmortem="$root/modes/postmortem.md"

need() {
  grep -Fq -- "$2" "$1" || { echo "FAIL missing '$2' in ${1#"$root/"}" >&2; return 2; }
}

watch_case_contract() {
  local file="$1"
  grep -Fq -- 'INTENT_INTERPRETATION_DELTA' "$file" || return 2
  grep -Fq -- 'SCOPE_REDUCTION_DELTA' "$file" || return 2
  grep -Fq -- 'SEMANTIC_PARITY_DELTA' "$file" || return 2
  grep -Fq -- 'SOURCE_BEHAVIOR_DISPOSITION_DELTA' "$file" || return 2
  grep -Fq -- 'Which existing or new case covers it?' "$file" || return 2
  grep -Fq -- 'Did this change silently narrow scope?' "$file" || return 2
  grep -Fq -- 'Use when a required case/oracle is missing, source-behavior disposition changed, or prompt interpretation narrowed semantics without authority.' "$file" || return 2
  grep -Fq -- 'source logic is being implicitly dropped' "$file" || return 2
  grep -Fq -- 'Did compatibility remain green while semantic parity regressed?' "$file" || return 2
  grep -Fq -- 'FIRST_GREEN` cannot erase an unresolved required case or `UNKNOWN_BLOCKING` member.' "$file" || return 2
}

need "$skill" 'default_mode: "MONITOR"'
need "$skill" 'allow the Builder to reason, design, implement, test, and refactor normally'
need "$skill" 'The Shadow Architect is not a second implementation writer.'
need "$skill" 'L0 OBSERVE'
need "$skill" 'L1 WARN'
need "$skill" 'L2 REVIEW'
need "$skill" 'L3 BLOCK'
need "$skill" 'FIRST_GREEN'
need "$skill" 'What did these tests not prove?'
need "$skill" 'A Level C/D task may never silently degrade into Level A implementation behavior.'
need "$watch" 'ASSUMPTION_DELTA'
need "$watch" 'EXTERNAL_SIDE_EFFECT_DELTA'
need "$watch" 'EVIDENCE_DELTA'
need "$watch" 'What became newly possible?'
need "$watch" 'FIRST_GREEN'
need "$monitor" 'Allow the Builder to explore, design, implement, test, and refactor normally.'
need "$precheck" 'high-risk or difficult to reverse'
need "$postmortem" 'Recover implicit architecture'
watch_case_contract "$watch" || {
  echo 'FAIL intent/case Shadow contract is incomplete' >&2
  exit 2
}

if grep -Fq 'MONITOR requires the complete A–L packet before implementation' "$skill"; then
  echo 'FAIL MONITOR was degraded into blocking precheck' >&2
  exit 2
fi
if grep -Fq 'Shadow Architect owns implementation mutation' "$watch"; then
  echo 'FAIL Shadow Architect became a second writer' >&2
  exit 2
fi

# Negative control #409-A: a silent semantic narrowing must not be allowed to
# remain L0. Plant the regression in the monitor contract and require the
# deciding contract check to turn red.
tmp="$(mktemp -d "${TMPDIR:-/tmp}/spatial-watch.XXXXXXXX")"
trap 'rm -rf "$tmp"' EXIT
cp "$watch" "$tmp/watch-l0.md"
python3 - "$tmp/watch-l0.md" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
s = s.replace(
    "Use when a required case/oracle is missing, source-behavior disposition changed, or prompt interpretation narrowed semantics without authority.",
    "Prompt interpretation may narrow semantics and remain L0 when compatibility is green.",
)
p.write_text(s, encoding="utf-8")
PY
if watch_case_contract "$tmp/watch-l0.md" >/dev/null 2>&1; then
  echo 'FAIL semantic-narrowing mutation remained L0' >&2
  exit 2
fi
echo 'CONTROL RED AS REQUIRED silent-semantic-drop-cannot-remain-L0'

# Negative control #409-B: FIRST_GREEN may not erase semantic-parity review.
cp "$watch" "$tmp/watch-first-green.md"
python3 - "$tmp/watch-first-green.md" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
s = s.replace(
    "Did compatibility remain green while semantic parity regressed?",
    "Compatibility green is sufficient; semantic parity need not be revisited.",
)
p.write_text(s, encoding="utf-8")
PY
if watch_case_contract "$tmp/watch-first-green.md" >/dev/null 2>&1; then
  echo 'FAIL FIRST_GREEN semantic-parity mutation remained green' >&2
  exit 2
fi
echo 'CONTROL RED AS REQUIRED semantic-drop-cannot-disappear-at-FIRST_GREEN'

echo 'ARCHITECTURE WATCH GREEN: exploration remains free, semantic drift cannot stay L0, FIRST_GREEN rechecks parity, and high-risk boundaries can block'
