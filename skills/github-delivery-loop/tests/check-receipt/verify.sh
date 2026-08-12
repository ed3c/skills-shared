#!/usr/bin/env bash
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(dirname "$(dirname "$test_dir")")"
checker="$skill_dir/scripts/github_delivery.py"
good="$test_dir/fixtures/good/registry.json"
hollow="$test_dir/fixtures/hollow/registry.json"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

python3 "$checker" check --registry "$good"

if python3 "$checker" check --registry "$hollow" >"$scratch/hollow.out" 2>"$scratch/hollow.err"; then
  echo "hollow fixture unexpectedly passed" >&2
  exit 1
fi
grep -q "UNMATERIALIZED portable-loop" "$scratch/hollow.err"

# A repository can legitimately grow a second PRD for a later product line.
# Keep this delivery line pinned to its existing receipt PRD instead of
# guessing from a title search.
python3 - "${skill_dir}/scripts/delivery_sync.py" <<'PY'
import importlib.util
import sys
from pathlib import Path

path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("delivery_sync", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
now = "2026-08-09T12:00:00Z"

def issue(number, title, state):
    return {
        "number": number,
        "title": title,
        "state": state,
        "created_at": now,
        "closed_at": now if state == "CLOSED" else None,
        "events": [],
        "labels": [],
    }

snapshot = {
    "schema": module.SNAPSHOT_SCHEMA,
    "fetched_at": now,
    "issues": [issue(1, "PRD: original delivery", "CLOSED"), issue(4, "PRD: next product", "OPEN")],
    "pulls": [],
    "project": {"url": "https://github.com/users/example/projects/1", "title": "p", "status_counts": {}},
    "repository": {
        "id": "R_fixture",
        "full_name": "example/repository",
        "license_spdx": "MIT",
        "history_root": True,
        "tree_sha": "2" * 40,
        "head_sha": "3" * 40,
        "file_count": 1,
        "url": "https://github.com/example/repository",
        "visibility": "PUBLIC",
    },
}
receipt, _publication, _metrics, _dashboard = module.build_outputs(
    line={"id": "fixture", "github_repository_id": "R_fixture"},
    snapshot=snapshot,
    export_source_commit="1" * 40,
    export_tree_sha="2" * 40,
    repo_root=Path("."),
    expected_prd_issue_url="https://github.com/example/repository/issues/1",
)
assert receipt["prd_issue_url"].endswith("/issues/1")
assert receipt["issue_urls"] == ["https://github.com/example/repository/issues/4"]
PY
