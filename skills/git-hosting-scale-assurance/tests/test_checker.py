#!/usr/bin/env python3
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check_hosting_assurance.py"
GOOD = json.loads((Path(__file__).parent / "fixtures" / "good.json").read_text())

MUTATIONS = {
 "GS-C01": lambda p: p["subject"].__setitem__("commit", "main"),
 "GS-C02": lambda p: p["durability"].__setitem__("persisted_before_ack", False),
 "GS-C03": lambda p: p["refs"].__setitem__("transaction_committed_before_visibility", False),
 "GS-C04": lambda p: p["refs"].__setitem__("multi_ref_atomic", False),
 "GS-C05": lambda p: p["refs"].__setitem__("cas_precondition", False),
 "GS-C06": lambda p: p["cache"].__setitem__("authority_validation_before_read", False),
 "GS-C07": lambda p: p["cache"].__setitem__("source_of_truth", True),
 "GS-C08": lambda p: p["gossip"].__setitem__("required_for_correctness", True),
 "GS-C09": lambda p: p["cache"].__setitem__("rebuild_reachability_proven", False),
 "GS-C10": lambda p: p["compaction"].__setitem__("reachable_objects_preserved", False),
 "GS-C11": lambda p: p["compaction"].__setitem__("per_replica_cost_reported", False),
 "GS-C12": lambda p: p["recovery"].__setitem__("corruption_detected", False),
 "GS-C13": lambda p: p["recovery"].__setitem__("history_complete_ordered", False),
 "GS-C14": lambda p: p["benchmark"].__setitem__("matched_topology", False),
 "GS-C15": lambda p: p["benchmark"].__setitem__("errors_in_denominator", False),
 "GS-C16": lambda p: p["claims"].__setitem__("source_performance_promoted", True),
 "GS-C17": lambda p: p["claims"].__setitem__("fixture_promoted_to_live", True),
 "GS-C18": lambda p: p["benchmark"].__setitem__("scope", "ARBITRARY_SCALE"),
 "GS-C19": lambda p: p["cleanup"].__setitem__("complete", False),
 "GS-C20": lambda p: (p["shadow"].__setitem__("independent", False), p["shadow"].__setitem__("human_admit", True)),
}

def run(packet):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(packet, f)
        name = f.name
    cp = subprocess.run([sys.executable, str(CHECK), name], text=True, capture_output=True)
    Path(name).unlink(missing_ok=True)
    return cp.returncode, json.loads(cp.stdout)

def main():
    rc, out = run(GOOD)
    assert rc == 0 and out["state"] == "CONTRACT_READY", (rc, out)
    killed = 0
    for code, mutate in MUTATIONS.items():
        packet = copy.deepcopy(GOOD)
        mutate(packet)
        rc, out = run(packet)
        assert rc == 2, (code, rc, out)
        assert out["code"] == code, (code, out)
        killed += 1
    print(f"PASS positive=1 mutations={killed}/20")

if __name__ == "__main__": main()
