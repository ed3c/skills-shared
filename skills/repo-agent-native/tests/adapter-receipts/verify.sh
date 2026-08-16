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

echo "PASS adapter receipt contract"
