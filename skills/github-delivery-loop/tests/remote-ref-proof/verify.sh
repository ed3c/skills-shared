#!/usr/bin/env bash
# Zero-network controls for exact remote-ref publication boundaries.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
skill_dir="$(cd "${test_dir}/../.." && pwd -P)"
producer="${skill_dir}/scripts/github_actions_snapshot_strict.py"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

python3 - "${scratch}" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
head = "1" * 40
base = {
  "schema": "github-actions-publish-observation/v1",
  "repository": {
    "full_name": "ed3c/skills-shared",
    "repository_id": 1326262274,
    "owner_login": "ed3c",
    "private": True
  },
  "branch": {"name": "feature", "head_sha": None},
  "pull_requests": [],
  "check_runs": [],
  "captured_at": "2026-08-12T05:02:00Z"
}
(root / "absent.json").write_text(json.dumps(base, indent=2, sort_keys=True) + "\n")
branch_only = json.loads(json.dumps(base)); branch_only["branch"]["head_sha"] = head
(root / "branch-only.json").write_text(json.dumps(branch_only, indent=2, sort_keys=True) + "\n")
pr = json.loads(json.dumps(base)); pr["branch"]["head_sha"] = head
pr["pull_requests"] = [{"number": 42, "draft": True, "head_sha": head, "updated_at": "2026-08-12T05:00:00Z"}]
(root / "pr.json").write_text(json.dumps(pr, indent=2, sort_keys=True) + "\n")
mismatch = json.loads(json.dumps(pr)); mismatch["branch"]["head_sha"] = "2" * 40
(root / "mismatch.json").write_text(json.dumps(mismatch, indent=2, sort_keys=True) + "\n")
PY

python3 "${producer}" replay \
  --observation "${scratch}/absent.json" \
  --check-name contract \
  --output "${scratch}/absent-snapshot.json"
grep -q '"state": "absent"' "${scratch}/absent-snapshot.json"

python3 "${producer}" replay \
  --observation "${scratch}/pr.json" \
  --check-name contract \
  --output "${scratch}/pr-snapshot.json"
grep -q '"state": "draft"' "${scratch}/pr-snapshot.json"

for fixture in branch-only mismatch; do
  if python3 "${producer}" replay \
    --observation "${scratch}/${fixture}.json" \
    --check-name contract \
    --output "${scratch}/${fixture}-snapshot.json" \
    >"${scratch}/${fixture}.out" 2>"${scratch}/${fixture}.err"; then
    echo "FAIL: ${fixture} produced a trusted publication snapshot" >&2
    exit 1
  fi
  grep -Eq "remote branch exists without an open PR|differs from exact remote branch ref" "${scratch}/${fixture}.err"
done

# Exercise the exact-ref HTTP 404 and encoded slash handling through a fake gh.
cat > "${scratch}/gh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
[ "$1" = api ]
case "$2" in
  *git/ref/heads/feature%2Fchild)
    cat <<'JSON'
{"ref":"refs/heads/feature/child","node_id":"fixture","url":"https://api.github.invalid/ref","object":{"sha":"1111111111111111111111111111111111111111","type":"commit","url":"https://api.github.invalid/commit"}}
JSON
    ;;
  *git/ref/heads/absent)
    echo 'gh: Not Found (HTTP 404)' >&2
    exit 1
    ;;
  *)
    echo "unexpected endpoint: $2" >&2
    exit 2
    ;;
esac
SH
chmod +x "${scratch}/gh"
PYTHONPATH="${skill_dir}/scripts" python3 - "${scratch}/gh" <<'PY'
import sys
import github_actions_snapshot_strict as strict
head = strict.exact_remote_ref("ed3c/skills-shared", "feature/child", sys.argv[1], 5)
assert head == "1" * 40
assert strict.exact_remote_ref("ed3c/skills-shared", "absent", sys.argv[1], 5) is None
PY

python3 "${producer}" --selftest
python3 -m py_compile "${producer}"

echo "PASS exact remote-ref publication proof"
