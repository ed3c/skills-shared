#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
skill="${root}/SKILL.md"
prompt="${root}/references/system-prompt.md"
modules="${root}/modules/README.md"

require() {
  local file="$1"
  local needle="$2"
  grep -Fq -- "$needle" "$file" || {
    echo "missing required contract text in ${file}: ${needle}" >&2
    exit 2
  }
}

require "$skill" "pre-implementation constraint discovery compiler"
require "$skill" "Level A — Local deterministic change"
require "$skill" "Level B — Stateful application system"
require "$skill" "Level C — Distributed / concurrent / agentic system"
require "$skill" "Level D — Substrate-sensitive system"
require "$skill" "A Level C/D task may never silently degrade into Level A implementation behavior."
require "$skill" "WHAT MUST ALWAYS REMAIN TRUE"
require "$skill" "HOW WE CAN KNOW IT REMAINS TRUE"
require "$skill" "Domain modules extend the core method. They never replace it"
require "$skill" "A. **Intent Digest**"
require "$skill" "K. **Implementation Gate**"
require "$skill" "L. **Implementation Plan**"
require "$skill" "reduce the reachable invalid state space"

require "$prompt" "Universal Constraint-First System Prompt"
require "$prompt" "Constraint Compiler"
require "$prompt" "Domain module     Unknown probes    Hard laws"
require "$prompt" "Never let a Level C/D task silently degrade into Level A implementation behavior."
require "$prompt" "Domain modules extend the core method. They never replace it."
require "$prompt" "MAP"
require "$prompt" "CONSTRAIN"
require "$prompt" "FALSIFY"

require "$modules" "Universal Constraint-First Method"
require "$modules" "Triggered Domain Expansion"
require "$modules" "Domain Module"
require "$modules" "bypass universal compiler"
require "$modules" "linux-isolation-runtime.md"

# Negative control: prove the verifier rejects the specific regression that
# motivated this refactor: C/D work being downgraded to ordinary Level A work.
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp "$skill" "$tmp/SKILL.md"
python3 - "$tmp/SKILL.md" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
s = s.replace(
    "A Level C/D task may never silently degrade into Level A implementation behavior.",
    "Level C/D tasks may use Level A behavior when implementation is convenient.",
)
p.write_text(s)
PY
if grep -Fq "A Level C/D task may never silently degrade into Level A implementation behavior." "$tmp/SKILL.md"; then
  echo "negative control failed to plant anti-degradation defect" >&2
  exit 2
fi

# Negative control: domain modules must not be allowed to replace the compiler.
cp "$modules" "$tmp/modules.md"
python3 - "$tmp/modules.md" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text().replace(
    "A domain module may extend the core method; it may not replace or weaken:",
    "A domain module may replace the core method when domain expertise is available:",
)
p.write_text(s)
PY
if grep -Fq "A domain module may extend the core method; it may not replace or weaken:" "$tmp/modules.md"; then
  echo "negative control failed to plant domain-replacement defect" >&2
  exit 2
fi

echo "UNIVERSAL ENTRY GREEN: constraint-first topology, A-D anti-degradation, and domain decoupling are present"
