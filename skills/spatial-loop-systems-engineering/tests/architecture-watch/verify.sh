#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
skill="$root/SKILL.md"
watch="$root/references/architecture-watch-loop.md"
overlay="$root/references/system-prompt-monitor-overlay.md"
packet="$root/references/spec-packet-template.md"
readme="$root/README.md"
monitor="$root/modes/monitor.md"
precheck="$root/modes/precheck.md"
postmortem="$root/modes/postmortem.md"

need() {
  grep -Fq -- "$2" "$1" || { echo "FAIL missing '$2' in ${1#"$root/"}" >&2; return 2; }
}

# Every surface that routes the monitor must carry the whole delta vocabulary
# and the whole question set; a surface that keeps only some of them narrows
# the monitor silently wherever a reader enters.
delta_tokens=(
  INTENT_INTERPRETATION_DELTA SCOPE_REDUCTION_DELTA USE_CASE_DELTA EDGE_CASE_DELTA
  SEMANTIC_PARITY_DELTA CASE_COVERAGE_DELTA CASE_ORACLE_DELTA SOURCE_BEHAVIOR_DISPOSITION_DELTA
)
# Stable fragments only: each surface phrases the questions slightly differently.
monitor_questions=(
  'made this path necessary?'
  'case covers it?'
  'Which semantic axis changed?'
  'silently narrow scope'
)
oracle_question='Which oracle .*loss'

watch_delta_surface() {
  local file="$1" needle
  for needle in "${delta_tokens[@]}" "${monitor_questions[@]}"; do
    grep -Fq -- "$needle" "$file" || return 2
  done
  grep -Eq -- "$oracle_question" "$file" || return 2
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
for surface in "$watch" "$overlay" "$packet" "$readme"; do
  watch_delta_surface "$surface" || {
    echo "FAIL delta vocabulary or monitor questions incomplete in ${surface#"$root/"}" >&2
    exit 2
  }
done

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
mutated = s.replace(
    "Use when a required case/oracle is missing, source-behavior disposition changed, or prompt interpretation narrowed semantics without authority.",
    "Prompt interpretation may narrow semantics and remain L0 when compatibility is green.",
)
# A replace that matched nothing would make the falsifier below pass vacuously.
if mutated == s:
    raise SystemExit("FAIL L0 mutation anchor absent; falsifier would pass vacuously")
p.write_text(mutated, encoding="utf-8")
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
mutated = s.replace(
    "Did compatibility remain green while semantic parity regressed?",
    "Compatibility green is sufficient; semantic parity need not be revisited.",
)
if mutated == s:
    raise SystemExit("FAIL FIRST_GREEN mutation anchor absent; falsifier would pass vacuously")
p.write_text(mutated, encoding="utf-8")
PY
if watch_case_contract "$tmp/watch-first-green.md" >/dev/null 2>&1; then
  echo 'FAIL FIRST_GREEN semantic-parity mutation remained green' >&2
  exit 2
fi
echo 'CONTROL RED AS REQUIRED semantic-drop-cannot-disappear-at-FIRST_GREEN'

# Negative control #409-C: every asserted token/question must be load-bearing on
# every surface that carries it. Strip one and that surface must turn red, so a
# grep that silently stopped matching cannot masquerade as coverage.
probe="$tmp/probe.md"
for surface in "$watch" "$overlay" "$packet" "$readme"; do
  rel="${surface#"$root/"}"
  for needle in "${delta_tokens[@]}" "${monitor_questions[@]}"; do
    if ! grep -Fv -- "$needle" "$surface" > "$probe"; then
      echo "FAIL probe emptied $rel while removing '$needle'" >&2
      exit 2
    fi
    if cmp -s "$surface" "$probe"; then
      echo "FAIL probe did not remove '$needle' from $rel" >&2
      exit 2
    fi
    if watch_delta_surface "$probe" >/dev/null 2>&1; then
      echo "FAIL '$needle' drift in $rel stayed green" >&2
      exit 2
    fi
  done
  if ! grep -Ev -- "$oracle_question" "$surface" > "$probe"; then
    echo "FAIL probe emptied $rel while removing the oracle question" >&2
    exit 2
  fi
  if cmp -s "$surface" "$probe"; then
    echo "FAIL probe did not remove the oracle question from $rel" >&2
    exit 2
  fi
  if watch_delta_surface "$probe" >/dev/null 2>&1; then
    echo "FAIL oracle-question drift in $rel stayed green" >&2
    exit 2
  fi
done
echo 'CONTROL RED AS REQUIRED delta-token-and-monitor-question-drift-on-every-surface'

echo 'ARCHITECTURE WATCH GREEN: exploration remains free, semantic drift cannot stay L0, FIRST_GREEN rechecks parity, and high-risk boundaries can block'
