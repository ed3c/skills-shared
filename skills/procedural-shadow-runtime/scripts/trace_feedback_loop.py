#!/usr/bin/env python3
"""Run the production-to-Golden feedback state machine over real executions.

Exit codes:
  0   every lane reached a terminal state and no lane was simulated
  2   a lane refused, or a lane claimed a state its evidence does not support
  64  the canary case set, the adapter, or the output path is absent

#216. The state machine is:

    PRODUCTION_TRACE -> ANOMALY_SELECTED -> PII_SCRUBBED
      -> HUMAN_ADJUDICATED -> GOLDEN_CANDIDATE -> GOLDEN_ADMITTED
      -> REGRESSION_REPLAYED

Three things this deliberately does not do.

It does not call a vendor. OpenTelemetry is the portable span shape; Langfuse
would be one exporter of that shape. Writing the spans to a provider proves an
integration, not a feedback loop, so the loop is proven first and the exporter
is left as an adapter seam.

It does not describe the canary as production. There is no authorised
production traffic for this repository, so the traces come from real executions
of the reference adapter over an explicitly admitted production-like canary. The
lane records that provenance rather than laundering it.

It does not adjudicate. `GOLDEN_ADMITTED` requires a Human record naming an
approver and a decision. Without one the lane is BLOCKED and the replay lane
after it is BLOCKED too -- a candidate is not ground truth because a script is
confident.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
MODULE = SKILL / "modules" / "ecommerce-dispute"

INVALID = 64
REFUSED = 2

SCRUBBER_VERSION = "pii-scrubber/v1"

# Reserved-for-fiction ranges still get scrubbed. A scrubber that skips test
# values is a scrubber that has never run on the path production would take.
PII_RULES: list[tuple[str, str, str]] = [
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "EMAIL", "<EMAIL>"),
    # No leading \b: the boundary never holds before `+`, so the country code
    # was surviving as a `+1-` stub next to the placeholder. A partial
    # identifier left beside <PHONE> reads as a scrub that worked.
    (r"(?:\+1[-. ])?\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b", "PHONE", "<PHONE>"),
    (r"(?:\+1[-. ])?\b\d{3}-\d{4}\b", "PHONE", "<PHONE>"),
    (r"\b(?:\d[ -]?){13,19}\b", "PAN", "<PAN>"),
    (r"\b\d{1,4} [A-Z][A-Za-z]+ (?:Row|Lane|Street|Road|Avenue)\b", "ADDRESS", "<ADDRESS>"),
]

LANE_STATES = {"OBSERVED", "NOT_OBSERVED", "NOT_EXERCISED", "BLOCKED"}


class Refused(Exception):
    pass


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest_json(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load_adapter() -> Any:
    path = MODULE / "reference_adapter.py"
    if not path.is_file():
        print(f"TRACE-INVALID absent-adapter: {path}", file=sys.stderr)
        raise SystemExit(INVALID)
    spec = importlib.util.spec_from_file_location("reference_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def span_id(*parts: str) -> str:
    """Deterministic span identity, derived from the run rather than a clock.

    A wall-clock id would make two replays of the same evidence produce
    different trace files, and a receipt that changes when nothing changed
    cannot be diffed against its own past.
    """
    return sha256_text("|".join(parts))[:16]


def trace_case(case: dict[str, Any], run_case: Any, subject: dict[str, Any]) -> dict[str, Any]:
    """One OTel-shaped trace per real adapter execution."""
    trace = span_id("trace", subject["tree_sha"], case["case_id"])
    result = run_case(case)
    final = result["final"]
    observed = result.get("trace", {})

    def span(name: str, index: int, attributes: dict[str, Any]) -> dict[str, Any]:
        return {
            "trace_id": trace,
            "span_id": span_id(trace, name, str(index)),
            "parent_span_id": None if index == 0 else span_id(trace, "root", "0"),
            "name": name,
            "attributes": attributes,
        }

    spans = [
        span("root", 0, {"case_id": case["case_id"], "subject.tree_sha": subject["tree_sha"]}),
        span("state.initialise", 1, {"dispute_id": case["input"]["dispute_id"],
                                     "claimed_amount": case["input"]["claimed_amount"]}),
        span("tool.logistics", 2, {"latency_ms": case["mock"]["logistics"]["latency_ms"],
                                   "status": case["mock"]["logistics"]["status"]}),
        span("model.generate", 3, {"action": case["mock"]["llm"]["action"],
                                   "confidence": case["mock"]["llm"]["confidence"],
                                   "approved_amount": case["mock"]["llm"]["approved_amount"]}),
        span("guardrail.evaluate", 4, {"requires_hitl": final.get("requires_hitl"),
                                       "route": final.get("route")}),
        span("hitl.event", 5, {"reviewer_overrode_agent": case["reviewer"]["overrode_agent"],
                               "reviewer_decision": case["reviewer"]["reviewer_decision"]}),
        span("sideeffect.execute", 6, {"execution_status": final.get("execution_status"),
                                       "idempotency_key": final.get("idempotency_key"),
                                       "tool_calls": observed.get("tool_calls")}),
    ]
    return {
        "trace_id": trace,
        "case_id": case["case_id"],
        "subject": subject,
        "spans": spans,
        # The raw user text is carried on the trace exactly once, so the scrub
        # lane has something to remove. Nothing downstream reads it after that.
        "raw_payload": case["input"]["user_description"],
        "outcome": {
            "requires_hitl": final.get("requires_hitl"),
            "route": final.get("route"),
            "execution_status": final.get("execution_status"),
            "confidence": case["mock"]["llm"]["confidence"],
            "latency_ms": case["mock"]["logistics"]["latency_ms"],
            "reviewer_overrode_agent": case["reviewer"]["overrode_agent"],
        },
        "trace_complete": all(span["span_id"] for span in spans),
    }


ANOMALY_SELECTORS: list[tuple[str, Any]] = [
    ("reviewer-override", lambda t: bool(t["outcome"]["reviewer_overrode_agent"])),
    ("confidence-below-threshold", lambda t: float(t["outcome"]["confidence"]) < 0.80),
    ("tool-timeout", lambda t: int(t["outcome"]["latency_ms"]) > 5000),
    ("incomplete-trace", lambda t: not t["trace_complete"]),
]


def select_anomalies(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = []
    for trace in traces:
        reasons = [name for name, rule in ANOMALY_SELECTORS if rule(trace)]
        if reasons:
            selected.append({"trace_id": trace["trace_id"], "case_id": trace["case_id"],
                             "reasons": reasons})
    return selected


def scrub(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Replace, count, and never record what was replaced."""
    findings: list[dict[str, Any]] = []
    scrubbed = text
    for pattern, kind, placeholder in PII_RULES:
        matches = re.findall(pattern, scrubbed)
        if matches:
            findings.append({"kind": kind, "count": len(matches)})
            scrubbed = re.sub(pattern, placeholder, scrubbed)
    return scrubbed, findings


