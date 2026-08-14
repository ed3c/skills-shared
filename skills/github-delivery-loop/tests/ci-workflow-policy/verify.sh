#!/usr/bin/env bash
# Controls for the repository seal on a private repo's publication workflow.
#
# `.github-delivery/ci-policy.json` landed in #82 with nothing in this tree able
# to read it: the policy named a workflow, a required job and a local
# verification command, and no gate compared any of that against the workflow
# actually on disk. A policy nobody checks is a policy that drifts silently, and
# the drift only shows up as a publication that paid for a runner and learned
# nothing.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${test_dir}/../.." && pwd)"
repo_root="$(cd "${skill_dir}/../.." && pwd)"
checker="${skill_dir}/scripts/ci_workflow_policy.py"
work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT

# 1. positive, against this repository's own policy and workflow rather than a
#    synthetic pair. The seal is only worth anything where it is load-bearing.
python3 "${checker}" check --repo-root "${repo_root}" > "${work}/good.out"
grep -q "^ALLOW workflow-policy" "${work}/good.out"
grep -q "repository=ed3c/skills-shared" "${work}/good.out"

# 2. negatives. Each mutates one field of a copy of the real policy, so a
#    refusal is about the rule it names rather than about a fixture that was
#    already malformed.
mkdir -p "${work}/repo/.github/workflows" "${work}/repo/.github-delivery"
cp "${repo_root}/.github-delivery/ci-policy.json" "${work}/repo/.github-delivery/ci-policy.json"
cp "${repo_root}/.github/workflows/skill-eval-contract.yml" \
   "${work}/repo/.github/workflows/skill-eval-contract.yml"
python3 "${checker}" check --repo-root "${work}/repo" | grep -q "^ALLOW"

refuse() {
  local label=$1 fragment=$2
  set +e
  python3 "${checker}" check --repo-root "${work}/repo" \
    --policy "${work}/mutated.json" > "${work}/${label}.out" 2> "${work}/${label}.err"
  local rc=$?
  set -e
  if [ "${rc}" -eq 0 ]; then
    echo "FAIL ${label}: a planted defect was admitted" >&2
    exit 1
  fi
  if ! grep -q "${fragment}" "${work}/${label}.err"; then
    echo "FAIL ${label}: refused for the wrong reason: $(cat "${work}/${label}.err")" >&2
    exit 1
  fi
}

mutate() {
  python3 - "${work}/repo/.github-delivery/ci-policy.json" "${work}/mutated.json" "$@" <<'PY'
import json, pathlib, sys
source, target, key, value = sys.argv[1:5]
policy = json.loads(pathlib.Path(source).read_text(encoding="utf-8"))
policy[key] = json.loads(value)
pathlib.Path(target).write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
PY
}

mutate schema '"github-ci-policy/v0"'
refuse wrong-schema "schema must be"

mutate private 'false'
refuse public-repository "private must be true"

mutate repository '"not-a-slug"'
refuse bad-repository "repository must be OWNER/REPOSITORY"

mutate workflow '"scripts/somewhere.yml"'
refuse workflow-outside-workflows "workflow must be under .github/workflows/"

# Under .github/workflows/ by prefix and still leaving the repository, so this
# reaches the path-safety rule rather than the directory rule in front of it.
mutate workflow '".github/workflows/../../../etc/passwd"'
refuse escaping-workflow "safe repository-relative path"

mutate required_jobs '[]'
refuse empty-required-jobs "required_jobs must be a non-empty string array"

mutate local_verification '"bash scripts/local_verification.sh"'
refuse shell-string-verification "local_verification must be a non-empty argv array"

# 3. the seal is about the workflow on disk, not only about the policy's own
#    shape. A required job the workflow does not declare must be refused, or the
#    policy can name anything and stay green.
mutate required_jobs '["a-job-that-does-not-exist"]'
set +e
python3 "${checker}" check --repo-root "${work}/repo" --policy "${work}/mutated.json" \
  > "${work}/missing-job.out" 2> "${work}/missing-job.err"
missing_job_rc=$?
set -e
if [ "${missing_job_rc}" -eq 0 ]; then
  echo "FAIL: a required job absent from the workflow was admitted" >&2
  exit 1
fi

echo "PASS github-delivery CI workflow policy seal"
