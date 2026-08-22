#!/usr/bin/env bash
# Deterministic, zero-network suite for the dual-track-code-review-loop consumer
# bootstrap (issue #527, as repaired). Discovered unconditionally by
# skills/shared-skills-infra/tests/run-all.sh, which globs tests/*/verify.sh.
set -eEuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"
python3 -m py_compile \
  skills/shared-skills-infra/scripts/consumer_bootstrap_dtcr.py \
  skills/shared-skills-infra/scripts/consumer_bootstrap_common.py \
  skills/shared-skills-infra/scripts/consumer_bootstrap_receipt.py \
  skills/shared-skills-infra/scripts/consumer_bootstrap_routes.py \
  skills/shared-skills-infra/tests/consumer-bootstrap-dtcr/support.py \
  skills/shared-skills-infra/tests/consumer-bootstrap-dtcr/verify.py
python3 -m json.tool skills/shared-skills-infra/references/repository-control-plane-profile.v1.schema.json >/dev/null
python3 -m json.tool skills/shared-skills-infra/references/repository-control-plane-profile.dual-track-code-review-loop.json >/dev/null
python3 skills/shared-skills-infra/scripts/consumer_bootstrap_dtcr.py --help >/dev/null

# The committed production profile must validate against the schema it claims to
# conform to; its subject pin must resolve as real ancestry against the exact
# commit named in the #527 repair; it must compose the shared bootstrap family
# without ever reaching `repository_control_plane` (whose `validate_profile`
# hard-fails on any non-default Skill closure); and it must declare no unmerged
# candidate source.
python3 - <<'PY'
import ast
import json
import subprocess

import jsonschema

root = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
).stdout.strip()
schema = json.load(open(f"{root}/skills/shared-skills-infra/references/repository-control-plane-profile.v1.schema.json"))
profile = json.load(open(f"{root}/skills/shared-skills-infra/references/repository-control-plane-profile.dual-track-code-review-loop.json"))
jsonschema.Draft202012Validator(schema).validate(profile)

assert profile["profile"] == "dual-track-code-review-loop", profile["profile"]
assert "dual-track-code-review-loop" in profile["skills"], profile["skills"]

pin = profile["subject_pin"]
assert pin["main_commit"] == "5341885f26b5e8e7baf5087a4d661e324f878242", pin["main_commit"]
assert pin["candidate_commit"] == pin["main_commit"], "this profile declares no unmerged candidate source"
assert pin["owned_tree_path"] == "skills/dual-track-code-review-loop", pin["owned_tree_path"]

observed_tree = subprocess.run(
    ["git", "-C", root, "rev-parse", f"{pin['main_commit']}:{pin['owned_tree_path']}"],
    capture_output=True, text=True, check=True,
).stdout.strip()
assert observed_tree == pin["owned_tree"], f"owned_tree drifted: {observed_tree} != {pin['owned_tree']}"

head = subprocess.run(
    ["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
).stdout.strip()
ancestor = subprocess.run(
    ["git", "-C", root, "merge-base", "--is-ancestor", pin["main_commit"], head], check=False
)
assert ancestor.returncode == 0, "pinned main_commit is not an ancestor of this checkout's HEAD"

catalogue = subprocess.run(
    ["git", "-C", root, "cat-file", "-t", f"{pin['main_commit']}:skills/dual-track-code-review-loop/references/prompts/README.md"],
    capture_output=True, text=True, check=False,
)
assert catalogue.returncode == 0 and catalogue.stdout.strip() == "blob", (
    "the pinned canonical prompt catalogue is absent at the pinned commit"
)

# Zero occurrences of `repository_control_plane` in the module's executable
# source. The module docstring is excluded on purpose: it explains WHY that
# import is refused, and an explanation is not a dependency.
module = open(f"{root}/skills/shared-skills-infra/scripts/consumer_bootstrap_dtcr.py").read()
docstring = ast.get_docstring(ast.parse(module), clean=False) or ""
assert docstring, "the dtcr module lost its docstring"
assert "repository_control_plane" not in module.replace(docstring, "", 1), (
    "the dtcr module must never import or reference repository_control_plane"
)

print("DTCR-PROFILE-PIN-OK schema-valid, main+owned_tree byte-exact, catalogue pinned, no repository_control_plane")
PY

python3 skills/shared-skills-infra/tests/consumer-bootstrap-dtcr/verify.py
echo "PASS dual-track-code-review-loop consumer bootstrap"
