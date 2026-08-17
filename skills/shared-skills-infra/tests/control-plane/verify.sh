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
python3 -m json.tool "${schema}" >/dev/null
python3 - "${schema}" <<'PY'
import json, sys, jsonschema
jsonschema.Draft202012Validator.check_schema(json.load(open(sys.argv[1])))
PY

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

# Exact dependency subject + applicability: open blocker orders the next wave;
# included closed blocker satisfies the edge; only explicit Stack applicability
# promotes the Stack receipt.
cat > "${tmp}/issues.json" <<'JSON'
[
  {"repository":"example/repo","number":1,"state":"open","depends_on":[]},
  {"repository":"example/repo","number":2,"state":"open","depends_on":["example/repo#1","example/repo#3"],"required_phases":["STACK_DELIVERY"]},
  {"repository":"example/repo","number":3,"state":"closed","depends_on":[]},
  {"repository":"example/repo","number":4,"state":"open","depends_on":["example/repo#3"]}
]
JSON
python3 "${cli}" monitor-plan --issues "${tmp}/issues.json" > "${tmp}/plan.json"
python3 - "${tmp}/plan.json" "${schema}" <<'PY'
import copy, json, sys, jsonschema
p=json.load(open(sys.argv[1])); s=json.load(open(sys.argv[2]))
validator=jsonschema.Draft202012Validator(s); validator.validate(p)
assert p['issues'] == ['example/repo#1','example/repo#2','example/repo#4'], p
assert p['waves'] == [['example/repo#1','example/repo#4'], ['example/repo#2']], p
simple=p['issue_plans']['example/repo#1']; stack=p['issue_plans']['example/repo#2']
assert simple['required_receipts'] == ['skill-resolution','shadow-admission','task-dag'], simple
sd={x['phase']:x['disposition'] for x in simple['phase_dispositions']}
assert sd['SPATIAL_INVARIANTS']=='MONITOR'
assert sd['STACK_DELIVERY']=='NOT_APPLICABLE_WITH_EVIDENCE'
assert sd['FORGE_RECONCILIATION']=='NOT_APPLICABLE_WITH_EVIDENCE'
assert stack['required_receipts'] == ['skill-resolution','shadow-admission','task-dag','git-town-stack'], stack
kd={x['phase']:x['disposition'] for x in stack['phase_dispositions']}
assert kd['STACK_DELIVERY']=='REQUIRED'
assert kd['FORGE_RECONCILIATION']=='NOT_APPLICABLE_WITH_EVIDENCE'
assert all(v['execution_state']=='NOT_EXERCISED' for v in p['issue_plans'].values())
# Planted mutations: each shape must stay invalid, otherwise the schema is
# decoration rather than a gate.
mutations=[]
m=copy.deepcopy(p); m['automatic_merge']=True; mutations.append(('automatic merge widening', m))
m=copy.deepcopy(p); m['issue_plans']['example/repo#1']['execution_state']='PASS'; mutations.append(('runtime PASS promotion', m))
m=copy.deepcopy(p); del m['issue_plans']; mutations.append(('missing issue_plans', m))
m=copy.deepcopy(p); m['issue_plans']['example/repo#1']['phase_dispositions'][4]['disposition']='PASS'; mutations.append(('unknown disposition value', m))
m=copy.deepcopy(p); m['issue_plans']['example/repo#1']['required_receipts'].append('provider-secret'); mutations.append(('unknown receipt', m))
m=copy.deepcopy(p); m['issue_plans']['example/repo#1']['phase_dispositions'].pop(); mutations.append(('truncated phase contract', m))
# Applicability is positional: the first three phases are unconditionally
# REQUIRED and each phase owns exactly one receipt, so neither a waived
# BOOTSTRAP nor a reordered contract may validate.
m=copy.deepcopy(p); m['issue_plans']['example/repo#1']['phase_dispositions'][0]['disposition']='NOT_APPLICABLE_WITH_EVIDENCE'; mutations.append(('waived mandatory phase', m))
m=copy.deepcopy(p); d=m['issue_plans']['example/repo#1']['phase_dispositions']; d[0], d[3] = d[3], d[0]; mutations.append(('reordered phase contract', m))
m=copy.deepcopy(p); m['issue_plans']['example/repo#1']['phase_dispositions'][3]['receipt']='git-town-stack'; mutations.append(('phase/receipt mismatch', m))
for label, candidate in mutations:
    if not list(validator.iter_errors(candidate)):
        raise AssertionError(f'schema accepted {label}')
