#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cli="${repo_root}/skills/shared-skills-infra/scripts/repository_control_plane.py"
profile="${repo_root}/skills/shared-skills-infra/references/repository-control-plane-profile.default.json"
monitor_schema="${repo_root}/skills/shared-skills-infra/references/repository-control-plane-monitor-plan.v1.schema.json"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

python3 "${cli}" profile-check --profile "${profile}"
python3 -m py_compile "${cli}"
python3 -m json.tool "${profile}" >/dev/null
python3 -m json.tool "${repo_root}/skills/shared-skills-infra/references/repository-control-plane-profile.v1.schema.json" >/dev/null
python3 -m json.tool "${monitor_schema}" >/dev/null

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

# automatic merge is never admitted by the canonical profile
python3 - "${profile}" "${tmp}/bad-authority.json" <<'PY'
import json, sys
p=json.load(open(sys.argv[1]))
p['authority']['automatic_merge']=True
json.dump(p, open(sys.argv[2],'w'), indent=2)
PY
if python3 "${cli}" profile-check --profile "${tmp}/bad-authority.json" >/dev/null 2>&1; then
  echo 'FAIL: automatic merge authority was accepted' >&2
  exit 1
fi

# Git Town installer state must stay NOT_IMPLEMENTED until runtime-env supplies a pinned receipt-producing installer.
python3 - "${profile}" "${tmp}/bad-installer.json" <<'PY'
import json, sys
p=json.load(open(sys.argv[1]))
p['runtime_capabilities']['git_town']['installer_state']='IMPLEMENTED'
json.dump(p, open(sys.argv[2],'w'), indent=2)
PY
if python3 "${cli}" profile-check --profile "${tmp}/bad-installer.json" >/dev/null 2>&1; then
  echo 'FAIL: unproven Git Town installer was accepted' >&2
  exit 1
fi

# A project-local body must not shadow the canonical Skill closure.
mkdir -p "${consumer}/.agents/skills/shared-skills-infra"
printf 'body\n' > "${consumer}/.agents/skills/shared-skills-infra/extra.md"
if python3 "${cli}" verify --profile "${profile}" --consumer "${consumer}" >/dev/null 2>&1; then
  echo 'FAIL: project-local body shadow was accepted' >&2
  exit 1
fi
rm -rf "${consumer}/.agents/skills/shared-skills-infra"

# Exact dependency subject plus applicability: issue #2 requests stack delivery,
# while #1 stays simple and #3 is an explicitly included closed blocker.
cat > "${tmp}/issues.json" <<'JSON'
[
  {"repository":"example/repo","number":1,"state":"open","depends_on":[]},
  {"repository":"example/repo","number":2,"state":"open","depends_on":["example/repo#1","example/repo#3"],"required_phases":["STACK_DELIVERY"]},
  {"repository":"example/repo","number":3,"state":"closed","depends_on":[]}
]
JSON
python3 "${cli}" monitor-plan --issues "${tmp}/issues.json" > "${tmp}/plan.json"
python3 - "${tmp}/plan.json" "${monitor_schema}" <<'PY'
import copy, json, sys
from jsonschema import Draft202012Validator

plan=json.load(open(sys.argv[1]))
schema=json.load(open(sys.argv[2]))
validator=Draft202012Validator(schema)
validator.validate(plan)

assert plan['issues'] == ['example/repo#1', 'example/repo#2'], plan
assert plan['waves'] == [['example/repo#1'], ['example/repo#2']], plan
assert plan['automatic_merge'] is False
assert plan['automatic_conflict_resolution'] is False

simple=plan['issue_plans']['example/repo#1']
stack=plan['issue_plans']['example/repo#2']
assert simple['required_receipts'] == ['skill-resolution','shadow-admission','task-dag'], simple
simple_disp={x['phase']:x['disposition'] for x in simple['phase_dispositions']}
assert simple_disp['SPATIAL_INVARIANTS'] == 'MONITOR', simple_disp
assert simple_disp['STACK_DELIVERY'] == 'NOT_APPLICABLE_WITH_EVIDENCE', simple_disp
assert simple_disp['FORGE_RECONCILIATION'] == 'NOT_APPLICABLE_WITH_EVIDENCE', simple_disp
assert stack['required_receipts'] == ['skill-resolution','shadow-admission','task-dag','git-town-stack'], stack
stack_disp={x['phase']:x['disposition'] for x in stack['phase_dispositions']}
assert stack_disp['STACK_DELIVERY'] == 'REQUIRED', stack_disp
assert stack_disp['FORGE_RECONCILIATION'] == 'NOT_APPLICABLE_WITH_EVIDENCE', stack_disp
assert simple['execution_state'] == 'NOT_EXERCISED'
assert stack['execution_state'] == 'NOT_EXERCISED'

