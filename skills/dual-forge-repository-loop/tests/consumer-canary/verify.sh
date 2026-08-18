#!/usr/bin/env bash
# Controls for the #234 consumer canary receipt.
#
# Zero network and no consumer access. run_consumer_canary.py is compiled but
# never invoked: it needs a checkout of the consumer, a reachable Forgejo and an
# authenticated gh, and a suite that quietly needs those is a suite that gets
# skipped on the host that most needs it.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
checker="${skill_dir}/scripts/check_consumer_canary.py"
receipt="${skill_dir}/evals/receipts/consumer-canary.receipt.json"

python3 -m py_compile "${checker}" "${skill_dir}/scripts/run_consumer_canary.py"
python3 -m json.tool "${receipt}" >/dev/null

python3 "${checker}" check --receipt "${receipt}"
python3 "${checker}" selftest --receipt "${receipt}"

# The canary's whole claim is that it changed nothing. If a later run mutates the
# consumer, that is a different experiment and this assertion should be the thing
# that says so.
python3 - "${receipt}" <<'PY'
import json, sys
body = json.load(open(sys.argv[1]))
mutations = body["mutations_performed"]
for field in ("branches_created", "issues_created", "prs_created", "pushes", "merges",
              "consumer_files_changed"):
    assert mutations[field] is False, f"{field} is true; this is no longer a read-only canary"

worktree = next(l for l in body["chain"] if l["link"] == "isolated-worktrees-and-leases")
if worktree["state"] == "EXERCISED":
    assert worktree["one_writer_per_branch_refused"] is True, \
        "git did not refuse a second checkout of the active branch"
    assert worktree["residue_after_cleanup"] == [], "worktree residue left in the consumer"
    assert worktree["consumer_dirty_after"] == 0, "the consumer is dirty after the canary"

declared = set(body["chain_declared"])
stated = {l["link"] for l in body["chain"]}
assert declared == stated, f"unstated links: {sorted(declared - stated)}"
print(f"PASS non-destructive: {len(stated)}/{len(declared)} links stated, consumer clean")
PY

# The synchronization link binds the planted-conflict run by digest. A digest
# that no longer matches the committed file is a binding to a receipt that no
# longer exists, and the checker cannot see it from inside one file.
python3 - "${receipt}" "${skill_dir}/evals/receipts" <<'PY'
import hashlib, json, pathlib, sys
body = json.load(open(sys.argv[1]))
link = next(l for l in body["chain"]
            if l["link"] == "git-town-dry-run-and-local-no-push-sync")
if link["state"] != "EXERCISED":
    print("SKIP conflict binding: synchronization link is not EXERCISED")
    raise SystemExit(0)
bound = link["conflict_canary"]
target = pathlib.Path(sys.argv[2]) / bound["receipt"]
assert target.is_file(), f"bound conflict receipt {bound['receipt']} is not committed"
digest = hashlib.sha256(target.read_bytes()).hexdigest()
assert digest == bound["receipt_sha256"], \
    f"{bound['receipt']} hashes to {digest}, the receipt binds {bound['receipt_sha256']}"
committed = json.loads(target.read_text(encoding="utf-8"))
assert committed["conflict_canary"]["sync_exit"] == bound["sync_exit"], \
    "the bound conflict exit differs from the run that produced it"
print(f"PASS conflict binding: {bound['receipt']} matches its digest, sync exited "
      f"{bound['sync_exit']}")
PY

echo "PASS consumer dual-forge canary"
