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

# An empty receipt directory must be refused rather than reported as a clean run.
empty="$(mktemp -d)"
trap 'rm -rf "${empty}"' EXIT
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

collapsed="$(mktemp)"
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