PY

# Closed blocker is satisfied only when it is present in the exact packet.
cat > "${tmp}/closed-only.json" <<'JSON'
[
  {"repository":"example/repo","number":10,"state":"open","depends_on":["example/repo#11"]},
  {"repository":"example/repo","number":11,"state":"closed","depends_on":[]}
]
JSON
python3 "${cli}" monitor-plan --issues "${tmp}/closed-only.json" > "${tmp}/closed-only-plan.json"
python3 - "${tmp}/closed-only-plan.json" "${schema}" <<'PY'
import json, sys, jsonschema
p=json.load(open(sys.argv[1])); s=json.load(open(sys.argv[2]))
jsonschema.Draft202012Validator(s).validate(p)
assert p['issues']==['example/repo#10']; assert p['waves']==[['example/repo#10']]
assert p['issue_plans']['example/repo#10']['execution_state']=='NOT_EXERCISED'
PY

cat > "${tmp}/missing.json" <<'JSON'
[
  {"repository":"example/repo","number":20,"state":"open","depends_on":["example/repo#21"]}
]
JSON
set +e
missing_output="$(python3 "${cli}" monitor-plan --issues "${tmp}/missing.json" 2>&1)"; missing_exit=$?
set -e
if [ "${missing_exit}" -ne 2 ]; then echo "FAIL: missing dependency exit=${missing_exit}" >&2; exit 1; fi
case "${missing_output}" in *"missing dependency closure: example/repo#20 -> example/repo#21"*) ;; *) echo "FAIL: missing edge diagnostic: ${missing_output}" >&2; exit 1 ;; esac

cat > "${tmp}/self.json" <<'JSON'
[
  {"repository":"example/repo","number":30,"state":"open","depends_on":["example/repo#30"]}
]
JSON
set +e
self_output="$(python3 "${cli}" monitor-plan --issues "${tmp}/self.json" 2>&1)"; self_exit=$?
set -e
if [ "${self_exit}" -ne 2 ]; then echo "FAIL: self dependency exit=${self_exit}" >&2; exit 1; fi
case "${self_output}" in *"self dependency: example/repo#30 -> example/repo#30"*) ;; *) echo "FAIL: self edge diagnostic: ${self_output}" >&2; exit 1 ;; esac

cat > "${tmp}/unknown-phase.json" <<'JSON'
[
  {"repository":"example/repo","number":35,"state":"open","depends_on":[],"required_phases":["MAGIC_DEPLOY"]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/unknown-phase.json" >/dev/null 2>&1; then echo 'FAIL: unknown phase accepted' >&2; exit 1; fi

cat > "${tmp}/duplicate.json" <<'JSON'
[
  {"repository":"example/repo","number":40,"state":"open","depends_on":[]},
  {"repository":"example/repo","number":40,"state":"open","depends_on":[]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/duplicate.json" >/dev/null 2>&1; then echo 'FAIL: duplicate identity accepted' >&2; exit 1; fi

cat > "${tmp}/cycle.json" <<'JSON'
[
  {"repository":"example/repo","number":50,"state":"open","depends_on":["example/repo#51"]},
  {"repository":"example/repo","number":51,"state":"open","depends_on":["example/repo#50"]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/cycle.json" >/dev/null 2>&1; then echo 'FAIL: dependency cycle accepted' >&2; exit 1; fi

cat > "${tmp}/bad-state.json" <<'JSON'
[
  {"repository":"example/repo","number":60,"state":"done","depends_on":[]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/bad-state.json" >/dev/null 2>&1; then echo 'FAIL: unknown state accepted' >&2; exit 1; fi

echo 'PASS repository control-plane profile, applicability, exact dependency closure, monitor schema, and Shadow authority gates'
