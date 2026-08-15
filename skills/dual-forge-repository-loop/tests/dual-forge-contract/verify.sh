#!/usr/bin/env bash
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${test_dir}/../.." && pwd)"
checker="${skill_dir}/scripts/check_dual_forge_contract.py"
exporter="${skill_dir}/scripts/export_git_proof.py"
origin_capture="${skill_dir}/scripts/capture_origin_ref.py"
reconciliation_capture="${skill_dir}/scripts/capture_reconciliation.py"
forgejo_delivery_capture="${skill_dir}/scripts/capture_forgejo_delivery.py"
good="${test_dir}/fixtures/good.json"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT
cp -R "${test_dir}/fixtures/proof" "${tmp}/proof"

python3 "${checker}" "${good}" >/dev/null || { echo 'good fixture rejected' >&2; exit 1; }
python3 "${reconciliation_capture}" replay \
  --transport "${test_dir}/fixtures/proof/reconciliation-transport.json" \
  --observation "${test_dir}/fixtures/proof/reconciliation.json" >/dev/null
python3 "${forgejo_delivery_capture}" replay \
  --transport "${test_dir}/fixtures/proof/forgejo-delivery-transport.json" \
  --observation "${test_dir}/fixtures/proof/forgejo-delivery.json" >/dev/null

# The live producer must obtain the worktree branch, HEAD/base ancestry, and
# exclusive branch lease from a real Git worktree, not from receipt prose.
worktree_case="${tmp}/worktree-producer"
mkdir -p "${worktree_case}/repo"
git -C "${worktree_case}/repo" init -q
git -C "${worktree_case}/repo" fast-import --quiet < "${test_dir}/fixtures/proof/repository.fast-import"
python3 - "${forgejo_delivery_capture}" "${test_dir}/fixtures/proof" \
  "${worktree_case}/repo" "${worktree_case}/repair" <<'PY'
import copy, importlib.util, json, pathlib, subprocess, sys
script, proof, repo, worktree = map(pathlib.Path, sys.argv[1:])
sys.path.insert(0, str(script.parent))
spec = importlib.util.spec_from_file_location("forgejo_delivery_producer_test", script)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
fixture = json.loads((proof / "forgejo-delivery-transport.json").read_text())
responses = {
    entry["argv"][1].removeprefix("/api/v1/"): entry["stdout"]
    for entry in fixture["captures"]
    if entry["argv"][0] == "forgejo-api-authenticated-read"
}
module.credentials = lambda _url: ("user", "password")
module.forgejo_json = lambda _url, endpoint, _auth: (
    json.loads(responses[endpoint]), responses[endpoint]
)
module.capture_artifact = lambda *_args: copy.deepcopy(fixture["desktop_artifacts"][0])
creation = module.materialize(
    repo, worktree, 12, "4cb614454eeb07e81ac1718746e2e99d3c3287d1",
    "8a14401b45489bdc9a24b3a8a20178f1c06452e6400cc1b542ebc908e9bb4049",
    "2026-08-14T09:55:05Z",
)
subprocess.run(
    ["git", "-C", str(worktree), "merge", "--ff-only", "572aa3d2f0d50771cf2ab856f59a9b5923fed1f2"],
    check=True, capture_output=True, text=True,
)
transport = module.capture(
    "neon/example", "main", [12], [8],
    "572aa3d2f0d50771cf2ab856f59a9b5923fed1f2", repo,
    "http://localhost:3000", 12, worktree,
    "4cb614454eeb07e81ac1718746e2e99d3c3287d1",
    creation,
)
observation = json.loads((proof / "forgejo-delivery.json").read_text())
observation["captured_at"] = transport["captured_at"]
observation["recovery_worktree"]["observed_at"] = transport["captured_at"]
observation["recovery_worktree"]["created_at"] = creation["created_at"]
observation["recovery_worktree"]["creation_receipt_sha256"] = module.hashlib.sha256(
    module.canonical(creation)
).hexdigest()
module.verify_observation(transport, observation)
assert transport["captures"][4]["stdout"].startswith("<worktree>\ntrue\n")
assert transport["captures"][9]["stdout"].count(
    "branch refs/heads/recovery/issue-12-4b50cc080d2d8fc8"
) == 1
try:
    module.capture(
        "neon/example", "main", [12], [8],
        "572aa3d2f0d50771cf2ab856f59a9b5923fed1f2", repo,
        "http://localhost:3000", 12, repo,
        "4cb614454eeb07e81ac1718746e2e99d3c3287d1", creation,
    )
except module.CaptureError as error:
    assert "main working tree" in str(error)
else:
    raise AssertionError("main working tree was accepted as recovery worktree")
alien = repo.parent / "alien"
alien_worktree = repo.parent / "alien-repair"
subprocess.run(["git", "clone", "-q", str(repo), str(alien)], check=True)
subprocess.run(
    ["git", "-C", str(alien), "worktree", "add", "-q", "--lock", "--reason",
     creation["lock_reason"], "-b", creation["branch"], str(alien_worktree),
     "572aa3d2f0d50771cf2ab856f59a9b5923fed1f2"],
    check=True,
)
try:
    module.capture(
        "neon/example", "main", [12], [8],
        "572aa3d2f0d50771cf2ab856f59a9b5923fed1f2", repo,
        "http://localhost:3000", 12, alien_worktree,
        "4cb614454eeb07e81ac1718746e2e99d3c3287d1", creation,
    )
