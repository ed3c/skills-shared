#!/usr/bin/env bash
# Controls for the live multi-Worker scheduler receipt.
#
# Zero network and no Agent: this validates the receipt a live run produced, so
# it is runnable in CI where no model is reachable. run_worker_scheduler.py is
# compiled here but never invoked -- running it needs a model, a writable temp
# tree and real minutes, and a suite that quietly needs those is a suite that
# gets skipped.
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

echo "PASS live multi-Worker scheduler receipt"
