#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL="$(cd "$HERE/../.." && pwd)"
SCRIPT="$SKILL/scripts/plan_tech_lead_stack.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 -m py_compile "$SCRIPT"
python3 - "$TMP" <<'PY'
import copy, json, pathlib, sys
root=pathlib.Path(sys.argv[1])
good={
  "schema":"git-town-stacked-pr-worker/tech-lead-plan/v1",
  "subject":{"repository":"example/monorepo","base_branch":"main","base_commit":"1111111111111111111111111111111111111111","tree":"2222222222222222222222222222222222222222"},
  "goal":"Introduce a path-disjoint blindspot contract and Tech Lead planner, then converge shared indexes.",
  "max_parallel_workers":2,
  "architecture_constraints":[
    {"id":"sqlite-authority","statement":"SQLite owns durable observations and LanceDB is a rebuildable projection.","enforced_by":["blindspot-contract","convergence"],"verification":["orphan vector projections fail","deleting vectors does not change ledger admission"]},
    {"id":"true-dependencies-only","statement":"A child branch must consume an explicit unmerged contract from its parent.","enforced_by":["tech-lead-planner","convergence"],"verification":["fake linear child fixture fails"]}
  ],
  "tasks":[
    {"id":"blindspot-contract","title":"Implement the hybrid blindspot ledger contract","stack_class":"sibling","head_branch":"agent/blindspot-contract","parent":"main","depends_on":[],"allowed_paths":["skills/repo-agent-native/**"],"excluded_paths":["skills/repo-agent-native/evals/sealed"],"provides_contracts":["blindspot-ledger-v1"],"consumes_contracts":[],"non_goals":["install provider binaries","merge the PR"],"required_evals":["bash skills/repo-agent-native/tests/blindspot-hybrid/verify.sh"],"negative_controls":["remove source readback and require exit 2"],"blindspot_queries":[{"id":"provider-boundaries","intent":"Find every provider output that could bypass source readback.","lanes":["grepai","scip","tree-sitter","serena","source-readback","test","lancedb"],"readback_required":true,"negative_control":"admit a provider row directly and require failure"}],"evidence_boundary":"Fixture PASS proves the checker contract only; live providers are NOT_EXERCISED.","cleanup_contract":"Temporary SQLite files and reports are removed by the test trap.","rollback_subject":"1111111111111111111111111111111111111111","human_owned_operations":["merge","provider installation"]},
    {"id":"tech-lead-planner","title":"Compile goal graphs into path-disjoint Worker packets","stack_class":"sibling","head_branch":"agent/tech-lead-planner","parent":"main","depends_on":[],"allowed_paths":["skills/git-town-stacked-pr-worker/**"],"excluded_paths":["skills/git-town-stacked-pr-worker/evals/sealed"],"provides_contracts":["tech-lead-plan-v1"],"consumes_contracts":[],"non_goals":["spawn Agents","create branches","merge the PR"],"required_evals":["bash skills/git-town-stacked-pr-worker/tests/tech-lead-planner/verify.sh"],"negative_controls":["overlapping sibling path leases must fail"],"blindspot_queries":[{"id":"task-boundaries","intent":"Find shared mutable paths that make sibling execution unsafe.","lanes":["grepai","tree-sitter","source-readback"],"readback_required":true,"negative_control":"give two siblings the same path and require failure"}],"evidence_boundary":"Plan compile does not prove Git Town or a Worker ran.","cleanup_contract":"Compiler output is written only to the explicit output directory.","rollback_subject":"1111111111111111111111111111111111111111","human_owned_operations":["merge","semantic conflict resolution"]},
    {"id":"convergence","title":"Converge the admitted sibling contracts and central indexes","stack_class":"convergence","head_branch":"agent/ade-convergence","parent":"main","depends_on":["blindspot-contract","tech-lead-planner"],"allowed_paths":["README.md","docs/traceability"],"excluded_paths":[],"provides_contracts":["ade-converged-v1"],"consumes_contracts":["blindspot-ledger-v1","tech-lead-plan-v1"],"non_goals":["change sibling implementations","merge without Human Admit"],"required_evals":["bash tests/verify.sh"],"negative_controls":["missing sibling receipt must block convergence"],"blindspot_queries":[{"id":"convergence-coverage","intent":"Verify central indexes cover every admitted sibling artifact.","lanes":["grepai","scip","source-readback","test"],"readback_required":true,"negative_control":"remove one sibling link and require the index checker to fail"}],"evidence_boundary":"Convergence starts only after both sibling inputs have immutable admitted subjects.","cleanup_contract":"No sibling branch or worktree is deleted by convergence.","rollback_subject":"1111111111111111111111111111111111111111","human_owned_operations":["merge","release promotion"]}
  ]
}
variants={"good":good}
overlap=copy.deepcopy(good); overlap['tasks'][1]['allowed_paths']=['skills/repo-agent-native/scripts']; variants['overlap']=overlap
cycle=copy.deepcopy(good); cycle['tasks'][0]['depends_on']=['tech-lead-planner']; cycle['tasks'][1]['depends_on']=['blindspot-contract']; variants['cycle']=cycle
missing=copy.deepcopy(good); missing['tasks'][0]['blindspot_queries'][0].update({'lanes':['grepai','scip'],'readback_required':False}); variants['missing-readback']=missing
fake=copy.deepcopy(good); fake['tasks'][1].update({'stack_class':'child','parent':'blindspot-contract','depends_on':['blindspot-contract'],'consumes_contracts':[]}); variants['fake-child']=fake
for name,value in variants.items(): (root/f'{name}.json').write_text(json.dumps(value,indent=2)+'\n')
PY

python3 "$SCRIPT" verify --plan "$TMP/good.json" >"$TMP/good-result.json"
python3 "$SCRIPT" compile --plan "$TMP/good.json" --output "$TMP/compiled" >"$TMP/receipt.json"

test -f "$TMP/compiled/normalized-plan.json"
test -f "$TMP/compiled/compile-receipt.json"
test -f "$TMP/compiled/stack.dot"
test -f "$TMP/compiled/worker-packets/blindspot-contract.json"
test -f "$TMP/compiled/worker-packets/tech-lead-planner.json"
test -f "$TMP/compiled/worker-packets/convergence.json"

python3 - "$TMP/compiled/compile-receipt.json" "$TMP/compiled/worker-packets/tech-lead-planner.json" <<'PY'
import json, sys
receipt=json.load(open(sys.argv[1])); packet=json.load(open(sys.argv[2]))
assert receipt['evidence_state']=='PASS' and receipt['runtime_state']=='NOT_EXERCISED'
assert receipt['effects']=={'branches_created':False,'worktrees_created':False,'agents_spawned':False,'providers_invoked':False,'remote_publication':False}
assert packet['parent_branch']=='main'
assert 'blindspot-contract' in packet['parallel_safe_siblings']
assert packet['blindspot_queries'][0]['readback_required'] is True
PY

expect_fail() {
  local fixture="$1" expected="$2"
  set +e
  python3 "$SCRIPT" verify --plan "$fixture" >"$TMP/out" 2>"$TMP/err"
  local status=$?
  set -e
  test "$status" -eq 2
  grep -q "$expected" "$TMP/err"
}
expect_fail "$TMP/overlap.json" PATH_LEASE_COLLISION
expect_fail "$TMP/cycle.json" TASK_DAG_CYCLE
expect_fail "$TMP/missing-readback.json" BLINDSPOT_QUERY_INCOMPLETE
expect_fail "$TMP/fake-child.json" FAKE_LINEAR_CHILD

echo "tech-lead-planner contract PASS"
