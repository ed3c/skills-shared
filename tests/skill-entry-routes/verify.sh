#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
python3 scripts/check_skill_entry_routes.py --selftest
for skill in $(python3 - <<'PY'
import json
for name in json.load(open('evals/skill-entry-routes.json'))['skills']:
    print(name)
PY
); do
  python3 scripts/check_skill_entry_routes.py --skill "${skill}" --print-index >/dev/null
done
echo 'PASS executable Skill mechanism navigation'
