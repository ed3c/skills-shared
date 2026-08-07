#!/usr/bin/env bash
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
installer="${skill_dir}/scripts/install-codex-merge-rule.sh"
fixture_root="$(mktemp -d)"
trap 'rm -rf "${fixture_root}"' EXIT

fake_codex="${fixture_root}/codex"
fake_log="${fixture_root}/codex.args"
installer_log="${fixture_root}/installer.out"
invalid_log="${fixture_root}/invalid.err"
rules_dir="${fixture_root}/rules"
good_repository="$(< "${test_dir}/fixtures/good/repository.txt")"
hollow_repository="$(< "${test_dir}/fixtures/hollow/repository.txt")"

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -euo pipefail' \
  'printf "%s\n" "$@" > "${FAKE_CODEX_LOG}"' \
  'printf "%s\n" "decision: allow"' > "${fake_codex}"
chmod 755 "${fake_codex}"

FAKE_CODEX_LOG="${fake_log}" bash "${installer}" \
  --repo "${good_repository}" \
  --rules-dir "${rules_dir}" \
  --codex-bin "${fake_codex}" > "${installer_log}"

rule_file="${rules_dir}/github-merge-example-infrastructure.rules"
test -f "${rule_file}"
grep -F 'pattern = ["gh", "pr", "merge", "--repo", "example/infrastructure"]' \
  "${rule_file}"
grep -F 'decision = "allow"' "${rule_file}"
grep -F 'This rule does not override repository PreToolUse hooks or human merge gates.' \
  "${installer_log}"

printf '%s\n' 'previous rule' > "${rule_file}"
FAKE_CODEX_LOG="${fake_log}" bash "${installer}" \
  --repo "${good_repository}" \
  --rules-dir "${rules_dir}" \
  --codex-bin "${fake_codex}" > "${installer_log}"
grep -F 'previous rule' "${rule_file}.bak"

if bash "${installer}" \
  --repo "${hollow_repository}" \
  --rules-dir "${rules_dir}" \
  --codex-bin "${fake_codex}" 2> "${invalid_log}"; then
  echo "FAIL: unsafe repository was accepted" >&2
  exit 1
fi
grep -F 'ERROR: --repo must be an exact OWNER/REPOSITORY name' "${invalid_log}"

echo "PASS scoped merge rule installer"
