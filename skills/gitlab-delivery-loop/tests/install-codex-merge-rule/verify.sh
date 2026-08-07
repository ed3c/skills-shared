#!/usr/bin/env bash
# The rule must be narrow, and "narrow" is measured by what it REFUSES.
# Checking that it allows the positive control says nothing about its width --
# that was the GitHub-side lesson, and it applies unchanged here.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
installer="${skill_dir}/scripts/install-codex-merge-rule.sh"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

good="$(tr -d '\n' < "${test_dir}/fixtures/good/project.txt")"
hollow="$(tr -d '\n' < "${test_dir}/fixtures/hollow/project.txt")"
rules="${scratch}/rules"

# 1. argument validation happens before anything is written or executed
for bad_args in \
  "--project ${hollow}" \
  "--project ../evil/project" \
  "--project ${good} --host not/a/host" ; do
  # shellcheck disable=SC2086
  if bash "${installer}" ${bad_args} --rules-dir "${rules}" \
    >/dev/null 2>"${scratch}/err"; then
    echo "FAIL: installer accepted '${bad_args}'" >&2
    exit 1
  fi
  test ! -d "${rules}" || test -z "$(ls -A "${rules}" 2>/dev/null)" || {
    echo "FAIL: installer wrote a rule for '${bad_args}'" >&2
    exit 1
  }
done

# 2. a relative --rules-dir is refused: a rule written to the wrong place is a
#    rule Codex will never load, which reads as "installed" and is not.
if bash "${installer}" --project "${good}" --rules-dir relative/path \
  >/dev/null 2>&1; then
  echo "FAIL: installer accepted a relative --rules-dir" >&2
  exit 1
fi

if ! command -v codex >/dev/null 2>&1; then
  echo "SKIP execpolicy controls: codex not on PATH"
  echo "PASS gitlab merge-rule installer (validation only)"
  exit 0
fi

# 3. install, then measure the rule against real argv shapes
bash "${installer}" --host gitlab.com --project "${good}" --rules-dir "${rules}" \
  > "${scratch}/install.out"
rule="$(ls "${rules}"/gitlab-merge-*.rules)"
test -f "${rule}"
# never the GitHub namespace: a stale github-merge-* rule must not read as
# coverage for a GitLab merge, and vice versa
test -z "$(ls "${rules}"/github-merge-* 2>/dev/null)"

decision() {  # decision <argv...>
  codex execpolicy check --rules "${rule}" -- "$@" 2>&1 |
    grep -qi '"decision": *"allow"' && echo allow || echo deny
}

# positive control: the exact argv `land` builds, not a shorter convenience form
test "$(decision glab mr merge -R "https://gitlab.com/${good}" 7 --squash \
  --sha 1111111111111111111111111111111111111111 --auto-merge=false --yes)" = allow

# negative controls: the width of the rule
test "$(decision glab mr merge -R https://gitlab.com/other/group/project 7 --squash)" = deny
test "$(decision glab mr merge 7 -R "https://gitlab.com/${good}" --squash)" = deny
test "$(decision glab mr merge -R "https://gitlab.example.com/${good}" 7 --squash)" = deny
test "$(decision glab repo delete "${good}")" = deny
test "$(decision glab mr close 7 -R "https://gitlab.com/${good}")" = deny
# cross-forge: a GitLab rule must never authorize a GitHub merge
test "$(decision gh pr merge --repo example/infra 7 --squash)" = deny

# 4. re-installing backs the old rule up instead of losing it
bash "${installer}" --host gitlab.com --project "${good}" --rules-dir "${rules}" >/dev/null
test -f "${rule}.bak"

echo "PASS gitlab merge-rule installer"
