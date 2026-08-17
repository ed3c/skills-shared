#!/usr/bin/env bash
# Positive and negative controls for the Tech Lead plan compiler.
#
# The positive fixture is not written here. It is
# references/tech-lead-plan.example.json, the example the contract publishes,
# so a published example that stopped validating would fail this test rather
# than sit next to a green suite. Every negative variant is derived from that
# same file, which means each control differs from the admitted plan in exactly
# one named way.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL="$(cd "$HERE/../.." && pwd)"
SCRIPT="$SKILL/scripts/compile_tech_lead_plan.py"
EXAMPLE="$SKILL/references/tech-lead-plan.example.json"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/tmp.XXXXXXXX")"
trap 'rm -rf "$TMP"' EXIT

test -f "$EXAMPLE"
python3 -m py_compile "$SCRIPT"

python3 - "$EXAMPLE" "$TMP" <<'PY'
import copy, json, pathlib, sys

good = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
root = pathlib.Path(sys.argv[2])

variants = {"good": good}

overlap = copy.deepcopy(good)
overlap["tasks"][1]["allowed_paths"] = ["skills/repo-agent-native/scripts"]
variants["overlap"] = overlap

cycle = copy.deepcopy(good)
cycle["tasks"][0]["depends_on"] = ["tech-lead-planner"]
cycle["tasks"][1]["depends_on"] = ["blindspot-contract"]
variants["cycle"] = cycle

missing = copy.deepcopy(good)
missing["tasks"][0]["blindspot_queries"][0].update(
    {"lanes": ["grepai", "scip"], "readback_required": False})
variants["missing-readback"] = missing

fake = copy.deepcopy(good)
fake["tasks"][1].update({
    "stack_class": "child",
    "parent": "blindspot-contract",
    "depends_on": ["blindspot-contract"],
    "consumes_contracts": [],
})
variants["fake-child"] = fake

for name, value in variants.items():
    (root / f"{name}.json").write_text(json.dumps(value, indent=2) + "\n")
PY

python3 "$SCRIPT" verify --plan "$TMP/good.json" >"$TMP/good-result.json"
python3 "$SCRIPT" compile --plan "$TMP/good.json" --output "$TMP/compiled" >"$TMP/receipt.json"

test -f "$TMP/compiled/normalized-plan.json"
test -f "$TMP/compiled/compile-receipt.json"
test -f "$TMP/compiled/stack.dot"
test -f "$TMP/compiled/worker-packets/blindspot-contract.json"
test -f "$TMP/compiled/worker-packets/tech-lead-planner.json"
test -f "$TMP/compiled/worker-packets/convergence.json"

python3 - "$TMP/compiled/compile-receipt.json" "$TMP/compiled/worker-packets/tech-lead-planner.json" <<'PY'
import json, sys
receipt = json.load(open(sys.argv[1]))
packet = json.load(open(sys.argv[2]))
assert receipt['evidence_state'] == 'PASS' and receipt['runtime_state'] == 'NOT_EXERCISED'
assert receipt['effects'] == {'branches_created': False, 'worktrees_created': False,
                              'agents_spawned': False, 'providers_invoked': False,
                              'remote_publication': False}
assert packet['parent_branch'] == 'main'
assert 'blindspot-contract' in packet['parallel_safe_siblings']
assert packet['blindspot_queries'][0]['readback_required'] is True
PY

expect_fail() {
  local fixture="$1" expected="$2"
  set +e
  python3 "$SCRIPT" verify --plan "$fixture" >"$TMP/out" 2>"$TMP/err"
  local status=$?
  set -e
  test "$status" -eq 2
  grep -q "$expected" "$TMP/err"
}
expect_fail "$TMP/overlap.json" PATH_LEASE_COLLISION
expect_fail "$TMP/cycle.json" TASK_DAG_CYCLE
expect_fail "$TMP/missing-readback.json" BLINDSPOT_QUERY_INCOMPLETE
expect_fail "$TMP/fake-child.json" FAKE_LINEAR_CHILD

echo "tech-lead-plan contract PASS"