except module.CaptureError as error:
    assert "object graph" in str(error)
else:
    raise AssertionError("same-commit worktree from another clone was accepted")
PY

# The live producer must accept Forgejo's array list responses and enumerate
# every open PR, not only PRs targeting the default branch.
python3 - "${reconciliation_capture}" <<'PY'
import importlib.util, json, pathlib, sys
path = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(path.parent))
spec = importlib.util.spec_from_file_location("capture_reconciliation_test", path)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
module.credentials = lambda _url: ("user", "password")
identity = {"invoked_path": "/usr/bin/gh", "resolved_path": "/usr/bin/gh", "sha256": "3" * 64, "version": "gh version 2.82.0 (fixture)"}
module.gh_identity = lambda _timeout: identity
def gh(gh_path, argv, _timeout):
    if argv[-1] == "repos/ed3c/example":
        payload = {"id": 123, "full_name": "ed3c/example", "default_branch": "main"}
    else:
        payload = [[]]
    return module.record([gh_path, *argv], 0, json.dumps(payload, separators=(",", ":")))
def forgejo(_url, endpoint, _auth):
    if endpoint == "repos/neon/example":
        payload = {"id": 456, "full_name": "neon/example", "default_branch": "main"}
    else:
        payload = []
    return payload, json.dumps(payload, separators=(",", ":"))
module.gh_capture = gh
module.forgejo_json = forgejo
transport = module.capture("ed3c/example", "neon/example", "main", "http://localhost:3000", 5)
argv = [entry["argv"] for entry in transport["captures"]]
assert ["/usr/bin/gh", "api", "--paginate", "--slurp", "repos/ed3c/example/pulls?state=open&per_page=100"] in argv
assert ["forgejo-api-authenticated-read", "/api/v1/repos/neon/example/pulls?state=open&limit=50&page=1"] in argv
PY

mkdir -p "${tmp}/fake-bin"
printf '#!/bin/sh\necho fake-gh\n' > "${tmp}/fake-bin/gh"
chmod +x "${tmp}/fake-bin/gh"
PATH="${tmp}/fake-bin:${PATH}" python3 - "${reconciliation_capture}" "${tmp}/fake-bin/gh" <<'PY'
import importlib.util, pathlib, sys
path = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(path.parent))
spec = importlib.util.spec_from_file_location("reconciliation_path_test", path)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
identity = module.gh_identity(5)
assert identity["invoked_path"] in module.GH_CANDIDATES
assert identity["invoked_path"] != sys.argv[2]
assert len(identity["sha256"]) == 64
PY

# Producer-to-checker arrival from a real Git object database.
export_case="${tmp}/export-positive"
mkdir -p "${export_case}/proof" "${export_case}/repo"
cp "${good}" "${export_case}/receipt.json"
cp "${test_dir}/fixtures/proof/"*.json "${export_case}/proof/"
git -C "${export_case}/repo" init -q
git -C "${export_case}/repo" fast-import --quiet < "${test_dir}/fixtures/proof/repository.fast-import"
python3 "${exporter}" \
  --repo-root "${export_case}/repo" \
  --github-main 93c33411137875108419c2abe4dbe8f4d84ad5d6 \
  --forgejo-main 4cb614454eeb07e81ac1718746e2e99d3c3287d1 \
  --local-main 572aa3d2f0d50771cf2ab856f59a9b5923fed1f2 \
  --candidate 997b637730f967af63f435d8f28fe6677a209574 \
  --output "${export_case}/proof/exported.fast-import" >/dev/null
python3 - "${export_case}/receipt.json" "${export_case}/proof/exported.fast-import" <<'PY'
import hashlib, json, pathlib, sys
receipt, proof = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
d = json.loads(receipt.read_text())
d["publication"]["git_proof"] = {
    "path": "proof/exported.fast-import",
    "sha256": hashlib.sha256(proof.read_bytes()).hexdigest(),
}
receipt.write_text(json.dumps(d, indent=2) + "\n")
PY
python3 "${checker}" "${export_case}/receipt.json" >/dev/null || {
  echo 'canonical Git proof producer output was rejected' >&2
  exit 1
}
if python3 "${exporter}" \
  --repo-root "${export_case}/repo" \
  --github-main 572aa3d2f0d50771cf2ab856f59a9b5923fed1f2 \
  --forgejo-main 4cb614454eeb07e81ac1718746e2e99d3c3287d1 \
  --local-main 572aa3d2f0d50771cf2ab856f59a9b5923fed1f2 \
  --candidate 93c33411137875108419c2abe4dbe8f4d84ad5d6 \
  --output "${export_case}/proof/uncontained.fast-import" >/dev/null 2>&1; then
  echo 'Git proof producer accepted an uncontained baseline' >&2
  exit 1
fi
git -C "${export_case}/repo" config user.name fixture
git -C "${export_case}/repo" config user.email fixture@example.invalid
forked_local="$(git -C "${export_case}/repo" commit-tree \
  '93c33411137875108419c2abe4dbe8f4d84ad5d6^{tree}' \
  -p 93c33411137875108419c2abe4dbe8f4d84ad5d6 -m 'forked local main')"
