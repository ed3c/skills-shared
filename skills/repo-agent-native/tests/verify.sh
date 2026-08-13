#!/usr/bin/env sh
set -eu
skill_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python3 "$skill_root/scripts/check_repo_agent_native.py" --selftest
python3 "$skill_root/scripts/check_repo_agent_native.py" "$skill_root"
repo_root=$(CDPATH= cd -- "$skill_root/../.." && pwd)
python3 "$repo_root/evals/verifiers/verify_repo_agent_native_output.py" --selftest
