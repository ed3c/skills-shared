#!/usr/bin/env bash
# Owning suite for issue #411's two blocked prerequisites:
#
#   (a) a case graph bound to an exact committed implementation subject
#       references/case-graph-local-handoff-wave1.json @ a9db0bd9
#   (b) a migration/copy task fixture with a planted semantic-loss
#       decision-branch removal that a deterministic oracle can detect
#
# Runs both entrypoints against the real subject first, then plants three
# mutations on throwaway copies. Each mutation is asserted to have actually
# landed before its exit code is read: a control that did not plant proves
# nothing. The headline control is the first one -- on one set of bytes the
# compatibility oracle stays green while the parity oracle goes red, which is
# the #407 failure mode made executable.
#
# This suite produces fixture and committed-byte evidence only. It does not
# exercise the live #411 Shadow canary, which stays HUMAN_ADMIT_REQUIRED.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${here}/../.." && pwd)"
graph="${skill_dir}/references/case-graph-local-handoff-wave1.json"
export PYTHONDONTWRITEBYTECODE=1

tmp="$(mktemp -d "${TMPDIR:-/tmp}/spatial-loop-migration-canary.XXXXXXXX")"
trap 'rm -rf "${tmp}"' EXIT

# The graph must be internally closed, then bound to bytes that really exist.
python3 "${skill_dir}/scripts/check_case_graph.py" check "${graph}" || {
  echo "FAIL check_case_graph.py red on the committed case graph" >&2
  exit 2
}
python3 "${here}/case_graph_evidence.py" --graph "${graph}" || {
  echo "FAIL case_graph_evidence.py red on the real subject" >&2
  exit 2
}
python3 "${here}/migration_canary.py" || {
  echo "FAIL migration_canary.py red on the faithful migration arm" >&2
  exit 2
}

planted=0

# Copy a real file, plant one mutation on the copy, and refuse to continue
# unless the literal it was supposed to remove is actually gone.
plant() {
  local name="$1" src="$2" copy="$3" expr="$4" gone="$5"
  cp "${src}" "${copy}"
  perl -0pi -e "${expr}" "${copy}"
  if grep -Fq -- "${gone}" "${copy}"; then
    echo "FAIL ${name}: mutation did not plant; the control proves nothing" >&2
    exit 2
  fi
}

# Run one entrypoint, require an exact exit code, and require the named reason
# to appear in its output when one is given.
expect() {
  local name="$1" want_rc="$2" needle="$3"
  shift 3
  local out rc
  out="$("$@" 2>&1)"
  rc=$?
  if [ "${rc}" -ne "${want_rc}" ]; then
    echo "FAIL ${name}: exited ${rc}, expected ${want_rc}" >&2
    echo "${out}" >&2
    exit 2
  fi
  if [ -n "${needle}" ] && ! printf '%s' "${out}" | grep -Fq -- "${needle}"; then
    echo "FAIL ${name}: expected reason ${needle} in output" >&2
    echo "${out}" >&2
    exit 2
  fi
}

# 1. The migrated target keeps its interface and loses decision branch B.
#    Compatibility cannot see it; the differential parity oracle must.
mutant_target="${tmp}/target_decide_branch_removed.py"
plant branch-removal "${here}/fixtures/target_decide.py" "${mutant_target}" \
  's/    "SKIPPED_BY_POLICY": "HOLD_FOR_POLICY_REVIEW",\n//' \
  '"SKIPPED_BY_POLICY": "HOLD_FOR_POLICY_REVIEW"'
expect compat-stays-blind 0 'COMPAT GREEN' \
  python3 "${here}/migration_canary.py" --oracle compat --target "${mutant_target}"
expect parity-detects-branch-removal 2 \
  'PARITY_MISMATCH state=SKIPPED_BY_POLICY human_admit_required=False source=RETURN:HOLD_FOR_POLICY_REVIEW target=RETURN:BLOCK' \
  python3 "${here}/migration_canary.py" --oracle parity --target "${mutant_target}"
planted=$((planted + 1))
echo "CONTROL RED AS REQUIRED branch-removal (compat green, parity red on the same bytes)"

# 2. The graph's recorded content digest drifts from the committed bytes.
mutant_digest_graph="${tmp}/case-graph-digest-drift.json"
plant graph-digest-drift "${graph}" "${mutant_digest_graph}" \
  's/980fabaf8fd64d71fbc7bd5d94144568ece21c03f222b346a20c4573259f385e/00000000fd64d71fbc7bd5d94144568ece21c03f222b346a20c4573259f385ee/' \
  '980fabaf8fd64d71fbc7bd5d94144568ece21c03f222b346a20c4573259f385e'
expect graph-digest-drift 2 'CONTENT_DIGEST_DRIFT' \
  python3 "${here}/case_graph_evidence.py" --graph "${mutant_digest_graph}"
planted=$((planted + 1))
echo "CONTROL RED AS REQUIRED graph-digest-drift"

# 3. The graph claims the #464 Shadow lane was executed. The committed receipt
#    says NOT_EXERCISED, and the readback must side with the receipt.
mutant_lane_graph="${tmp}/case-graph-shadow-promotion.json"
plant readback-lane-promotion "${graph}" "${mutant_lane_graph}" \
  's{"pointer": "/lanes/shadow_readback", "equals": "NOT_EXERCISED"}{"pointer": "/lanes/shadow_readback", "equals": "PASS"}' \
  '"pointer": "/lanes/shadow_readback", "equals": "NOT_EXERCISED"'
expect readback-lane-promotion 2 'READBACK_MISMATCH ORACLE-RECEIPT-LANES' \
  python3 "${here}/case_graph_evidence.py" --graph "${mutant_lane_graph}"
planted=$((planted + 1))
echo "CONTROL RED AS REQUIRED readback-lane-promotion"

echo "MIGRATION COPY CANARY GREEN: case graph bound to a9db0bd9, ${planted} planted mutations refused; live #411 Shadow lane remains HUMAN_ADMIT_REQUIRED"
