#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cli="${repo_root}/skills/shared-skills-infra/scripts/repository_control_plane.py"
profile="${repo_root}/skills/shared-skills-infra/references/repository-control-plane-profile.default.json"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

python3 "${cli}" profile-check --profile "${profile}"
python3 -m py_compile "${cli}"
python3 -m json.tool "${profile}" >/dev/null
python3 -m json.tool "${repo_root}/skills/shared-skills-infra/references/repository-control-plane-profile.v1.schema.json" >/dev/null

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

cat > "${tmp}/issues.json" <<'JSON'
[
  {"repository":"example/repo","number":1,"state":"open","depends_on":[]},
  {"repository":"example/repo","number":2,"state":"open","depends_on":["example/repo#1"]},
  {"repository":"example/repo","number":3,"state":"closed","depends_on":[]}
]
JSON
python3 "${cli}" monitor-plan --issues "${tmp}/issues.json" > "${tmp}/plan.json"
python3 - "${tmp}/plan.json" <<'PY'
import json, sys
p=json.load(open(sys.argv[1]))
assert p['waves'] == [['example/repo#1'], ['example/repo#2']], p
assert p['automatic_merge'] is False
assert p['automatic_conflict_resolution'] is False
PY

cat > "${tmp}/duplicate.json" <<'JSON'
[
  {"repository":"example/repo","number":1,"state":"open","depends_on":[]},
  {"repository":"example/repo","number":1,"state":"open","depends_on":[]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/duplicate.json" >/dev/null 2>&1; then
  echo 'FAIL: duplicate issue identity was accepted' >&2
  exit 1
fi

cat > "${tmp}/cycle.json" <<'JSON'
[
  {"repository":"example/repo","number":1,"state":"open","depends_on":["example/repo#2"]},
  {"repository":"example/repo","number":2,"state":"open","depends_on":["example/repo#1"]}
]
JSON
if python3 "${cli}" monitor-plan --issues "${tmp}/cycle.json" >/dev/null 2>&1; then
  echo 'FAIL: dependency cycle was accepted' >&2
  exit 1
fi

echo 'PASS repository control-plane profile and thin attachment'
