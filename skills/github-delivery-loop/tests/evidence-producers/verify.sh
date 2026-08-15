#!/usr/bin/env bash
# Positive and negative controls for exact-HEAD local evidence and trusted
# GitHub publication snapshots. Zero network.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
skill_dir="$(cd "${test_dir}/../.." && pwd -P)"
local_verify="${skill_dir}/scripts/local_verification.py"
snapshot="${skill_dir}/scripts/github_actions_snapshot.py"
fixtures="${test_dir}/fixtures"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

repo="${scratch}/repo"
mkdir -p "${repo}"
git -C "${repo}" init -q
git -C "${repo}" config user.name fixture
git -C "${repo}" config user.email fixture@example.invalid
printf 'value = 1\n' > "${repo}/fixture.py"
git -C "${repo}" add fixture.py
git -C "${repo}" commit -qm fixture

cp "${fixtures}/local/contract.json" "${scratch}/contract.json"
python3 "${local_verify}" verify \
  --repo-root "${repo}" \
  --contract "${scratch}/contract.json" \
  --repository-id 1326262274 \
  --receipt "${scratch}/verification.json" \
  --evidence "${scratch}/evidence.json"

python3 - "${scratch}/verification.json" "${scratch}/evidence.json" <<'PY'
import hashlib, json, pathlib, sys
receipt = json.loads(pathlib.Path(sys.argv[1]).read_text())
evidence = json.loads(pathlib.Path(sys.argv[2]).read_text())
assert receipt["schema"] == "github-delivery-local-verification/v1"
assert receipt["status"] == "PASS"
assert receipt["head_sha"] == evidence["head_sha"]
assert receipt["commands"] == ["syntax"]
canonical = json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
assert receipt["evidence_sha256"] == hashlib.sha256(canonical).hexdigest()
PY

printf 'dirty\n' > "${repo}/dirty.txt"
if python3 "${local_verify}" verify \
  --repo-root "${repo}" \
  --contract "${scratch}/contract.json" \
  --repository-id 1326262274 \
  --receipt "${scratch}/dirty-receipt.json" \
  --evidence "${scratch}/dirty-evidence.json" \
  >"${scratch}/dirty.out" 2>"${scratch}/dirty.err"; then
  echo "FAIL: dirty worktree received a verification receipt" >&2
  exit 1
fi
grep -q "working tree is dirty" "${scratch}/dirty.err"
rm "${repo}/dirty.txt"

python3 "${snapshot}" replay \
  --observation "${fixtures}/good/observation.json" \
  --check-name contract \
  --output "${scratch}/good-snapshot.json"
python3 - "${scratch}/good-snapshot.json" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert value["schema"] == "github-actions-publish-snapshot/v4"
assert value["branch"] == {"name": "feature", "head_sha": "1" * 40}
assert value["pull_request"]["feedback"]["id"] == "check-run:9001"
assert value["actions"]["latest_check"]["conclusion"] == "failure"
PY

python3 "${snapshot}" replay \
  --observation "${fixtures}/billing/observation.json" \
  --check-name contract \
  --output "${scratch}/billing-snapshot.json"
python3 - "${scratch}/billing-snapshot.json" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert value["actions"]["circuit"] == "billing-open"
assert value["actions"]["blocker"] == "billing-or-spending-limit"
assert value["actions"]["latest_check"] is None
PY

if python3 "${snapshot}" replay \
  --observation "${fixtures}/stale/observation.json" \
  --check-name contract \
  --output "${scratch}/stale-snapshot.json" \
  >"${scratch}/stale.out" 2>"${scratch}/stale.err"; then
  echo "FAIL: stale check observation produced a trusted snapshot" >&2
  exit 1
fi
grep -q "stale head" "${scratch}/stale.err"

# The strict lane. Without an independently observed ref these two
# observations are byte-identical apart from a field nothing reads, which is
# the defect #70 names: an absent pull request is not an absent branch.
python3 "${snapshot}" replay \
  --observation "${fixtures}/initial/observation.json" \
  --check-name contract --strict \
  --output "${scratch}/initial-snapshot.json"
