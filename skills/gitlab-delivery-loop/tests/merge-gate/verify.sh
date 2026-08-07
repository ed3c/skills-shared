#!/usr/bin/env bash
# Positive control for the merge-authority preflight. Zero network: every case
# replays a snapshot and points HOME at a scratch tree so the probes read
# fixture host policy instead of this machine's.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
gate="${skill_dir}/scripts/gitlab_merge_gate.py"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

project="example/infrastructure"
clean_home="${scratch}/home-clean"
mkdir -p "${clean_home}"

run() {  # run <HOME> <command...>
  local home="$1"
  shift
  env -u CLAUDECODE -u CODEX_SANDBOX HOME="${home}" "$@"
}

# 1. good: admitted by an Owner, after the head commit, mergeable -> GREEN
run "${clean_home}" python3 "${gate}" preflight --project "${project}" \
  --snapshot "${test_dir}/fixtures/good/snapshot.json" > "${scratch}/good.out"
grep -q "PREFLIGHT GREEN: 1 MR" "${scratch}/good.out"
grep -q "READY !7" "${scratch}/good.out"

# 2. hollow: a Developer's label and a stale admit are refusals, not passes.
#    GitLab has no single "repository owner" for group projects -- the project
#    payload's `owner` is null there -- so authority is read from access level.
if run "${clean_home}" python3 "${gate}" preflight --project "${project}" \
  --snapshot "${test_dir}/fixtures/hollow/snapshot.json" \
  >"${scratch}/hollow.out" 2>"${scratch}/hollow.err"; then
  echo "FAIL: hollow snapshot was admitted" >&2
  exit 1
fi
grep -q "BLOCK !8 .*L1 HUMAN-ADMIT.*access_level=30" "${scratch}/hollow.err"
grep -q "BLOCK !9 .*L1 HUMAN-ADMIT.*admit-stale" "${scratch}/hollow.err"

# 2b. personal namespace: the owner of a user namespace may not appear in the
#     members list at all, so namespace ownership is accepted on its own.
run "${clean_home}" python3 "${gate}" preflight --project "solo-owner/portable-loop" \
  --snapshot "${test_dir}/fixtures/personal/snapshot.json" > "${scratch}/personal.out"
grep -q "PREFLIGHT GREEN" "${scratch}/personal.out"

# 3. absence is its own exit: nothing admitted != a layer refused
set +e
run "${clean_home}" python3 "${gate}" preflight --project "${project}" \
  --snapshot "${test_dir}/fixtures/empty/snapshot.json" > "${scratch}/empty.out"
empty_status=$?
set -e
test "${empty_status}" -eq 3
grep -q "NO-ADMIT gitlab.com/${project}" "${scratch}/empty.out"

# 3b. "not computed yet" and "refused" must not read alike. `unchecked` is a
#     retry; `ci_still_running` is a policy choice behind --allow-unstable.
set +e
run "${clean_home}" python3 "${gate}" preflight --project "${project}" \
  --snapshot "${test_dir}/fixtures/unstable/snapshot.json" \
  >"${scratch}/unstable.out" 2>"${scratch}/unstable.err"
set -e
grep -q "BLOCK !11 .*ci_still_running (pass --allow-unstable)" "${scratch}/unstable.err"
grep -q "BLOCK !12 .*unchecked -- GitLab has not finished computing" "${scratch}/unstable.err"
set +e
run "${clean_home}" python3 "${gate}" preflight --project "${project}" --allow-unstable \
  --snapshot "${test_dir}/fixtures/unstable/snapshot.json" \
  >"${scratch}/unstable2.out" 2>"${scratch}/unstable2.err"
set -e
grep -q "READY !11" "${scratch}/unstable2.out"
grep -q "BLOCK !12" "${scratch}/unstable2.err"   # still not computed, still not ready

