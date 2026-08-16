#!/usr/bin/env python3
"""Blindspot Hybrid SQLite contract. Exit 0/2/64/70."""
from __future__ import annotations

import argparse, hashlib, json, re, sqlite3, sys
from pathlib import Path, PurePosixPath
from typing import Any

OK, ASSERT, INVALID, MECHANISM = 0, 2, 64, 70
EVENT_SCHEMA = "blindspot-hybrid/events/v1"
SUBJECT_SCHEMA = "blindspot-hybrid/subject/v1"
REPORT_SCHEMA = "blindspot-hybrid/report/v1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
EID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
KINDS = {
    "grepai": {"intent_anchor", "runtime_exploration"},
    "scip": {"declaration", "reference", "implementation", "relation"},
    "tree-sitter": {"ast_skeleton", "syntax_capture"},
    "serena": {"symbol_read", "reference_read", "diagnostic", "edit_proposal", "execution_observation"},
    "lancedb": {"similarity_projection"},
    "source-readback": {"source_readback"},
    "test": {"test_observation"},
}
READBACK_LANES = {"grepai", "scip", "serena"}
AST_KINDS = {
    ("scip", "declaration"), ("scip", "reference"),
    ("scip", "implementation"), ("scip", "relation"),
    ("serena", "edit_proposal"), ("serena", "execution_observation"),
}


class Bad(ValueError): pass
class Broken(RuntimeError): pass


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canon(value).encode()).hexdigest()


def need(condition: bool, message: str) -> None:
    if not condition: raise Bad(message)


def load(path: Path) -> Any:
    try: return json.loads(path.read_text())
    except FileNotFoundError as exc: raise Bad(f"ABSENT: {path}") from exc
    except json.JSONDecodeError as exc: raise Bad(f"UNREADABLE_JSON: {path}: {exc}") from exc
    except OSError as exc: raise Broken(f"UNREADABLE_FILE: {path}: {exc}") from exc


