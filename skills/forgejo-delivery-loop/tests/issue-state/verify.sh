#!/usr/bin/env bash
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
validator="${skill_dir}/scripts/issue_state.py"
fixture="${test_dir}/fixtures/request-valid.json"
scratch="$(mktemp -d)"
trap 'rm -rf "${scratch}"' EXIT

python3 "${validator}" validate --request "${fixture}" > "${scratch}/validated.json"
grep -Fq '"status":"validated"' "${scratch}/validated.json"
grep -Fq '"desired_state":"closed"' "${scratch}/validated.json"

python3 - "${fixture}" "${scratch}/not-admitted.json" <<'PY'
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
value["admission"]["status"] = "projected"
json.dump(value, open(sys.argv[2], "w", encoding="utf-8"))
PY
if python3 "${validator}" validate --request "${scratch}/not-admitted.json" > /dev/null 2>&1; then
  echo "FAIL: non-admitted request was accepted" >&2
  exit 1
fi

python3 - "${fixture}" "${scratch}/external.json" <<'PY'
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
value["forge_url"] = "https://forgejo.example.com"
json.dump(value, open(sys.argv[2], "w", encoding="utf-8"))
PY
if python3 "${validator}" validate --request "${scratch}/external.json" > /dev/null 2>&1; then
  echo "FAIL: external Forgejo request was accepted" >&2
  exit 1
fi

python3 - "${fixture}" "${scratch}/same-state.json" <<'PY'
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
value["expected_state"] = value["desired_state"]
json.dump(value, open(sys.argv[2], "w", encoding="utf-8"))
PY
if python3 "${validator}" validate --request "${scratch}/same-state.json" > /dev/null 2>&1; then
  echo "FAIL: no-op state transition was accepted" >&2
  exit 1
fi

python3 - "${validator}" "${fixture}" "${scratch}/pre.json" "${scratch}/receipt.json" <<'PY'
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import sys

