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

# 3b. Explicit owner-auto policy replaces only the per-PR label. Repository
# identity is bound to immutable owner/viewer IDs, personal User type, exact
# canonical name, and admin permission. This includes future repos owned by the
# same user while rejecting collaborators and organization repositories.
owner_policy="${test_dir}/fixtures/owner-auto/policy.json"
run "${clean_home}" python3 "${gate}" preflight --repo "${repo}" \
  --policy "${owner_policy}" \
  --snapshot "${test_dir}/fixtures/owner-auto/good.json" \
  > "${scratch}/owner-good.out"
grep -q "READY #7" "${scratch}/owner-good.out"
grep -q "PREFLIGHT GREEN: 1 PR" "${scratch}/owner-good.out"

# 3b-i. A requested PR is the complete evaluation scope. A failure in another
# open PR must not block it, and another ready PR must not become landable by
# accident.
run "${clean_home}" python3 "${gate}" preflight --repo "${repo}" --pr 31 \
  --policy "${owner_policy}" \
  --snapshot "${test_dir}/fixtures/owner-auto/multiple.json" \
  > "${scratch}/owner-scoped.out"
grep -q "READY #31" "${scratch}/owner-scoped.out"
grep -q "PREFLIGHT GREEN: 1 PR" "${scratch}/owner-scoped.out"
if grep -Eq "#(2|6)([^0-9]|$)" "${scratch}/owner-scoped.out"; then
  echo "FAIL: scoped preflight evaluated an unrelated PR" >&2
  exit 1
fi

set +e
run "${clean_home}" python3 "${gate}" preflight --repo "${repo}" --pr 404 \
  --policy "${owner_policy}" \
  --snapshot "${test_dir}/fixtures/owner-auto/multiple.json" \
  >"${scratch}/owner-missing.out" 2>"${scratch}/owner-missing.err"
owner_missing_status=$?
run "${clean_home}" python3 "${gate}" preflight --repo "${repo}" --pr 0 \
  --policy "${owner_policy}" \
  --snapshot "${test_dir}/fixtures/owner-auto/multiple.json" \
  >"${scratch}/owner-zero.out" 2>"${scratch}/owner-zero.err"
owner_zero_status=$?
set -e
test "${owner_missing_status}" -eq 1
grep -q "PR #404 must appear exactly once.*found 0" "${scratch}/owner-missing.err"
test "${owner_zero_status}" -eq 2
grep -q -- "--pr must be a positive integer" "${scratch}/owner-zero.err"

# 3b-ii. Live scoped preflight reads the selected PR directly; it must not list
# every open PR and then filter locally.
fake_bin="${scratch}/fake-bin"
mkdir -p "${fake_bin}"
apply_log="${scratch}/fake-gh.log"
cat > "${fake_bin}/gh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
echo "$*" >> "${GH_LOG}"
case "$*" in
  "api repos/example/infrastructure --jq "*)
    echo '{"full_name":"example/infrastructure","node_id":"R_example","owner":{"login":"example","id":42,"type":"User"},"permissions":{"admin":true}}'
    ;;
  "api user --jq "*)
    echo '{"login":"example","id":42,"type":"User"}'
    ;;
  "pr view 31 --repo example/infrastructure --json "*)
    echo '{"id":"PR_owner_auto_31","number":31,"url":"https://github.com/example/infrastructure/pull/31","title":"selected live PR","state":"OPEN","isDraft":false,"headRefOid":"3131313131313131313131313131313131313131","mergeable":"MERGEABLE","mergeStateStatus":"CLEAN"}'
    ;;
  "pr view 6 --repo example/infrastructure --json "*)
    echo '{"id":"PR_owner_auto_6","number":6,"url":"https://github.com/example/infrastructure/pull/6","title":"selected failing PR","state":"OPEN","isDraft":false,"headRefOid":"6666666666666666666666666666666666666666","mergeable":"MERGEABLE","mergeStateStatus":"UNSTABLE"}'
    ;;
  "pr view 8 --repo example/infrastructure --json "*)
    echo '{"id":"PR_human_admit_8","number":8,"url":"https://github.com/example/infrastructure/pull/8","title":"selected PR admitted by non-owner","state":"OPEN","isDraft":false,"headRefOid":"8888888888888888888888888888888888888888","mergeable":"MERGEABLE","mergeStateStatus":"CLEAN"}'
    ;;
  "pr view 404 --repo example/infrastructure --json "*)
    ;;
  "api repos/example/infrastructure/commits/3131313131313131313131313131313131313131 --jq "*)
    echo '{"d":"2026-08-12T01:00:00Z"}'
    ;;
  "api repos/example/infrastructure/commits/6666666666666666666666666666666666666666 --jq "*)
    echo '{"d":"2026-08-12T01:00:00Z"}'
    ;;
  "api repos/example/infrastructure/commits/8888888888888888888888888888888888888888 --jq "*)
    echo '{"d":"2026-08-12T01:00:00Z"}'
    ;;
  "api repos/example/infrastructure/issues/8/events --paginate --jq "*)
    echo '{"actor":"delivery-bot","at":"2026-08-12T02:00:00Z"}'
    ;;
  "api graphql -f query=mutation"*)
    echo '{"data":{"mergePullRequest":{"pullRequest":{"number":31,"merged":true}}}}'
    ;;
  *)
    echo "unexpected gh call: $*" >&2
    exit 70
    ;;