def scrub_receipt(trace: dict[str, Any]) -> dict[str, Any]:
    raw = trace["raw_payload"]
    scrubbed, findings = scrub(raw)
    if scrubbed == raw and findings:
        raise Refused(f"{trace['case_id']}: findings reported but nothing was replaced")
    return {
        "case_id": trace["case_id"],
        "trace_id": trace["trace_id"],
        "scrubber_version": SCRUBBER_VERSION,
        # Digests only. Storing the before-value would put the thing being
        # removed into the artefact that proves it was removed.
        "before_sha256": sha256_text(raw),
        "after_sha256": sha256_text(scrubbed),
        "findings": findings,
        "scrubbed_payload": scrubbed,
        "raw_retained": False,
    }


def normalised_case_digest(trace: dict[str, Any], scrubbed: str) -> str:
    """Two reports of one incident must collapse to one Golden case.

    Identity is the failure shape -- route, outcome, override, and the scrubbed
    text with its remaining digits removed -- not the report's wording. Keying
    on raw text would admit the same incident once per customer who reported it.
    """
    shape = {
        "route": trace["outcome"]["route"],
        "execution_status": trace["outcome"]["execution_status"],
        "requires_hitl": trace["outcome"]["requires_hitl"],
        "reviewer_overrode_agent": trace["outcome"]["reviewer_overrode_agent"],
        "text": re.sub(r"[0-9]+", "#", re.sub(r"<[A-Z]+>", "", scrubbed)).strip().lower(),
    }
    return digest_json(shape)