forked_candidate="$(git -C "${export_case}/repo" commit-tree \
  "${forked_local}^{tree}" -p "${forked_local}" \
  -p 4cb614454eeb07e81ac1718746e2e99d3c3287d1 -m 'late Forgejo merge')"
if python3 "${exporter}" \
  --repo-root "${export_case}/repo" \
  --github-main 93c33411137875108419c2abe4dbe8f4d84ad5d6 \
  --forgejo-main 4cb614454eeb07e81ac1718746e2e99d3c3287d1 \
  --local-main "${forked_local}" \
  --candidate "${forked_candidate}" \
  --output "${export_case}/proof/late-forgejo.fast-import" >/dev/null 2>&1; then
  echo 'Git proof producer accepted Forgejo merged after local main' >&2
  exit 1
fi

# Canonical local origin producer binds its transport bytes rather than a
# hand-authored authority string.
git -C "${export_case}/repo" update-ref refs/heads/main 572aa3d2f0d50771cf2ab856f59a9b5923fed1f2
git -C "${export_case}/repo" remote add github git@github.com:ed3c/example.git
git -C "${export_case}/repo" remote add forgejo http://localhost:3000/neon/example.git
python3 "${origin_capture}" local \
  --repository ed3c/example \
  --forgejo-repository neon/example \
  --default-branch main \
  --repo-root "${export_case}/repo" \
  --output-dir "${export_case}/captured" >/dev/null
python3 - "${export_case}/captured/local-main-observation.json" "${export_case}/captured/local-main-transport.json" <<'PY'
import hashlib, json, pathlib, sys
observation = json.loads(pathlib.Path(sys.argv[1]).read_text())
transport = pathlib.Path(sys.argv[2])
assert observation["transport"]["sha256"] == hashlib.sha256(transport.read_bytes()).hexdigest()
assert observation["sha"] == "572aa3d2f0d50771cf2ab856f59a9b5923fed1f2"
PY

# A local admitted remote is one exact destination, not merely the first URL
# printed from a multi-push remote.
git -C "${export_case}/repo" config --add remote.forgejo.pushurl http://localhost:3000/neon/example.git
git -C "${export_case}/repo" config --add remote.forgejo.pushurl git@github.com:ed3c/example.git
if python3 "${origin_capture}" local \
  --repository ed3c/example \
  --forgejo-repository neon/example \
  --default-branch main \
  --repo-root "${export_case}/repo" \
  --output-dir "${export_case}/captured-multi-url" >/dev/null 2>&1; then
  echo 'local origin capture accepted multiple Forgejo push URLs' >&2
  exit 1
fi
git -C "${export_case}/repo" config --unset-all remote.forgejo.pushurl

# Positive recovery arrival: billing-open is admitted only when the manifest,
# snapshot, and content-addressed owner recovery all bind the same timestamps.
recovery_case="${tmp}/recovery-positive"
mkdir -p "${recovery_case}"
cp "${good}" "${recovery_case}/receipt.json"
cp -R "${test_dir}/fixtures/proof" "${recovery_case}/proof"
python3 - "${recovery_case}/receipt.json" "${recovery_case}/proof" <<'PY'
import hashlib, json, pathlib, sys
receipt, root = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
d = json.loads(receipt.read_text())
def write(name, value):
    payload = (json.dumps(value, indent=2) + "\n").encode()
    (root / name).write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()
recovery = {
    "schema": "github-actions-billing-recovery/v1",
    "repository_id": 123,
    "owner_login": "ed3c",
    "blocker_observed_at": "2026-08-14T09:59:30Z",
    "recovered_at": "2026-08-14T10:00:04Z",
    "note": "owner restored billing before publication evaluation",
}
recovery_sha = write("recovery.json", recovery)
snapshot = json.loads((root / "pre-snapshot.json").read_text())
snapshot["actions"] = {
    "circuit": "billing-open",
    "observed_at": recovery["blocker_observed_at"],
    "blocker": "billing-or-spending-limit",
    "latest_check": None,
}
snapshot_sha = write("pre-snapshot.json", snapshot)
bundle = d["publication"]["decision_bundle"]
bundle["snapshot"]["sha256"] = snapshot_sha
bundle["recovery"] = {"path": "proof/recovery.json", "sha256": recovery_sha}
manifest = json.loads((root / "decision.json").read_text())
manifest["inputs"]["snapshot_sha256"] = snapshot_sha
manifest["inputs"]["recovery_sha256"] = recovery_sha
bundle["manifest"]["sha256"] = write("decision.json", manifest)
receipt.write_text(json.dumps(d, indent=2) + "\n")
PY
python3 "${checker}" "${recovery_case}/receipt.json" >/dev/null || {
  echo 'valid content-addressed billing recovery rejected' >&2
  exit 1
}

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

