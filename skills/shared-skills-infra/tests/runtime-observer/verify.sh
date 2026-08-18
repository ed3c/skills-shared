#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
test_root="${repo_root}/skills/shared-skills-infra/tests/runtime-observer"

python3 -m py_compile \
  "${repo_root}/skills/shared-skills-infra/scripts/observe_consumer_runtime.py" \
  "${test_root}/support.py" \
  "${test_root}/verify.py"
python3 -m json.tool \
  "${repo_root}/skills/shared-skills-infra/references/runtime-requirements.json" \
  >/dev/null
python3 \
  "${repo_root}/skills/shared-skills-infra/scripts/check_skill_requirements.py" \
  "${repo_root}/skills/shared-skills-infra/references/runtime-requirements.json"
python3 "${test_root}/verify.py"