esac
SH
chmod 755 "${fake_bin}/gh"
GH_LOG="${apply_log}" PATH="${fake_bin}:${PATH}" run "${clean_home}" \
  python3 "${gate}" preflight --repo "${repo}" --pr 31 \
  --policy "${owner_policy}" > "${scratch}/owner-live-scoped.out"
grep -q "READY #31" "${scratch}/owner-live-scoped.out"
grep -q "pr view 31 --repo ${repo}" "${apply_log}"
if grep -q "pr list" "${apply_log}"; then
  echo "FAIL: live scoped preflight listed unrelated PRs" >&2
  exit 1
fi

: > "${apply_log}"
GH_LOG="${apply_log}" PATH="${fake_bin}:${PATH}" run "${clean_home}" \
  python3 "${gate}" land --repo "${repo}" --pr 31 \
  --policy "${owner_policy}" > "${scratch}/owner-live-land.out"
grep -q "LANDED #31 3131313" "${scratch}/owner-live-land.out"
grep -q "LANDED=1" "${scratch}/owner-live-land.out"
test "$(grep -c "api graphql" "${apply_log}")" -eq 1
grep -q "pullRequestId=PR_owner_auto_31" "${apply_log}"
if grep -Eq "pr list|pullRequestId=PR_owner_auto_2" "${apply_log}"; then
  echo "FAIL: scoped land touched an unrelated PR" >&2
  exit 1
fi

: > "${apply_log}"
GH_LOG="${apply_log}" PATH="${fake_bin}:${PATH}" run "${clean_home}" \
  python3 "${gate}" land --repo "${repo}" --pr 31 --dry-run \
  --policy "${owner_policy}" > "${scratch}/owner-live-dry-run.out"
grep -q "pullRequestId=PR_owner_auto_31" "${scratch}/owner-live-dry-run.out"
grep -q "expectedHeadOid=3131313131313131313131313131313131313131" \
  "${scratch}/owner-live-dry-run.out"
if grep -Eq "pr list|pullRequestId=PR_owner_auto_2" "${apply_log}"; then
  echo "FAIL: scoped dry-run touched an unrelated PR" >&2
  exit 1
fi

: > "${apply_log}"
set +e
GH_LOG="${apply_log}" PATH="${fake_bin}:${PATH}" run "${clean_home}" \
  python3 "${gate}" land --repo "${repo}" --pr 6 \
  --policy "${owner_policy}" \
  >"${scratch}/owner-live-blocked.out" 2>"${scratch}/owner-live-blocked.err"
owner_land_blocked_status=$?
set -e
test "${owner_land_blocked_status}" -eq 1
grep -q "BLOCK #6 .*L3 GITHUB.*mergeStateStatus=UNSTABLE" \
  "${scratch}/owner-live-blocked.err"
