#!/usr/bin/env bash
# Controls for the #225 executed baseline and the #238 frozen rerun.
#
# Zero network and no model. run_prompt_baseline.py is exercised only through
# --dry-run: the real mode spends fifteen paid sessions, and a suite that spends
# money is a suite nobody runs.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
checker="${skill_dir}/scripts/check_prompt_baseline.py"
runner="${skill_dir}/scripts/run_prompt_baseline.py"
frozen="${skill_dir}/evals/prompt-baseline-v2-preregistration.json"
work="$(mktemp -d "${TMPDIR:-/tmp}/prompt-baseline-XXXXXX")"
trap 'rm -rf "${work}"' EXIT

python3 -m py_compile "${checker}" "${runner}"

for artifact in prompt-baseline-preregistration prompt-baseline-cases \
                prompt-baseline-result prompt-baseline-v2-preregistration; do
  python3 -m json.tool "${skill_dir}/evals/${artifact}.json" >/dev/null
done

python3 "${checker}" check
python3 "${checker}" selftest

# The rerun's whole claim is that its rule-naming mean is comparable with the
# executed run's. That holds only while the case set, the scorer, the repetition
# count and the two baseline arms are literally the same objects, so compare them
# rather than trusting the prose that says they are.
python3 - "${skill_dir}" <<'PY'
import json, sys
from pathlib import Path
evals = Path(sys.argv[1]) / "evals"
old = json.loads((evals / "prompt-baseline-preregistration.json").read_text())
new = json.loads((evals / "prompt-baseline-v2-preregistration.json").read_text())

assert new["supersedes"]["preregistration_id"] == old["preregistration_id"]
assert new["case_set"] == old["case_set"] | {"why_this_task": new["case_set"]["why_this_task"]}, \
    "the rerun no longer holds the executed run's case set; its numbers are not comparable"
assert new["design"]["repetitions_per_arm"] == old["design"]["repetitions_per_arm"]
assert new["runtime"]["identity"] == old["runtime"]["identity"]
assert new["runtime"]["carrier"] == old["runtime"]["carrier"]
assert new["eligibility_threshold"]["rule"] == old["eligibility_threshold"]["rule"]

by_arm = {arm["arm"]: arm for arm in new["arms"]}
for shared in ("NO_PROMPT", "CURRENT_REPOSITORY_PROMPT"):
    was = next(arm for arm in old["arms"] if arm["arm"] == shared)
    is_ = by_arm[shared]
    assert is_["prompt_bytes"] == was["prompt_bytes"], f"{shared} changed size between runs"
    assert is_["prompt_commit"] == was["prompt_commit"], f"{shared} changed commit between runs"
    assert (was["prompt_sha256"] is None
            or is_["prompt_sha256"].startswith(was["prompt_sha256"])), \
        f"{shared} changed bytes between runs"
print(f"PASS comparability: same case set, same scorer, same "
      f"{new['design']['repetitions_per_arm']} repetitions, same two baseline arms")
PY

# The runner writes the eligibility block the checker recomputes. Replay it over
# the committed cells: it has to reproduce the executed run's own block, or the
# next result would disagree with history for a reason nothing recorded.
python3 - "${skill_dir}" <<'PY'
import json, sys
from pathlib import Path
skill = Path(sys.argv[1])
sys.path.insert(0, str(skill / "scripts"))
from run_prompt_baseline import eligibility

prereg = json.loads((skill / "evals" / "prompt-baseline-preregistration.json").read_text())
result = json.loads((skill / "evals" / "prompt-baseline-result.json").read_text())
derived = eligibility(prereg, result["cells"])
recorded = result["eligibility"]
for field in ("rule_naming_accuracy", "verdict_accuracy", "strongest_baseline",
              "regression_against_strongest_baseline", "outcome"):
    assert derived[field] == recorded[field], \
        f"{field}: runner derives {derived[field]!r}, the executed run recorded {recorded[field]!r}"
print(f"PASS eligibility derivation: reproduces the executed run's "
      f"{recorded['outcome']} from its cells")
PY

# The runner resolves each arm from the commit it pins and refuses to start when
# the bytes moved. Both designs must resolve, and the refusal must be reachable:
# a pin nothing recomputes is a pin that cannot fail.
python3 "${runner}" --output "${work}/dry-executed" --dry-run >"${work}/dry-executed.log"
python3 "${runner}" --output "${work}/dry-frozen" --dry-run \
  --preregistration "${frozen}" >"${work}/dry-frozen.log"
grep -q "DRY-RUN COMPLETE" "${work}/dry-executed.log"
grep -q "DRY-RUN COMPLETE" "${work}/dry-frozen.log"

python3 - "${frozen}" "${work}/drifted.json" <<'PY'
import json, sys
body = json.loads(open(sys.argv[1]).read())
for arm in body["arms"]:
    if arm["arm"].startswith("CANDIDATE"):
        arm["prompt_sha256"] = "0" * 64
open(sys.argv[2], "w").write(json.dumps(body))
PY
set +e
python3 "${runner}" --output "${work}/dry-drifted" --dry-run \
  --preregistration "${work}/drifted.json" >/dev/null 2>"${work}/drifted.err"
drift_exit=$?
set -e
test "${drift_exit}" -eq 64 || {
  echo "FAIL: a drifted candidate pin exited ${drift_exit}, expected 64" >&2
  exit 1
}
grep -q "prompt-drift" "${work}/drifted.err"
echo "PASS runner pin gate: both designs resolve, a drifted pin refuses with exit 64"

echo "PASS prompt baseline designs"