def relpath(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value: return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and all(part not in {"", "."} for part in path.parts)


def subject(value: Any) -> dict[str, str]:
    need(isinstance(value, dict), "subject must be an object")
    need(set(value) <= {"schema", "repository", "commit", "tree"}, "subject contains unknown fields")
    need(value.get("schema") == SUBJECT_SCHEMA, "subject.schema invalid")
    need(isinstance(value.get("repository"), str) and REPO.fullmatch(value["repository"]), "subject.repository invalid")
    need(isinstance(value.get("commit"), str) and SHA40.fullmatch(value["commit"]), "subject.commit invalid")
    need(isinstance(value.get("tree"), str) and SHA40.fullmatch(value["tree"]), "subject.tree invalid")
    return {key: value[key] for key in ("repository", "commit", "tree")}


def links(value: Any, event_id: str) -> list[str]:
    need(isinstance(value, list), f"{event_id}: links must be an array")
    need(all(isinstance(item, str) and EID.fullmatch(item) and item != event_id for item in value), f"{event_id}: linked id invalid")
    need(len(value) == len(set(value)), f"{event_id}: duplicate links")
    return value


def event(value: Any) -> dict[str, Any]:
    need(isinstance(value, dict), "event must be an object")
    allowed = {"id", "lane", "kind", "path", "symbol", "target_path", "target_symbol", "links", "admitted", "payload"}
    need(set(value) <= allowed, "event contains unknown fields")
    event_id, lane, kind = value.get("id"), value.get("lane"), value.get("kind")
    need(isinstance(event_id, str) and EID.fullmatch(event_id), "event.id invalid")
    need(lane in KINDS and kind in KINDS[lane], f"{event_id}: kind invalid for lane {lane}")
    for key in ("path", "target_path"):
        if value.get(key) is not None: need(relpath(value[key]), f"{event_id}: {key} invalid")
    for key in ("symbol", "target_symbol"):
        if value.get(key) is not None: need(isinstance(value[key], str) and value[key].strip(), f"{event_id}: {key} invalid")
    linked = links(value.get("links", []), event_id)
    admitted, payload = value.get("admitted", False), value.get("payload", {})
    need(isinstance(admitted, bool), f"{event_id}: admitted must be boolean")
    need(isinstance(payload, dict), f"{event_id}: payload must be an object")
    need(not admitted or lane in {"source-readback", "test"}, f"PROVIDER_SELF_ADMISSION: {event_id}")
    if lane == "source-readback":
        need(linked and admitted and value.get("path"), f"{event_id}: admitted readback requires path and links")
    elif lane == "test":
        need(linked and isinstance(payload.get("passed"), bool), f"{event_id}: test requires links and payload.passed")
        need(admitted is payload["passed"], f"{event_id}: test admission must equal payload.passed")
    elif lane == "lancedb":
        need(len(linked) == 1 and not admitted, f"{event_id}: LanceDB needs one source link and cannot self-admit")
    elif lane == "grepai": need(value.get("path") or value.get("symbol"), f"{event_id}: intent anchor needs path or symbol")
    elif lane == "scip":
        need(value.get("path") and value.get("symbol"), f"{event_id}: SCIP needs path and symbol")
        if kind == "relation": need(value.get("target_path") or value.get("target_symbol"), f"{event_id}: relation needs target")
    elif lane == "tree-sitter": need(value.get("path"), f"{event_id}: AST event needs path")
    elif lane == "serena":
        need(value.get("path") or value.get("symbol"), f"{event_id}: Serena event needs path or symbol")
        need(payload.get("effect", "read-only") in {"read-only", "proposal", "observed"}, f"{event_id}: Serena effect invalid")
    return {key: value.get(key) for key in ("id", "lane", "kind", "path", "symbol", "target_path", "target_symbol")} | {"links": linked, "admitted": admitted, "payload": payload}


def db(path: Path) -> sqlite3.Connection:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(path); con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON"); con.execute("PRAGMA journal_mode=WAL")
        con.executescript("""
          CREATE TABLE IF NOT EXISTS subjects(digest TEXT PRIMARY KEY, json TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, subject_digest TEXT NOT NULL REFERENCES subjects(digest), lane TEXT NOT NULL, kind TEXT NOT NULL, path TEXT, admitted INTEGER NOT NULL, digest TEXT NOT NULL, json TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS links(source TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE, target TEXT NOT NULL, ordinal INTEGER NOT NULL, PRIMARY KEY(source,target));
          CREATE INDEX IF NOT EXISTS events_lane ON events(subject_digest,lane,kind);
          CREATE INDEX IF NOT EXISTS links_target ON links(target);
        """)
        return con
    except (OSError, sqlite3.Error) as exc: raise Broken(f"DATABASE_OPEN_FAILED: {exc}") from exc


def db_subject(con: sqlite3.Connection) -> tuple[str, dict[str, str]] | None:
    rows = con.execute("SELECT digest,json FROM subjects ORDER BY digest").fetchall()
    if not rows: return None
    if len(rows) != 1: raise Broken("DATABASE_CONTAINS_MULTIPLE_SUBJECTS")
    return rows[0]["digest"], json.loads(rows[0]["json"])


def cmd_init(args: argparse.Namespace) -> int:
    value = subject(load(args.subject)); key = digest(value); con = db(args.db)
    try:
        prior = db_subject(con)
        if prior: need(prior[0] == key, "DATABASE_SUBJECT_MISMATCH")
        else: con.execute("INSERT INTO subjects VALUES (?,?)", (key, canon(value)))
        con.commit()
    finally: con.close()
    print(canon({"state": "INITIALIZED", "subject_digest": key})); return OK


def cmd_ingest(args: argparse.Namespace) -> int:
    bundle = load(args.input)
    need(isinstance(bundle, dict) and set(bundle) <= {"schema", "subject", "events"}, "event bundle invalid")
    need(bundle.get("schema") == EVENT_SCHEMA, "event bundle schema invalid")
    subj = subject(bundle.get("subject")); key = digest(subj)
    need(isinstance(bundle.get("events"), list) and bundle["events"], "events must be non-empty")
    values = [event(item) for item in bundle["events"]]
    need(len({item["id"] for item in values}) == len(values), "duplicate event ids")
    con = db(args.db)
    try:
        prior_subject = db_subject(con); need(prior_subject is not None, "DATABASE_NOT_INITIALIZED")
        need(prior_subject[0] == key, "EVENT_SUBJECT_MISMATCH")
        for item in values:
            item_digest = digest(item)
            prior = con.execute("SELECT digest FROM events WHERE id=?", (item["id"],)).fetchone()
            if prior:
                if prior["digest"] != item_digest: raise Broken(f"EVENT_ID_DRIFT: {item['id']}")
                continue
            con.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?)", (item["id"], key, item["lane"], item["kind"], item.get("path"), int(item["admitted"]), item_digest, canon(item)))
            con.executemany("INSERT INTO links VALUES (?,?,?)", [(item["id"], target, ordinal) for ordinal, target in enumerate(item["links"])])
        con.commit()
    finally: con.close()
    print(canon({"state": "INGESTED", "event_count": len(values)})); return OK


