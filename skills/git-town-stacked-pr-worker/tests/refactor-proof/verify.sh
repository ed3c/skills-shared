#!/usr/bin/env bash
# Zero-network controls for the #270 refactor proof.
#
# The frozen treatments are historical evidence, not implementation: the
# entrypoint recomputes their Git blob identities on every run, so editing a
# treatment to improve its score turns this suite red instead of green.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(realpath "${test_dir}/../..")"
entrypoint="${test_dir}/refactor_ab.py"

python3 -m py_compile "${entrypoint}"

# The A/B comparison plus the matched hermetic task, then the planted controls
# that prove the entrypoint can refuse.
python3 "${entrypoint}" >/dev/null
python3 "${entrypoint}" --selftest

# The three treatments are exactly the bytes the registry pins. Recomputed here
# too, so a fixture rewritten without touching the entrypoint is still caught.
python3 - "${skill_dir}" <<'PY'
import hashlib
import sys
from pathlib import Path

expected = {
    "pre-refactor-SKILL.txt": "36d894d756ceca6d754b4c248b70680c7d199148",
    "refactor-as-landed-SKILL.txt": "714f1b0e3abb6d569f59c0eef18c09318d0886cf",
    "molecular-index-bound-SKILL.txt": "b06742db95cff1e43ed8eeae7db451012b3a2fb6",
}
fixtures = Path(sys.argv[1]) / "tests" / "refactor-proof" / "fixtures"
failed = False
for name, want in expected.items():
    raw = (fixtures / name).read_bytes()
    got = hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()
    if got != want:
        print(f"FAIL: {name} expected={want} observed={got}", file=sys.stderr)
        failed = True
if failed:
    raise SystemExit(1)
print(f"PASS: {len(expected)} frozen treatment(s) still hold their registered blobs")
PY

# A usage error is not a proof failure: an unknown flag exits 64.
set +e
python3 "${entrypoint}" --not-a-flag >/dev/null 2>&1
usage_code=$?
set -e
if [ "${usage_code}" -ne 64 ]; then
  echo "FAIL: unknown flag exited ${usage_code}, expected 64" >&2
  exit 1
fi

echo "PASS Git Town refactor proof (#270 treatments, matched hermetic task, 3 controls)"
