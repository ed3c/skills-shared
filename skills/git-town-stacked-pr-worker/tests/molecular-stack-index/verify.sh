#!/usr/bin/env bash
# Zero-network controls for the Molecular Stack index.
#
# The defect these guard against is silent: an index that no longer describes
# the Stack still parses, still renders, and still reads as a plan.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(realpath "${test_dir}/../..")"
checker="${skill_dir}/scripts/assert_molecular_stack_index.py"
schema="${skill_dir}/references/molecular-stack-index.schema.json"
example="${skill_dir}/references/example-molecular-stack-index.json"

python3 -m json.tool "${schema}" >/dev/null
python3 -m json.tool "${example}" >/dev/null
python3 -m py_compile "${checker}"

# The schema is load-bearing, not decorative: it must accept the positive
# example that the semantic checker also accepts.
python3 -c "
import json, sys
from pathlib import Path
from jsonschema import Draft202012Validator

schema = json.loads(Path('${schema}').read_text(encoding='utf-8'))
Draft202012Validator.check_schema(schema)
errors = [
    f\"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}\"
    for error in Draft202012Validator(schema).iter_errors(
        json.loads(Path('${example}').read_text(encoding='utf-8'))
    )
]
if errors:
    print('FAIL: positive example does not satisfy molecular-stack-index.schema.json', file=sys.stderr)
    for error in errors:
        print(f'FAIL: {error}', file=sys.stderr)
    raise SystemExit(1)
print('PASS: molecular-stack-index.schema.json validated the positive example')
"

python3 "${checker}" --index "${example}"
python3 "${checker}" --index "${example}" --selftest

# A checker error is not an index failure: an absent index exits 64.
set +e
python3 "${checker}" --index "${test_dir}/absent-index.json" >/dev/null 2>&1
absent_code=$?
set -e
if [ "${absent_code}" -ne 64 ]; then
  echo "FAIL: absent index exited ${absent_code}, expected 64" >&2
  exit 1
fi

echo "PASS Git Town Molecular Stack index"
