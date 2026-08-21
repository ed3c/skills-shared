#!/usr/bin/env bash
set -eEuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"
python3 -m py_compile \
  skills/shared-skills-infra/scripts/consumer_bootstrap_ghpc.py \
  skills/shared-skills-infra/scripts/consumer_bootstrap_common.py \
  skills/shared-skills-infra/scripts/consumer_bootstrap_receipt.py \
  skills/shared-skills-infra/scripts/consumer_bootstrap_routes.py \
  skills/shared-skills-infra/tests/consumer-bootstrap-ghpc/support.py \
  skills/shared-skills-infra/tests/consumer-bootstrap-ghpc/verify.py
python3 -m json.tool skills/shared-skills-infra/references/repository-control-plane-profile.v1.schema.json >/dev/null
python3 -m json.tool skills/shared-skills-infra/references/repository-control-plane-profile.github-portfolio-control.json >/dev/null
python3 -m json.tool skills/shared-skills-infra/references/portfolio-stub.v1.schema.json >/dev/null
python3 skills/shared-skills-infra/scripts/consumer_bootstrap_ghpc.py --help >/dev/null

# The committed production profile must itself validate against the schema it
# claims to conform to, and its subject pin must resolve as real ancestry
# against the exact commits named in issue #559 (main and the ghpc tree are
# checked byte-for-byte here; the not-yet-merged candidate is only asserted
# reachable, since it deliberately lives on a branch that is not this
# checkout's own history).
python3 - <<'PY'
import json
import subprocess
import sys

import jsonschema

root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
schema = json.load(open(f"{root}/skills/shared-skills-infra/references/repository-control-plane-profile.v1.schema.json"))
profile = json.load(open(f"{root}/skills/shared-skills-infra/references/repository-control-plane-profile.github-portfolio-control.json"))
jsonschema.Draft202012Validator(schema).validate(profile)

pin = profile["subject_pin"]
assert pin["main_commit"] == "28f394785aa8b13c4e6d2f21ad74c5e32a6a6dc5", pin["main_commit"]
assert pin["owned_tree"] == "795de8e9ada4d0927f9a792760232ef75dda84e4", pin["owned_tree"]
assert pin["candidate_commit"] == "aad3ff0728b9519615b63be80c225389005bfc1d", pin["candidate_commit"]

observed_tree = subprocess.run(
    ["git", "-C", root, "rev-parse", f"{pin['main_commit']}:{pin['owned_tree_path']}"],
    capture_output=True, text=True, check=True,
).stdout.strip()
assert observed_tree == pin["owned_tree"], f"owned_tree drifted: {observed_tree} != {pin['owned_tree']}"

candidate_type = subprocess.run(
    ["git", "-C", root, "cat-file", "-t", pin["candidate_commit"]],
    capture_output=True, text=True, check=False,
)
assert candidate_type.returncode == 0 and candidate_type.stdout.strip() == "commit", (
    "pinned candidate_commit is not a reachable commit in this checkout's object database"
)
ancestor = subprocess.run(
    ["git", "-C", root, "merge-base", "--is-ancestor", pin["main_commit"], pin["candidate_commit"]],
    check=False,
)
assert ancestor.returncode == 0, "pinned main_commit is not an ancestor of the pinned candidate_commit"

print("PROFILE-PIN-OK schema-valid main+owned_tree byte-exact, candidate reachable and descends from main")
PY

python3 skills/shared-skills-infra/tests/consumer-bootstrap-ghpc/verify.py
echo "PASS github-portfolio-control consumer bootstrap"
