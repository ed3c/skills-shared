#!/usr/bin/env bash
# Controls for the adapter receipt contract.
#
# Zero network and zero provider execution: this validates receipts that
# `capture_adapter_receipt.py` wrote on a host that had the providers, so it is
# runnable on a host that has none of them. The capture script is only compiled
# here, never run -- running it would need grepai, Serena, ollama and a git
# checkout, and a test that silently needs those is a test that gets disabled.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
checker="${skill_dir}/scripts/check_adapter_receipts.py"
capture="${skill_dir}/scripts/capture_adapter_receipt.py"
receipts="${skill_dir}/evals/receipts"

python3 -m py_compile "${checker}" "${capture}"

for file in "${receipts}"/*.receipt.json; do
  python3 -m json.tool "${file}" >/dev/null
done

python3 "${checker}" check --receipts "${receipts}"
python3 "${checker}" selftest --receipts "${receipts}"

# Every lane the contract names must have a receipt, present or absent. A lane
# that is simply missing from the directory reads exactly like a lane that
# passed, which is the failure mode absent-receipts exist to prevent.
for lane in grepai serena tree-sitter sqlite worktree scip git-town forgejo lancedb; do
  test -f "${receipts}/${lane}.receipt.json" \
    || { echo "MISSING RECEIPT ${lane}" >&2; exit 1; }
done

# The git-town lane starts a binary this repository does not install, so the gate
# in front of it is what has to be tested here. A host without the artifact must
# still be able to prove that the refusal works -- and that it is a gate rather
# than a constant no.
tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/tmp-root.XXXXXXXX")"
trap 'rm -rf "${tmp_root}"' EXIT

admission="${skill_dir}/evals/git-town-darwin-admission.json"
test -f "${admission}" || { echo "MISSING ADMISSION ${admission}" >&2; exit 1; }
python3 -m json.tool "${admission}" >/dev/null

# The darwin git-town capture is a second subject, so it is a second directory:
# it was taken at the commit that added the lane, and one capture is one subject.
# Same checker, same laws, no exemption.
darwin="${skill_dir}/evals/receipts-git-town-darwin"
test -f "${darwin}/git-town.receipt.json" \
  || { echo "MISSING RECEIPT git-town (darwin capture)" >&2; exit 1; }
python3 -m json.tool "${darwin}/git-town.receipt.json" >/dev/null
python3 "${checker}" check --receipts "${darwin}"

python3 - "${skill_dir}" "${tmp_root}" <<'PY'
import hashlib
import importlib.util
import json
import pathlib
import sys

skill = pathlib.Path(sys.argv[1])
tmp = pathlib.Path(sys.argv[2])
spec = importlib.util.spec_from_file_location(
    "capture", skill / "scripts" / "capture_adapter_receipt.py")
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)

record = json.loads(capture.GIT_TOWN_ADMISSION.read_text(encoding="utf-8"))
for field, expected in (("schema", "human-admit/v1"),
                        ("decision", "ADMITTED_FOR_BOUND_SCOPE"),
                        ("approver", "ed3c (repository owner)"),
                        ("decided_at", "2026-08-17")):
    if record.get(field) != expected:
        raise SystemExit(f"admission {field} is {record.get(field)!r}, expected {expected!r}")
for pin in (record["admitted_artifact"]["asset"]["sha256"],
            record["derived_executable_identity"]["sha256"]):
    if len(pin) != 64 or pin.strip("0123456789abcdef"):
        raise SystemExit(f"admission pins {pin!r}, which is not a SHA-256")


# The captured receipt has to name the artifact this record admits, and the
# record it names has to be these bytes. Editing the admission without
# recapturing would otherwise leave a PASS standing for a decision that changed.
captured = json.loads(
    (skill / "evals" / "receipts-git-town-darwin" / "git-town.receipt.json")
    .read_text(encoding="utf-8"))
if captured["adapter"]["executable_sha256"] != record["derived_executable_identity"]["sha256"]:
    raise SystemExit("the darwin receipt records a binary the admission does not pin")
bound = captured["policy"]["admission"]["record_sha256"]
actual = hashlib.sha256(capture.GIT_TOWN_ADMISSION.read_bytes()).hexdigest()
if bound != actual:
    raise SystemExit(f"the darwin receipt was captured against admission {bound}, "
                     f"but this record hashes {actual}; recapture or revert")
print(f"BOUND    receipt <- admission {actual[:12]} <- artifact "
      f"{record['derived_executable_identity']['sha256'][:12]}")


def gate(executable, admission=None):
    original = capture.GIT_TOWN_ADMISSION
    if admission is not None:
        capture.GIT_TOWN_ADMISSION = admission
    try:
        return capture.git_town_gate(executable)
    finally:
        capture.GIT_TOWN_ADMISSION = original


decoy = tmp / "not-git-town"
decoy.write_bytes(b"this is not the admitted artifact\n")
revoked = tmp / "revoked-admission.json"
revoked.write_text(json.dumps({**record, "decision": "HOLD_FOR_MORE_EVIDENCE"}),
                   encoding="utf-8")

# A gate that always refuses would pass every control above, so the last case
# plants a stand-in whose digest the record does admit and requires a yes.
stand_in = tmp / "stand-in-artifact"
stand_in.write_bytes(b"stand-in for an admitted artifact\n")
digest = hashlib.sha256(stand_in.read_bytes()).hexdigest()
matching = tmp / "matching-admission.json"
matching.write_text(
    json.dumps({**record, "derived_executable_identity": {"sha256": digest}}),
    encoding="utf-8")

cases = [
    ("no binary at all is ABSENT, not a refusal", gate(None), "ABSENT"),
    ("an unadmitted digest is refused", gate(str(decoy)), "SKIPPED_BY_POLICY"),
    ("a missing admission refuses",
     gate(str(decoy), tmp / "no-such-admission.json"), "SKIPPED_BY_POLICY"),
    ("a withdrawn admission refuses", gate(str(decoy), revoked), "SKIPPED_BY_POLICY"),
    ("a matching digest is admitted", gate(str(stand_in), matching), "ADMITTED"),
]
failed = []
for name, (state, detail), expected in cases:
    ok = state == expected and (state != "ADMITTED" or detail == digest)
    print(f"{'GATE' if ok else 'GATE FAILED'} {expected:18} {name}")
    if not ok:
        failed.append(f"{name}: got {state}")
if failed:
    raise SystemExit("git-town admission gate controls failed: " + "; ".join(failed))
PY

# An empty receipt directory must be refused rather than reported as a clean run.
empty="${tmp_root}/empty"
mkdir "${empty}"
set +e
python3 "${checker}" check --receipts "${empty}" >/dev/null 2>&1
status=$?
set -e
test "${status}" -eq 2 || { echo "empty directory was not refused (exit ${status})" >&2; exit 1; }
echo "REFUSED empty-receipt-directory"

# #231's live scheduler receipt binds as a CROSS-SUBJECT reference: it is real
# evidence, but of a disposable canary repository, not of the tree these
# adapter lanes describe. The binding is only honest while the two subjects
# stay different, so plant the collapse and require it to go red.
scheduler="$(realpath "${skill_dir}/../dual-forge-repository-loop/evals/receipts/scheduler-run.receipt.json")"
test -f "${scheduler}" || { echo "MISSING SCHEDULER RECEIPT ${scheduler}" >&2; exit 1; }
python3 "${checker}" check --receipts "${receipts}" --bind-scheduler "${scheduler}" \
  | grep -q '^CROSS_SUBJECT_BINDING ' \
  || { echo "scheduler binding did not report CROSS_SUBJECT_BINDING" >&2; exit 1; }

collapsed="$(mktemp "${TMPDIR:-/tmp}/collapsed.XXXXXXXX")"
trap 'rm -rf "${empty}" "${collapsed}"' EXIT
python3 -c 'import json, sys
body = json.loads(open(sys.argv[1], encoding="utf-8").read())
adapter = json.loads(open(sys.argv[2], encoding="utf-8").read())["subject"]["commit_sha"]
body["subject"]["initial_sha"] = adapter
body["subject"]["final_sha"] = adapter
open(sys.argv[3], "w", encoding="utf-8").write(json.dumps(body))
' "${scheduler}" "${receipts}/worktree.receipt.json" "${collapsed}"
# Exit 2 alone is not enough: any refusal would produce it, including one about
# the mutated file's shape rather than about the collapse. Require the code.
set +e
refusal="$(python3 "${checker}" check --receipts "${receipts}" \
  --bind-scheduler "${collapsed}" 2>&1 >/dev/null)"
status=$?
set -e
test "${status}" -eq 2 \
  || { echo "collapsed cross-subject binding was not refused (exit ${status})" >&2; exit 1; }
case "${refusal}" in
  *"REFUSED SUBJECT_COLLAPSED"*) ;;
  *) echo "collapsed binding was refused for the wrong reason: ${refusal}" >&2; exit 1 ;;
esac
echo "REFUSED scheduler-subject-collapsed-into-adapter-subject"

echo "PASS adapter receipt contract"
