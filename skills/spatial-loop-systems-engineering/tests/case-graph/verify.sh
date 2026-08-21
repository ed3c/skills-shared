#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${here}/../.." && pwd)"
skill="${skill_dir}/SKILL.md"

# Canonical entry must reach the ICPG reference, checker, semantic-loss law and monitor delta.
grep -Fq 'references/intent-case-proof-graph.md' "${skill}"
grep -Fq 'scripts/check_case_graph.py' "${skill}"
grep -Fq 'Prompt-brevity non-suppression law' "${skill}"
grep -Fq 'SOURCE_BEHAVIOR_DISPOSITION_DELTA' "${skill}"
grep -Fq 'compatibility test does not prove copied decision logic' "${skill}"

python3 "${skill_dir}/scripts/check_case_graph.py" check "${here}/fixtures/good.json"
python3 "${here}/verify.py"
