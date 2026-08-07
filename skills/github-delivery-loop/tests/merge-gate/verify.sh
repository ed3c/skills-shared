#!/usr/bin/env bash
# Positive control for the merge-authority preflight. Zero network: every case
# replays a snapshot and points HOME at a scratch tree so the probes read
# fixture host policy instead of this machine's.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
gate="${skill_dir}/scripts/merge_gate.py"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

repo="example/infrastructure"
clean_home="${scratch}/home-clean"
mkdir -p "${clean_home}"

run() {  # run <HOME> <extra-env...> -- <args...>
  local home="$1"
  shift
  env -u CLAUDECODE -u CODEX_SANDBOX HOME="${home}" "$@"
}

# 1. good: admitted by the owner, after the head commit, mergeable -> GREEN
run "${clean_home}" python3 "${gate}" preflight --repo "${repo}" \
  --snapshot "${test_dir}/fixtures/good/snapshot.json" > "${scratch}/good.out"
grep -q "PREFLIGHT GREEN: 1 PR" "${scratch}/good.out"
grep -q "READY #7" "${scratch}/good.out"

# 2. hollow: wrong admit actor and stale admit are both refusals, not passes
if run "${clean_home}" python3 "${gate}" preflight --repo "${repo}" \
  --snapshot "${test_dir}/fixtures/hollow/snapshot.json" \
  >"${scratch}/hollow.out" 2>"${scratch}/hollow.err"; then
  echo "FAIL: hollow snapshot was admitted" >&2
  exit 1
fi
grep -q "BLOCK #8 .*L1 HUMAN-ADMIT.*not repository owner" "${scratch}/hollow.err"
grep -q "BLOCK #9 .*L1 HUMAN-ADMIT.*admit-stale" "${scratch}/hollow.err"

# 3. absence is its own exit: nothing admitted != a layer refused
set +e
run "${clean_home}" python3 "${gate}" preflight --repo "${repo}" \
  --snapshot "${test_dir}/fixtures/empty/snapshot.json" > "${scratch}/empty.out"
empty_status=$?
set -e
test "${empty_status}" -eq 3
grep -q "NO-ADMIT ${repo}" "${scratch}/empty.out"

# 4. host policy: a PreToolUse hook that exits 2 must refuse the whole run,
#    and only when that host is the active one.
blocked_home="${scratch}/home-blocked"
mkdir -p "${blocked_home}/.claude/hooks"
printf '%s\n' '#!/usr/bin/env bash' 'cat >/dev/null' \
  'echo "BLOCKED: fixture blacklist gh pr merge" >&2' 'exit 2' \
  > "${blocked_home}/.claude/hooks/deny.sh"
chmod 755 "${blocked_home}/.claude/hooks/deny.sh"
cat > "${blocked_home}/.claude/settings.json" <<JSON
{"hooks":{"PreToolUse":[{"matcher":"*","hooks":[
  {"type":"command","command":"${blocked_home}/.claude/hooks/deny.sh"}]}]}}
JSON

set +e
env -u CODEX_SANDBOX CLAUDECODE=1 HOME="${blocked_home}" python3 "${gate}" preflight \
  --repo "${repo}" --snapshot "${test_dir}/fixtures/good/snapshot.json" \
  >"${scratch}/host.out" 2>"${scratch}/host.err"
host_status=$?
set -e
test "${host_status}" -eq 1
grep -q "L2 HOST-POLICY claude-code: BLOCK" "${scratch}/host.err"
grep -q "REFUSED by L2 HOST-POLICY on claude-code" "${scratch}/host.err"

# 4b. Codex mirrors the PreToolUse plane in ~/.codex/hooks.json. A rule that
#     allows and a profile with network still lose to a hook that exits 2, so
#     probing only execpolicy/network reports a false green. Regression guard.
codex_home="${scratch}/home-codex"
mkdir -p "${codex_home}/.codex/hooks" "${codex_home}/.codex/rules"
printf '%s\n' '#!/usr/bin/env bash' 'cat >/dev/null' \
  'echo "BLOCKED: codex-side blacklist gh pr merge" >&2' 'exit 2' \
  > "${codex_home}/.codex/hooks/deny.sh"
chmod 755 "${codex_home}/.codex/hooks/deny.sh"
cat > "${codex_home}/.codex/hooks.json" <<JSON
{"hooks":{"PreToolUse":[{"matcher":"*","hooks":[
  {"type":"command","command":"${codex_home}/.codex/hooks/deny.sh"}]}]}}
JSON
# network granted and a rule present, so only the hook can refuse
cat > "${codex_home}/.codex/config.toml" <<'TOML'
default_permissions = "probe"
[permissions.probe]
extends = ":workspace"
[permissions.probe.network]
enabled = true
TOML
touch "${codex_home}/.codex/rules/github-merge-example-infrastructure.rules"

# neutral CWD so the probe reads fixture config, not this machine's repos
neutral="${scratch}/neutral"
mkdir -p "${neutral}"

set +e
(cd "${neutral}" && env -u CLAUDECODE CODEX_SANDBOX=seatbelt HOME="${codex_home}" \
  python3 "${gate}" preflight --repo "${repo}" \
  --snapshot "${test_dir}/fixtures/good/snapshot.json") \
  >"${scratch}/codexhook.out" 2>"${scratch}/codexhook.err"
codex_status=$?
set -e
test "${codex_status}" -eq 1
grep -q "L2 HOST-POLICY codex: BLOCK.*codex-side blacklist" "${scratch}/codexhook.err"
grep -q "REFUSED by L2 HOST-POLICY on codex" "${scratch}/codexhook.err"

# 4c. Codex layers project config over user config. A repo whose .codex/config.toml
#     exists purely for MCP servers must inherit the user-level permission
#     profile, not be reported as "network disabled" -- the false-red mirror of 4b.
layered_home="${scratch}/home-layered"
mkdir -p "${layered_home}/.codex"
cat > "${layered_home}/.codex/config.toml" <<'TOML'
default_permissions = "agent-default"
[permissions.agent-default]
extends = ":workspace"
[permissions.agent-default.network]
enabled = true
TOML
project_dir="${scratch}/mcp-only-project"
mkdir -p "${project_dir}/.codex"
printf '[mcp_servers.demo]\ncommand = "true"\n' > "${project_dir}/.codex/config.toml"

set +e
(cd "${project_dir}" && run "${layered_home}" python3 "${gate}" preflight --repo "${repo}" \
  --snapshot "${test_dir}/fixtures/good/snapshot.json") \
  >"${scratch}/layered.out" 2>"${scratch}/layered.err"
set -e
cat "${scratch}/layered.err" >> "${scratch}/layered.out"
if grep -q "built-in presets disable network" "${scratch}/layered.out"; then
  echo "FAIL: project MCP-only config shadowed the inherited user profile" >&2
  exit 1
fi
grep -q "no execpolicy rule" "${scratch}/layered.out"   # reached the next sub-gate

# 5. same hook, inactive host: reported but not blocking (shell is active)
(cd "${neutral}" && run "${clean_home}" python3 "${gate}" preflight --repo "${repo}" \
  --snapshot "${test_dir}/fixtures/good/snapshot.json") > "${scratch}/inactive.out"
grep -q "L2 HOST-POLICY codex: BLOCK" "${scratch}/inactive.out"
grep -q "PREFLIGHT GREEN" "${scratch}/inactive.out"

echo "PASS merge-authority preflight"