# Schema mutations: these shapes must never become a valid monitor receipt.
mutations=[]
m=copy.deepcopy(plan); del m['issue_plans']; mutations.append(('missing issue_plans', m))
m=copy.deepcopy(plan); m['issue_plans']['example/repo#1']['execution_state']='PASS'; mutations.append(('runtime PASS promotion', m))
m=copy.deepcopy(plan); m['automatic_merge']=True; mutations.append(('automatic merge widening', m))
m=copy.deepcopy(plan); m['issue_plans']['example/repo#1']['phase_dispositions'][4]['disposition']='PASS'; mutations.append(('invalid phase disposition', m))
m=copy.deepcopy(plan); m['issue_plans']['example/repo#1']['required_receipts'].append('provider-secret'); mutations.append(('unknown receipt', m))
m=copy.deepcopy(plan); m['issue_plans']['example/repo#1']['phase_dispositions'].pop(); mutations.append(('truncated phase contract', m))
for label, candidate in mutations:
    errors=list(validator.iter_errors(candidate))
    assert errors, f'{label} unexpectedly validated'
PY

# A closed blocker must be present in the exact packet. Presence, not network
# inference, is what distinguishes satisfied closure from an absent edge.
cat > "${tmp}/closed-only.json" <<'JSON'
[
  {"repository":"example/repo","number":10,"state":"open","depends_on":["example/repo#11"]},
  {"repository":"example/repo","number":11,"state":"closed","depends_on":[]}
]
JSON
python3 "${cli}" monitor-plan --issues "${tmp}/closed-only.json" > "${tmp}/closed-only-plan.json"
python3 - "${tmp}/closed-only-plan.json" "${monitor_schema}" <<'PY'
import json, sys
from jsonschema import Draft202012Validator
p=json.load(open(sys.argv[1]))
s=json.load(open(sys.argv[2]))
Draft202012Validator(s).validate(p)
assert p['issues'] == ['example/repo#10'], p
assert p['waves'] == [['example/repo#10']], p
assert p['issue_plans']['example/repo#10']['execution_state'] == 'NOT_EXERCISED'
PY

# Unknown phase hints must fail closed instead of silently widening execution.
cat > "${tmp}/unknown-phase.json" <<'JSON'
[
  {"repository":"example/repo","number":9,"state":"open","depends_on":[],"required_phases":["MAGIC_DEPLOY"]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/unknown-phase.json" >/dev/null 2>&1; then
  echo 'FAIL: unknown required phase was accepted' >&2
  exit 1
fi

# An absent dependency is not shorthand for "closed somewhere on the provider".
cat > "${tmp}/missing.json" <<'JSON'
[
  {"repository":"example/repo","number":20,"state":"open","depends_on":["example/repo#21"]}
]
JSON
set +e
missing_output="$(python3 "${cli}" monitor-plan --issues "${tmp}/missing.json" 2>&1)"
missing_exit=$?
set -e
if [ "${missing_exit}" -ne 2 ]; then
  echo "FAIL: missing dependency exit=${missing_exit}" >&2
  exit 1
fi
case "${missing_output}" in
  *"missing dependency closure: example/repo#20 -> example/repo#21"*) ;;
  *) echo "FAIL: missing dependency did not identify exact edge: ${missing_output}" >&2; exit 1 ;;
esac

# Self-edges receive their own diagnostic instead of hiding inside a generic cycle.
cat > "${tmp}/self.json" <<'JSON'
[
  {"repository":"example/repo","number":30,"state":"open","depends_on":["example/repo#30"]}
]
JSON
set +e
self_output="$(python3 "${cli}" monitor-plan --issues "${tmp}/self.json" 2>&1)"
self_exit=$?
set -e
if [ "${self_exit}" -ne 2 ]; then
  echo "FAIL: self dependency exit=${self_exit}" >&2
  exit 1
fi
case "${self_output}" in
  *"self dependency: example/repo#30 -> example/repo#30"*) ;;
  *) echo "FAIL: self dependency did not identify exact edge: ${self_output}" >&2; exit 1 ;;
esac

cat > "${tmp}/duplicate.json" <<'JSON'
[
  {"repository":"example/repo","number":40,"state":"open","depends_on":[]},
  {"repository":"example/repo","number":40,"state":"open","depends_on":[]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/duplicate.json" >/dev/null 2>&1; then
  echo 'FAIL: duplicate issue identity was accepted' >&2
  exit 1
fi

cat > "${tmp}/cycle.json" <<'JSON'
[
  {"repository":"example/repo","number":50,"state":"open","depends_on":["example/repo#51"]},
  {"repository":"example/repo","number":51,"state":"open","depends_on":["example/repo#50"]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/cycle.json" >/dev/null 2>&1; then
  echo 'FAIL: dependency cycle was accepted' >&2
  exit 1
fi

echo 'PASS repository control-plane profile, exact dependency closure, applicability gate, and monitor-plan schema'
