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
  "${skill_dir}/scripts/audit_crossstack_metric.py" \
  "${skill_dir}/scripts/crossstack_rubric.py"

for artifact in prompt-crossstack-preregistration prompt-crossstack-cases \
                prompt-crossstack-result prompt-crossstack-v2-preregistration \
                prompt-crossstack-v2-cases; do
  python3 -m json.tool "${skill_dir}/evals/${artifact}.json" >/dev/null
done

# The rubric scorer decides generation-2's rule metric, so it carries its own
# planted defects: a marker-only rubric and a self-contradicting one must both
# be refused, or the metric repair is a rename.
python3 "${skill_dir}/scripts/crossstack_rubric.py" --selftest

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

# Generation 2 is the repair, and these are the two properties it exists for: a
# constant verdict must lose, and a correct answer in the model's own words must
# score while a bare marker echo must not. Both are read off the committed case
# file and re-scored through the scorer the live runner uses.
python3 - "${skill_dir}" <<'PY'
import json, sys
from pathlib import Path
skill = Path(sys.argv[1])
sys.path.insert(0, str(skill / "scripts"))
from run_prompt_crossstack import rule_named

body = json.loads((skill / "evals" / "prompt-crossstack-v2-cases.json").read_text())
cases = body["cases"]
verdicts = [c["ground_truth"]["verdict"] for c in cases]
share = max(verdicts.count("ADMIT"), verdicts.count("REFUSE")) / len(verdicts)
assert share <= body["max_constant_verdict_share"], \
    f"a constant verdict scores {share:.3f}; the ceiling generation 1 died of is back"
assert body["rule_metric"] == "PARAPHRASE_RUBRIC"

refusals = [c for c in cases if c["ground_truth"]["verdict"] == "REFUSE"]
paraphrased = 0
for case in refusals:
    marker = case["ground_truth"]["violated_rule"]
    rubric = case["rule_rubric"]
    marker_words = {w for w in marker.split("-") if len(w) > 3}
    for phrasing in rubric["examples"]["accept"]:
        assert rule_named(marker, rubric, phrasing), \
            f"{case['case_id']}: the runner scores a declared-correct phrasing zero: {phrasing!r}"
        if not (marker_words & set(phrasing.lower().replace("-", " ").split())):
            paraphrased += 1
    for phrasing in rubric["examples"]["reject"]:
        assert not rule_named(marker, rubric, phrasing), \
            f"{case['case_id']}: the runner scores a declared-wrong phrasing: {phrasing!r}"
    assert any(marker_words & set(p.lower().replace("-", " ").split())
               for p in rubric["examples"]["reject"]), \
        f"{case['case_id']}: no rejected phrasing echoes the marker, so echo was never tested"

assert paraphrased >= len(refusals), \
    "not every refusal family has an accepted phrasing free of the checker's words"
print(f"PASS generation 2 instrument: constant verdict scores {share:.3f}, "
      f"{paraphrased} marker-free phrasings score across {len(refusals)} families")
PY

echo "PASS cross-stack held-out evaluation"
