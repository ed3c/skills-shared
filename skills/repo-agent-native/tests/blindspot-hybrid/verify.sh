#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL="$(cd "$HERE/../.." && pwd)"
SCRIPT="$SKILL/scripts/blindspot_contract.py"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/tmp.XXXXXXXX")"
trap 'rm -rf "$TMP"' EXIT

python3 -m py_compile "$SCRIPT"
python3 - "$TMP" <<'PY'
import copy, json, pathlib, sys
root=pathlib.Path(sys.argv[1])
subject={
  "schema":"blindspot-hybrid/subject/v1",
  "repository":"example/repository",
  "commit":"1111111111111111111111111111111111111111",
  "tree":"2222222222222222222222222222222222222222"
}
good={
  "schema":"blindspot-hybrid/events/v1",
  "subject":subject,
  "events":[
    {"id":"intent-auth","lane":"grepai","kind":"intent_anchor","path":"src/auth.py","symbol":"authenticate","links":[],"admitted":False,"payload":{"query":"authentication boundary"}},
    {"id":"ast-auth","lane":"tree-sitter","kind":"ast_skeleton","path":"src/auth.py","symbol":"authenticate","links":["intent-auth"],"admitted":False,"payload":{"node":"function_definition"}},
    {"id":"scip-auth-ref","lane":"scip","kind":"reference","path":"src/auth.py","symbol":"authenticate","links":["intent-auth"],"admitted":False,"payload":{"relation":"reference"}},
    {"id":"serena-auth","lane":"serena","kind":"symbol_read","path":"src/auth.py","symbol":"authenticate","links":["intent-auth","scip-auth-ref"],"admitted":False,"payload":{"operation":"find_symbol","effect":"read-only"}},
    {"id":"readback-auth","lane":"source-readback","kind":"source_readback","path":"src/auth.py","symbol":"authenticate","links":["intent-auth","scip-auth-ref","serena-auth"],"admitted":True,"payload":{"line_start":10,"line_end":28}},
    {"id":"vector-auth","lane":"lancedb","kind":"similarity_projection","path":"src/auth.py","symbol":"authenticate","links":["readback-auth"],"admitted":False,"payload":{"vector_key":"obs:readback-auth"}},
    {"id":"test-auth","lane":"test","kind":"test_observation","path":"tests/test_auth.py","symbol":"test_authenticate","links":["readback-auth"],"admitted":True,"payload":{"passed":True,"exit":0}}
  ]
}
hollow=copy.deepcopy(good)
hollow["events"]=[e for e in hollow["events"] if e["id"] not in {"ast-auth","readback-auth","test-auth"}]
wrong=copy.deepcopy(good); wrong["subject"]["commit"]="3333333333333333333333333333333333333333"
self_admit=copy.deepcopy(good); self_admit["events"][0]["admitted"]=True
drift=copy.deepcopy(good); drift["events"][0]["payload"]["query"]="changed bytes"
for name,value in {"subject":subject,"good":good,"hollow":hollow,"wrong-subject":wrong,"self-admit":self_admit,"drift":drift}.items():
    (root/f"{name}.json").write_text(json.dumps(value,indent=2)+"\n")
PY

python3 "$SCRIPT" init --db "$TMP/run.sqlite" --subject "$TMP/subject.json"
python3 "$SCRIPT" ingest --db "$TMP/run.sqlite" --input "$TMP/good.json"
python3 "$SCRIPT" verify --db "$TMP/run.sqlite" >"$TMP/verify.json"
python3 "$SCRIPT" report --db "$TMP/run.sqlite" --output "$TMP/report.json"
python3 - "$TMP/report.json" <<'PY'
import json,sys
report=json.load(open(sys.argv[1]))
assert report['state']=='PASS'
assert report['blindspots']==[]
assert report['counts']['lancedb']==1
assert report['counts']['source-readback']==1
assert report['authority']['sqlite']=='AUTHORITATIVE_LEDGER'
PY

# Identical replay is idempotent; changed bytes for an existing ID are a mechanism error.
python3 "$SCRIPT" ingest --db "$TMP/run.sqlite" --input "$TMP/good.json"
python3 "$SCRIPT" verify --db "$TMP/run.sqlite" >/dev/null

expect_exit() {
  local expected="$1"; shift
  set +e
  "$@" >"$TMP/out" 2>"$TMP/err"
  local status=$?
  set -e
  test "$status" -eq "$expected"
}

expect_exit 70 python3 "$SCRIPT" ingest --db "$TMP/run.sqlite" --input "$TMP/drift.json"
grep -q EVENT_ID_DRIFT "$TMP/err"

python3 "$SCRIPT" init --db "$TMP/hollow.sqlite" --subject "$TMP/subject.json"
python3 "$SCRIPT" ingest --db "$TMP/hollow.sqlite" --input "$TMP/hollow.json"
expect_exit 2 python3 "$SCRIPT" verify --db "$TMP/hollow.sqlite"
grep -Eq 'SOURCE_READBACK_MISSING|AST_COVERAGE_MISSING|LINK_TARGET_MISSING' "$TMP/err"

python3 "$SCRIPT" init --db "$TMP/wrong.sqlite" --subject "$TMP/subject.json"
expect_exit 64 python3 "$SCRIPT" ingest --db "$TMP/wrong.sqlite" --input "$TMP/wrong-subject.json"
grep -q EVENT_SUBJECT_MISMATCH "$TMP/err"

python3 "$SCRIPT" init --db "$TMP/self.sqlite" --subject "$TMP/subject.json"
expect_exit 64 python3 "$SCRIPT" ingest --db "$TMP/self.sqlite" --input "$TMP/self-admit.json"
grep -q PROVIDER_SELF_ADMISSION "$TMP/err"

echo "blindspot-hybrid contract PASS"