expect_semantic_red() {
  local name="$1" code="$2"
  local case_dir="${tmp}/${name}"
  mkdir -p "${case_dir}"
  cp "${good}" "${case_dir}/receipt.json"
  cp -R "${test_dir}/fixtures/proof" "${case_dir}/proof"
  python3 - "${case_dir}/receipt.json" "${case_dir}/proof" "${code}" <<'PY'
import hashlib, json, pathlib, re, subprocess, sys, tempfile
receipt, proof_root, code = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
d = json.loads(receipt.read_text())
bindings = {
    "decision.json": d["publication"]["decision_bundle"]["manifest"],
    "policy.json": d["publication"]["decision_bundle"]["policy"],
    "pre-snapshot.json": d["publication"]["decision_bundle"]["snapshot"],
    "verification.json": d["publication"]["decision_bundle"]["verification"],
    "evidence.json": d["publication"]["decision_bundle"]["evidence"],
    "contract.json": d["publication"]["decision_bundle"]["contract"],
    "actions-observation.json": d["actions"]["proof"]["observation"],
    "actions-snapshot.json": d["actions"]["proof"]["snapshot"],
    "actions-transport.json": d["actions"]["proof"]["transport"],
    "repository.fast-import": d["publication"]["git_proof"],
    "github-main-observation.json": d["observations"]["github_main"],
    "forgejo-main-observation.json": d["observations"]["forgejo_main"],
    "local-main-observation.json": d["observations"]["local_main"],
    "reconciliation.json": d["reconciliation"],
    "forgejo-delivery.json": d["implementation"]["forgejo_delivery"],
}
def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
def load(name):
    return json.loads((proof_root / name).read_text())
def save(name, value):
    payload = (json.dumps(value, indent=2) + "\n").encode()
    (proof_root / name).write_bytes(payload)
    bindings[name]["sha256"] = hashlib.sha256(payload).hexdigest()
def save_bytes(name, payload):
    (proof_root / name).write_bytes(payload)
    bindings[name]["sha256"] = hashlib.sha256(payload).hexdigest()
exec(code, globals(), locals())
receipt.write_text(json.dumps(d, indent=2) + "\n")
PY
  if python3 "${checker}" "${case_dir}/receipt.json" >/dev/null 2>&1; then
    echo "semantic mutation stayed green: ${name}" >&2
    exit 1
  fi
}

expect_red same-remote "d['forgejo']['remote_name']=d['github']['remote_name']"
expect_red split-github-repository "d['github']['repository_full_name']='other/repository'"
expect_red split-local-default-branch "d['local']['main_branch']='trunk'"
expect_red collapsed-namespace "d['issue_namespaces']['forgejo']=d['issue_namespaces']['github']"
expect_red wrong-order "d['history'][5],d['history'][6]=d['history'][6],d['history'][5]"
expect_red stale-actions-head "d['publication']['candidate_sha']='5555555555555555555555555555555555555555'"
expect_red tampered-decision-digest "d['publication']['decision_bundle']['manifest']['sha256']='0'*64"
expect_red missing-local-evidence "d['publication']['decision_bundle']['evidence']['path']='proof/missing.json'"
expect_red tampered-actions-snapshot "d['actions']['proof']['snapshot']['sha256']='0'*64"
expect_red tampered-git-proof-digest "d['publication']['git_proof']['sha256']='0'*64"
expect_red local-runtime-unproved "d['evidence']['forgejo_runtime']='NOT_EXERCISED'"
expect_red worktree-unproved "d['evidence']['local_worktrees']='NOT_EXERCISED'"
expect_red github-actions-unproved "d['evidence']['github_actions']='SKIPPED_BY_POLICY'"
expect_red missing-evidence-lane "del d['evidence']['github_ingress']"
expect_red fabricated-final-merge "d['evidence']['final_merge']='PASS'"
expect_red missing-forgejo-delivery "del d['implementation']"

