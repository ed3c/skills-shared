#!/usr/bin/env bash
# Owning suite for the proof-carrying refactor migration of this Skill (#352).
#
# Runs both proof entrypoints against the real tree, then proves each one can go
# red: a scorer that cannot fail is a green light with nothing behind it. Every
# mutation is planted on a throwaway copy of the Skill root, asserted to have
# actually landed, and required to exit 2 with a named reason.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "${here}/../.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1

python3 "${here}/refactor_ab.py" || {
  echo "FAIL refactor_ab.py red on the real tree" >&2
  exit 2
}
python3 "${here}/real_task_ab.py" || {
  echo "FAIL real_task_ab.py red on the real tree" >&2
  exit 2
}

tmp="$(mktemp -d "${TMPDIR:-/tmp}/spatial-loop-proof.XXXXXXXX")"
trap 'rm -rf "${tmp}"' EXIT

mutant=0
# name, entrypoint, file to mutate, perl expression, literal that must disappear
control() {
  local name="$1" entry="$2" target="$3" expr="$4" gone="$5" copy rc
  copy="${tmp}/${name}"
  rm -rf "${copy}"
  cp -R "${root}" "${copy}"
  perl -0pi -e "${expr}" "${copy}/${target}"
  if grep -Fq -- "${gone}" "${copy}/${target}"; then
    echo "FAIL ${name}: mutation did not plant; the control proves nothing" >&2
    exit 2
  fi
  python3 "${here}/${entry}" --skill-root "${copy}" >/dev/null 2>&1
  rc=$?
  if [ "${rc}" -ne 2 ]; then
    echo "FAIL ${name}: ${entry} exited ${rc}, expected 2" >&2
    exit 2
  fi
  mutant=$((mutant + 1))
  echo "CONTROL RED AS REQUIRED ${name}"
}

# A frozen historical treatment is edited instead of measured.
control frozen-treatment-drift refactor_ab.py \
  tests/refactor-proof/fixtures/pre-refactor-SKILL.txt \
  's/version: "1\.1\.0"/version: "1.1.1"/' \
  'version: "1.1.0"'

# The live body loses the law that an executed oracle outranks prose.
control live-body-loses-authority-law refactor_ab.py SKILL.md \
  's/never outrank an executed deterministic oracle/may outweigh an executed deterministic oracle/' \
  'never outrank an executed deterministic oracle'

# The live body keeps the word "qualifying" but loses the exclusion rule that
# decides whether ABSENT / NOT_EXERCISED / SKIPPED_BY_POLICY count as repairs.
# Match the semantic sentence rather than a historical Markdown line wrap.
control live-body-loses-qualifying-rule real_task_ab.py SKILL.md \
  's/`ABSENT`, `NOT_EXERCISED`, and `SKIPPED_BY_POLICY` are not failed repairs\./Other results are not failed repairs./' \
  '`ABSENT`, `NOT_EXERCISED`, and `SKIPPED_BY_POLICY` are not failed repairs.'

# The checker stops refusing a gate promoted above its capability evidence.
control checker-admits-promoted-gate real_task_ab.py \
  scripts/check_system_contract.py \
  's/    errors = validate_contract\(document\)/    errors = []/' \
  'errors = validate_contract(document)'

# The task fixture is retuned instead of the treatments being measured.
control task-fixture-drift real_task_ab.py \
  tests/refactor-proof/fixtures/attempts.json \
  's/"escalation_threshold": 3/"escalation_threshold": 2/' \
  '"escalation_threshold": 3'

echo "REFACTOR PROOF GREEN: 4 treatments scored, 1 matched hermetic task, ${mutant} planted mutations refused"
