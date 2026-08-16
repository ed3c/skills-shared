#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cli="${repo_root}/skills/shared-skills-infra/scripts/repository_control_plane.py"
profile="${repo_root}/skills/shared-skills-infra/references/repository-control-plane-profile.default.json"
schema="${repo_root}/skills/shared-skills-infra/references/repository-control-plane-monitor-plan.v1.schema.json"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

python3 "${cli}" profile-check --profile "${profile}"
python3 -m py_compile "${cli}"
python3 -m json.tool "${profile}" >/dev/null
python3 -m json.tool "${repo_root}/skills/shared-skills-infra/references/repository-control-plane-profile.v1.schema.json" >/dev/null
if [[ -f "${schema}" ]]; then python3 -m json.tool "${schema}" >/dev/null; fi

consumer="${tmp}/consumer"
mkdir -p "${consumer}"
git -C "${consumer}" init -q
git -C "${consumer}" config user.email control-plane@example.invalid
git -C "${consumer}" config user.name control-plane-selftest
printf 'fixture\n' > "${consumer}/README.md"
git -C "${consumer}" add README.md
git -C "${consumer}" commit -qm init

python3 "${cli}" attach --profile "${profile}" --consumer "${consumer}"
python3 "${cli}" verify --profile "${profile}" --consumer "${consumer}"
test -f "${consumer}/.agents/control-plane/profile.json"
test -f "${consumer}/.agents/control-plane/requirements.json"
test -f "${consumer}/.agents/bindings/repository-control-plane.json"

python3 - "${profile}" "${tmp}/bad-authority.json" <<'PY'
import json, sys
p=json.load(open(sys.argv[1])); p['authority']['automatic_merge']=True
json.dump(p, open(sys.argv[2],'w'), indent=2)
PY
if python3 "${cli}" profile-check --profile "${tmp}/bad-authority.json" >/dev/null 2>&1; then
  echo 'FAIL: automatic merge authority was accepted' >&2; exit 1
fi

python3 - "${profile}" "${tmp}/bad-installer.json" <<'PY'
import json, sys
p=json.load(open(sys.argv[1])); p['runtime_capabilities']['git_town']['installer_state']='IMPLEMENTED'
json.dump(p, open(sys.argv[2],'w'), indent=2)
PY
if python3 "${cli}" profile-check --profile "${tmp}/bad-installer.json" >/dev/null 2>&1; then
  echo 'FAIL: unproven Git Town installer was accepted' >&2; exit 1
fi

mkdir -p "${consumer}/.agents/skills/shared-skills-infra"
printf 'body\n' > "${consumer}/.agents/skills/shared-skills-infra/extra.md"
if python3 "${cli}" verify --profile "${profile}" --consumer "${consumer}" >/dev/null 2>&1; then
  echo 'FAIL: project-local body shadow was accepted' >&2; exit 1
fi
rm -rf "${consumer}/.agents/skills/shared-skills-infra"

cat > "${tmp}/issues.json" <<'JSON'
[
  {"repository":"example/repo","number":1,"state":"open","depends_on":[]},
  {"repository":"example/repo","number":2,"state":"open","depends_on":["example/repo#1"],"required_phases":["STACK_DELIVERY"]},
  {"repository":"example/repo","number":3,"state":"closed","depends_on":[]},
  {"repository":"example/repo","number":4,"state":"open","depends_on":["example/repo#3"]}
]
JSON
python3 "${cli}" monitor-plan --issues "${tmp}/issues.json" > "${tmp}/plan.json"
python3 - "${tmp}/plan.json" <<'PY'
import json, sys
p=json.load(open(sys.argv[1]))
assert p['waves'] == [['example/repo#1','example/repo#4'], ['example/repo#2']], p
assert p['automatic_merge'] is False
assert p['automatic_conflict_resolution'] is False
simple=p['issue_plans']['example/repo#1']
stack=p['issue_plans']['example/repo#2']
closed_dep=p['issue_plans']['example/repo#4']
assert simple['required_receipts'] == ['skill-resolution','shadow-admission','task-dag'], simple
simple_disp={x['phase']:x['disposition'] for x in simple['phase_dispositions']}
assert simple_disp['SPATIAL_INVARIANTS'] == 'MONITOR', simple_disp
assert simple_disp['STACK_DELIVERY'] == 'NOT_APPLICABLE_WITH_EVIDENCE', simple_disp
assert simple_disp['FORGE_RECONCILIATION'] == 'NOT_APPLICABLE_WITH_EVIDENCE', simple_disp
assert stack['required_receipts'] == ['skill-resolution','shadow-admission','task-dag','git-town-stack'], stack
stack_disp={x['phase']:x['disposition'] for x in stack['phase_dispositions']}
assert stack_disp['STACK_DELIVERY'] == 'REQUIRED', stack_disp
assert stack_disp['FORGE_RECONCILIATION'] == 'NOT_APPLICABLE_WITH_EVIDENCE', stack_disp
assert closed_dep['execution_state'] == 'NOT_EXERCISED'
assert all(x['execution_state']=='NOT_EXERCISED' for x in p['issue_plans'].values())
PY

cat > "${tmp}/missing.json" <<'JSON'
[
  {"repository":"example/repo","number":5,"state":"open","depends_on":["example/repo#999"]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/missing.json" >/dev/null 2>&1; then
  echo 'FAIL: absent dependency was treated as satisfied' >&2; exit 1
fi

cat > "${tmp}/self.json" <<'JSON'
[
  {"repository":"example/repo","number":6,"state":"open","depends_on":["example/repo#6"]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/self.json" >/dev/null 2>&1; then
  echo 'FAIL: self dependency was accepted' >&2; exit 1
fi

cat > "${tmp}/unknown-phase.json" <<'JSON'
[
  {"repository":"example/repo","number":9,"state":"open","depends_on":[],"required_phases":["MAGIC_DEPLOY"]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/unknown-phase.json" >/dev/null 2>&1; then
  echo 'FAIL: unknown required phase was accepted' >&2; exit 1
fi

cat > "${tmp}/duplicate.json" <<'JSON'
[
  {"repository":"example/repo","number":1,"state":"open","depends_on":[]},
  {"repository":"example/repo","number":1,"state":"open","depends_on":[]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/duplicate.json" >/dev/null 2>&1; then
  echo 'FAIL: duplicate issue identity was accepted' >&2; exit 1
fi

cat > "${tmp}/cycle.json" <<'JSON'
[
  {"repository":"example/repo","number":1,"state":"open","depends_on":["example/repo#2"]},
  {"repository":"example/repo","number":2,"state":"open","depends_on":["example/repo#1"]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/cycle.json" >/dev/null 2>&1; then
  echo 'FAIL: dependency cycle was accepted' >&2; exit 1
fi

cat > "${tmp}/bad-state.json" <<'JSON'
[
  {"repository":"example/repo","number":10,"state":"done","depends_on":[]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/bad-state.json" >/dev/null 2>&1; then
  echo 'FAIL: unknown issue state was accepted' >&2; exit 1
fi

echo 'PASS repository control-plane profile, applicability, and exact dependency closure'