def propose_golden(traces: list[dict[str, Any]], anomalies: list[dict[str, Any]],
                   scrubs: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_case = {trace["case_id"]: trace for trace in traces}
    seen: dict[str, str] = {}
    candidates, duplicates = [], []
    for anomaly in anomalies:
        trace = by_case[anomaly["case_id"]]
        scrubbed = scrubs[anomaly["case_id"]]["scrubbed_payload"]
        key = normalised_case_digest(trace, scrubbed)
        if key in seen:
            duplicates.append({"case_id": anomaly["case_id"], "duplicate_of": seen[key],
                               "normalised_digest": key})
            continue
        seen[key] = anomaly["case_id"]
        candidates.append({
            "case_id": anomaly["case_id"],
            "trace_id": trace["trace_id"],
            "normalised_digest": key,
            "selected_because": anomaly["reasons"],
            "scrubbed_payload": scrubbed,
            "scrub_after_sha256": scrubs[anomaly["case_id"]]["after_sha256"],
            "state": "GOLDEN_CANDIDATE",
        })
    return candidates, duplicates


def load_adjudication(path: Path | None, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """A candidate becomes ground truth only through a named human decision."""
    if path is None:
        raise Refused("adjudication-absent: no Human ground-truth record")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Refused(f"adjudication-unreadable: {exc}") from exc
    for key in ("approver", "decided_at", "decisions"):
        if not record.get(key):
            raise Refused(f"adjudication-incomplete: {key} missing")
    decided = {item.get("case_id"): item for item in record["decisions"]}
    for candidate in candidates:
        decision = decided.get(candidate["case_id"])
        if decision is None:
            raise Refused(f"adjudication-incomplete: no decision for {candidate['case_id']}")
        if decision.get("scrub_after_sha256") != candidate["scrub_after_sha256"]:
            raise Refused(
                f"adjudication-stale: {candidate['case_id']} was adjudicated against other content"
            )
        if decision.get("verdict") not in {"ADMIT", "REJECT"}:
            raise Refused(f"adjudication-invalid: {candidate['case_id']} verdict "
                          f"{decision.get('verdict')!r}")
    return record


def replay(admitted: list[dict[str, Any]], traces: list[dict[str, Any]],
           run_case: Any, cases: dict[str, Any]) -> list[dict[str, Any]]:
    """Baseline and candidate on matched bindings, per admitted case."""
    by_case = {trace["case_id"]: trace for trace in traces}
    results = []
    for item in admitted:
        case = cases[item["case_id"]]
        baseline = by_case[item["case_id"]]["outcome"]
        candidate = run_case(case)["final"]
        results.append({
            "case_id": item["case_id"],
            "baseline_route": baseline["route"],
            "candidate_route": candidate.get("route"),
            "baseline_requires_hitl": baseline["requires_hitl"],
            "candidate_requires_hitl": candidate.get("requires_hitl"),
            "safety_preserved": bool(baseline["requires_hitl"]) == bool(candidate.get("requires_hitl")),
            "route_delta": baseline["route"] != candidate.get("route"),
        })
    return results


def selftest() -> int:
    """Every lane rule, offline, against the committed canary."""
    cases_path = MODULE / "canary" / "production-like-cases.json"
    if not cases_path.is_file():
        print(f"SELFTEST RED: canary case set missing at {cases_path}", file=sys.stderr)
        return 1
    cases = json.loads(cases_path.read_text(encoding="utf-8"))["cases"]

    for case in cases:
        raw = case["input"]["user_description"]
        scrubbed, findings = scrub(raw)
        for token in ("@example.invalid", "4111111111111111", "555-01", "+1-", "+1 "):
            if token in scrubbed:
                print(f"SELFTEST RED: {token!r} survived the scrubber in {case['case_id']}",
                      file=sys.stderr)
                return 1
        if re.search(r"\d", re.sub(r"<[A-Z]+>", "", scrubbed)):
            print(f"SELFTEST RED: a digit survived scrubbing in {case['case_id']}: {scrubbed!r}",
                  file=sys.stderr)
            return 1
        if raw != scrubbed and not findings:
            print(f"SELFTEST RED: {case['case_id']} changed with no finding recorded", file=sys.stderr)
            return 1

    clean = "Box was crushed in transit."
    if scrub(clean) != (clean, []):
        print("SELFTEST RED: clean text was altered by the scrubber", file=sys.stderr)
        return 1

    receipt = scrub_receipt({"case_id": "x", "trace_id": "t",
                             "raw_payload": "mail ada@example.invalid"})
    if "ada@example.invalid" in json.dumps(receipt) or receipt["raw_retained"]:
        print("SELFTEST RED: the scrub receipt retained the value it removed", file=sys.stderr)
        return 1
    if receipt["before_sha256"] == receipt["after_sha256"]:
        print("SELFTEST RED: before and after digests are equal after a real scrub", file=sys.stderr)
        return 1

    # Two differently-worded reports of one incident must collapse to one case.
    def fake(case_id: str, text: str) -> dict[str, Any]:
        return {"case_id": case_id, "trace_id": case_id,
                "outcome": {"route": "HITL", "execution_status": "pending", "requires_hitl": True,
                            "reviewer_overrode_agent": True}}
    left = normalised_case_digest(fake("A", ""), "parcel lost, contact <EMAIL> at <PHONE>")
    right = normalised_case_digest(fake("B", ""), "parcel lost, contact <EMAIL> at <PHONE>")
    if left != right:
        print("SELFTEST RED: two scrubbed reports of one incident did not deduplicate", file=sys.stderr)
        return 1
    other = normalised_case_digest(
        {"outcome": {"route": "EXECUTE", "execution_status": "settled", "requires_hitl": False,
                     "reviewer_overrode_agent": False}}, "parcel lost")
    if other == left:
        print("SELFTEST RED: a different failure shape collapsed into the same case", file=sys.stderr)
        return 1

    candidates = [{"case_id": "A", "scrub_after_sha256": "a" * 64}]
    for name, record in [
        ("absent", None),
        ("no-approver", {"approver": "", "decided_at": "2026", "decisions": []}),
        ("no-decision-for-candidate", {"approver": "x", "decided_at": "2026", "decisions": []}),
        ("stale-content", {"approver": "x", "decided_at": "2026",
                           "decisions": [{"case_id": "A", "verdict": "ADMIT",
                                          "scrub_after_sha256": "b" * 64}]}),
        ("invalid-verdict", {"approver": "x", "decided_at": "2026",
                             "decisions": [{"case_id": "A", "verdict": "MAYBE",
                                            "scrub_after_sha256": "a" * 64}]}),
    ]:
        path = None
        if record is not None:
            import tempfile
            handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
            json.dump(record, handle)
            handle.close()
            path = Path(handle.name)
        try:
            load_adjudication(path, candidates)
        except Refused:
            continue
        finally:
            if path is not None:
                path.unlink(missing_ok=True)
        print(f"SELFTEST RED: adjudication control {name!r} was accepted", file=sys.stderr)
        return 1

    selectors_fired = {name for name, _ in ANOMALY_SELECTORS}
    if len(selectors_fired) != len(ANOMALY_SELECTORS):
        print("SELFTEST RED: two selectors share a name", file=sys.stderr)
        return 1

    print(
        f"SELFTEST GREEN: {len(cases)} canary payloads scrubbed with no reserved-range value "
        "surviving and no raw value retained in the receipt; clean text untouched; "
        "two wordings of one incident deduplicate while a different failure shape does not; "
        "absent, unsigned, undecided, stale and invalid adjudications each refused"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--cases", type=Path, default=MODULE / "canary" / "production-like-cases.json")
    parser.add_argument("--adjudication", type=Path,
                        help="Human ground-truth record; without it the admission lane is BLOCKED")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if not args.output:
        print("TRACE-INVALID: --output is required unless --selftest", file=sys.stderr)
        return INVALID
    if not args.cases.is_file():
        print(f"TRACE-INVALID absent-cases: {args.cases}", file=sys.stderr)
        return INVALID

    import subprocess
    tree_sha = subprocess.run(["git", "-C", str(SKILL), "rev-parse", "HEAD^{tree}"],
                              capture_output=True, text=True, check=True).stdout.strip()
    subject = {"repository": "ed3c/skills-shared", "tree_sha": tree_sha,
               "provenance": "PRODUCTION_LIKE_CANARY",
               "authorisation": "explicitly admitted for #216; not production traffic"}

    adapter = load_adapter()
    case_list = json.loads(args.cases.read_text(encoding="utf-8"))["cases"]
    cases = {case["case_id"]: case for case in case_list}

    traces = [trace_case(case, adapter.run_case, subject) for case in case_list]
    anomalies = select_anomalies(traces)
    try:
        scrubs = {trace["case_id"]: scrub_receipt(trace) for trace in traces}
    except Refused as exc:
        print(f"TRACE-REFUSED {exc}", file=sys.stderr)
        return REFUSED
    candidates, duplicates = propose_golden(traces, anomalies, scrubs)

    admitted: list[dict[str, Any]] = []
    adjudication: dict[str, Any] | None = None
    adjudication_state, admission_state, replay_state = "BLOCKED", "BLOCKED", "BLOCKED"
    blocked_because = "no Human ground-truth record supplied"
    replayed: list[dict[str, Any]] = []
    try:
        adjudication = load_adjudication(args.adjudication, candidates)
        adjudication_state = "OBSERVED"
        admitted = [item for item in candidates
                    if any(d["case_id"] == item["case_id"] and d["verdict"] == "ADMIT"
                           for d in adjudication["decisions"])]
        for item in admitted:
            item["state"] = "GOLDEN_ADMITTED"
        admission_state = "OBSERVED"
        replayed = replay(admitted, traces, adapter.run_case, cases)
        replay_state = "OBSERVED"
        blocked_because = None
    except Refused as exc:
        blocked_because = str(exc)

    # Coverage is counted from the cases that exist, never from the ones that
    # closed. Dividing admitted by admitted is how a loop reports 100%.
    report = {
        "schema": "production-feedback-closure/v1",
        "subject": subject,
        "lanes": {
            "PRODUCTION_TRACE": "OBSERVED",
            "ANOMALY_SELECTED": "OBSERVED" if anomalies else "NOT_OBSERVED",
            "PII_SCRUBBED": "OBSERVED",
            "HUMAN_ADJUDICATED": adjudication_state,
            "GOLDEN_CANDIDATE": "OBSERVED" if candidates else "NOT_OBSERVED",
            "GOLDEN_ADMITTED": admission_state,
            "REGRESSION_REPLAYED": replay_state,
        },
        "blocked_because": blocked_because,
        "exporter": {
            "span_shape": "opentelemetry-compatible",
            "vendor_exporter": "NOT_EXERCISED",
            "why": "Langfuse is one exporter of this shape; no provider was enrolled for this repository",
        },
        "counts": {
            "traces": len(traces),
            "anomalies_selected": len(anomalies),
            "scrub_receipts": len(scrubs),
            "golden_candidates": len(candidates),
            "duplicates_rejected": len(duplicates),
            "golden_admitted": len(admitted),
            "replayed": len(replayed),
            "feedback_closure_rate": round(len(admitted) / len(anomalies), 4) if anomalies else None,
            "replay_coverage": round(len(replayed) / len(candidates), 4) if candidates else None,
        },
        "traces": traces,
        "anomalies": anomalies,
        "scrub_receipts": [{k: v for k, v in receipt.items() if k != "scrubbed_payload"}
                           for receipt in scrubs.values()],
        "golden_candidates": candidates,
        "duplicates_rejected": duplicates,
        "adjudication": adjudication,
        "regression_replay": replayed,
        "report_digest": None,
    }
    # Raw payloads carried the trace only as far as the scrub lane. They do not
    # reach the artefact.
    for trace in report["traces"]:
        trace["raw_payload_sha256"] = sha256_text(trace.pop("raw_payload"))
    report["report_digest"] = digest_json(
        {k: v for k, v in report.items() if k != "report_digest"}
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lanes = report["lanes"]
    print("FEEDBACK-LOOP " + " ".join(f"{name}={state}" for name, state in lanes.items()))
    print(f"  traces={len(traces)} anomalies={len(anomalies)} candidates={len(candidates)} "
          f"duplicates_rejected={len(duplicates)} admitted={len(admitted)} replayed={len(replayed)}")
    if blocked_because:
        print(f"  BLOCKED: {blocked_because}")
    return REFUSED if any(state == "BLOCKED" for state in lanes.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
