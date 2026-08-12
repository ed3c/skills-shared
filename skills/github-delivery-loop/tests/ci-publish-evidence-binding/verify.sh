#!/usr/bin/env bash
# End-to-end zero-network control for the strict sidecar-bound publication gate.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
skill_dir="$(cd "${test_dir}/../.." && pwd -P)"
producer="${skill_dir}/scripts/local_verification.py"
gate="${skill_dir}/scripts/ci_publish_bound_gate.py"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

repo="${scratch}/repo"
mkdir -p "${repo}"
git -C "${repo}" init -q
git -C "${repo}" config user.name fixture
git -C "${repo}" config user.email fixture@example.invalid
printf '{}\n' > "${repo}/registry.json"
git -C "${repo}" add registry.json
git -C "${repo}" commit -qm fixture
head="$(git -C "${repo}" rev-parse HEAD)"

cat > "${scratch}/contract.json" <<'JSON'
{
  "schema": "github-delivery-local-verification-contract/v1",
  "repository_id": 1326262274,
  "inherit_env": ["PATH"],
  "commands": [
    {
      "id": "registry-json",
      "argv": ["python3", "-m", "json.tool", "registry.json"],
      "cwd": ".",
      "timeout_seconds": 10,
      "max_output_bytes": 4096
    }
  ]
}
JSON

python3 "${producer}" verify \
  --repo-root "${repo}" \
  --contract "${scratch}/contract.json" \
  --repository-id 1326262274 \
  --receipt "${scratch}/verification.json" \
  --evidence "${scratch}/evidence.json"

cat > "${scratch}/snapshot.json" <<JSON
{
  "schema": "github-actions-publish-snapshot/v1",
  "repository": {
    "full_name": "ed3c/skills-shared",
    "repository_id": 1326262274,
    "owner_login": "ed3c",
    "private": true
  },
  "pull_request": {
    "number": null,
    "state": "absent",
    "head_sha": null,
    "last_published_sha": null,
    "last_published_at": null,
    "feedback": null
  },
  "actions": {
    "circuit": "closed",
    "observed_at": null,
    "blocker": null,
    "latest_check": null
  }
}
JSON

python3 "${gate}" evaluate \
  --repo-root "${repo}" \
  --snapshot "${scratch}/snapshot.json" \
  --verification "${scratch}/verification.json" \
  --verification-evidence "${scratch}/evidence.json" \
  --intent initial-pr \
  --json > "${scratch}/allow.json"
python3 - "${scratch}/allow.json" "${head}" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert value["decision"] == "ALLOW"
assert value["reason"] == "allow-initial-pr"
assert value["head_sha"] == sys.argv[2]
assert value["operation"] == "push-and-create-draft-pr"
PY

# Missing sidecar is a usage/evidence failure, never an ALLOW.
if python3 "${gate}" evaluate \
  --repo-root "${repo}" \
  --snapshot "${scratch}/snapshot.json" \
  --verification "${scratch}/verification.json" \
  --verification-evidence "${scratch}/missing.json" \
  --intent initial-pr \
  --json >"${scratch}/missing.out" 2>"${scratch}/missing.err"; then
  echo "FAIL: missing evidence sidecar authorized publication" >&2
  exit 1
fi
grep -q "invalid-policy-input" "${scratch}/missing.err"

# One changed sidecar byte without a matching compact receipt must fail.
python3 - "${scratch}/evidence.json" "${scratch}/tampered.json" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
value["commands"][0]["stdout_bytes"] += 1
pathlib.Path(sys.argv[2]).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
PY
if python3 "${gate}" evaluate \
  --repo-root "${repo}" \
  --snapshot "${scratch}/snapshot.json" \
  --verification "${scratch}/verification.json" \
  --verification-evidence "${scratch}/tampered.json" \
  --intent initial-pr \
  --json >"${scratch}/tamper.out" 2>"${scratch}/tamper.err"; then
  echo "FAIL: tampered evidence authorized publication" >&2
  exit 1
fi
grep -q "invalid-policy-input" "${scratch}/tamper.err"

# A compact receipt cannot name an invented evidence digest.
python3 - "${scratch}/verification.json" "${scratch}/forged.json" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
value["evidence_sha256"] = "f" * 64
pathlib.Path(sys.argv[2]).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
PY
if python3 "${gate}" evaluate \
  --repo-root "${repo}" \
  --snapshot "${scratch}/snapshot.json" \
  --verification "${scratch}/forged.json" \
  --verification-evidence "${scratch}/evidence.json" \
  --intent initial-pr \
  --json >"${scratch}/forged.out" 2>"${scratch}/forged.err"; then
  echo "FAIL: forged compact receipt authorized publication" >&2
  exit 1
fi
grep -q "invalid-policy-input" "${scratch}/forged.err"

python3 "${gate}" --selftest
python3 -m py_compile "${gate}"

echo "PASS strict publication evidence binding"