def build_report(con: sqlite3.Connection) -> dict[str, Any]:
    subj = db_subject(con); need(subj is not None, "DATABASE_NOT_INITIALIZED")
    rows = con.execute("SELECT * FROM events ORDER BY id").fetchall()
    values = {row["id"]: json.loads(row["json"]) for row in rows}
    outgoing: dict[str, list[str]] = {event_id: [] for event_id in values}
    incoming: dict[str, list[str]] = {}
    for row in con.execute("SELECT source,target FROM links ORDER BY source,ordinal"):
        outgoing.setdefault(row["source"], []).append(row["target"])
        incoming.setdefault(row["target"], []).append(row["source"])
    ast_paths = {value.get("path") for value in values.values() if value["lane"] == "tree-sitter" and value.get("path")}
    blind: list[dict[str, Any]] = []
    for event_id, value in values.items():
        lane, kind = value["lane"], value["kind"]
        for target in outgoing[event_id]:
            if target not in values: blind.append({"code": "LINK_TARGET_MISSING", "event_id": event_id, "target_id": target})
        if lane in READBACK_LANES:
            admitted = [values[src] for src in incoming.get(event_id, []) if src in values and values[src]["admitted"] and values[src]["lane"] in {"source-readback", "test"}]
            if not admitted: blind.append({"code": "SOURCE_READBACK_MISSING", "event_id": event_id, "lane": lane})
        if (lane, kind) in AST_KINDS:
            for path in (value.get("path"), value.get("target_path")):
                if path and path not in ast_paths: blind.append({"code": "AST_COVERAGE_MISSING", "event_id": event_id, "path": path})
        if lane == "source-readback":
            for target in outgoing[event_id]:
                if target in values and values[target]["lane"] in {"source-readback", "test", "lancedb"}: blind.append({"code": "READBACK_TARGET_INVALID", "event_id": event_id, "target_id": target})
        if lane == "lancedb":
            target = outgoing[event_id][0]
            if target not in values: blind.append({"code": "VECTOR_PROJECTION_ORPHAN", "event_id": event_id, "target_id": target})
            elif values[target]["lane"] == "lancedb": blind.append({"code": "VECTOR_PROJECTION_CHAINED", "event_id": event_id, "target_id": target})
        if lane == "test" and value["payload"].get("passed") is not True: blind.append({"code": "TEST_OBSERVATION_FAILED", "event_id": event_id})
    counts: dict[str, int] = {}
    for value in values.values(): counts[value["lane"]] = counts.get(value["lane"], 0) + 1
    blind.sort(key=canon)
    return {"schema": REPORT_SCHEMA, "state": "PASS" if not blind else "BLINDSPOTS", "subject": subj[1], "counts": dict(sorted(counts.items())), "blindspots": blind, "authority": {"sqlite": "AUTHORITATIVE_LEDGER", "lancedb": "REBUILDABLE_PROJECTION_ONLY", "providers": "CANDIDATE_ONLY_UNTIL_READBACK"}}


def cmd_verify(args: argparse.Namespace) -> int:
    con = db(args.db)
    try: report = build_report(con)
    finally: con.close()
    print(canon(report), file=sys.stdout if report["state"] == "PASS" else sys.stderr)
    return OK if report["state"] == "PASS" else ASSERT


def cmd_report(args: argparse.Namespace) -> int:
    con = db(args.db)
    try: report = build_report(con)
    finally: con.close()
    try: args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(canon(report) + "\n")
    except OSError as exc: raise Broken(f"REPORT_WRITE_FAILED: {exc}") from exc
    print(canon({"state": report["state"], "output": str(args.output)})); return OK if report["state"] == "PASS" else ASSERT


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__); sub = root.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init"); init.add_argument("--db", type=Path, required=True); init.add_argument("--subject", type=Path, required=True); init.set_defaults(run=cmd_init)
    ingest = sub.add_parser("ingest"); ingest.add_argument("--db", type=Path, required=True); ingest.add_argument("--input", type=Path, required=True); ingest.set_defaults(run=cmd_ingest)
    verify = sub.add_parser("verify"); verify.add_argument("--db", type=Path, required=True); verify.set_defaults(run=cmd_verify)
    report = sub.add_parser("report"); report.add_argument("--db", type=Path, required=True); report.add_argument("--output", type=Path, required=True); report.set_defaults(run=cmd_report)
    return root


def main() -> int:
    args = parser().parse_args()
    try: return args.run(args)
    except Bad as exc: print(f"INVALID: {exc}", file=sys.stderr); return INVALID
    except (Broken, OSError, sqlite3.Error) as exc: print(f"MECHANISM_ERROR: {exc}", file=sys.stderr); return MECHANISM


if __name__ == "__main__": raise SystemExit(main())
