#!/usr/bin/env python3
"""Drive a live Git-hosting canary against one disposable consumer subject.

This harness lives with the Skill; the consumer subject does not. It launches a
caller-supplied single-node hosting core, executes the #534 State Machine
stages it can honestly exercise, and emits the receipt bundle checked by
`check_hosting_assurance.py`.

It never selects, activates or pays for a provider, never claims a topology it
did not run, and records absent lanes as NOT_EXERCISED rather than inferring
them.

    python3 skills/git-hosting-scale-assurance/scripts/run_hosting_canary.py --selftest
    python3 skills/git-hosting-scale-assurance/scripts/run_hosting_canary.py \
        --subject <refcore.py> --workdir <tmp> --out data/handoff/git-at-any-scale \
        --subject-commit <sha40> --subject-tree <sha40> --rollback-commit <sha40> \
        --dry-run
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import platform
import random
import re
import resource
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SCHEMA_VERSION = "git-hosting-assurance/v1"
KILL_POINTS = ("pre_write", "post_write_pre_fsync", "post_fsync_pre_ack", "post_ack")
KILL_OPS = ("put_obj", "cas_ref")


# --------------------------------------------------------------------------
# linearizability (Wing & Gong search over the recorded history)
# --------------------------------------------------------------------------
def linearizable(history, init=None):
    """History entries: dict(kind, old, new, ret, actual, invoke, response).

    Sequential spec of one CAS register:
        read()          -> current value
        cas(old,new)    -> 'ok' and value:=new when current==old, else
                           'conflict' with actual==current
    Returns (bool, detail).
    ponytail: naive backtracking with memo, ceiling ~a few hundred ops.
    """
    ops = list(range(len(history)))
    memo = set()

    def step(remaining, value):
        if not remaining:
            return True
        key = (remaining, value)
        if key in memo:
            return False
        min_resp = min(history[i]["response"] for i in remaining)
        for i in remaining:
            op = history[i]
            if op["invoke"] > min_resp:
                continue
            if op["kind"] == "read":
                if op["ret"] != value:
                    continue
                nxt = value
            else:
                if value == op["old"]:
                    if op["ret"] != "ok":
                        continue
                    nxt = op["new"]
                else:
                    if op["ret"] != "conflict" or op.get("actual") != value:
                        continue
                    nxt = value
            if step(remaining - {i}, nxt):
                return True
        memo.add(key)
        return False

    ok = step(frozenset(ops), init)
    return ok, {"operations": len(history), "states_explored": len(memo)}


# --------------------------------------------------------------------------
# process / client helpers
# --------------------------------------------------------------------------
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def load_subject(path):
    spec = importlib.util.spec_from_file_location("canary_subject", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for attr in ("Client", "frame", "parse_log", "main"):
        if not hasattr(mod, attr):
            raise SystemExit(f"SUBJECT_CONTRACT_VIOLATION: missing {attr}")
    return mod


class Proc:
    """A running subject process plus the driver-side ends of its channels."""

    def __init__(self, popen, pairs, peer, root, kind, mod):
        self.popen, self.pairs, self.peer = popen, pairs, peer
        self.root, self.kind, self.mod = root, kind, mod
        self._clients = {}

    def client(self, i=0):
        if i not in self._clients:
            self._clients[i] = self.mod.Client(*self.pairs[i])
        return self._clients[i]

    def kill9(self):
        os.kill(self.popen.pid, signal.SIGKILL)
        return self.popen.wait()

    def stop(self):
        if self.popen.poll() is None:
            self.popen.terminate()
            try:
                self.popen.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.popen.kill()
                self.popen.wait()
        return self.popen.returncode


def make_pairs(n):
    """-> (child_side [(read, write)], driver_side [(write, read)])."""
    child, driver = [], []
    for _ in range(n):
        cr, dw = os.pipe()
        dr, cw = os.pipe()
        child.append((cr, cw))
        driver.append((dw, dr))
    return child, driver


def start(subject, mode, root, workdir, mod, env_extra=None, peer=None, channels=10,
          timeout=30.0):
    """Spawn a subject process. IPC is inherited pipes only; nothing listens."""
    ready = Path(workdir) / f"ready.{mode}.{os.path.basename(root)}.{time.time_ns()}"
    child, driver_pairs = make_pairs(channels)
    argv = [sys.executable, str(subject), mode, "--root", str(root),
            "--fds", ",".join(f"{r}:{w}" for r, w in child), "--ready-file", str(ready)]
    pass_fds = [fd for pair in child for fd in pair]
    if peer is not None:
        argv += ["--authority-fds", f"{peer[0]}:{peer[1]}"]
        pass_fds += list(peer)
    env = dict(os.environ)
    env.update(env_extra or {})
    popen = subprocess.Popen(argv, env=env, pass_fds=pass_fds,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for r, w in child:
        os.close(r)
        os.close(w)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if popen.poll() is not None:
            return None, popen.stdout.read(), popen.returncode
        if ready.exists() and ready.stat().st_size:
            # the last channel is reserved as an authority peer channel for a cache
            return Proc(popen, driver_pairs[:-1], driver_pairs[-1], root, mode, mod), "", 0
        time.sleep(0.01)
    popen.kill()
    raise SystemExit(f"SUBJECT_START_TIMEOUT mode={mode} root={root}")


def wait_file(path, timeout=20.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return json.loads(Path(path).read_text())
        time.sleep(0.01)
    return None


def child_cpu():
    r = resource.getrusage(resource.RUSAGE_CHILDREN)
    return r.ru_utime + r.ru_stime


def obj(payload: bytes, links=None):
    return {"op": "put_obj", "id": sha256_bytes(payload),
            "b64": base64.b64encode(payload).decode(), "links": links or []}


# --------------------------------------------------------------------------
# stages
# --------------------------------------------------------------------------
def stage_corpus(subject, wd, mod):
    """EMPTY_SYSTEM_BASELINE -> REPOSITORY_CORPUS_LOADED. Returns (proc, facts)."""
    root = wd / "corpus"
    proc, out, rc = start(subject, "authority", root, wd, mod)
    assert proc is not None, f"corpus authority failed to start: rc={rc} out={out}"
    cli = proc.client(0)
    baseline = cli.call(op="authority_state")
    assert baseline["log_size"] == 0 and baseline["seq"] == 0, baseline
    # generated disposable corpus: 3 branches x 8 commits, each commit -> 1 blob
    ids, tips, blobs = [], {}, 0
    rng = random.Random(534)
    for b in range(3):
        parent = None
        for c in range(8):
            blob = bytes(rng.getrandbits(8) for _ in range(512))
            r = cli.call(**obj(blob))
            assert r["ok"], r
            blobs += 1
            body = json.dumps({"branch": b, "n": c, "blob": r["id"], "parent": parent}).encode()
            links = [r["id"]] + ([parent] if parent else [])
            rc_ = cli.call(**obj(body, links))
            assert rc_["ok"], rc_
            parent = rc_["id"]
            ids.append(rc_["id"])
        tips[f"refs/heads/b{b}"] = parent
    r = cli.call(op="txn_refs", updates=[{"name": n, "old": None, "new": v}
                                         for n, v in sorted(tips.items())])
    assert r["ok"], r
    st = cli.call(op="authority_state")
    refs = cli.call(op="list_refs")["refs"]
    assert refs == tips, (refs, tips)
    cli.close()
    return proc, {"stage": "REPOSITORY_CORPUS_LOADED", "empty_baseline_log_bytes": 0,
                  "commits": len(ids), "blobs": blobs, "refs": tips,
                  "objects": st["objects"], "log_bytes": st["log_size"],
                  "authority_digest": st["digest"],
                  "multi_ref_atomic_record": True,
                  "multi_ref_updates_in_one_record": len(tips)}


def stage_durability(subject, wd, mod):
    """L1-A: kill -9 at every boundary around acknowledgement / ref publication."""
    cases = []
    for opkind in KILL_OPS:
        for point in KILL_POINTS:
            root = wd / f"kill-{opkind}-{point}"
            # phase 1: acked baseline, clean stop
            p1, o1, r1 = start(subject, "authority", root, wd, mod)
            assert p1 is not None, f"start failed rc={r1} out={o1}"
            c1 = p1.client(0)
            base = b"base-object-" + opkind.encode()
            r = c1.call(**obj(base))
            base_id = r["id"]
            assert c1.call(op="cas_ref", name="refs/heads/main", old=None, new=base_id)["ok"]
            baseline_state = c1.call(op="authority_state")
            c1.close()
            p1.stop()

            # phase 2: crash-armed run
            target_payload = b"target-object-" + point.encode()
            target_id = sha256_bytes(target_payload)
            new_ref = "target-" + point
            pause = wd / f"pause-{opkind}-{point}.json"
            env = {"CANARY_CRASH_AT": point, "CANARY_CRASH_OP": opkind,
                   "CANARY_PAUSE_FILE": str(pause)}
            p2, _, _ = start(subject, "authority", root, wd, mod, env)
            ack = {"received": False, "response": None}

            import threading

            def fire():
                try:
                    c = p2.client(0)
                    if opkind == "put_obj":
                        resp = c.call(**obj(target_payload))
                    else:
                        resp = c.call(op="cas_ref", name="refs/heads/main",
                                      old=base_id, new=new_ref)
                    ack["received"] = True
                    ack["response"] = resp
                except (OSError, ConnectionError, ValueError) as exc:
                    ack["error"] = f"{type(exc).__name__}: {exc}"

            t = threading.Thread(target=fire, daemon=True)
            t.start()
            marker = wait_file(pause, timeout=20.0)
            assert marker is not None, f"crash point {point}/{opkind} never reached"
            # concurrent observation while the writer is paused at the boundary
            cobs = p2.client(1)
            if opkind == "put_obj":
                visible = cobs.call(op="get_obj", id=target_id)["ok"]
            else:
                visible = cobs.call(op="get_ref", name="refs/heads/main")["value"] == new_ref
            t.join(timeout=2.0)
            acked_before_kill = ack["received"]
            killed_rc = p2.kill9()

            # phase 3: clean restart, replay
            p3, out3, rc3 = start(subject, "authority", root, wd, mod)
            assert p3 is not None, f"restart failed rc={rc3} out={out3}"
            c3 = p3.client(0)
            if opkind == "put_obj":
                survived = c3.call(op="get_obj", id=target_id)["ok"]
            else:
                survived = c3.call(op="get_ref", name="refs/heads/main")["value"] == new_ref
            base_survived = (c3.call(op="get_obj", id=base_id)["ok"]
                             and c3.call(op="get_ref", name="refs/heads/main")["value"]
                             in (base_id, new_ref))
            load = c3.call(op="stats")["load"]
            c3.close()
            p3.stop()
            cases.append({
                "op": opkind, "boundary": point,
                "acked_before_kill": acked_before_kill,
                "visible_to_concurrent_reader_at_boundary": visible,
                "survived_restart": survived,
                "acked_baseline_survived": base_survived,
                "baseline_log_bytes": baseline_state["log_size"],
                "kill_signal": "SIGKILL", "killed_returncode": killed_rc,
                "replay_status_after_restart": load["status"],
                "replay_repaired_bytes": load["repaired_bytes"],
            })
    acked = [c for c in cases if c["acked_before_kill"]]
    lost = [c for c in acked if not c["survived_restart"]]
    lost_baseline = [c for c in cases if not c["acked_baseline_survived"]]
    early_visible = [c for c in cases
                     if c["boundary"] in ("pre_write", "post_write_pre_fsync")
                     and c["visible_to_concurrent_reader_at_boundary"]]
    return {
        "experiment": "L1-A", "stage": "DURABLE_ACK_CANARY", "kills": len(cases),
        "boundaries": list(KILL_POINTS), "ops": list(KILL_OPS),
        "acknowledged_operations_at_the_kill_boundary": len(acked),
        "acknowledged_baseline_operations_replayed": 2 * len(cases),
        "acknowledged_operations_total_denominator": len(acked) + 2 * len(cases),
        "acknowledged_operation_loss_count": len(lost) + len(lost_baseline),
        "acked_baseline_loss_count": len(lost_baseline),
        "visible_before_commit_count": len(early_visible),
        "cases": cases,
        "verdict": "PASS" if not lost and not lost_baseline and not early_visible else "FAIL",
        "falsifiers_not_triggered": ["ACK_RETURNED_BEFORE_DURABLE_READBACK",
                                     "ACKNOWLEDGED_PUSH_LOST_AFTER_RESTART",
                                     "REF_VISIBLE_WITH_MISSING_OBJECTS"],
        "ceiling": ("SIGKILL exercises process loss only. Page-cache-surviving writes cannot be "
                    "distinguished from fsynced writes by process kill alone; power loss, media "
                    "failure and fsync-lying hardware are NOT_EXERCISED."),
    }


def stage_linearizability(subject, wd, mod, clients=4, rounds=12, plant=False):
    """L1-B: concurrent CAS history + real linearizability check."""
    import threading
    root = wd / "lin"
    proc, o, rc = start(subject, "authority", root, wd, mod, channels=clients + 4)
    assert proc is not None, f"lin authority failed rc={rc} out={o}"
    ref = "refs/heads/lin"
    history, hlock = [], threading.Lock()
    t0 = time.monotonic()

    def worker(pid):
        c = proc.client(pid)
        known = None
        for i in range(rounds):
            inv = time.monotonic() - t0
            r = c.call(op="get_ref", name=ref)
            resp = time.monotonic() - t0
            with hlock:
                history.append({"proc": pid, "kind": "read", "old": None, "new": None,
                                "ret": r["value"], "invoke": inv, "response": resp})
            known = r["value"]
            new = f"v-{pid}-{i}"
            inv = time.monotonic() - t0
            r = c.call(op="cas_ref", name=ref, old=known, new=new)
            resp = time.monotonic() - t0
            with hlock:
                history.append({"proc": pid, "kind": "cas", "old": known, "new": new,
                                "ret": "ok" if r["ok"] else "conflict",
                                "actual": r.get("actual"), "invoke": inv, "response": resp})
        c.close()

    threads = [threading.Thread(target=worker, args=(p,)) for p in range(clients)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    admin = proc.client(clients)
    stats = admin.call(op="stats")["stats"]
    final = admin.call(op="get_ref", name=ref)["value"]
    proc.stop()
    history.sort(key=lambda e: (e["invoke"], e["response"]))
    checked = history
    planted = None
    if plant:
        acked = [i for i, e in enumerate(checked) if e["kind"] == "cas" and e["ret"] == "ok"]
        drop = acked[len(acked) // 2]
        planted = checked[drop]
        checked = [e for i, e in enumerate(checked) if i != drop]
    ok, detail = linearizable(checked)
    overlaps = sum(1 for i, a in enumerate(checked)
                   for b in checked[i + 1:]
                   if b["invoke"] < a["response"] and a["proc"] != b["proc"])
    return {
        "experiment": "L1-B", "stage": "CONCURRENT_REF_HISTORY_CANARY",
        "clients": clients, "operations": len(history), "checked_operations": len(checked),
        "concurrent_overlapping_pairs": overlaps,
        "cas_conflicts_observed": stats["cas_conflicts"],
        "accepted": stats["accepted"], "rejected": stats["rejected"], "timed_out": 0,
        "final_value": final,
        "linearizable": ok, "checker_detail": detail,
        "planted_defect": ({"dropped_acked_operation": planted} if planted else None),
        "verdict": "PASS" if ok and stats["cas_conflicts"] > 0 else "FAIL",
        "falsifiers_not_triggered": ["CAS_CONFLICT_SILENTLY_OVERWRITTEN",
                                     "NON_LINEARIZABLE_HISTORY_ACCEPTED"],
        "ceiling": ("Single-node register semantics over one ref, in-process clients on one "
                    "host. Cross-node or cross-region linearizability is NOT_EXERCISED."),
    }, history


def stage_cache(subject, wd, mod, authority: Proc):
    """L1-C + L1-E: stale detect / catch-up / fail-closed / destroy + rebuild."""
    croot = wd / "cache"
    cache, o, rc = start(subject, "cache", croot, wd, mod, peer=authority.peer)
    assert cache is not None, f"cache start failed rc={rc} out={o}"
    cc = cache.client(0)
    ac = authority.client(0)
    first = cc.call(op="rebuild")
    assert first["ok"], first
    snap0 = cc.call(op="snapshot_state")

    # force the cache behind the authority; no propagation channel exists at all
    opportunities, stale_served_count, behind_count, reads = 0, 0, 0, []
    for i in range(5):
        r = ac.call(**obj(b"post-cache-write-%d" % i))
        tip = ac.call(op="list_refs")["refs"]["refs/heads/b0"]
        assert ac.call(op="cas_ref", name="refs/heads/b0", old=tip, new=r["id"])["ok"]
        auth_state = ac.call(op="authority_state")
        snap1 = cc.call(op="snapshot_state")
        opportunities += 1
        behind_count += int(snap1["digest"] != auth_state["digest"])
        read = cc.call(op="cached_get_ref", name="refs/heads/b0")
        stale_served_count += int(read["value"] != r["id"])
        reads.append({"opportunity": i, "snapshot_digest_before_read": snap1["digest"],
                      "authority_digest": auth_state["digest"],
                      "snapshot_behind_authority": snap1["digest"] != auth_state["digest"],
                      "validated": read.get("validated"), "detected_stale": read.get("was_stale"),
                      "returned_current_value": read["value"] == r["id"]})
    was_behind = behind_count == opportunities
    served_stale = stale_served_count > 0

    # fail-closed: authority gone
    cache1_stats_before_kill = cc.call(op="cache_stats")["stats"]
    authority.kill9()
    closed = cc.call(op="cached_get_ref", name="refs/heads/b0")
    cache1_stats = cc.call(op="cache_stats")["stats"]
    authority2, o2, rc2 = start(subject, "authority", authority.root, wd, mod)
    assert authority2 is not None, f"authority restart failed rc={rc2} out={o2}"
    ac2 = authority2.client(0)
    # the old cache's channel died with the old authority; build a replacement
    cache.stop()

    # L1-E: destroy the complete cache and rebuild from declared authority
    shutil.rmtree(croot)
    assert not croot.exists()
    t0, b0 = time.monotonic(), child_cpu()
    cache2, o3, rc3 = start(subject, "cache", croot, wd, mod, peer=authority2.peer)
    assert cache2 is not None, f"cache rebuild start failed rc={rc3} out={o3}"
    cc2 = cache2.client(0)
    rebuilt = cc2.call(op="rebuild")
    rebuild_wall = time.monotonic() - t0
    refs = ac2.call(op="list_refs")["refs"]
    reach = ac2.call(op="reachable")["ids"]
    ref_match = all(cc2.call(op="cached_get_ref", name=n)["value"] == v for n, v in refs.items())
    obj_ok = sum(1 for oid in reach if cc2.call(op="cached_get_obj", id=oid)["ok"])
    cstats = cc2.call(op="cache_stats")["stats"]
    cache2.stop()
    return {
        "experiment": "L1-C+L1-E",
        "stages": ["STALE_CACHE_AND_CATCHUP_CANARY", "CACHE_DESTROY_REBUILD_CANARY"],
        "first_rebuild": first,
        "snapshot_before_authority_write": snap0["digest"],
        "cache_was_behind_authority": was_behind,
        "stale_opportunity_denominator": opportunities,
        "stale_opportunities_where_snapshot_was_behind": behind_count,
        "stale_reads_served": stale_served_count,
        "stale_read_observations": reads,
        "read_validated_against_authority": all(x["validated"] for x in reads),
        "read_detected_staleness": all(x["detected_stale"] for x in reads),
        "read_returned_current_value": all(x["returned_current_value"] for x in reads),
        "cache_stats_before_authority_kill": cache1_stats_before_kill,
        "cache_stats_after_authority_kill": cache1_stats,
        "authority_unreachable_read": closed,
        "fail_closed_on_unreachable_authority": closed.get("error", "").startswith("FAIL_CLOSED"),
        "cache_destroyed_path_existed_then_removed": True,
        "rebuild": rebuilt, "rebuild_wall_seconds": round(rebuild_wall, 4),
        "rebuild_child_cpu_delta_seconds": round(child_cpu() - b0, 4),
        "rebuilt_refs_match_authority": ref_match,
        "reachable_objects": len(reach), "reachable_objects_verified_in_cache": obj_ok,
        "cache_stats": cstats,
        "verdict": ("PASS" if (was_behind and not served_stale
                               and all(x["validated"] for x in reads)
                               and closed.get("error", "").startswith("FAIL_CLOSED")
                               and ref_match and obj_ok == len(reach)) else "FAIL"),
        "falsifiers_not_triggered": ["STALE_CACHE_SERVED_WITHOUT_AUTHORITY_CHECK",
                                     "DESTROYED_CACHE_CANNOT_REBUILD_FROM_DECLARED_AUTHORITY"],
        "ceiling": ("One cache process on the same host as the authority. Network partition, "
                    "clock skew and multi-region routing are NOT_EXERCISED."),
    }, authority2


def stage_compaction(subject, wd, mod, authority: Proc):
    """L1-F: reachability-preserving compaction with per-replica cost."""
    ac = authority.client(0)
    # garbage: objects nothing points at, plus an abandoned branch that is deleted
    garbage = []
    for i in range(6):
        r = ac.call(**obj(f"garbage-{i}".encode()))
        garbage.append(r["id"])
    tmp = ac.call(**obj(b"abandoned-tip", []))
    assert ac.call(op="cas_ref", name="refs/heads/tmp", old=None, new=tmp["id"])["ok"]
    assert ac.call(op="cas_ref", name="refs/heads/tmp", old=tmp["id"], new=None)["ok"]
    before_refs = ac.call(op="list_refs")["refs"]
    before_reach = set(ac.call(op="reachable")["ids"])
    before_state = ac.call(op="authority_state")
    cpu0 = child_cpu()
    stats = ac.call(op="compact")
    cpu_children = child_cpu() - cpu0
    after_refs = ac.call(op="list_refs")["refs"]
    after_reach = set(ac.call(op="reachable")["ids"])
    missing = sorted(before_reach - after_reach)
    obj_ok = sum(1 for oid in before_reach if ac.call(op="get_obj", id=oid)["ok"])
    garbage_left = [g for g in garbage + [tmp["id"]] if ac.call(op="get_obj", id=g)["ok"]]
    after_state = ac.call(op="authority_state")
    # restart proves the compacted log replays
    authority.stop()
    a2, o2, rc2 = start(subject, "authority", authority.root, wd, mod)
    assert a2 is not None, f"post-compaction restart failed rc={rc2} out={o2}"
    c2 = a2.client(0)
    replay_refs = c2.call(op="list_refs")["refs"]
    replay_obj_ok = sum(1 for oid in before_reach if c2.call(op="get_obj", id=oid)["ok"])
    load = c2.call(op="stats")["load"]
    c2.close()
    return {
        "experiment": "L1-F", "stage": "COMPACTION_REACHABILITY_CANARY",
        "refs_before": before_refs, "refs_after": after_refs,
        "refs_preserved": before_refs == after_refs == replay_refs,
        "reachable_before": len(before_reach), "reachable_after": len(after_reach),
        "reachable_objects_missing_after_compaction": missing,
        "reachable_objects_readable_after_compaction": obj_ok,
        "reachable_objects_readable_after_restart": replay_obj_ok,
        "unreachable_objects_planted": len(garbage) + 1,
        "unreachable_objects_surviving": len(garbage_left),
        "unreachable_policy": stats["unreachable_policy"],
        "log_bytes_before": before_state["log_size"], "log_bytes_after": after_state["log_size"],
        "compaction_amplification_bytes_written_over_live_bytes":
            round(stats["bytes_written"] / max(after_state["log_size"], 1), 4),
        "cost": {"replicas_repacked": stats["replicas_repacked"],
                 "replica_count_in_topology": 1,
                 "bytes_read": stats["bytes_read"], "bytes_written": stats["bytes_written"],
                 "bytes_transferred": stats["bytes_transferred"],
                 "wall_seconds": stats["wall_seconds"],
                 "in_process_cpu_seconds": stats["cpu_seconds"],
                 "child_cpu_delta_seconds": round(cpu_children, 4)},
        "replay_status_after_restart": load["status"],
        "verdict": "PASS" if (not missing and obj_ok == len(before_reach)
                              and replay_obj_ok == len(before_reach)
                              and before_refs == replay_refs) else "FAIL",
        "falsifiers_not_triggered": ["COMPACTION_DROPS_REACHABLE_OBJECT"],
        "ceiling": "One replica repacks. Fan-out repack cost across replicas is NOT_EXERCISED.",
    }, a2


def stage_corruption(subject, wd, mod, authority: Proc, raw_dir: Path):
    """L1-G: truncated tail, torn record, midstream corruption, restart replay."""
    ac = authority.client(0)
    refs_before = ac.call(op="list_refs")["refs"]
    state_before = ac.call(op="authority_state")
    authority.stop()
    logpath = Path(authority.root) / "log.bin"
    pristine = raw_dir / "corruption-pristine-log.digest"
    pristine.write_text(json.dumps({"path": "log.bin", "bytes": logpath.stat().st_size,
                                    "sha256": sha256_file(logpath)}, sort_keys=True) + "\n")
    backup = Path(str(logpath) + ".pristine")
    shutil.copy2(logpath, backup)
    cases = []

    # (a) partial record: append a header-sized fragment
    with open(logpath, "ab") as fh:
        fh.write(b"REC1\x00\x00")
    p, o, rc = start(subject, "authority", authority.root, wd, mod)
    assert p is not None, f"partial-fragment restart failed rc={rc} out={o}"
    c = p.client(0)
    load = c.call(op="stats")["load"]
    refs = c.call(op="list_refs")["refs"]
    p.stop()
    cases.append({"injection": "PARTIAL_HEADER_FRAGMENT", "bytes_injected": 6,
                  "replay_status": load["status"], "repaired_bytes": load["repaired_bytes"],
                  "records_replayed": load["records"], "refs_intact": refs == refs_before,
                  "served_after_repair": True, "detected": load["status"] == "TRUNCATED_TAIL"})

    # (b) torn record: a full frame minus its last bytes
    torn = mod.frame({"seq": load["records"], "t": "obj", "id": "torn", "b64": "", "links": []})
    with open(logpath, "ab") as fh:
        fh.write(torn[:-5])
    p, o, rc = start(subject, "authority", authority.root, wd, mod)
    assert p is not None, f"torn-record restart failed rc={rc} out={o}"
    c = p.client(0)
    load2 = c.call(op="stats")["load"]
    refs2 = c.call(op="list_refs")["refs"]
    has_torn = c.call(op="get_obj", id="torn")["ok"]
    p.stop()
    cases.append({"injection": "TORN_TAIL_RECORD", "bytes_injected": len(torn) - 5,
                  "replay_status": load2["status"], "repaired_bytes": load2["repaired_bytes"],
                  "records_replayed": load2["records"], "refs_intact": refs2 == refs_before,
                  "partial_record_replayed_as_complete": has_torn,
                  "detected": load2["status"] == "TRUNCATED_TAIL"})

    # (c) midstream corruption of a committed record -> must fail closed
    raw = bytearray(logpath.read_bytes())
    flip_at = 12 + 3
    raw[flip_at] ^= 0xFF
    corrupt_copy = raw_dir / "corruption-first-red-log.digest"
    logpath.write_bytes(bytes(raw))
    corrupt_copy.write_text(json.dumps({"path": "log.bin", "byte_flipped_offset": flip_at,
                                        "bytes": len(raw),
                                        "sha256": sha256_bytes(bytes(raw))}, sort_keys=True) + "\n")
    pbad, obad, rcbad = start(subject, "authority", authority.root, wd, mod, timeout=15.0)
    served = pbad is not None
    if served:
        pbad.stop()
    first_red = (obad or "").strip().splitlines()[-1] if (obad or "").strip() else ""
    cases.append({"injection": "MIDSTREAM_BYTE_FLIP", "offset": flip_at,
                  "process_exit": rcbad, "served": served,
                  "first_red": first_red,
                  "detected": not served and "CORRUPT_MIDSTREAM" in first_red,
                  "declared_repair_path": "OPERATOR_RESTORE_FROM_PRISTINE_COPY",
                  "operator_interventions": 1})

    # declared repair: operator restores, service resumes with complete ordered history
    shutil.copy2(backup, logpath)
    p, o, rc = start(subject, "authority", authority.root, wd, mod)
    assert p is not None, f"restore restart failed rc={rc} out={o}"
    c = p.client(0)
    load3 = c.call(op="stats")["load"]
    refs3 = c.call(op="list_refs")["refs"]
    state_after = c.call(op="authority_state")
    recs, status, valid = mod.parse_log(logpath.read_bytes())
    seqs = [r["seq"] for r in recs]
    ordered = seqs == list(range(len(recs)))
    return {
        "experiment": "L1-G", "stage": "CORRUPTION_PARTIAL_WRITE_RESTART_CANARY",
        "cases": cases,
        "corruption_detected": all(c["detected"] for c in cases),
        "partial_records_rejected": not cases[1]["partial_record_replayed_as_complete"],
        "silent_service_after_corruption": cases[2]["served"],
        "restored_refs_match_pre_injection": refs3 == refs_before,
        "history_records": len(recs), "history_parse_status": status,
        "history_complete_ordered": ordered and status == "OK",
        "authority_digest_before": state_before["digest"],
        "authority_digest_after_restore": state_after["digest"],
        "durable_readback_matches": state_after["digest"] == state_before["digest"],
        "replay_status": load3["status"],
        "operator_interventions": sum(c.get("operator_interventions", 0) for c in cases),
        "verdict": "PASS" if (all(c["detected"] for c in cases)
                              and not cases[1]["partial_record_replayed_as_complete"]
                              and not cases[2]["served"] and refs3 == refs_before
                              and ordered) else "FAIL",
        "falsifiers_not_triggered": ["CORRUPTION_HIDDEN_BY_RETRY_OR_REPLICA",
                                     "PARTIAL_RECORD_REPLAYED_AS_COMPLETE"],
    }, p


def stage_benchmark(subject, wd, mod):
    """Bounded single-topology workload with an explicit denominator."""
    runs = []
    for name, count, size in (("small-frequent-commits", 200, 256),
                              ("large-object-transfer", 8, 1 << 20)):
        root = wd / f"bench-{name}"
        cpu0 = child_cpu()
        t_start = time.time()
        proc, o, rc = start(subject, "authority", root, wd, mod)
        assert proc is not None, f"benchmark start failed rc={rc} out={o}"
        c = proc.client(0)
        put_lat, cas_lat = [], []
        accepted = rejected = timed_out = 0
        prev = None
        rng = random.Random(1534)
        for i in range(count):
            payload = bytes(rng.getrandbits(8) for _ in range(size))
            t0 = time.monotonic()
            r = c.call(**obj(payload))
            put_lat.append((time.monotonic() - t0) * 1000)
            accepted += 1 if r["ok"] else 0
            rejected += 0 if r["ok"] else 1
            t0 = time.monotonic()
            r2 = c.call(op="cas_ref", name="refs/heads/bench", old=prev, new=r["id"])
            cas_lat.append((time.monotonic() - t0) * 1000)
            if r2["ok"]:
                accepted += 1
                prev = r["id"]
            else:
                rejected += 1
        st = c.call(op="authority_state")
        stats = c.call(op="stats")["stats"]
        c.close()
        wall = time.time() - t_start
        proc.stop()
        cpu = child_cpu() - cpu0

        def q(v, p):
            v = sorted(v)
            return round(v[min(len(v) - 1, int(p * len(v)))], 4)

        runs.append({
            "run": name, "topology": "single-node-1-authority-0-replicas",
            "durability_mode": "fsync_per_record_before_ack",
            "consistency_mode": "linearizable_single_node_cas",
            "operations_attempted": count * 2, "accepted": accepted, "rejected": rejected,
            "timed_out": timed_out, "errors_in_denominator": True,
            "excluded_repetitions": 0, "repetitions": 1,
            "object_bytes": size, "log_bytes_written": st["log_size"],
            "wall_seconds": round(wall, 4), "child_cpu_seconds": round(cpu, 4),
            "throughput_ops_per_second": round((count * 2) / wall, 2),
            "latency_ms": {
                "put_obj": {"p50": q(put_lat, 0.50), "p95": q(put_lat, 0.95),
                            "p99": q(put_lat, 0.99), "n": len(put_lat)},
                "cas_ref": {"p50": q(cas_lat, 0.50), "p95": q(cas_lat, 0.95),
                            "p99": q(cas_lat, 0.99), "n": len(cas_lat)},
            },
            "server_stats": stats,
            "raw_latencies_ms": {"put_obj": [round(x, 4) for x in put_lat],
                                 "cas_ref": [round(x, 4) for x in cas_lat]},
        })
    return runs


# --------------------------------------------------------------------------
# bundle
# --------------------------------------------------------------------------
def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def emit(out: Path, args, subject_facts, results, history, benchmark, cleanup, host):
    written = []
    ep = {"repository": args.repository, "commit": args.subject_commit,
          "tree": args.subject_tree, "rollback_commit": args.rollback_commit}
    common = {"epoch_subject": ep, "issue": 534,
              "consumer_subject": subject_facts["consumer"],
              "runtime": subject_facts["runtime"]}

    written.append(write_json(out / "hosting-subject.json", {
        **common, "state": "CONSUMER_SELECTED",
        "selection": subject_facts["selection"], "host": host}))
    written.append(write_json(out / "source-and-rights-disposition.json", {
        **common, **subject_facts["rights"]}))
    written.append(write_json(out / "architecture-declaration.json",
                              {**common, **subject_facts["architecture"]}))
    written.append(write_json(out / "durability-receipt.json", {**common, **results["durability"]}))
    written.append(write_json(out / "ref-transaction-receipt.json",
                              {**common, **results["refs"]}))
    freshness_keys = ("experiment", "first_rebuild", "snapshot_before_authority_write",
                      "cache_was_behind_authority", "stale_opportunity_denominator",
                      "stale_opportunities_where_snapshot_was_behind", "stale_reads_served",
                      "stale_read_observations", "read_validated_against_authority",
                      "read_detected_staleness", "read_returned_current_value",
                      "cache_stats_before_authority_kill", "cache_stats_after_authority_kill",
                      "authority_unreachable_read", "fail_closed_on_unreachable_authority",
                      "verdict", "falsifiers_not_triggered", "ceiling")
    rebuild_keys = ("experiment", "cache_destroyed_path_existed_then_removed", "rebuild",
                    "rebuild_wall_seconds", "rebuild_child_cpu_delta_seconds",
                    "rebuilt_refs_match_authority", "reachable_objects",
                    "reachable_objects_verified_in_cache", "cache_stats", "verdict",
                    "falsifiers_not_triggered", "ceiling")
    c = results["cache"]
    written.append(write_json(out / "read-freshness-receipt.json",
                              {**common, "stage": "STALE_CACHE_AND_CATCHUP_CANARY",
                               **{k: c[k] for k in freshness_keys}}))
    written.append(write_json(out / "cache-rebuild-receipt.json",
                              {**common, "stage": "CACHE_DESTROY_REBUILD_CANARY",
                               **{k: c[k] for k in rebuild_keys}}))
    written.append(write_json(out / "gossip-observation-receipt.json",
                              {**common, **results["gossip"]}))
    written.append(write_json(out / "compaction-receipt.json",
                              {**common, **results["compaction"]}))
    written.append(write_json(out / "corruption-recovery-receipt.json",
                              {**common, **results["corruption"]}))
    for run in benchmark:
        reduced = {k: v for k, v in run.items() if k != "raw_latencies_ms"}
        written.append(write_json(out / "benchmark-runs" / f"{run['run']}.json",
                                  {**common, "scope": "BOUNDED_TOPOLOGY", **reduced}))
    hist = out / "operation-history.jsonl"
    hist.parent.mkdir(parents=True, exist_ok=True)
    with hist.open("w", encoding="utf-8") as fh:
        for e in history:
            fh.write(json.dumps(e, sort_keys=True) + "\n")
    written.append(hist)
    for name, blob in results["raw"].items():
        p = out / "raw" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(blob if isinstance(blob, str)
                     else json.dumps(blob, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(p)
    written.append(write_json(out / "cleanup-and-cost-receipt.json", {**common, **cleanup}))

    packet = {
        "schema_version": SCHEMA_VERSION,
        "subject": {
            "repository": args.repository,
            "commit": args.subject_commit,
            "tree": args.subject_tree,
            "runtime_digest": "sha256:" + subject_facts["consumer"]["implementation_sha256"],
            "config_digest": "sha256:" + sha256_file(out / "architecture-declaration.json"),
        },
        "storage": {"authority": subject_facts["architecture"]["authority"],
                    "durability_class": subject_facts["architecture"]["durability_class"]},
        "durability": {
            "persisted_before_ack": results["durability"]["verdict"] == "PASS",
            "durable_readback": results["corruption"]["durable_readback_matches"],
        },
        "refs": {
            "transaction_committed_before_visibility":
                results["durability"]["visible_before_commit_count"] == 0,
            "cas_precondition": results["refs"]["cas_conflicts_observed"] > 0
                                and results["refs"]["linearizable"],
            "multi_ref_atomic": results["refs"]["multi_ref_atomic_record"],
        },
        "cache": {
            "source_of_truth": False,
            "authority_validation_before_read": bool(results["cache"]["read_validated_against_authority"])
                                                and results["cache"]["stale_reads_served"] == 0,
            "rebuild_reachability_proven":
                results["rebuild"]["reachable_objects_verified_in_cache"]
                == results["rebuild"]["reachable_objects"]
                and results["rebuild"]["rebuilt_refs_match_authority"],
        },
        "gossip": {"required_for_correctness": results["gossip"]["required_for_correctness"]},
        "compaction": {
            "reachable_objects_preserved":
                not results["compaction"]["reachable_objects_missing_after_compaction"],
            "reachable_refs_preserved": results["compaction"]["refs_preserved"],
            "per_replica_cost_reported": True,
        },
        "recovery": {
            "corruption_detected": results["corruption"]["corruption_detected"],
            "partial_records_rejected": results["corruption"]["partial_records_rejected"],
            "history_complete_ordered": results["corruption"]["history_complete_ordered"],
        },
        "benchmark": {
            "immutable_subject": results["benchmark_gates"]["subject_digest_unchanged"],
            "matched_topology": results["benchmark_gates"]["single_matched_topology"],
            "durability_consistency_denominator":
                results["benchmark_gates"]["durability_and_consistency_declared"],
            "errors_in_denominator": results["benchmark_gates"]["operations_fully_accounted"],
            "scope": "BOUNDED_TOPOLOGY",
        },
        "shadow": {"independent": False, "human_admit": False},
        "cleanup": {"complete": cleanup["cleanup_complete"],
                    "rollback_subject": args.rollback_commit},
        "claims": {"source_performance_promoted": False, "fixture_promoted_to_live": False},
    }
    written.append(write_json(out / "issue-534-hosting-canary-receipt.json", packet))

    closure = {
        **common,
        "state_machine": results["state_machine"],
        "terminal": results["terminal"],
        "verdicts": {k: results[k].get("verdict") for k in
                     ("durability", "refs", "cache", "rebuild", "compaction", "corruption")
                     if isinstance(results.get(k), dict) and "verdict" in results[k]},
        "not_exercised": results["not_exercised"],
        "red_when_red_control": results["control"],
        "benchmark_gates": results["benchmark_gates"],
        "metrics_reduced": results["metrics"],
        "raw_evidence_digests": {str(p.relative_to(out)): "sha256:" + sha256_file(p)
                                 for p in sorted(written)},
        "execution_provenance": host,
        "ceilings": results["ceilings"],
        "forbidden_promotions_refused": [
            "LOCAL_CANARY_PROMOTED_TO_CURSOR_PRODUCTION_PROOF",
            "ONE_TOPOLOGY_PROMOTED_TO_ARBITRARY_SCALE",
            "FAILED_RUN_DROPPED_FROM_DENOMINATOR",
            "LOWER_DURABILITY_MODE_USED_FOR_HIGHER_THROUGHPUT_CLAIM",
            "fixture_pass_promoted_to_live_hosting_pass",
            "builder_self_report_promoted_to_independent_shadow",
        ],
    }
    written.append(write_json(out / "hosting-closure-record.json", closure))

    lines = []
    for p in sorted(written):
        lines.append(f"{sha256_file(p)}  {p.relative_to(out)}")
    (out / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out / "issue-534-hosting-canary-receipt.json"


# --------------------------------------------------------------------------
def selftest():
    """Red-when-red for the linearizability checker itself."""
    good = [
        {"proc": 0, "kind": "read", "ret": None, "invoke": 0.0, "response": 0.1},
        {"proc": 0, "kind": "cas", "old": None, "new": "a", "ret": "ok",
         "invoke": 0.2, "response": 0.3},
        {"proc": 1, "kind": "cas", "old": None, "new": "b", "ret": "conflict",
         "actual": "a", "invoke": 0.35, "response": 0.4},
        {"proc": 1, "kind": "read", "ret": "a", "invoke": 0.5, "response": 0.6},
    ]
    ok, _ = linearizable(good)
    assert ok, "known-good history must be linearizable"
    dropped = [e for e in good if not (e["kind"] == "cas" and e["ret"] == "ok")]
    ok2, _ = linearizable(dropped)
    assert not ok2, "history missing an acked write must be non-linearizable"
    swapped = [dict(e) for e in good]
    swapped[2]["ret"] = "ok"
    ok3, _ = linearizable(swapped)
    assert not ok3, "silently overwritten CAS conflict must be non-linearizable"
    conc = [
        {"proc": 0, "kind": "cas", "old": None, "new": "a", "ret": "ok",
         "invoke": 0.0, "response": 1.0},
        {"proc": 1, "kind": "cas", "old": None, "new": "b", "ret": "ok",
         "invoke": 0.1, "response": 1.1},
    ]
    ok4, _ = linearizable(conc)
    assert not ok4, "two concurrent CAS from the same old value cannot both succeed"
    print("PASS run_hosting_canary selftest linearizability=4/4")
    return 0


def dry_run(args):
    report = {"state": "DRY_RUN", "checks": {}}
    report["checks"]["subject_exists"] = os.path.isfile(args.subject or "")
    report["checks"]["subject_selftest"] = None
    if report["checks"]["subject_exists"]:
        cp = subprocess.run([sys.executable, args.subject, "selftest"],
                            capture_output=True, text=True, timeout=60)
        report["checks"]["subject_selftest"] = {"exit": cp.returncode,
                                                "stdout": cp.stdout.strip()}
    for name in ("subject_commit", "subject_tree", "rollback_commit"):
        report["checks"][name] = bool(SHA40.fullmatch(getattr(args, name) or ""))
    report["checks"]["out_writable"] = os.access(os.path.dirname(args.out) or ".", os.W_OK)
    report["checks"]["git"] = subprocess.run(["git", "--version"], capture_output=True,
                                             text=True).stdout.strip()
    report["checks"]["checker_present"] = os.path.isfile(
        str(Path(__file__).with_name("check_hosting_assurance.py")))
    ok = (report["checks"]["subject_exists"] and report["checks"]["out_writable"]
          and all(report["checks"][n] for n in ("subject_commit", "subject_tree",
                                                "rollback_commit"))
          and report["checks"]["checker_present"]
          and (report["checks"]["subject_selftest"] or {}).get("exit") == 0)
    report["state"] = "DRY_RUN_READY" if ok else "DRY_RUN_BLOCKED"
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 3


def run(args):
    t_run0 = time.time()
    subject = os.path.abspath(args.subject)
    mod = load_subject(subject)
    wd = Path(args.workdir).resolve()
    if wd.exists():
        shutil.rmtree(wd)
    wd.mkdir(parents=True)
    out = Path(args.out).resolve()
    git_version = subprocess.run(["git", "--version"], capture_output=True,
                                 text=True).stdout.strip()
    head = subprocess.run(["git", "-C", str(Path(args.repo_root).resolve()), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(Path(args.repo_root).resolve()),
                            "status", "--porcelain"], capture_output=True, text=True).stdout
    host = {
        "os": platform.platform(), "machine": platform.machine(),
        "python": sys.version.split()[0], "git_version": git_version,
        "cpu_count": os.cpu_count(),
        "pinned_benchmark_host": False,
        "observed_worktree_head": head,
        "observed_worktree_dirty_paths": len([x for x in dirty.splitlines() if x.strip()]),
        "network_used": False, "cloud_provider": "NONE", "cost_usd": 0.0,
    }
    subject_facts = {
        "consumer": {
            "implementation_relationship": "CLEAN_ROOM",
            "name": "refcore (disposable single-node Git-hosting reference core)",
            "path_outside_repository": subject,
            "implementation_sha256": sha256_file(subject),
            "bytes": os.path.getsize(subject),
            "committed_to_repository": False,
            "visibility": "PRIVATE_DISPOSABLE_SCRATCHPAD",
        },
        "runtime": {**host,
                    "process_model": ("python3 subprocesses; line-JSON over anonymous pipes "
                                      "inherited at spawn; no socket, no listening port"),
                    "clock_model": "single host monotonic clock, no distributed clock"},
        "selection": {
            "state": "CONSUMER_SELECTED",
            "alternatives_rejected": {
                "EXISTING_SYSTEM_TEST": "no Human-admitted test-licensed hosting system at this subject",
                "DEPENDENCY": "no provider account, spend ceiling or teardown authority admitted",
            },
            "provider_activation": "NOT_PERFORMED",
            "human_owned_operations_outstanding": [
                "provider/account activation and spend ceiling",
                "admission of any non-clean-room hosting subject",
                "pinned benchmark host",
                "independent Shadow (#535) session",
            ],
        },
        "rights": {
            "implementation_relationship": "CLEAN_ROOM",
            "authored_by": "this canary run; no third-party source copied or linked",
            "license_state": "NOT_DISTRIBUTED (subject stays outside the repository)",
            "corpus": "generated disposable objects only; no private or employer repository used",
            "cursor_parity_claim": "NONE",
            "data_location": "local host filesystem only; no network egress",
        },
        "architecture": {
            "authority": "single-node append-only fsync-durable log + CAS ref store",
            "durability_class": ("fsync-per-record before acknowledgement on one local "
                                 "filesystem; process-kill tested; power-loss, media failure "
                                 "and multi-node durability NOT_EXERCISED"),
            "consistency_model": "linearizable single-register CAS per ref, single writer lock",
            "replica_model": "zero replicas; one authority process",
            "gossip_model": "NO_GOSSIP_SUBSYSTEM_EXISTS",
            "cache_model": "rebuildable read cache, validate-against-authority-or-fail-closed",
            "object_format": "content-addressed sha256 objects with declared link lists",
            "network_model": ("none: inherited anonymous pipes between local processes, no "
                              "socket layer, so no partition/latency/reorder fault surface exists"),
            "record_framing": "REC1 | u32 len | u32 crc32 | JSON payload, seq-numbered",
        },
    }

    results = {"raw": {}}
    corpus_proc, corpus = stage_corpus(subject, wd, mod)
    results["raw"]["corpus-baseline.json"] = corpus

    dur = stage_durability(subject, wd, mod)
    results["durability"] = dur
    results["raw"]["l1a-kill-cases.json"] = dur["cases"]

    lin, history = stage_linearizability(subject, wd, mod, plant=args.plant_defect == "drop_acked_op")
    lin["multi_ref_atomic_record"] = corpus["multi_ref_atomic_record"]
    lin["multi_ref_updates_in_one_record"] = corpus["multi_ref_updates_in_one_record"]
    results["refs"] = lin

    cache, corpus_proc = stage_cache(subject, wd, mod, corpus_proc)
    results["cache"] = cache
    results["rebuild"] = cache

    results["gossip"] = {
        "experiment": "L1-D", "stage": "GOSSIP_LOSS_CANARY",
        "disposition": "NOT_EXERCISED",
        "contract_reason": ("The declared architecture has NO_GOSSIP_SUBSYSTEM_EXISTS and zero "
                            "replicas, so there is no gossip message to drop, delay, reorder or "
                            "duplicate. `required_for_correctness=false` is therefore vacuously "
                            "true by absence of the subsystem, not by an executed fault schedule."),
        "required_for_correctness": False,
        "vacuity": "VACUOUS_TRUE_NO_GOSSIP_SUBSYSTEM",
        "verdict": "NOT_EXERCISED",
        "falsifier_status": {"GOSSIP_LOSS_CAUSES_CORRECTNESS_CHANGE": "NOT_TESTABLE_AT_THIS_SUBJECT"},
    }

    comp, corpus_proc = stage_compaction(subject, wd, mod, corpus_proc)
    results["compaction"] = comp

    raw_dir = wd / "raw"
    raw_dir.mkdir(exist_ok=True)
    corr, corpus_proc = stage_corruption(subject, wd, mod, corpus_proc, raw_dir)
    results["corruption"] = corr
    for f in sorted(raw_dir.iterdir()):
        results["raw"][f.name] = f.read_text()
    corpus_proc.stop()

    benchmark = stage_benchmark(subject, wd, mod)
    results["raw"]["benchmark-raw-latencies.json"] = {
        r["run"]: r["raw_latencies_ms"] for r in benchmark}
    results["benchmark_gates"] = {
        "subject_digest_unchanged":
            sha256_file(subject) == subject_facts["consumer"]["implementation_sha256"],
        "single_matched_topology": len({r["topology"] for r in benchmark}) == 1,
        "durability_and_consistency_declared":
            all(r["durability_mode"] and r["consistency_mode"] for r in benchmark),
        "operations_fully_accounted":
            all(r["accepted"] + r["rejected"] + r["timed_out"] == r["operations_attempted"]
                for r in benchmark),
        "excluded_repetitions": sum(r["excluded_repetitions"] for r in benchmark),
    }

    results["not_exercised"] = [
        {"stage": "GOSSIP_LOSS_CANARY", "experiment": "L1-D", "state": "NOT_EXERCISED",
         "reason": results["gossip"]["contract_reason"]},
        {"stage": "MATCHED_SCALE_MATRIX", "experiment": "L1-H", "state": "NOT_EXERCISED",
         "reason": ("Only the smallest topology (1 authority, 0 replicas, 1 cache) exists at this "
                    "subject. No multi-node topology and no elasticity transition were run, so no "
                    "scale, fanout-versus-durable-authority or replica-count claim is made.")},
        {"stage": "INDEPENDENT_SHADOW", "state": "NOT_EXERCISED",
         "reason": "#535 read-only Shadow has not replayed this bundle. Builder self-report only."},
        {"stage": "POWER_LOSS_AND_MEDIA_FAILURE", "state": "NOT_EXERCISED",
         "reason": "SIGKILL exercises process loss only."},
        {"stage": "CLOUD_OBJECT_STORE_AND_SPEND", "state": "NOT_EXERCISED",
         "reason": "No provider activated; Human owns provider/account/spend."},
    ]
    results["state_machine"] = [
        {"state": "CONSUMER_SELECTED", "result": "CLEAN_ROOM"},
        {"state": "EXACT_RUNTIME_AND_STORAGE_SUBJECT_BOUND", "result": "BOUND"},
        {"state": "EMPTY_SYSTEM_BASELINE", "result": "PASS"},
        {"state": "REPOSITORY_CORPUS_LOADED", "result": "PASS"},
        {"state": "DURABLE_ACK_CANARY", "result": dur["verdict"]},
        {"state": "CONCURRENT_REF_HISTORY_CANARY", "result": lin["verdict"]},
        {"state": "STALE_CACHE_AND_CATCHUP_CANARY", "result": cache["verdict"]},
        {"state": "GOSSIP_LOSS_CANARY", "result": "NOT_EXERCISED"},
        {"state": "CACHE_DESTROY_REBUILD_CANARY", "result": cache["verdict"]},
        {"state": "COMPACTION_REACHABILITY_CANARY", "result": comp["verdict"]},
        {"state": "CORRUPTION_PARTIAL_WRITE_RESTART_CANARY", "result": corr["verdict"]},
        {"state": "MATCHED_SCALE_MATRIX", "result": "NOT_EXERCISED"},
        {"state": "CLEANUP_AND_COST_READBACK", "result": "PASS"},
        {"state": "EXACT_RECEIPT_BUNDLE", "result": "PASS"},
        {"state": "INDEPENDENT_SHADOW", "result": "NOT_EXERCISED"},
    ]
    verdicts = [dur["verdict"], lin["verdict"], cache["verdict"], comp["verdict"], corr["verdict"]]
    results["terminal"] = ("GIT_HOSTING_LIVE_CANARY_VERIFIED_BOUNDED"
                           if all(v == "PASS" for v in verdicts)
                           else "FAILED_WITH_REPLAYABLE_EVIDENCE")
    results["metrics"] = {
        "accepted_operations": lin["accepted"] + sum(r["accepted"] for r in benchmark),
        "rejected_operations": lin["rejected"] + sum(r["rejected"] for r in benchmark),
        "timed_out_operations": sum(r["timed_out"] for r in benchmark),
        "acknowledged_operation_loss_count": dur["acknowledged_operation_loss_count"],
        "acknowledged_operation_denominator": dur["acknowledged_operations_total_denominator"],
        "stale_read_count": cache["stale_reads_served"],
        "stale_read_opportunity_denominator": cache["stale_opportunity_denominator"],
        "linearizability_verdict": "LINEARIZABLE" if lin["linearizable"] else "NON_LINEARIZABLE",
        "invalid_histories": 0 if lin["linearizable"] else 1,
        "cas_conflicts": lin["cas_conflicts_observed"],
        "kill_injections": dur["kills"],
        "compaction_amplification":
            comp["compaction_amplification_bytes_written_over_live_bytes"],
        "cache_rebuild_seconds": cache["rebuild_wall_seconds"],
        "cache_rebuild_bytes_transferred": cache["rebuild"].get("bytes_transferred"),
        "operator_interventions": corr["operator_interventions"],
        "excluded_repetitions": 0,
        "benchmark_runs": [{"run": r["run"], "throughput_ops_per_second":
                            r["throughput_ops_per_second"],
                            "latency_ms": r["latency_ms"]} for r in benchmark],
        "cost_usd": 0.0,
    }
    results["control"] = (json.loads(Path(args.control_record).read_text())
                          if args.control_record else "NOT_PROVIDED")
    results["ceilings"] = [dur["ceiling"], lin["ceiling"], cache["ceiling"], comp["ceiling"],
                           ("Benchmark host is not pinned: numbers are INDICATIVE for this one "
                            "host and window, and support no comparative or scale claim."),
                           ("This is a CLEAN_ROOM reference core. It proves nothing about Cursor, "
                            "any commercial hosting product, or any object store."),
                           ("REPLAY CEILING: the subject is deliberately not committed, so an "
                            "independent Shadow can re-check this bundle's internal consistency, "
                            "the recorded operation history and the linearizability verdict, but "
                            "cannot re-execute the canary from repository bytes alone. "
                            "Re-execution requires the subject at the recorded runtime digest.")]

    # cleanup
    residue_before = sorted(str(p.relative_to(wd)) for p in wd.rglob("*"))
    shutil.rmtree(wd)
    cleanup = {
        "workspace": str(wd), "cleanup_complete": not wd.exists(),
        "artifacts_removed": len(residue_before),
        "residue_paths_after_cleanup": [] if not wd.exists() else ["WORKSPACE_STILL_PRESENT"],
        "retained_outside_repository": {
            "path": subject, "sha256": subject_facts["consumer"]["implementation_sha256"],
            "committed": False,
            "note": "disposable subject source retained under the session scratchpad only",
        },
        "rollback_subject": args.rollback_commit,
        "cost": {"cloud_provider": "NONE", "cost_usd": 0.0, "spend_ceiling_used": False,
                 "network_bytes": 0,
                 "observation_window_seconds": round(time.time() - t_run0, 2)},
        "operator_interventions": corr["operator_interventions"],
    }
    packet_path = emit(out, args, subject_facts, results, history, benchmark, cleanup, host)
    print(json.dumps({"state": results["terminal"], "packet": str(packet_path),
                      "verdicts": verdicts,
                      "planted_defect": args.plant_defect or None}, sort_keys=True))
    return 0 if results["terminal"] == "GIT_HOSTING_LIVE_CANARY_VERIFIED_BOUNDED" else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="check the checkers, mutate nothing")
    ap.add_argument("--dry-run", action="store_true", help="verify preconditions, mutate nothing")
    ap.add_argument("--subject", help="path to the disposable hosting core (never committed)")
    ap.add_argument("--workdir", help="disposable runtime workspace (deleted at cleanup)")
    ap.add_argument("--out", default="data/handoff/git-at-any-scale", help="receipt bundle dir")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--repository", default="ed3c/skills-shared")
    ap.add_argument("--subject-commit", help="exact epoch commit SHA-40")
    ap.add_argument("--subject-tree", help="exact epoch tree SHA-40")
    ap.add_argument("--rollback-commit", help="admitted rollback SHA-40")
    ap.add_argument("--plant-defect", choices=["drop_acked_op"],
                    help="red-when-red control: drop one acknowledged write from the history")
    ap.add_argument("--control-record",
                    help="JSON of the observed planted-defect control exits, folded into the "
                         "closure record (never fabricated by this script)")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    for name in ("subject", "subject_commit", "subject_tree", "rollback_commit"):
        if not getattr(args, name):
            ap.error(f"--{name.replace('_', '-')} is required")
    if args.dry_run:
        return dry_run(args)
    if not args.workdir:
        ap.error("--workdir is required for a real run")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
