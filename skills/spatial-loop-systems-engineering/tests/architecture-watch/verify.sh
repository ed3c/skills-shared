#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
skill="$root/SKILL.md"
watch="$root/references/architecture-watch-loop.md"
monitor="$root/modes/monitor.md"
precheck="$root/modes/precheck.md"
postmortem="$root/modes/postmortem.md"

need() {
  grep -Fq -- "$2" "$1" || { echo "FAIL missing '$2' in ${1#"$root/"}" >&2; exit 2; }
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

if grep -Fq 'MONITOR requires the complete A–L packet before implementation' "$skill"; then
  echo 'FAIL MONITOR was degraded into blocking precheck' >&2
  exit 2
fi
if grep -Fq 'Shadow Architect owns implementation mutation' "$watch"; then
  echo 'FAIL Shadow Architect became a second writer' >&2
  exit 2
fi

echo 'ARCHITECTURE WATCH GREEN: exploration remains free, material deltas are monitored, first-green is reviewed, and high-risk boundaries can block'
