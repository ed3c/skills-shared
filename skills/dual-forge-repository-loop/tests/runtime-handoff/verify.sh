#!/usr/bin/env bash
# Controls for the runtime handoff contract.
#
# Zero network and no runtime probing: the capability matrix inside a packet is
# a record of what was observed elsewhere, and this checks that a plan is
# consistent with it. Probing the live host here would make the suite pass or
# fail on which machine it ran on.
set -euo pipefail

test_dir="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
skill_dir="$(realpath "${test_dir}/../..")"
checker="${skill_dir}/scripts/check_runtime_handoff.py"
example="${skill_dir}/references/runtime-handoff.example.json"
schema="${skill_dir}/references/runtime-handoff.schema.json"

python3 -m py_compile "${checker}"
python3 -m json.tool "${example}" >/dev/null
python3 -m json.tool "${schema}" >/dev/null

python3 "${checker}" check --packet "${example}"
python3 "${checker}" selftest --packet "${example}"

# The example is the #255 handoff. Its value is that the blocker was real, so a
# future edit that turns it into a hypothetical should fail here.
python3 - "${example}" <<'PY'
import json, sys
packet = json.load(open(sys.argv[1]))
blocker = packet["blocker"]
assert blocker["missing_capability"] == "git_author_identity", \
    "the worked example is the identity boundary; a different blocker needs its own example"
sender = packet["capability_matrix"][packet["sender"]["runtime"]]
assert sender["git_author_identity"]["verdict"] == "OBSERVED_ABSENT", \
    "the sender's missing capability must be recorded as measured, not assumed"
assert blocker["evidence_reference"].strip(), "the blocker must stay reproducible"

# Every capability any step needs must appear in the matrix for some runtime, or
# the packet is planning against capabilities it never characterised.
needed = {c for step in packet["steps"] for c in step["requires"]}
described = {c for row in packet["capability_matrix"].values() for c in row}
missing = sorted(needed - described)
assert not missing, f"steps need capabilities absent from the matrix: {missing}"

human = [s for s in packet["steps"] if s["assigned_to"] == "HUMAN"]
assert human, "a handoff that leaves nothing to a Human has quietly moved admission"
print(f"PASS example: blocked on {blocker['missing_capability']}, "
      f"{len(packet['steps'])} steps, {len(human)} human-owned")
PY

echo "PASS runtime handoff contract"