spec = importlib.util.spec_from_file_location("issue_state", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
request = json.load(open(sys.argv[2], encoding="utf-8"))

def issue(state):
    return {
        "number": request["issue_number"],
        "state": state,
        "body": "Source: " + request["idempotency_marker"],
    }

def source_reader(command, _name):
    if "/issues/" in command[-1]:
        return {"html_url": request["source_receipt"]["issue_url"], "state": "closed"}
    return {
        "html_url": request["source_receipt"]["pull_request_url"],
        "merged_at": "2026-08-12T16:26:16Z",
        "merge_commit_sha": request["source_receipt"]["merge_sha"],
        "body": "Closes #50",
    }

pre = module.capture_pre_live(request, lambda _: issue("open"))

def closure_timeline(_request):
    pre_time = datetime.fromisoformat(pre["observed_at"])
    return [{
        "type": "close",
        "created_at": (pre_time + timedelta(seconds=1)).isoformat(),
        "user": {"login": "neon"},
    }]

receipt = module.verify_live(
    request, pre, lambda _: issue("closed"), source_reader=source_reader,
    timeline_reader=closure_timeline,
)
assert receipt["status"] == "verified"
json.dump(pre, open(sys.argv[3], "w", encoding="utf-8"))
json.dump(receipt, open(sys.argv[4], "w", encoding="utf-8"))

def rejected(label, mutate):
    candidate = deepcopy(pre)
    mutate(candidate)
    try:
        module.verify_live(
            request, candidate, lambda _: issue("closed"), source_reader=source_reader,
            timeline_reader=closure_timeline,
        )
    except ValueError:
        return
    raise AssertionError(label)

rejected("wrong repository accepted", lambda value: value.update(repository="neon/wrong"))
rejected(
    "wrong marker accepted",
    lambda value: value.update(idempotency_marker="https://github.com/wrong/repo/issues/1"),
)
rejected("boolean issue number accepted", lambda value: value.update(issue_number=True))
rejected("wrong pre-state accepted", lambda value: value.update(state="closed"))
rejected(
    "stale observation accepted",
    lambda value: value.update(
        observed_at=(datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    ),
)

try:
    module.verify_live(
        request, pre, lambda _: issue("open"), source_reader=source_reader,
        timeline_reader=closure_timeline,
    )
except ValueError:
    pass
else:
    raise AssertionError("wrong live post-state accepted")

assert module.validate_source_live(request, source_reader)["status"] == "source-verified"

def rejected_source(label, issue_patch=None, pull_patch=None):
    def reader(command, name):
        value = dict(source_reader(command, name))
        value.update(
            (issue_patch or {}) if "/issues/" in command[-1] else (pull_patch or {})
        )
        return value
    try:
        module.verify_live(
            request, pre, lambda _: issue("closed"), source_reader=reader,
            timeline_reader=closure_timeline,
        )
    except ValueError:
        return
    raise AssertionError(label)

rejected_source("open source issue accepted", issue_patch={"state": "open"})
rejected_source("unmerged source PR accepted", pull_patch={"merged_at": None})
rejected_source("wrong source SHA accepted", pull_patch={"merge_commit_sha": "0" * 40})
rejected_source("missing closure relation accepted", pull_patch={"body": "Does not close it"})

wrong_marker_issue = issue("open")
wrong_marker_issue["body"] = request["idempotency_marker"] + "0"
try:
    module.capture_pre_live(request, lambda _: wrong_marker_issue)
except ValueError:
    pass
else:
    raise AssertionError("issue #50 marker matched issue #500")

for suffix in ("abc", "/comments", "?tracked=1"):
    wrong_marker_issue = issue("open")
    wrong_marker_issue["body"] = request["idempotency_marker"] + suffix
    try:
        module.capture_pre_live(request, lambda _: wrong_marker_issue)
    except ValueError:
        pass
    else:
        raise AssertionError("marker matched URL suffix " + suffix)

try:
    module.verify_live(
        request, pre, lambda _: issue("closed"), source_reader=source_reader,
        timeline_reader=lambda _: [],
    )
except ValueError:
    pass
else:
    raise AssertionError("missing authenticated closure event was accepted")
PY
grep -Fq '"status": "verified"' "${scratch}/receipt.json"

python3 - "${skill_dir}" "${fixture}" "${scratch}/pre.json" "${scratch}/receipt.json" <<'PY'
import json
from pathlib import Path
import sys
from jsonschema import Draft202012Validator, FormatChecker

skill = Path(sys.argv[1])
cases = (
    ("contracts/forgejo-terminal-issue-state-request.v2.schema.json", sys.argv[2]),
    ("contracts/forgejo-issue-state-observation.v1.schema.json", sys.argv[3]),
    ("contracts/forgejo-issue-state-readback-receipt.v1.schema.json", sys.argv[4]),
)
for schema_path, value_path in cases:
    schema = json.loads((skill / schema_path).read_text(encoding="utf-8"))
    value = json.loads(Path(value_path).read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)
PY

cp "${fixture}" "${scratch}/short-merge-sha.json"
python3 - "${scratch}/short-merge-sha.json" <<'PY'
import json, sys
path = sys.argv[1]
value = json.load(open(path, encoding="utf-8"))
value["source_receipt"]["merge_sha"] = "ca73dfc"
json.dump(value, open(path, "w", encoding="utf-8"))
PY
if python3 "${validator}" validate --request "${scratch}/short-merge-sha.json" \
  > /dev/null 2>&1; then
  echo "FAIL: abbreviated source merge SHA was accepted" >&2
  exit 1
fi

cp "${fixture}" "${scratch}/source-marker-mismatch.json"
python3 - "${scratch}/source-marker-mismatch.json" <<'PY'
import json, sys
path = sys.argv[1]
value = json.load(open(path, encoding="utf-8"))
value["source_receipt"]["issue_url"] = (
    "https://github.com/ed3c/blackbox-auto-research/issues/49"
)
json.dump(value, open(path, "w", encoding="utf-8"))
PY
if python3 "${validator}" validate --request "${scratch}/source-marker-mismatch.json" \
  > /dev/null 2>&1; then
  echo "FAIL: source issue not bound to marker was accepted" >&2
  exit 1
fi

echo "PASS typed Forgejo issue state transition"
