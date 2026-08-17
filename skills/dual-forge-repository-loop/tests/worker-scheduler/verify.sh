#!/usr/bin/env bash
# Controls for the live multi-Worker scheduler receipt.
#
# Zero network and no Agent: this validates the receipt a live run produced, so
# it is runnable in CI where no model is reachable. The scheduler itself is also
# driven once with --skip-agent, which needs a writable temp tree and git but no
# model: without that, the only proof that the receipt the runner writes is one
# the checker admits would be a committed file neither of them touched since.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
checker="${skill_dir}/scripts/check_scheduler_receipt.py"
runner="${skill_dir}/scripts/run_worker_scheduler.py"
receipt="${skill_dir}/evals/receipts/scheduler-run.receipt.json"

python3 -m py_compile "${checker}" "${runner}"
python3 -m json.tool "${receipt}" >/dev/null

python3 "${checker}" check --receipt "${receipt}"
python3 "${checker}" selftest --receipt "${receipt}"

# The receipt must show a real multi-Worker shape, not one Worker run three
# times: at least two path-disjoint siblings and one convergence owner, each
# integrated behind its own oracle.
python3 - "${receipt}" <<'PY'
import json, sys
body = json.load(open(sys.argv[1]))
attempts = {a["attempt_id"]: a for a in body["attempts"]}
integrated = [t for t in body["transitions"] if t["state"] == "INTEGRATED"]
classes = [attempts[t["attempt_id"]].get("stack_class") for t in integrated]
assert classes.count("sibling") >= 2, f"expected two integrated siblings, got {classes}"
assert "convergence" in classes, f"no convergence owner integrated: {classes}"

leases = [set(attempts[t["attempt_id"]]["allowed_paths"]) for t in integrated
          if attempts[t["attempt_id"]].get("stack_class") == "sibling"]
for left in range(len(leases)):
    for right in range(left + 1, len(leases)):
        assert not (leases[left] & leases[right]), "integrated siblings shared a path"

verified = {t["attempt_id"] for t in body["transitions"] if t["state"] == "RESULT_VERIFIED"}
for transition in integrated:
    assert transition["attempt_id"] in verified, "an integration had no oracle"
print(f"PASS shape: {classes.count('sibling')} disjoint siblings + convergence, "
      f"{len(integrated)} integrated behind oracles")
PY

# The committed receipt predates the budget ledger, so its budget state is
# BUDGET_UNMEASURED and it stays that way -- a run that never measured its spend
# is not the same as a run that spent nothing, and no edit here may turn one into
# the other.
python3 - "${receipt}" <<'PY'
import json, sys
body = json.load(open(sys.argv[1]))
assert "budget_ledger" not in body, \
    "the committed live receipt gained a budget_ledger; a ledger it never recorded " \
    "is a retro-fit, not evidence"
assert not body.get("budgets_reconciled"), "an unmeasured run may not claim reconciliation"
active = [a["attempt_id"] for a in body["attempts"]
          if (a.get("lease") or {}).get("status") == "ACTIVE"]
assert not active, f"attempts still hold leases at close: {active}"
print("PASS historical receipt: budget BUDGET_UNMEASURED, no lease held at close")
PY

# Drive the scheduler itself without a model. This is the producer/checker
# boundary: the ledger the runner writes has to be one the checker reconciles,
# and a run that ends with a Worker still holding its lease has to come out red.
work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT
python3 "${runner}" --out "${work}" --skip-agent >"${work}/run.json"
python3 "${checker}" check --receipt "${work}/scheduler-run.receipt.json"
python3 - "${work}/scheduler-run.receipt.json" <<'PY'
import json, sys
body = json.load(open(sys.argv[1]))
ledger = body["budget_ledger"]
assert {e["attempt_id"] for e in ledger["attempts"]} == \
    {a["attempt_id"] for a in body["attempts"]}, "an attempt spent nothing on the record"
assert "wall_clock_seconds" not in ledger["unobserved_dimensions"], \
    "the one dimension this harness always measures came back unobserved"
assert set(ledger["unobserved_dimensions"]) == {"cost_usd", "tokens", "turns"}, \
    f"a model-free run reported model usage: {ledger['unobserved_dimensions']}"
for entry in ledger["attempts"]:
    for dimension in ledger["unobserved_dimensions"]:
        if dimension not in entry["observed"]:
            assert not entry["spend"][dimension], \
                f"{entry['attempt_id']} charges unobserved {dimension}"
print(f"PASS produced ledger: {len(ledger['attempts'])} attempts reconciled, "
      f"unobserved {', '.join(ledger['unobserved_dimensions'])}")
PY

echo "PASS live multi-Worker scheduler receipt"