# 4. host policy: a PreToolUse hook that exits 2 must refuse the whole run,
#    and only when that host is the active one.
blocked_home="${scratch}/home-blocked"
mkdir -p "${blocked_home}/.claude/hooks"
printf '%s\n' '#!/usr/bin/env bash' 'cat >/dev/null' \
  'echo "BLOCKED: fixture blacklist glab mr merge" >&2' 'exit 2' \
  > "${blocked_home}/.claude/hooks/deny.sh"
chmod 755 "${blocked_home}/.claude/hooks/deny.sh"
cat > "${blocked_home}/.claude/settings.json" <<JSON
{"hooks":{"PreToolUse":[{"matcher":"*","hooks":[
  {"type":"command","command":"${blocked_home}/.claude/hooks/deny.sh"}]}]}}
JSON

set +e
env -u CODEX_SANDBOX CLAUDECODE=1 HOME="${blocked_home}" python3 "${gate}" preflight \
  --project "${project}" --snapshot "${test_dir}/fixtures/good/snapshot.json" \
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
  'echo "BLOCKED: codex-side blacklist glab mr merge" >&2' 'exit 2' \
  > "${codex_home}/.codex/hooks/deny.sh"
chmod 755 "${codex_home}/.codex/hooks/deny.sh"
cat > "${codex_home}/.codex/hooks.json" <<JSON
{"hooks":{"PreToolUse":[{"matcher":"*","hooks":[
  {"type":"command","command":"${codex_home}/.codex/hooks/deny.sh"}]}]}}
JSON
cat > "${codex_home}/.codex/config.toml" <<'TOML'
default_permissions = "probe"
[permissions.probe]
extends = ":workspace"
[permissions.probe.network]
enabled = true
TOML
touch "${codex_home}/.codex/rules/gitlab-merge-gitlab-com-example-infrastructure.rules"

neutral="${scratch}/neutral"
mkdir -p "${neutral}"

set +e
(cd "${neutral}" && env -u CLAUDECODE CODEX_SANDBOX=seatbelt HOME="${codex_home}" \
  python3 "${gate}" preflight --project "${project}" \
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
(cd "${project_dir}" && run "${layered_home}" python3 "${gate}" preflight \
  --project "${project}" --snapshot "${test_dir}/fixtures/good/snapshot.json") \
  >"${scratch}/layered.out" 2>"${scratch}/layered.err"
set -e
cat "${scratch}/layered.err" >> "${scratch}/layered.out"
if grep -q "built-in presets disable network" "${scratch}/layered.out"; then
  echo "FAIL: project MCP-only config shadowed the inherited user profile" >&2
  exit 1
fi
grep -q "no execpolicy rule" "${scratch}/layered.out"   # reached the next sub-gate

# 5. same hook, inactive host: reported but not blocking (shell is active)
(cd "${neutral}" && run "${clean_home}" python3 "${gate}" preflight --project "${project}" \
  --snapshot "${test_dir}/fixtures/good/snapshot.json") > "${scratch}/inactive.out"
grep -q "L2 HOST-POLICY codex: BLOCK" "${scratch}/inactive.out"
grep -q "PREFLIGHT GREEN" "${scratch}/inactive.out"

# 6. the landing command itself. `glab mr merge` turns auto-merge ON by default
#    whenever a pipeline is running, which reports success while nothing merged.
#    That default is outside any execpolicy prefix, so it is guarded here.
run "${clean_home}" python3 - "${gate}" <<'PY' > "${scratch}/cmd.out"
import importlib.util, sys
spec = importlib.util.spec_from_file_location("gate", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(" ".join(module.merge_command("gitlab.com", "example/infrastructure", 7, "1" * 40)))
PY
grep -q -- "--auto-merge=false" "${scratch}/cmd.out"
grep -q -- "--sha 1111111111111111111111111111111111111111" "${scratch}/cmd.out"
grep -q -- "-R https://gitlab.com/example/infrastructure" "${scratch}/cmd.out"

echo "PASS gitlab merge-authority preflight"
