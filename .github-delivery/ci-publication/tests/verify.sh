#!/usr/bin/env bash
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
checker="${root}/.github-delivery/ci-publication/scripts/check_profile.py"

python3 "${checker}" --root "${root}"
python3 "${checker}" --selftest
python3 -m json.tool "${root}/.github-delivery/ci-publication/profile.json" >/dev/null
python3 -m json.tool "${root}/.github-delivery/ci-publication/local-verification.contract.json" >/dev/null
python3 -m py_compile "${checker}"

echo "PASS skills-shared CI publication profile controls"
