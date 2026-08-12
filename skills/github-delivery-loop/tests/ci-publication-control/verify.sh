#!/usr/bin/env bash
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

python3 -m unittest "$test_dir/test_control.py" -v

mkdir -p "$scratch/repo/.github/workflows" "$scratch/repo/.github-delivery"
git -C "$scratch/repo" init -q
git -C "$scratch/repo" remote add github git@github.com:ed3c/example.git
cp "$test_dir/fixtures/verify.yml" "$scratch/repo/.github/workflows/verify.yml"
cp "$test_dir/fixtures/policy.json" "$scratch/repo/.github-delivery/ci-policy.json"
printf 'ok\n' > "$scratch/repo/README.md"
git -C "$scratch/repo" add .
git -C "$scratch/repo" -c user.name=Test -c user.email=test@example.invalid commit -qm 'test fixture'

python3 "$skill_dir/scripts/ci_publish.py" verify \
  --repo-root "$scratch/repo" > "$scratch/verify.out"
grep -F 'PASS local-verification' "$scratch/verify.out"

receipt="$(git -C "$scratch/repo" rev-parse --git-path github-delivery/local-verification.json)"
case "$receipt" in
  /*) ;;
  *) receipt="$scratch/repo/$receipt" ;;
esac
python3 - "$receipt" "$scratch/snapshot.json" <<'PY'
import json
import sys
from pathlib import Path

receipt = json.loads(Path(sys.argv[1]).read_text())
snapshot = {
    "schema": "github-ci-publish-snapshot/v1",
    "repository": "ed3c/example",
    "repository_owner": "ed3c",
    "private": True,
    "intent": "initial-pr",
    "local_head": receipt["head_sha"],
    "local_verification": {
        "head_sha": receipt["head_sha"],
        "status": receipt["status"],
        "completed_at": receipt["completed_at"],
    },
    "pull_request": None,
    "actionable_feedback": None,
    "billing_blocker": None,
    "recovery": None,
}
Path(sys.argv[2]).write_text(json.dumps(snapshot))
PY

python3 "$skill_dir/scripts/ci_publish.py" publish \
  --repo-root "$scratch/repo" \
  --snapshot "$scratch/snapshot.json" \
  --remote github \
  --branch agent/example > "$scratch/publish.out"
grep -F 'ALLOW initial-pr DRY-RUN' "$scratch/publish.out"
grep -F 'git push github ' "$scratch/publish.out"

printf 'dirty\n' >> "$scratch/repo/README.md"
if python3 "$skill_dir/scripts/ci_publish.py" publish \
  --repo-root "$scratch/repo" \
  --snapshot "$scratch/snapshot.json" \
  --remote github \
  --branch agent/example > "$scratch/dirty.out" 2> "$scratch/dirty.err"; then
  echo 'FAIL: dirty worktree was admitted using an exact-HEAD receipt' >&2
  exit 1
fi
grep -F 'working tree must be clean' "$scratch/dirty.err"

printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"git push github main","cwd":"'"$scratch/repo"'"}}' \
  > "$scratch/hook.json"
if python3 "$skill_dir/scripts/ci_publish_guard.py" < "$scratch/hook.json" \
  > "$scratch/hook.out" 2> "$scratch/hook.err"; then
  echo 'FAIL: direct managed GitHub push bypassed publication guard' >&2
  exit 1
fi
grep -F 'BLOCK ci-publication-guard:' "$scratch/hook.err"

printf '%s\n' '{"hooks":{"PreToolUse":[]}}' > "$scratch/codex-hooks.json"
printf '%s\n' '{"hooks":{"PreToolUse":[]},"model":"test"}' > "$scratch/claude-settings.json"
python3 "$skill_dir/scripts/install-ci-publish-guard.py" \
  --guard "$skill_dir/scripts/ci_publish_guard.py" \
  --codex-hooks "$scratch/codex-hooks.json" \
  --claude-settings "$scratch/claude-settings.json" \
  --apply > "$scratch/install.out"
grep -F "INSTALLED $scratch/codex-hooks.json" "$scratch/install.out"
grep -F "INSTALLED $scratch/claude-settings.json" "$scratch/install.out"
python3 "$skill_dir/scripts/install-ci-publish-guard.py" \
  --guard "$skill_dir/scripts/ci_publish_guard.py" \
  --codex-hooks "$scratch/codex-hooks.json" \
  --claude-settings "$scratch/claude-settings.json" \
  --apply > "$scratch/reinstall.out"
grep -F "OK $scratch/codex-hooks.json" "$scratch/reinstall.out"
grep -F "OK $scratch/claude-settings.json" "$scratch/reinstall.out"

echo 'PASS[ci-publication-control]: workflow contract, exact-head receipt, dry-run wrapper, and direct-push hollow'
