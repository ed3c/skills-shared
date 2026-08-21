#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

SHA40 = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def refuse(code, detail):
    print(json.dumps({"state":"REFUSED","code":code,"detail":detail}, sort_keys=True))
    return 2


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"state":"MALFORMED","detail":str(exc)}, sort_keys=True))
        raise SystemExit(64)


def check(p):
    required = {"schema_version","subject","storage","durability","refs","cache","gossip","compaction","recovery","benchmark","shadow","cleanup","claims"}
    if set(p) != required or p.get("schema_version") != "git-hosting-assurance/v1":
        return refuse("GS-C01", "packet shape/version or immutable implementation subject is invalid")
    s = p["subject"]
    if not SHA40.fullmatch(str(s.get("commit",""))) or not SHA40.fullmatch(str(s.get("tree",""))) or not DIGEST.fullmatch(str(s.get("runtime_digest",""))) or not DIGEST.fullmatch(str(s.get("config_digest",""))):
        return refuse("GS-C01", "implementation/runtime/config subject must be immutable")
    d, r, c = p["durability"], p["refs"], p["cache"]
    if not d.get("persisted_before_ack"): return refuse("GS-C02", "acknowledgement precedes durable persistence")
    if not d.get("durable_readback"): return refuse("GS-C12", "durable/corruption readback is absent")
    if not r.get("transaction_committed_before_visibility"): return refuse("GS-C03", "ref visible before transaction commit")
    if not r.get("multi_ref_atomic"): return refuse("GS-C04", "multi-ref publication is not atomic")
    if not r.get("cas_precondition"): return refuse("GS-C05", "CAS/expected-value precondition absent")
    if not c.get("authority_validation_before_read"): return refuse("GS-C06", "stale read can be served without authority validation")
    if c.get("source_of_truth"): return refuse("GS-C07", "local cache promoted to source of truth")
    if p["gossip"].get("required_for_correctness"): return refuse("GS-C08", "gossip delivery promoted to correctness authority")
    if not c.get("rebuild_reachability_proven"): return refuse("GS-C09", "cache rebuild lacks object/ref reachability proof")
    comp = p["compaction"]
    if not comp.get("reachable_objects_preserved") or not comp.get("reachable_refs_preserved"): return refuse("GS-C10", "compaction loses reachable object/ref")
    if not comp.get("per_replica_cost_reported"): return refuse("GS-C11", "per-replica compaction/repack cost omitted")
    rec = p["recovery"]
    if not rec.get("corruption_detected") or not rec.get("partial_records_rejected"): return refuse("GS-C12", "corruption or partial record is hidden")
    if not rec.get("history_complete_ordered"): return refuse("GS-C13", "replay history has gap/reordering")
    b = p["benchmark"]
    if not b.get("immutable_subject") or not b.get("matched_topology"): return refuse("GS-C14", "benchmark subject/topology is mutable or unmatched")
    if not b.get("durability_consistency_denominator") or not b.get("errors_in_denominator"): return refuse("GS-C15", "throughput claim lacks durability/consistency/error denominator")
    if p["claims"].get("source_performance_promoted"): return refuse("GS-C16", "source performance claim promoted to local result")
    if p["claims"].get("fixture_promoted_to_live"): return refuse("GS-C17", "fixture PASS promoted to live hosting PASS")
    if b.get("scope") == "ARBITRARY_SCALE": return refuse("GS-C18", "bounded topology promoted to arbitrary scale")
    cl = p["cleanup"]
    if not cl.get("complete") or not SHA40.fullmatch(str(cl.get("rollback_subject",""))): return refuse("GS-C19", "cleanup or immutable rollback identity absent")
    sh = p["shadow"]
    if sh.get("human_admit") and not sh.get("independent"): return refuse("GS-C20", "non-independent Shadow/model agreement promoted to Human Admit")
    print(json.dumps({"state":"CONTRACT_READY","code":"PASS","next":"LIVE_CANARY_REQUIRED"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_hosting_assurance.py PACKET.json", file=sys.stderr)
        raise SystemExit(64)
    raise SystemExit(check(load(sys.argv[1])))
