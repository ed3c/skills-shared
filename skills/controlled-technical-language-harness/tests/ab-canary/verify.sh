#!/usr/bin/env bash
# Controls for the integrated A/B canary. The subject under test is the
# experiment's validity, not only its arithmetic: an unfair comparison produces
# the same shape of numbers as a fair one and reads better.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(realpath "${test_dir}/../..")"
scorer="${skill_dir}/scripts/score_ab.py"

python3 "${scorer}" --selftest
python3 -m py_compile "${scorer}"
python3 -m json.tool "${test_dir}/fixtures/good-run.json" >/dev/null
python3 -m json.tool "${test_dir}/fixtures/unfair-run.json" >/dev/null

# Shape gate. It answers only whether the bundle has the declared shape, and
# both committed bundles pass it -- the unfair one included, which is the
# point: a schema that also refused unfairness would let a reader believe the
# fairness question had been asked when only the shape had been checked.
# Executed as a deciding gate rather than pretty-printed, and required to
# refuse three planted shape defects, because a schema nobody validates against
# is documentation.
python3 - "${skill_dir}/references/controlled-language-ab-run.schema.json" \
         "${test_dir}/fixtures/good-run.json" \
         "${test_dir}/fixtures/unfair-run.json" <<'PY'
import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

schema = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
Draft202012Validator.check_schema(schema)
validator = Draft202012Validator(schema)

for name in sys.argv[2:]:
    body = json.loads(Path(name).read_text(encoding="utf-8"))
    errors = sorted(validator.iter_errors(body), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        where = "/".join(str(part) for part in first.absolute_path) or "<root>"
        print(f"FAIL: committed bundle {name} is not shape-valid: {where}: {first.message}",
              file=sys.stderr)
        raise SystemExit(1)

good = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))


def drop_evaluator_identities(bundle):
    del bundle["evaluator_identities"]


def unknown_root_field(bundle):
    bundle["uplift"] = 0.42


def untyped_lane(bundle):
    bundle["conditions"][0]["results"][0]["execution_lane"] = "SOMEWHERE_ELSE"


survivors = []
for plant in (drop_evaluator_identities, unknown_root_field, untyped_lane):
    mutated = copy.deepcopy(good)
    plant(mutated)
    if validator.is_valid(mutated):
        survivors.append(plant.__name__)
if survivors:
    print(f"FAIL: shape gate admitted planted defect(s): {', '.join(survivors)}", file=sys.stderr)
    raise SystemExit(1)
print("PASS controlled-language A/B bundle shape gate: 2 bundles valid, 3 planted defects refused")
PY

python3 "${scorer}" --bundle "${test_dir}/fixtures/good-run.json" >/dev/null

# The unfair bundle must be refused, and must emit no metric: a number computed
# from an invalid experiment reads as evidence.
set +e
unfair_output="$(python3 "${scorer}" --bundle "${test_dir}/fixtures/unfair-run.json" 2>&1)"
unfair_code=$?
set -e
if [ "${unfair_code}" -ne 2 ]; then
  echo "FAIL: unfair experiment exited ${unfair_code}, expected 2" >&2
  exit 1
fi
if ! grep -Fq "AB EXPERIMENT INVALID" <<<"${unfair_output}"; then
  echo "FAIL: unfair experiment was not named invalid" >&2
  exit 1
fi
if grep -Fq "deterministic_hard_gate_pass_rate" <<<"${unfair_output}"; then
  echo "FAIL: metrics were emitted for an invalid experiment" >&2
  exit 1
fi

# An unreadable bundle stays distinct from an invalid one.
work="$(mktemp -d "${TMPDIR:-/tmp}/work.XXXXXXXX")"
set +e
python3 "${scorer}" --bundle "${work}/absent.json" >/dev/null 2>&1
absent_code=$?
set -e
if [ "${absent_code}" -ne 64 ]; then
  echo "FAIL: absent bundle exited ${absent_code}, expected 64" >&2
  exit 1
fi

echo "PASS controlled-language integrated A/B canary"
