#!/usr/bin/env bash
# Zero network. Good fixture passes; the hollow one has no materialized
# artifact and must fail as UNMATERIALIZED rather than being skipped.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(dirname "$(dirname "$test_dir")")"
checker="$skill_dir/scripts/gitlab_delivery.py"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

python3 "$checker" check --registry "$test_dir/fixtures/good/registry.json"

if python3 "$checker" check --registry "$test_dir/fixtures/hollow/registry.json" \
  >"$scratch/hollow.out" 2>"$scratch/hollow.err"; then
  echo "hollow fixture unexpectedly passed" >&2
  exit 1
fi
grep -q "UNMATERIALIZED portable-loop" "$scratch/hollow.err"

# A single-slash project path is a GitHub-shaped assumption. GitLab nests
# groups, so the registry must accept 3+ segments (the good fixture) and reject
# a bare namespace with no project segment.
bad="$scratch/flat"
mkdir -p "$bad"
sed 's#"example/infrastructure/portable-loop"#"solo"#' \
  "$test_dir/fixtures/good/registry.json" > "$bad/registry.json"
if python3 "$checker" check --registry "$bad/registry.json" >/dev/null 2>"$scratch/flat.err"; then
  echo "unnamespaced project path unexpectedly passed" >&2
  exit 1
fi
grep -q "namespaced path" "$scratch/flat.err"

echo "PASS gitlab receipt gate"
