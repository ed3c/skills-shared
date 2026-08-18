#!/usr/bin/env bash
# Controls for the #262 private-lineage live canary receipt and its documents.
#
# Zero network and no forge. run_private_lineage_canary.py is compiled but never
# invoked: it needs a reachable Forgejo and an admitted credential, and a suite
# that quietly needs those is a suite that gets skipped on the host that most
# needs it.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
mode_dir="${skill_dir}/modes/forgejo-private-repository-loop"
checker="${skill_dir}/scripts/check_private_lineage_canary.py"
receipts="${skill_dir}/evals/receipts"
receipt="${receipts}/private-lineage-canary.receipt.json"
substrate="${receipts}/forgejo-substrate.receipt.json"
disposition="${receipts}/private-lineage-provider-disposition.json"
inventory="${receipts}/private-lineage-retirement-inventory.json"

python3 -m py_compile "${checker}" "${skill_dir}/scripts/run_private_lineage_canary.py"
for document in "${receipt}" "${substrate}" "${disposition}" "${inventory}"; do
  python3 -m json.tool "${document}" >/dev/null
done

python3 "${checker}" check --receipt "${receipt}"
python3 "${checker}" selftest --receipt "${receipt}"

# The two disposition documents are the canary's terminal claims, so they are
# re-derived here by their own owners rather than trusted from the receipt.
python3 "${mode_dir}/scripts/check_provider_retention.py" "${disposition}"
python3 "${mode_dir}/scripts/check_retirement_inventory.py" "${inventory}"

# A receipt that records a digest for a document, and a document that no longer
# hashes to it, is the drift this binding exists to catch: the checkers above
# would still pass on a document the canary never saw.
python3 - "${receipt}" "${disposition}" "${inventory}" "${substrate}" <<'PY'
import hashlib
import json
import pathlib
import sys

receipt = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
digests = {
    "disposition_sha256": sys.argv[2],
    "inventory_sha256": sys.argv[3],
}
links = {item["link"]: item for item in receipt["chain"]}
bound = 0
for entry in links.values():
    for field, path in digests.items():
        if field not in entry:
            continue
        actual = hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
        assert entry[field] == actual, (
            f"{entry['link']}.{field} names a document that is no longer the committed one"
        )
        bound += 1
assert bound == len(digests), f"expected {len(digests)} document bindings, found {bound}"

# The substrate receipt is the evidence other issues read to correct a Forgejo
# lane from ABSENT. An ABSENT-shaped substrate receipt cannot do that job.
sub = json.loads(pathlib.Path(sys.argv[4]).read_text(encoding="utf-8"))
assert sub["schema"] == "dual-forge-repository-loop/forgejo-substrate-receipt/v1"
assert sub["state"] == "PASS", "substrate receipt does not observe a reachable forge"
assert sub["version_request"]["http_status"] == 200
assert sub["authenticated_identity_request"]["http_status"] == 200
assert sub["declared_non_claims"], "substrate evidence must declare what it does not prove"
assert sub["forge_url"] == receipt["forge"]["url"], "substrate and canary observed different forges"
assert sub["version"] == receipt["forge"]["version"], "substrate and canary observed different versions"
print(f"PASS document bindings: {bound} digests bound, substrate agrees with the canary")
PY

echo "PASS private-lineage live canary"
