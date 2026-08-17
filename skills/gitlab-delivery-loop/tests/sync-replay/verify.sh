#!/usr/bin/env bash
# Offline replay of one snapshot through sync, then through the check gate.
# Zero network: the only external process is git, against a scratch repository
# created here -- which is exactly what the export-tree binding needs, because
# GitLab publishes no root tree sha for the remote head.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
delivery="${skill_dir}/scripts/gitlab_delivery.py"
scratch="$(mktemp -d "${TMPDIR:-/tmp}/scratch.XXXXXXXX")"
trap 'rm -rf "${scratch}"' EXIT

work="${scratch}/work"
mkdir -p "${work}/artifact"
printf 'materialized small-loop output\n' > "${work}/artifact/output.txt"
printf 'MIT\n' > "${work}/LICENSE"
printf '# portable loop\n' > "${work}/README.md"

git init -q "${work}"
git -C "${work}" add -A
git -C "${work}" -c user.email=t@example.com -c user.name=t commit -q -m "export"
head="$(git -C "${work}" rev-parse HEAD)"
tree="$(git -C "${work}" rev-parse 'HEAD^{tree}')"

sed "s/REPLACED_HEAD_SHA/${head}/" "${test_dir}/fixtures/snapshot.json" \
  > "${work}/snapshot.json"

cat > "${work}/registry.json" <<'JSON'
{
  "schema": "gitlab-delivery-registry/v1",
  "repo_root": ".",
  "lines": [
    {
      "id": "portable-loop",
      "gitlab_host": "gitlab.com",
      "gitlab_project": "example/infrastructure/portable-loop",
      "gitlab_project_id": 34675721,
      "artifact_path": "artifact",
      "receipt_path": "receipt.json",
      "publication_path": "publication.json"
    }
  ]
}
JSON

sync_once() {  # sync_once <export-tree-sha> <out>
  python3 "${delivery}" sync \
    --registry "${work}/registry.json" --line portable-loop \
    --snapshot "${work}/snapshot.json" \
    --metrics "${work}/metrics.json" --dashboard "${work}/dashboard.md" \
    --export-source-commit "${head}" --export-tree-sha "$1" \
    --export-repo "${work}" > "$2"
}

# 1. the verified tree is the tree the remote head points at -> no blockers
sync_once "${tree}" "${scratch}/sync.out"
grep -q "SYNCED portable-loop" "${scratch}/sync.out"
if grep -q "BLOCKER" "${scratch}/sync.out"; then
  echo "FAIL: aligned export reported blockers" >&2
  cat "${scratch}/sync.out" >&2
  exit 1
fi

# 2. what sync writes must survive the zero-network gate it feeds
python3 "${delivery}" check --registry "${work}/registry.json"

# 3. event-derived metrics, not restated registry values
python3 - "${work}/metrics.json" <<'PY'
import json, sys
metrics = json.load(open(sys.argv[1]))
slices = {item["issue_iid"]: item for item in metrics["slices"]}
assert set(slices) == {2, 3, 6}, slices.keys()
# blocked label added 01:00, removed 03:00
assert slices[3]["blocked_seconds"] == 7200, slices[3]["blocked_seconds"]
assert slices[3]["reopened"] is True
# `Closes #2` / `Resolves #3` accept their slices
assert slices[2]["accepted_mr"] == 4, slices[2]
assert slices[3]["accepted_mr"] == 5, slices[3]
# `Part of #6` is a start marker, not a closing keyword: MR !7 merged, yet slice
# !6 was never accepted. Treating "part of" as closing would flip both of these.
assert slices[6]["started_mr"] == 7, slices[6]
assert slices[6]["accepted_mr"] is None, slices[6]
assert metrics["summary"]["accepted_slices"] == 2
assert metrics["summary"]["closed_without_merge"] == 1
assert abs(metrics["quality"]["reopen_rate"] - 1 / 3) < 1e-9
# GitLab cannot produce a first-pass rate: absence must be explicit, not zero
assert metrics["quality"]["first_pass_rate"] is None
assert metrics["quality"]["first_pass_rate_absent"]
print("metrics OK")
PY

# 4. receipt URLs carry GitLab's /-/ separator and merge_requests noun
grep -q -- "/-/merge_requests/4" "${work}/receipt.json"
grep -q -- "/-/issues/1" "${work}/receipt.json"

# 5. drift: a tree that is not the remote head's tree is a blocker, not a pass.
#    GitHub compares tree ids over the wire; GitLab exposes none, so the binding
#    is resolved locally -- it must still fail closed.
sync_once "0000000000000000000000000000000000000000" "${scratch}/drift.out"
grep -q "BLOCKER export-tree-drift" "${scratch}/drift.out"

# 5b. a board URL that does not resolve is an exit, not a nameless placeholder:
#     a receipt pointing at a board nobody has is a green receipt for an absent
#     artifact. Pure function, so it is testable without touching the network.
python3 - "${skill_dir}/scripts" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from gitlab_sync import SyncError, resolve_board

boards = [{"id": 5, "name": "Development", "lists": []}]
ok = resolve_board("gitlab.com", "g/s/p", "https://gitlab.com/g/s/p/-/boards/5", boards, [])
assert ok["name"] == "Development", ok

for url, cause in [
    ("https://gitlab.com/g/s/p/-/boards/9", "no board 9"),
    ("https://gitlab.com/other/project/-/boards/5", "points at project"),
    ("https://gitlab.com/g/s/p/-/issues/5", "board_url must be"),
    ("https://github.com/g/p/projects/5", "board_url must be"),
]:
    try:
        resolve_board("gitlab.com", "g/s/p", url, boards, [])
    except SyncError as error:
        assert cause in str(error), (url, str(error))
    else:
        raise AssertionError(f"unresolvable board URL accepted: {url}")
print("board resolution OK")
PY

# 6. a remote head this clone has never seen proves nothing about any tree
sed "s/${head}/$(printf 'a%.0s' {1..40})/" "${work}/snapshot.json" \
  > "${work}/snapshot.unknown.json"
mv "${work}/snapshot.unknown.json" "${work}/snapshot.json"
sync_once "${tree}" "${scratch}/unknown.out"
grep -q "BLOCKER remote-head-unverifiable" "${scratch}/unknown.out"

echo "PASS gitlab sync replay"
