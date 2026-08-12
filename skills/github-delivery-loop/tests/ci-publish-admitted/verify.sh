#!/usr/bin/env bash
# Prove the admitted entrypoint validates compact receipt shape before binding.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
skill_dir="$(cd "${test_dir}/../.." && pwd -P)"
producer="${skill_dir}/scripts/local_verification.py"
gate="${skill_dir}/scripts/ci_publish_admitted.py"
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

cat > "${scratch}/contract.json" <<'JSON'
{
  "schema": "github-delivery-local-verification-contract/v1",
  "repository_id": 1326262274,
  "inherit_env": ["PATH"],
  "commands": [{
    "id": "registry-json",
    "argv": ["python3", "-m", "json.tool", "registry.json"],
    "cwd": ".",
    "timeout_seconds": 10,
    "max_output_bytes": 4096
  }]
}
JSON
python3 "${producer}" verify \
  --repo-root "${repo}" \
  --contract "${scratch}/contract.json" \
  --repository-id 1326262274 \
  --receipt "${scratch}/verification.json" \
  --evidence "${scratch}/evidence.json"

cat > "${scratch}/snapshot.json" <<'JSON'
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
grep -q '"decision": "ALLOW"' "${scratch}/allow.json"

# Remove one compact field. The result must be a bounded invalid-policy-input,
# not a traceback and never an ALLOW.
python3 - "${scratch}/verification.json" "${scratch}/malformed.json" <<'PY'
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text())
value.pop("commands")
pathlib.Path(sys.argv[2]).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
PY
set +e
python3 "${gate}" evaluate \
  --repo-root "${repo}" \
  --snapshot "${scratch}/snapshot.json" \
  --verification "${scratch}/malformed.json" \
  --verification-evidence "${scratch}/evidence.json" \
  --intent initial-pr \
  --json >"${scratch}/malformed.out" 2>"${scratch}/malformed.err"
rc=$?
set -e
test "${rc}" -eq 64
grep -q "invalid-policy-input" "${scratch}/malformed.err"
! grep -q "Traceback" "${scratch}/malformed.err"

python3 "${gate}" --selftest
python3 -m py_compile "${gate}"

echo "PASS admitted publication entrypoint"