expect_semantic_red cross-branch-actions "o=load('actions-observation.json'); o['branch']['name']='agent/other'; save('actions-observation.json',o); s=load('actions-snapshot.json'); s['branch']['name']='agent/other'; save('actions-snapshot.json',s)"
expect_semantic_red missing-pr-sweep "r=load('reconciliation.json'); r['github_open_prs']=None; save('reconciliation.json',r)"
expect_semantic_red omitted-publication-pr "r=load('reconciliation.json'); r['github_open_prs']=[x for x in r['github_open_prs'] if x['number']!=42]; save('reconciliation.json',r)"
expect_semantic_red provider-and-route-omit-publication-pr "t=load('reconciliation-transport.json'); pages=json.loads(t['captures'][1]['stdout']); pages[0]=[x for x in pages[0] if x['number']!=42]; stdout=json.dumps(pages,separators=(',',':')); t['captures'][1]['stdout']=stdout; t['captures'][1]['stdout_sha256']=hashlib.sha256(stdout.encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'reconciliation-transport.json').write_bytes(payload); r=load('reconciliation.json'); r['transport']['sha256']=hashlib.sha256(payload).hexdigest(); r['github_open_prs']=[x for x in r['github_open_prs'] if x['number']!=42]; save('reconciliation.json',r)"
expect_semantic_red omitted-open-issue "r=load('reconciliation.json'); r['open_issues']=[x for x in r['open_issues'] if not (x['forge']=='github' and x['number']==99)]; save('reconciliation.json',r)"
expect_semantic_red publication-no-longer-wip "r=load('reconciliation.json'); r['publication_subject']['wip']=False; r['github_open_prs'][1]['wip']=False; save('reconciliation.json',r)"
expect_semantic_red publication-route-forged "r=load('reconciliation.json'); r['github_open_prs'][1]['classification']='UNAFFECTED'; r['github_open_prs'][1]['terminal_route']='NO_ACTION'; save('reconciliation.json',r)"
expect_semantic_red duplicate-candidate-wip-subject "t=load('reconciliation-transport.json'); pages=json.loads(t['captures'][1]['stdout']); pages[0].append({'number':43,'draft':True,'head':{'sha':d['publication']['candidate_sha']},'base':{'ref':'other'}}); stdout=json.dumps(pages,separators=(',',':')); t['captures'][1]['stdout']=stdout; t['captures'][1]['stdout_sha256']=hashlib.sha256(stdout.encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'reconciliation-transport.json').write_bytes(payload); r=load('reconciliation.json'); r['transport']['sha256']=hashlib.sha256(payload).hexdigest(); r['github_open_prs'].append({'number':43,'head_sha':d['publication']['candidate_sha'],'base_branch':'other','wip':True,'classification':'PUBLICATION_SUBJECT','terminal_route':'WIP_CAPTURED','receipt':'github:pr/43@candidate'}); save('reconciliation.json',r)"
expect_semantic_red closed-issue-reappears-open "t=load('reconciliation-transport.json'); stdout='[{\"number\":12}]'; t['captures'][-1]['stdout']=stdout; t['captures'][-1]['stdout_sha256']=hashlib.sha256(stdout.encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'reconciliation-transport.json').write_bytes(payload); r=load('reconciliation.json'); r['transport']['sha256']=hashlib.sha256(payload).hexdigest(); r['open_issues'].append({'forge':'forgejo','number':12,'scope':'AFFECTED','terminal_route':'IMPLEMENTED','receipt':'forgejo:issue/12'}); save('reconciliation.json',r)"
expect_semantic_red blocking-pr-route "r=load('reconciliation.json'); r['github_open_prs'].append({'number':35,'head_sha':'93c33411137875108419c2abe4dbe8f4d84ad5d6','classification':'SEMANTIC_CONFLICT','terminal_route':'UNRESOLVED','receipt':'github:pr/35'}); save('reconciliation.json',r)"
expect_semantic_red unrouted-affected-issue "r=load('reconciliation.json'); r['open_issues'][0]['terminal_route']='NO_ACTION'; save('reconciliation.json',r)"
expect_semantic_red unresolved-conflicts "r=load('reconciliation.json'); r['unresolved_conflicts']=[{'path':'conflicted.txt'}]; save('reconciliation.json',r)"
expect_semantic_red stale-origin-observation "o=load('github-main-observation.json'); o['captured_at']='2000-01-01T00:00:00Z'; save('github-main-observation.json',o)"
expect_semantic_red split-observation-default-branch "o=load('forgejo-main-observation.json'); o['default_branch']='trunk'; o['ref']='refs/heads/trunk'; save('forgejo-main-observation.json',o)"
expect_semantic_red forged-origin-transport "t=load('github-main-transport.json'); t['producer']='agent-self-asserted'; payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'github-main-transport.json').write_bytes(payload); o=load('github-main-observation.json'); o['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('github-main-observation.json',o)"
expect_semantic_red forged-origin-source "t=load('forgejo-main-transport.json'); t['source_identity']='agent-self-asserted-no-capture'; payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-main-transport.json').write_bytes(payload); o=load('forgejo-main-observation.json'); o['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-main-observation.json',o)"
expect_semantic_red resigned-provider-repository-id "t=load('github-main-transport.json'); raw=json.loads(t['capture']['stdout'][0]); raw['id']=999; stdout=json.dumps(raw,separators=(',',':')); t['capture']['stdout'][0]=stdout; t['capture']['stdout_sha256'][0]=hashlib.sha256(stdout.encode()).hexdigest(); t['repository_id']=999; payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'github-main-transport.json').write_bytes(payload); o=load('github-main-observation.json'); o['repository_id']=999; o['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('github-main-observation.json',o)"
expect_semantic_red unrelated-local-remote-binding "t=load('local-main-transport.json'); t['remote_bindings']['github_repository']='unrelated/repo'; t['capture']['stdout'][1]='unrelated/repo'; t['capture']['stdout_sha256'][1]=hashlib.sha256(b'unrelated/repo').hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'local-main-transport.json').write_bytes(payload); o=load('local-main-observation.json'); o['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('local-main-observation.json',o)"
expect_semantic_red resigned-actions-raw-check "t=load('actions-transport.json'); raw=json.loads(t['captures'][3]['stdout']); raw[0]['check_runs'][0]['id']=999; stdout=json.dumps(raw,separators=(',',':')); t['captures'][3]['stdout']=stdout; t['captures'][3]['stdout_sha256']=hashlib.sha256(stdout.encode()).hexdigest(); save('actions-transport.json',t)"
expect_semantic_red duplicate-actions-run-fully-resigned "t=load('actions-transport.json'); raw=json.loads(t['captures'][3]['stdout']); second=dict(raw[0]['check_runs'][0]); second.update({'id':9002,'details_url':'https://github.com/ed3c/example/actions/runs/7002/job/5002','check_suite':{'id':8002}}); raw[0]['check_runs'].append(second); stdout=json.dumps(raw,separators=(',',':')); t['captures'][3]['stdout']=stdout; t['captures'][3]['stdout_sha256']=hashlib.sha256(stdout.encode()).hexdigest(); empty=hashlib.sha256(b'').hexdigest(); run_stdout=json.dumps({'id':7002,'workflow_id':6001,'head_sha':d['publication']['candidate_sha']},separators=(',',':')); ann_stdout='[[]]'; gh=t['gh_executable']['invoked_path']; t['captures'].extend([{'argv':[gh,'api','repos/ed3c/example/actions/runs/7002'],'exit':0,'stdout':run_stdout,'stdout_sha256':hashlib.sha256(run_stdout.encode()).hexdigest(),'stderr':'','stderr_sha256':empty},{'argv':[gh,'api','--paginate','--slurp','repos/ed3c/example/check-runs/9002/annotations?per_page=100'],'exit':0,'stdout':ann_stdout,'stdout_sha256':hashlib.sha256(ann_stdout.encode()).hexdigest(),'stderr':'','stderr_sha256':empty}]); save('actions-transport.json',t); o=load('actions-observation.json'); second_o=dict(o['check_runs'][0]); second_o.update({'id':9002,'check_suite_id':8002,'workflow_run_id':7002,'job_id':5002}); o['check_runs'].append(second_o); save('actions-observation.json',o)"
expect_semantic_red omitted-forgejo-issue-receipt "f=load('forgejo-delivery.json'); f['issues']=[]; save('forgejo-delivery.json',f)"
expect_semantic_red short-forgejo-issue-context "t=load('forgejo-delivery-transport.json'); raw=json.loads(t['captures'][1]['stdout']); raw['body']='short'; stdout=json.dumps(raw,separators=(',',':')); t['captures'][1]['stdout']=stdout; t['captures'][1]['stdout_sha256']=hashlib.sha256(stdout.encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); f['issues'][0]['body_sha256']=hashlib.sha256(b'short').hexdigest(); f['issues'][0]['context_state']='INCOMPLETE'; save('forgejo-delivery.json',f)"
expect_semantic_red unsent-desktop-recovery "t=load('forgejo-delivery-transport.json'); comments=json.loads(t['captures'][2]['stdout']); comments[0]['body']='## Why this fresh session exists\n## Independent review BLOCKS\n## Required output and implementation boundary\n## Desktop submission receipt requirement\ncomposer only'; stdout=json.dumps(comments,separators=(',',':')); t['captures'][2]['stdout']=stdout; t['captures'][2]['stdout_sha256']=hashlib.sha256(stdout.encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); f['issues'][0]['comments_sha256']=hashlib.sha256(comments[0]['body'].encode()).hexdigest(); f['issues'][0]['desktop_submission_state']='NOT_EXERCISED'; save('forgejo-delivery.json',f)"
expect_semantic_red desktop-screenshot-digest-forged "t=load('forgejo-delivery-transport.json'); comments=json.loads(t['captures'][2]['stdout']); body=comments[0]['body']; match=re.search(r'<!--\\s*three-strike-recovery\\s*(\\{.*?\\})\\s*-->',body,re.S); packet=json.loads(match.group(1)); packet['desktop_submission']['screenshot_sha256']='0'*64; comments[0]['body']=body[:match.start(1)]+json.dumps(packet,separators=(',',':'))+body[match.end(1):]; stdout=json.dumps(comments,separators=(',',':')); t['captures'][2]['stdout']=stdout; t['captures'][2]['stdout_sha256']=hashlib.sha256(stdout.encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-delivery.json',f)"
expect_semantic_red desktop-observer-not-comment-author "t=load('forgejo-delivery-transport.json'); comments=json.loads(t['captures'][2]['stdout']); body=comments[0]['body']; match=re.search(r'<!--\\s*three-strike-recovery\\s*(\\{.*?\\})\\s*-->',body,re.S); packet=json.loads(match.group(1)); packet['desktop_submission']['observer']['id']=99; comments[0]['body']=body[:match.start(1)]+json.dumps(packet,separators=(',',':'))+body[match.end(1):]; stdout=json.dumps(comments,separators=(',',':')); t['captures'][2]['stdout']=stdout; t['captures'][2]['stdout_sha256']=hashlib.sha256(stdout.encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-delivery.json',f)"
expect_semantic_red incomplete-three-strike-ledger "t=load('forgejo-delivery-transport.json'); comments=json.loads(t['captures'][2]['stdout']); body=comments[0]['body']; match=re.search(r'<!--\\s*three-strike-recovery\\s*(\\{.*?\\})\\s*-->',body,re.S); packet=json.loads(match.group(1)); packet['attempts']=packet['attempts'][:2]; comments[0]['body']=body[:match.start(1)]+json.dumps(packet,separators=(',',':'))+body[match.end(1):]; stdout=json.dumps(comments,separators=(',',':')); t['captures'][2]['stdout']=stdout; t['captures'][2]['stdout_sha256']=hashlib.sha256(stdout.encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-delivery.json',f)"
expect_semantic_red missing-recovery-worktree "f=load('forgejo-delivery.json'); del f['recovery_worktree']; save('forgejo-delivery.json',f)"
expect_semantic_red recovery-worktree-before-desktop-response "t=load('forgejo-delivery-transport.json'); t['captured_at']='2026-08-14T09:55:04Z'; payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['captured_at']=t['captured_at']; f['recovery_worktree']['observed_at']=t['captured_at']; f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-delivery.json',f)"
expect_semantic_red recovery-worktree-wrong-issue "t=load('forgejo-delivery-transport.json'); t['recovery_worktree']['issue_number']=13; payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); f['recovery_worktree']['issue_number']=13; save('forgejo-delivery.json',f)"
expect_semantic_red recovery-worktree-wrong-head "t=load('forgejo-delivery-transport.json'); entry=t['captures'][4]; entry['stdout']=entry['stdout'].replace('572aa3d2f0d50771cf2ab856f59a9b5923fed1f2','0'*40); entry['stdout_sha256']=hashlib.sha256(entry['stdout'].encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-delivery.json',f)"
expect_semantic_red duplicate-recovery-writer-lease "t=load('forgejo-delivery-transport.json'); entry=t['captures'][9]; entry['stdout'] += '\nworktree <other-worktree-2>\nHEAD 572aa3d2f0d50771cf2ab856f59a9b5923fed1f2\nbranch refs/heads/recovery/issue-12-4b50cc080d2d8fc8\nlocked desktop-recovery:8a14401b45489bdc\n'; entry['stdout_sha256']=hashlib.sha256(entry['stdout'].encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-delivery.json',f)"
expect_semantic_red missing-worktree-creation "t=load('forgejo-delivery-transport.json'); del t['recovery_worktree']['creation']; payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-delivery.json',f)"
expect_semantic_red stale-worktree-creation "t=load('forgejo-delivery-transport.json'); t['recovery_worktree']['creation']['created_at']='2026-08-14T09:55:04Z'; payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); f['recovery_worktree']['created_at']='2026-08-14T09:55:04Z'; save('forgejo-delivery.json',f)"
expect_semantic_red preexisting-worktree-before-creation "t=load('forgejo-delivery-transport.json'); entry=t['recovery_worktree']['creation']['captures'][0]; entry['stdout'] += 'worktree <worktree>\n'; entry['stdout_sha256']=hashlib.sha256(entry['stdout'].encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-delivery.json',f)"
expect_semantic_red split-worktree-common-dir "t=load('forgejo-delivery-transport.json'); entry=t['captures'][8]; entry['stdout']='<other-common-git-dir>\n'; entry['stdout_sha256']=hashlib.sha256(entry['stdout'].encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-delivery.json',f)"
expect_semantic_red missing-forgejo-pr-closure-link "t=load('forgejo-delivery-transport.json'); raw=json.loads(t['captures'][3]['stdout']); raw['body']='No closure link'; stdout=json.dumps(raw,separators=(',',':')); t['captures'][3]['stdout']=stdout; t['captures'][3]['stdout_sha256']=hashlib.sha256(stdout.encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); f['merged_prs'][0]['body_sha256']=hashlib.sha256(b'No closure link').hexdigest(); f['merged_prs'][0]['closes_issues']=[]; save('forgejo-delivery.json',f)"
expect_semantic_red forged-forgejo-merged-pr "f=load('forgejo-delivery.json'); f['merged_prs'][0]['merged']=False; save('forgejo-delivery.json',f)"
expect_semantic_red forged-local-main-merge "f=load('forgejo-delivery.json'); f['local_main_merge']['parents']=[]; save('forgejo-delivery.json',f)"
expect_semantic_red split-forgejo-repository-id "t=load('forgejo-delivery-transport.json'); raw=json.loads(t['captures'][0]['stdout']); raw['id']=999; stdout=json.dumps(raw,separators=(',',':')); t['captures'][0]['stdout']=stdout; t['captures'][0]['stdout_sha256']=hashlib.sha256(stdout.encode()).hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-delivery-transport.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['forgejo_repository_id']=999; f['transport']['sha256']=hashlib.sha256(payload).hexdigest(); c=load('forgejo-verification-contract.json'); c['repository_id']=999; payload=(json.dumps(c,indent=2)+'\n').encode(); (proof_root/'forgejo-verification-contract.json').write_bytes(payload); f['verification']['contract']['sha256']=hashlib.sha256(payload).hexdigest(); e=load('forgejo-verification-evidence.json'); e['repository_id']=999; e['contract_sha256']=hashlib.sha256(canonical(c)).hexdigest(); content=dict(e); content.pop('content_sha256'); e['content_sha256']=hashlib.sha256(canonical(content)).hexdigest(); payload=(json.dumps(e,indent=2)+'\n').encode(); (proof_root/'forgejo-verification-evidence.json').write_bytes(payload); f['verification']['evidence']['sha256']=hashlib.sha256(payload).hexdigest(); v=load('forgejo-verification.json'); v['repository_id']=999; v['evidence_sha256']=hashlib.sha256(canonical(e)).hexdigest(); payload=(json.dumps(v,indent=2)+'\n').encode(); (proof_root/'forgejo-verification.json').write_bytes(payload); f['verification']['receipt']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-delivery.json',f)"
expect_semantic_red failed-forgejo-verification "v=load('forgejo-verification.json'); v['status']='FAIL'; payload=(json.dumps(v,indent=2)+'\n').encode(); (proof_root/'forgejo-verification.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['verification']['receipt']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-delivery.json',f)"
expect_semantic_red forged-forgejo-verification-command "v=load('forgejo-verification.json'); v['commands']=['false']; payload=(json.dumps(v,indent=2)+'\n').encode(); (proof_root/'forgejo-verification.json').write_bytes(payload); f=load('forgejo-delivery.json'); f['verification']['receipt']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-delivery.json',f)"
expect_semantic_red unrequired-smoke-check "d['actions']['proof']['check_name']='unrequired-smoke'; o=load('actions-observation.json'); o['check_runs'][0]['name']='unrequired-smoke'; save('actions-observation.json',o); s=load('actions-snapshot.json'); save('actions-snapshot.json',s)"
expect_semantic_red cross-pr-transition "o=load('actions-observation.json'); o['pull_requests'][0]['number']=43; save('actions-observation.json',o); s=load('actions-snapshot.json'); s['pull_request']['number']=43; save('actions-snapshot.json',s)"
expect_semantic_red unauthorized-ready-transition "o=load('actions-observation.json'); o['pull_requests'][0]['draft']=True; save('actions-observation.json',o); s=load('actions-snapshot.json'); s['pull_request']['state']='draft'; save('actions-snapshot.json',s)"
expect_semantic_red stale-same-head-check "o=load('actions-observation.json'); o['check_runs'][0]['completed_at']='2026-08-14T09:59:00Z'; save('actions-observation.json',o); s=load('actions-snapshot.json'); s['actions']['latest_check']['completed_at']='2026-08-14T09:59:00Z'; save('actions-snapshot.json',s)"
expect_semantic_red future-resigned-actions "o=load('actions-observation.json'); o['pull_requests'][0]['updated_at']='2099-01-01T00:01:00Z'; o['check_runs'][0]['completed_at']='2099-01-01T00:04:00Z'; o['captured_at']='2099-01-01T00:05:00Z'; save('actions-observation.json',o); s=load('actions-snapshot.json'); s['pull_request']['last_published_at']='2099-01-01T00:01:00Z'; s['actions']['latest_check']['completed_at']='2099-01-01T00:04:00Z'; s['captured_at']='2099-01-01T00:05:00Z'; save('actions-snapshot.json',s)"
expect_semantic_red post-capture-check "o=load('actions-observation.json'); o['check_runs'][0]['completed_at']='2026-08-14T10:06:00Z'; save('actions-observation.json',o); s=load('actions-snapshot.json'); s['actions']['latest_check']['completed_at']='2026-08-14T10:06:00Z'; save('actions-snapshot.json',s)"
expect_semantic_red rewritten-evaluation-time "m=load('decision.json'); m['evaluated_at']='2000-01-01T00:00:00Z'; save('decision.json',m)"
expect_semantic_red manifest-input-drift "m=load('decision.json'); m['inputs']['snapshot_sha256']='0'*64; save('decision.json',m)"
expect_semantic_red recovery-binding-drift "m=load('decision.json'); m['inputs']['recovery_sha256']='0'*64; save('decision.json',m)"
expect_semantic_red resigned-command-drift "e=load('evidence.json'); e['commands'][0]['argv']=['false']; body=dict(e); body.pop('content_sha256'); e['content_sha256']=hashlib.sha256(canonical(body)).hexdigest(); ev_digest=hashlib.sha256(canonical(e)).hexdigest(); save('evidence.json',e); v=load('verification.json'); v['evidence_sha256']=ev_digest; save('verification.json',v)"
expect_semantic_red uncontained-candidate "stream=(proof_root/'repository.fast-import').read_bytes().replace(b'from :6\nM 100644 :7 candidate.txt',b'M 100644 :7 candidate.txt',1); save_bytes('repository.fast-import',stream); td=tempfile.TemporaryDirectory(); repo=pathlib.Path(td.name)/'r.git'; subprocess.run(['git','init','-q','--bare',str(repo)],check=True); subprocess.run(['git',f'--git-dir={repo}','fast-import','--quiet'],input=stream,check=True); d['publication']['candidate_sha']=subprocess.check_output(['git',f'--git-dir={repo}','rev-parse','refs/heads/candidate'],text=True).strip()"

partial="${tmp}/partial.json"
python3 - "${good}" "${partial}" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
d["history"] = d["history"][:-1]
d["evidence"]["github_actions"] = "NOT_EXERCISED"
json.dump(d, open(sys.argv[2], "w"), indent=2)
PY
set +e
partial_output="$(python3 "${checker}" "${partial}" 2>&1)"
partial_rc=$?
set -e
[ "${partial_rc}" -eq 3 ] || { echo "partial receipt exit=${partial_rc}, want 3" >&2; exit 1; }
grep -q '^NOT_EXERCISED ' <<<"${partial_output}" || { echo 'partial receipt falsely claimed PASS' >&2; exit 1; }

set +e
python3 "${checker}" "${tmp}/absent.json" >/dev/null 2>&1
rc=$?
set -e
[ "${rc}" -eq 64 ] || { echo "absent input exit=${rc}, want 64" >&2; exit 1; }

echo "SELFTEST GREEN: positive admitted; 68 planted publication/order/authority defects refused; partial and absent inputs stayed distinct"
