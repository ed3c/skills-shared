#!/usr/bin/env bash
# Controls for the #229 cross-stack artifacts.
#
# Zero network and no model. run_prompt_crossstack.py and build_crossstack_cases.py
# are compiled but never invoked here: one needs two provider binaries and real
# spend, the other regenerates the frozen case set, and a suite that does either
# is a suite that rewrites the evidence it is checking.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
checker="${skill_dir}/scripts/check_prompt_crossstack.py"

python3 -m py_compile \
  "${checker}" \
  "${skill_dir}/scripts/run_prompt_crossstack.py" \
  "${skill_dir}/scripts/build_crossstack_cases.py" \
  "${skill_dir}/scripts/audit_crossstack_metric.py"

for artifact in prompt-crossstack-preregistration prompt-crossstack-cases \
                prompt-crossstack-result; do
  python3 -m json.tool "${skill_dir}/evals/${artifact}.json" >/dev/null
done

python3 "${checker}" check
python3 "${checker}" selftest

# The finding this run exists for: every arm judged every refusal case correctly,
# so the rule-naming gap is vocabulary. If that ever stops being true the outcome
# has to be revisited, and a silent change here is the thing to catch.
python3 - "${skill_dir}/evals/prompt-crossstack-result.json" <<'PY'
import json, sys
body = json.load(open(sys.argv[1]))
audit = body["metric_audit"]
assert audit["verdict_correct_on_every_refusal_case_in_every_arm"] is True, \
    "an arm now gets a refusal case wrong; the INDETERMINATE reading rests on all of " \
    "them being right"
assert audit["cases_where_a_correct_answer_scored_no_token_hit"] is True, \
    "no correct answer scores zero any more; re-examine whether the metric is still lexical"
assert body["eligibility"]["outcome"] == "INDETERMINATE"

separating = [row["case_id"] for row in audit["per_case"]
              if len({arm["token_hit"] for arm in row["arms"].values()}) > 1]
print(f"PASS metric audit: verdicts unanimous, score separated only by "
      f"{separating or 'nothing'}")
PY

echo "PASS cross-stack held-out evaluation"
