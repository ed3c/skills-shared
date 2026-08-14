#!/usr/bin/env bash
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${test_dir}/../.." && pwd)"
checker="${skill_dir}/scripts/check_dual_forge_contract.py"
exporter="${skill_dir}/scripts/export_git_proof.py"
origin_capture="${skill_dir}/scripts/capture_origin_ref.py"
good="${test_dir}/fixtures/good.json"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT
cp -R "${test_dir}/fixtures/proof" "${tmp}/proof"

python3 "${checker}" "${good}" >/dev/null || { echo 'good fixture rejected' >&2; exit 1; }

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
import hashlib, json, pathlib, subprocess, sys, tempfile
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
    "repository.fast-import": d["publication"]["git_proof"],
    "github-main-observation.json": d["observations"]["github_main"],
    "forgejo-main-observation.json": d["observations"]["forgejo_main"],
    "local-main-observation.json": d["observations"]["local_main"],
    "reconciliation.json": d["reconciliation"],
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

expect_semantic_red cross-branch-actions "o=load('actions-observation.json'); o['branch']['name']='agent/other'; save('actions-observation.json',o); s=load('actions-snapshot.json'); s['branch']['name']='agent/other'; save('actions-snapshot.json',s)"
expect_semantic_red missing-pr-sweep "r=load('reconciliation.json'); r['github_open_prs']=None; save('reconciliation.json',r)"
expect_semantic_red blocking-pr-route "r=load('reconciliation.json'); r['github_open_prs'].append({'number':35,'head_sha':'93c33411137875108419c2abe4dbe8f4d84ad5d6','classification':'SEMANTIC_CONFLICT','terminal_route':'UNRESOLVED','receipt':'github:pr/35'}); save('reconciliation.json',r)"
expect_semantic_red unrouted-affected-issue "r=load('reconciliation.json'); r['affected_issues'].append({'forge':'github','number':99,'terminal_route':'UNROUTED','receipt':'github:issue/99'}); save('reconciliation.json',r)"
expect_semantic_red unresolved-conflicts "r=load('reconciliation.json'); r['unresolved_conflicts']=[{'path':'conflicted.txt'}]; save('reconciliation.json',r)"
expect_semantic_red stale-origin-observation "o=load('github-main-observation.json'); o['captured_at']='2000-01-01T00:00:00Z'; save('github-main-observation.json',o)"
expect_semantic_red split-observation-default-branch "o=load('forgejo-main-observation.json'); o['default_branch']='trunk'; o['ref']='refs/heads/trunk'; save('forgejo-main-observation.json',o)"
expect_semantic_red forged-origin-transport "t=load('github-main-transport.json'); t['producer']='agent-self-asserted'; payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'github-main-transport.json').write_bytes(payload); o=load('github-main-observation.json'); o['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('github-main-observation.json',o)"
expect_semantic_red forged-origin-source "t=load('forgejo-main-transport.json'); t['source_identity']='agent-self-asserted-no-capture'; payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'forgejo-main-transport.json').write_bytes(payload); o=load('forgejo-main-observation.json'); o['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('forgejo-main-observation.json',o)"
expect_semantic_red resigned-provider-repository-id "t=load('github-main-transport.json'); raw=json.loads(t['capture']['stdout'][0]); raw['id']=999; stdout=json.dumps(raw,separators=(',',':')); t['capture']['stdout'][0]=stdout; t['capture']['stdout_sha256'][0]=hashlib.sha256(stdout.encode()).hexdigest(); t['repository_id']=999; payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'github-main-transport.json').write_bytes(payload); o=load('github-main-observation.json'); o['repository_id']=999; o['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('github-main-observation.json',o)"
expect_semantic_red unrelated-local-remote-binding "t=load('local-main-transport.json'); t['remote_bindings']['github_repository']='unrelated/repo'; t['capture']['stdout'][1]='unrelated/repo'; t['capture']['stdout_sha256'][1]=hashlib.sha256(b'unrelated/repo').hexdigest(); payload=(json.dumps(t,indent=2)+'\n').encode(); (proof_root/'local-main-transport.json').write_bytes(payload); o=load('local-main-observation.json'); o['transport']['sha256']=hashlib.sha256(payload).hexdigest(); save('local-main-observation.json',o)"
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

echo "SELFTEST GREEN: positive admitted; 37 planted publication/order/authority defects refused; partial and absent inputs stayed distinct"
