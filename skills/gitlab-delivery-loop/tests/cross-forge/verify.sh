#!/usr/bin/env bash
# The non-confusion contract, enforced mechanically rather than by documentation.
# GitHub state reaching the GitLab skill must fail loudly and name the other
# skill -- never be ignored as an unknown field and never half-validate against
# whatever gitlab_* keys happen to sit beside it.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(dirname "$(dirname "$test_dir")")"
checker="$skill_dir/scripts/gitlab_delivery.py"
gate="$skill_dir/scripts/gitlab_merge_gate.py"
scratch="$(mktemp -d "${TMPDIR:-/tmp}/scratch.XXXXXXXX")"
trap 'rm -rf "$scratch"' EXIT

refuse() {  # refuse <fixture> <expected-substring>
  local fixture="$1" expected="$2"
  if python3 "$checker" check --registry "$test_dir/fixtures/$fixture/registry.json" \
    >"$scratch/$fixture.out" 2>"$scratch/$fixture.err"; then
    echo "FAIL: $fixture was accepted by the GitLab skill" >&2
    exit 1
  fi
  grep -q "$expected" "$scratch/$fixture.err" || {
    echo "FAIL: $fixture did not name the cross-forge cause" >&2
    cat "$scratch/$fixture.err" >&2
    exit 1
  }
}

# 1. a whole GitHub registry: refused at the schema, pointing at the other skill
refuse github-registry "github-delivery-loop"

# 2. a GitLab registry carrying a GitHub identity field: refused, not ignored.
#    An unknown key is normally harmless; this one means the wrong forge.
refuse github-key "GitHub field 'github_repo'"

# 3. a github.com URL inside an otherwise valid GitLab receipt
refuse github-url "cross-forge URL"

# 4. a GitHub merge-gate snapshot must not replay through the GitLab gate
cat > "$scratch/github-snapshot.json" <<'JSON'
{"repo":"example/infrastructure","owner":"example","pulls":[]}
JSON
if python3 "$gate" preflight --project example/infrastructure \
  --snapshot "$scratch/github-snapshot.json" >"$scratch/gate.out" 2>"$scratch/gate.err"; then
  echo "FAIL: GitHub snapshot replayed through the GitLab merge gate" >&2
  exit 1
fi
grep -q "github-delivery-loop" "$scratch/gate.err"

echo "PASS cross-forge refusal"
