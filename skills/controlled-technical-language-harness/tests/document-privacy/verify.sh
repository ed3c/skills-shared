#!/usr/bin/env bash
# Zero-network controls for document-format preservation and privacy routing.
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(realpath "${test_dir}/../..")"
preservation="${skill_dir}/scripts/check_document_preservation.py"
routing="${skill_dir}/scripts/check_privacy_routing.py"

python3 "${preservation}" --selftest
python3 "${routing}" --selftest
python3 -m py_compile "${preservation}" "${routing}"

# CLI exit contract: a lossy rewrite must exit 2, and an absent file must exit
# 64, so a broken invocation is not read as a lossy document.
work="$(mktemp -d)"
cat > "${work}/source.xml" <<'XML'
<dmodule><content><procedure>
  <warning id="W-1"><simplePara>De-energise the system.</simplePara></warning>
  <proceduralStep id="S-1"><para>Open the panel.</para></proceduralStep>
</procedure></content></dmodule>
XML
cat > "${work}/lossy.xml" <<'XML'
<dmodule><content><procedure>
  <proceduralStep id="S-1"><para>Open the panel.</para></proceduralStep>
</procedure></content></dmodule>
XML

set +e
python3 "${preservation}" --source "${work}/source.xml" --output "${work}/lossy.xml" >/dev/null 2>&1
lossy_code=$?
python3 "${preservation}" --source "${work}/source.xml" --output "${work}/absent.xml" >/dev/null 2>&1
absent_code=$?
set -e

if [ "${lossy_code}" -ne 2 ]; then
  echo "FAIL: dropped warning exited ${lossy_code}, expected 2" >&2
  exit 1
fi
if [ "${absent_code}" -ne 64 ]; then
  echo "FAIL: absent output exited ${absent_code}, expected 64" >&2
  exit 1
fi

python3 "${preservation}" --source "${work}/source.xml" --output "${work}/source.xml" >/dev/null

echo "PASS controlled-language document format and privacy routing"