python3 - "${scratch}/initial-snapshot.json" <<'PYEOF'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert value["initial_boundary"] == "trusted-initial", value["initial_boundary"]
assert value["pull_request"]["state"] == "absent"
PYEOF

if python3 "${snapshot}" replay \
  --observation "${fixtures}/orphan/observation.json" \
  --check-name contract --strict \
  --output "${scratch}/orphan-snapshot.json" \
  >"${scratch}/orphan.out" 2>"${scratch}/orphan.err"; then
  echo "FAIL: an orphaned remote branch passed as an initial publication" >&2
  exit 1
fi
grep -q "remote branch exists without an open pull request" "${scratch}/orphan.err"

# Lenient mode still replays it, but says so rather than claiming an initial
# boundary it cannot support.
python3 "${snapshot}" replay \
  --observation "${fixtures}/orphan/observation.json" \
  --check-name contract \
  --output "${scratch}/orphan-lenient.json"
python3 - "${scratch}/orphan-lenient.json" <<'PYEOF'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert value["initial_boundary"] == "branch-present-without-pr", value["initial_boundary"]
PYEOF

python3 "${local_verify}" --selftest
python3 "${snapshot}" --selftest

# The production capture CLI owns the canonical `gh` executable. Offline tests
# may replay fixture bytes, but cannot inject a fake provider executable and
# then call that provider provenance.
if python3 "${snapshot}" capture \
  --repository ed3c/example \
  --branch feature \
  --check-name contract \
  --gh "${scratch}/fake-gh" \
  --transport-output "${scratch}/actions-transport.json" \
  --output "${scratch}/captured-snapshot.json" \
  >"${scratch}/fake-gh.out" 2>"${scratch}/fake-gh.err"; then
  echo "FAIL: capture CLI accepted a caller-selected provider executable" >&2
  exit 1
fi
grep -q "unrecognized arguments: --gh" "${scratch}/fake-gh.err"

mkdir -p "${scratch}/fake-bin"
printf '#!/bin/sh\necho fake-gh\n' > "${scratch}/fake-bin/gh"
chmod +x "${scratch}/fake-bin/gh"
PATH="${scratch}/fake-bin:${PATH}" python3 - "${snapshot}" "${scratch}/fake-bin/gh" <<'PY'
import importlib.util, pathlib, sys
path = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("actions_snapshot_path_test", path)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
identity = module._gh_identity(5)
assert identity["invoked_path"] in module.GH_CANDIDATES
assert identity["invoked_path"] != sys.argv[2]
assert len(identity["sha256"]) == 64
PY

python3 - "${snapshot}" <<'PY'
import importlib.util, hashlib, json, pathlib, sys
path = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("actions_snapshot_test", path)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
empty = hashlib.sha256(b"").hexdigest()
transport = {
    "schema": module.TRANSPORT_SCHEMA,
    "producer": "github_actions_snapshot.py",
    "gh_executable": {
        "invoked_path": "/tmp/fake-gh", "resolved_path": "/tmp/fake-gh",
        "sha256": "3" * 64, "version": "gh version fake",
    },
    "repository": "ed3c/example",
    "branch": "feature",
    "check_name": "contract",
    "captured_at": "2026-08-14T10:05:00Z",
    "captures": [{
        "argv": ["/tmp/fake-gh", "api", "repos/ed3c/example"],
        "exit": 0,
        "stdout": "{}",
        "stdout_sha256": hashlib.sha256(b"{}").hexdigest(),
        "stderr": "",
        "stderr_sha256": empty,
    }],
}
try:
    module.observation_from_transport(transport)
except module.SnapshotError:
    pass
else:
    raise AssertionError("replay accepted non-canonical provider executable")
PY

echo "PASS GitHub Actions publication evidence producers"