if grep -q "api graphql" "${apply_log}"; then
  echo "FAIL: scoped land attempted a merge after L3 refusal" >&2
  exit 1
fi

: > "${apply_log}"
set +e
GH_LOG="${apply_log}" PATH="${fake_bin}:${PATH}" run "${clean_home}" \
  python3 "${gate}" land --repo "${repo}" --pr 8 \
  >"${scratch}/human-live-blocked.out" 2>"${scratch}/human-live-blocked.err"
human_land_blocked_status=$?
GH_LOG="${apply_log}" PATH="${fake_bin}:${PATH}" run "${clean_home}" \
  python3 "${gate}" land --repo "${repo}" --pr 404 \
  --policy "${owner_policy}" \
  >"${scratch}/owner-live-missing.out" 2>"${scratch}/owner-live-missing.err"
owner_land_missing_status=$?
set -e
test "${human_land_blocked_status}" -eq 1
grep -q "BLOCK #8 .*L1 HUMAN-ADMIT.*not repository owner" \
  "${scratch}/human-live-blocked.err"
test "${owner_land_missing_status}" -eq 1
grep -q "could not read PR #404" "${scratch}/owner-live-missing.err"
if grep -Eq "api graphql|(^| )pr merge " "${apply_log}"; then
  echo "FAIL: scoped land attempted a merge after L1 refusal or missing target" >&2
  exit 1
fi

sed 's/"CLEAN"/"UNSTABLE"/' \
  "${test_dir}/fixtures/owner-auto/good.json" > "${scratch}/owner-unstable.json"
set +e
run "${clean_home}" python3 "${gate}" preflight --repo "${repo}" \
  --allow-unstable --policy "${owner_policy}" \
  --snapshot "${scratch}/owner-unstable.json" \
  >"${scratch}/owner-unstable.out" 2>"${scratch}/owner-unstable.err"
owner_unstable_status=$?
set -e
test "${owner_unstable_status}" -eq 1
grep -q "L3 GITHUB.*mergeStateStatus=UNSTABLE" "${scratch}/owner-unstable.err"

set +e
run "${clean_home}" python3 "${gate}" preflight \
  --repo "someone-else/infrastructure" --policy "${owner_policy}" \
  --snapshot "${test_dir}/fixtures/owner-auto/foreign.json" \
  >"${scratch}/foreign.out" 2>"${scratch}/foreign.err"
foreign_status=$?
run "${clean_home}" python3 "${gate}" preflight --repo "${repo}" \
  --policy "${owner_policy}" \
  --snapshot "${test_dir}/fixtures/owner-auto/organization.json" \
  >"${scratch}/organization.out" 2>"${scratch}/organization.err"
organization_status=$?
set -e
test "${foreign_status}" -eq 1
test "${organization_status}" -eq 1
grep -q "L1 OWNER-IDENTITY.*does not match configured owner" "${scratch}/foreign.err"
grep -q "L1 OWNER-IDENTITY.*not personal User" "${scratch}/organization.err"

# 3c. Owner-auto lands through GraphQL while pinning expectedHeadOid and
# exposing no admin bypass. authorEmail is intentionally omitted: GitHub
# rejects caller overrides when web-based Git privacy controls the address.
python3 - "${gate}" "${owner_policy}" > "${scratch}/command.out" <<'PY'
import importlib.util
import sys
from pathlib import Path

