#!/usr/bin/env bash
set -uo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${test_dir}/../.." && pwd)"
checker="${skill_dir}/scripts/check_dual_forge_contract.py"
good="${test_dir}/fixtures/good.json"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

python3 "${checker}" "${good}" >/dev/null || { echo 'good fixture rejected' >&2; exit 1; }

expect_red() {
  local name="$1" code="$2"
  local target="${tmp}/${name}.json"
  python3 - "${good}" "${target}" "${code}" <<'PY'
import json, sys
src, dst, code = sys.argv[1:]
d = json.load(open(src))
exec(code, {"d": d})
json.dump(d, open(dst, "w"), indent=2)
PY
  if python3 "${checker}" "${target}" >/dev/null 2>&1; then
    echo "mutation stayed green: ${name}" >&2
    exit 1
  fi
}

expect_red same-remote "d['forgejo']['remote_name']=d['github']['remote_name']"
expect_red collapsed-namespace "d['issue_namespaces']['forgejo']=d['issue_namespaces']['github']"
expect_red wrong-order "d['history'][5],d['history'][6]=d['history'][6],d['history'][5]"
expect_red missing-pr-sweep "d['reconciliation']['open_prs_enumerated']=False"
expect_red unresolved-conflicts "d['reconciliation']['conflicts_routed']=False"
expect_red stale-actions-head "d['actions']['head_sha']='5555555555555555555555555555555555555555'"
expect_red local-runtime-unproved "d['evidence']['forgejo_runtime']='NOT_EXERCISED'"
expect_red worktree-unproved "d['evidence']['local_worktrees']='NOT_EXERCISED'"
expect_red github-actions-unproved "d['evidence']['github_actions']='SKIPPED_BY_POLICY'"

set +e
python3 "${checker}" "${tmp}/absent.json" >/dev/null 2>&1
rc=$?
set -e
[ "${rc}" -eq 64 ] || { echo "absent input exit=${rc}, want 64" >&2; exit 1; }

echo "SELFTEST GREEN: positive admitted; 9 planted publication/order/authority defects refused; absent input stayed distinct"