gate_path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("merge_gate", gate_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
policy, _ = module.load_policy(Path(sys.argv[2]))
pull = {
    "id": "PR_owner_auto_7",
    "number": 7,
    "headRefOid": "1" * 40,
}
print(" ".join(module.merge_command("example/infrastructure", pull, policy)))
PY
grep -q "expectedHeadOid=1111111111111111111111111111111111111111" "${scratch}/command.out"
if grep -q "authorEmail" "${scratch}/command.out"; then
  echo "FAIL: owner-auto merge overrides GitHub web commit email settings" >&2
  exit 1
fi
if grep -q -- "--admin" "${scratch}/command.out"; then
  echo "FAIL: owner-auto merge grew an admin bypass" >&2
  exit 1
fi

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

# 4d. A hook that cannot RUN is not a hook that refused. Both exit 2 -- an
#     interpreter that cannot open its script uses the same code as the blocking
#     contract -- so this was reported as `BLOCK` and preflight refused on a
#     policy decision nobody had made. Two guards, and the first is the fix:
#     CLAUDE_PROJECT_DIR must reach the hook, and a command referencing anything
#     the probe cannot resolve must exit UNEVALUABLE (4), never 1.
projdir_home="${scratch}/home-projdir"
mkdir -p "${projdir_home}/.claude/hooks"
# Refuses only the merge command, and only when it can read its own file --
# i.e. a realistic blacklist hook, not one that refuses everything.
printf '%s\n' '#!/usr/bin/env bash' 'payload="$(cat)"' \
  'case "${payload}" in *"pr merge"*) echo "BLOCKED: fixture blacklist" >&2; exit 2;; esac' \
  'exit 0' > "${projdir_home}/.claude/hooks/guard.sh"
chmod 755 "${projdir_home}/.claude/hooks/guard.sh"
cat > "${projdir_home}/.claude/settings.json" <<JSON
{"hooks":{"PreToolUse":[{"matcher":"*","hooks":[
  {"type":"command","command":"bash \"\${CLAUDE_PROJECT_DIR}/.claude/hooks/guard.sh\""}]}]}}
JSON

# 4d-i: CLAUDE_PROJECT_DIR is deliberately NOT in the environment. The probe has
#       to supply it the way Claude Code does, or the hook cannot find its own
#       file. Setting it here instead would make this case pass with the fix
#       removed -- which is what the first version did, caught by planting.
set +e
(cd "${projdir_home}" && env -u CODEX_SANDBOX -u CLAUDE_PROJECT_DIR CLAUDECODE=1 \
  HOME="${projdir_home}" python3 "${gate}" preflight --repo "${repo}" \
  --snapshot "${test_dir}/fixtures/good/snapshot.json") \
  >"${scratch}/projdir.out" 2>"${scratch}/projdir.err"
projdir_status=$?
set -e
test "${projdir_status}" -eq 1
grep -q "L2 HOST-POLICY claude-code: BLOCK.*fixture blacklist" "${scratch}/projdir.err"

# 4d-ii: strip the variable from the environment AND from git discovery. The
#        gate is now un-evaluable, and that must NOT wear a refusal's exit code.
novar_home="${scratch}/home-novar"
cp -R "${projdir_home}" "${novar_home}"
cat > "${novar_home}/.claude/settings.json" <<JSON
{"hooks":{"PreToolUse":[{"matcher":"*","hooks":[
  {"type":"command","command":"bash \"\${NO_SUCH_HOOK_ROOT}/guard.sh\""}]}]}}
JSON
set +e
(cd "${novar_home}" && env -u CODEX_SANDBOX -u NO_SUCH_HOOK_ROOT CLAUDECODE=1 \
  HOME="${novar_home}" python3 "${gate}" preflight --repo "${repo}" \
  --snapshot "${test_dir}/fixtures/good/snapshot.json") \
  >"${scratch}/novar.out" 2>"${scratch}/novar.err"
novar_status=$?
set -e
test "${novar_status}" -eq 4
grep -q "L2 HOST-POLICY claude-code: ERROR" "${scratch}/novar.err"
grep -q "UNEVALUABLE L2 HOST-POLICY" "${scratch}/novar.err"
if grep -q "REFUSED by L2" "${scratch}/novar.err"; then
  echo "FAIL: an un-evaluable gate was reported as a refusal" >&2
  exit 1
fi

# 5. same hook, inactive host: reported but not blocking (shell is active)
(cd "${neutral}" && run "${clean_home}" python3 "${gate}" preflight --repo "${repo}" \
  --snapshot "${test_dir}/fixtures/good/snapshot.json") > "${scratch}/inactive.out"
grep -q "L2 HOST-POLICY codex: BLOCK" "${scratch}/inactive.out"
grep -q "PREFLIGHT GREEN" "${scratch}/inactive.out"

echo "PASS merge-authority preflight"
