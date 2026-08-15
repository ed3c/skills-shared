#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json, os, subprocess, sys, zipfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "evals" / "contract.json"


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


# Receipts are digested and compared against a committed expectation, so anything
# host-specific reaching the digest makes the eval unreproducible off the machine
# that generated the expectation. sys.executable is an absolute versioned path, so
# it is reduced to the interpreter name at the one boundary every probe crosses.
def portable_argv(argv: list[str]) -> list[str]:
    return ["python3", *argv[1:]]


# Tool prose is not a stable observation: unittest's elapsed time changes per run
# and its test-id format changes per interpreter version. The semantic fields
# (exit_code, skip_observed, executed_checks, ...) carry the finding, so the digest
# is taken over those and the raw prose stays in the receipt for diagnosis.
DIGEST_VOLATILE = ("stdout", "stderr")


def digest_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: digest_payload(v) for k, v in value.items() if k not in DIGEST_VOLATILE}
    if isinstance(value, list):
        return [digest_payload(v) for v in value]
    return value


def run(code: str, cwd: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    p = subprocess.run(
        [sys.executable, "-c", code], cwd=cwd, env=env,
        capture_output=True, text=True, check=False, timeout=20,
    )
    return {"argv": portable_argv([sys.executable, "-c", code]), "exit_code": p.returncode,
            "stdout": p.stdout, "stderr": p.stderr}


def observations(out: Path) -> dict[str, dict[str, Any]]:
    rt = out / "runtime"; rt.mkdir(parents=True)
    obs: dict[str, dict[str, Any]] = {}
    probe = lambda d, c="print('probe')", e=None: run(c, d, e)

    d = rt / "subject-drift"; d.mkdir()
    obs["subject-drift"] = {"probe": probe(d), "expected_subject": digest("expected"),
                            "observed_subject": digest("other")}
    d = rt / "evidence-level-overclaim"; d.mkdir()
    obs["evidence-level-overclaim"] = {"probe": probe(d), "required_level": 6, "observed_level": 3}

    d = rt / "silent-skip"; d.mkdir()
    (d / "test_optional.py").write_text(
        "import unittest\nclass T(unittest.TestCase):\n @unittest.skip('absent')\n def test_x(self): self.fail()\n",
        encoding="utf-8")
    p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", ".", "-v"],
                       cwd=d, capture_output=True, text=True, check=False)
    obs["silent-skip"] = {"probe": {"argv": portable_argv(list(p.args)), "exit_code": p.returncode,
                           "stdout": p.stdout, "stderr": p.stderr},
                           "skip_observed": "skipped" in (p.stdout + p.stderr).lower(),
                           "required_checks": 1, "executed_checks": 0}

    d = rt / "runtime-alias"; d.mkdir()
    obs["runtime-alias"] = {"probe": probe(d), "claimed_runtime": "specialized-substrate",
                            "observed_runtime": "generic-host-process"}
    d = rt / "denial-without-positive-control"; d.mkdir()
    obs["denial-without-positive-control"] = {
        "positive": {"attempted": False, "exit_code": None},
        "negative": {"attempted": True, **run("raise SystemExit(13)", d), "expected_exit": 13}}
    d = rt / "failure-evidence-loss"; d.mkdir()
    p = run("import json; print(json.dumps({'action':'Denied'})); raise SystemExit(17)", d)
    obs["failure-evidence-loss"] = {"probe": p, "raw_negative": {"action": "Denied"},
                                     "positive_artifact_present": False, "normalized_negative": []}

    d = rt / "hidden-artifact-omission"; packet = d / "packet"; (packet / ".runtime").mkdir(parents=True)
    (packet / "summary.txt").write_text("visible\n"); (packet / ".runtime" / "receipt.json").write_text('{"ok":true}\n')
    expected = sorted(str(p.relative_to(packet)) for p in packet.rglob("*") if p.is_file())
    archive = d / "packet.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(packet.rglob("*")):
            rel = p.relative_to(packet)
            if p.is_file() and not any(x.startswith(".") for x in rel.parts):
                info = zipfile.ZipInfo(str(rel), (2026, 1, 1, 0, 0, 0)); info.external_attr = 0o100644 << 16
                z.writestr(info, p.read_bytes())
    with zipfile.ZipFile(archive) as z: delivered = sorted(x for x in z.namelist() if not x.endswith("/"))
    obs["hidden-artifact-omission"] = {"probe": probe(d), "expected_files": expected,
                                       "delivered_files": delivered, "complete": expected == delivered,
                                       "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}
    d = rt / "mutable-external-ref"; d.mkdir()
    obs["mutable-external-ref"] = {"probe": probe(d), "requested_ref": "main",
                                    "resolved_identity": None, "immutable": False}
    d = rt / "ambient-secret-leak"; d.mkdir(); env = dict(os.environ); env["RCA_FIXTURE_SECRET"] = "fixture-secret"
    p = run("import os; print(os.getenv('RCA_FIXTURE_SECRET',''))", d, env)
    obs["ambient-secret-leak"] = {"probe": p, "secret_marker": "fixture-secret",
                                   "leaked": "fixture-secret" in p["stdout"]}
    d = rt / "zero-access-gap"; d.mkdir()
    obs["zero-access-gap"] = {"probe": probe(d), "packet_fields": ["artifact", "verdict"],
                               "required_fields": ["original_intent", "exact_subject", "claimed_completion",
                                                   "scope_boundary", "command", "runtime_identity",
                                                   "raw_evidence", "verdict", "non_claims"]}
    d = rt / "first-green-coverage-gap"; d.mkdir()
    obs["first-green-coverage-gap"] = {"probe": run("print('1 passed')", d),
                                        "material_claims": ["a", "b"], "executed_claims": ["a"],
                                        "uncovered_claims": ["b"]}
    d = rt / "stronger-claim-leak"; d.mkdir()
    obs["stronger-claim-leak"] = {"probe": probe(d), "established_claims": ["fixture"],
                                   "reported_claims": ["fixture", "production"],
                                   "unresolved_rows_visible": False}
    d = rt / "text-only-non-trigger"; d.mkdir()
    obs["text-only-non-trigger"] = {"probe": probe(d), "request_class": "text-only-correction",
                                     "material_capability_question": False}
    d = rt / "obvious-runtime-failure"; d.mkdir()
    obs["obvious-runtime-failure"] = {"probe": run("raise SystemExit(2)", d)}
    d = rt / "healthy-bounded-run"; d.mkdir()
    obs["healthy-bounded-run"] = {"probe": run("print('ok')", d), "subject_matches": True,
                                   "evidence_complete": True, "claims_bounded": True}

    for case_id, value in obs.items():
        value["observation_digest"] = digest(digest_payload(value))
        write_json(out / "observations" / f"{case_id}.json", value)
    return obs


def detects(rule: str, o: dict[str, Any]) -> bool:
    checks: dict[str, Callable[[dict[str, Any]], bool]] = {
        "RCA-001": lambda x: x["expected_subject"] != x["observed_subject"],
        "RCA-002": lambda x: x["observed_level"] < x["required_level"],
        "RCA-003": lambda x: x["skip_observed"] and x["executed_checks"] < x["required_checks"],
        "RCA-004": lambda x: x["claimed_runtime"] != x["observed_runtime"],
        "RCA-005": lambda x: not (x["positive"]["attempted"] and x["positive"]["exit_code"] == 0 and
                                   x["negative"]["attempted"] and x["negative"]["exit_code"] == x["negative"]["expected_exit"]),
        "RCA-006": lambda x: x["raw_negative"]["action"] == "Denied" and not x["normalized_negative"],
        "RCA-007": lambda x: not x["complete"],
        "RCA-008": lambda x: not x["immutable"] or x["resolved_identity"] is None,
        "RCA-009": lambda x: x["leaked"],
        "RCA-010": lambda x: not set(x["required_fields"]).issubset(x["packet_fields"]),
        "RCA-011": lambda x: bool(x["uncovered_claims"]),
        "RCA-012": lambda x: not set(x["reported_claims"]).issubset(x["established_claims"]),
        "RCA-013": lambda x: not x["material_capability_question"],
    }
    return checks[rule](o)


def profile(name: str, rules: set[str], cases: list[dict[str, Any]], obs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    correct = detected = false_pass = evidence = defects = tp = fp = healthy = 0
    outcomes = []
    for case in cases:
        cid, kind, rule = case["id"], case["kind"], case["required_rule"]
        trigger = True; found = False
        if kind == "non_trigger":
            trigger = not (rule in rules and detects(rule, obs[cid])); ok = not trigger; fp += int(trigger)
        elif kind == "defect":
            defects += 1; found = obs[cid]["probe"]["exit_code"] != 0 if rule is None else rule in rules and detects(rule, obs[cid])
            ok = found; detected += int(found); false_pass += int(not found); evidence += int(found); tp += 1
        else:
            ok = obs[cid]["probe"]["exit_code"] == 0 and obs[cid]["evidence_complete"] and obs[cid]["claims_bounded"]
            healthy += int(ok); tp += 1
        correct += int(ok); outcomes.append({"case_id": cid, "correct": ok, "triggered": trigger, "detected": found})
    precision = tp / (tp + fp) if tp + fp else 1.0
    metrics = {"correct_cases": correct, "total_cases": len(cases), "accuracy": round(correct / len(cases), 6),
               "defect_recall": round(detected / defects, 6), "false_pass_count": false_pass,
               "evidence_completeness": round(evidence / defects, 6), "trigger_precision": round(precision, 6),
               "healthy_true_pass": healthy}
    metrics["score"] = round((metrics["accuracy"] + metrics["defect_recall"] +
                               metrics["evidence_completeness"] + metrics["trigger_precision"]) / 4, 6)
    return {"name": name, "metrics": metrics, "outcome_digest": digest(outcomes)}


def source_counts(contract: dict[str, Any], supported: set[str]) -> dict[str, Any]:
    result = {}
    dep_supported = dep_total = 0
    for source, claims in contract["source_claims"].items():
        count = sum(c in supported for c in claims); total = len(claims)
        result[source] = {"supported": count, "total": total, "supported_fraction": round(count / total, 6)}
        if source != "current-system-prompt": dep_supported += count; dep_total += total
    result["dependency_aggregate"] = {"supported": dep_supported, "total": dep_total,
                                      "supported_fraction": round(dep_supported / dep_total, 6)}
    return result


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--output", type=Path, required=True); args = ap.parse_args()
    out = args.output.resolve()
    if out.exists():
        for p in sorted(out.rglob("*"), reverse=True): p.unlink() if p.is_file() or p.is_symlink() else p.rmdir()
    out.mkdir(parents=True, exist_ok=True)
    contract = json.loads(CONTRACT.read_text()); cases = contract["cases"]
    retained = {x["id"] for x in contract["retained"]}; obs = observations(out)
    base = profile("candidate_trimmed_skill", retained, cases, obs)
    profiles = {"no_skill": profile("no_skill", set(), cases, obs),
                "current_full_composition": profile("current_full_composition", retained, cases, obs),
                "candidate_trimmed_skill": base}
    ablations = {}; supported = set()
    for rule in sorted(retained):
        p = profile(f"candidate_minus_{rule}", retained - {rule}, cases, obs)
        delta = round(p["metrics"]["score"] - base["metrics"]["score"], 6)
        affected = [c["id"] for c in cases if c["required_rule"] == rule and not next(x for x in p_outcomes(p, cases, obs, retained - {rule}) if x["case_id"] == c["id"])["correct"]]
        effective = delta < 0 and bool(affected)
        supported.update([rule] if effective else [])
        ablations[rule] = {"effective": effective, "score_delta": delta, "affected_cases": affected}
    unproven = contract["unproven_for_core"]
    report = {"schema": "repository-capability-audit-effectiveness/v1",
              "evidence_class": "deterministic-procedure-ablation", "profiles": profiles,
              "retained_rules": sorted(retained), "runtime_supported_rules": sorted(supported),
              "core_supported_fraction": round(len(supported) / len(retained), 6), "ablations": ablations,
              "source_effectiveness": source_counts(contract, supported),
              "full_unique_procedure_count": len(retained) + len(unproven),
              "trimmed_unique_procedure_count": len(retained),
              "procedure_reduction_fraction": round(len(unproven) / (len(retained) + len(unproven)), 6),
              "observation_receipt_digest": digest({k: v["observation_digest"] for k, v in sorted(obs.items())}),
              "observed_external_trace_digest": digest(contract["observed_external_trace"]),
              "limitations": ["Committed deterministic fixtures prove necessity only for these cases.",
                              "One external trace covers one repository and one composed-agent run.",
                              "This suite does not measure whether a model recalls or follows skill text.",
                              "Cross-model and cross-repository uplift needs repeated held-out physical runs."]}
    write_json(out / "effectiveness.json", report); print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if supported == retained and base["metrics"]["score"] == 1.0 else 2


def p_outcomes(_p: dict[str, Any], cases: list[dict[str, Any]], obs: dict[str, dict[str, Any]], rules: set[str]) -> list[dict[str, Any]]:
    # Recompute only the booleans needed by the ablation ledger; profile output stays compact.
    out = []
    for c in cases:
        if c["kind"] == "non_trigger": ok = c["required_rule"] in rules and detects(c["required_rule"], obs[c["id"]])
        elif c["kind"] == "defect": ok = obs[c["id"]]["probe"]["exit_code"] != 0 if c["required_rule"] is None else c["required_rule"] in rules and detects(c["required_rule"], obs[c["id"]])
        else: ok = obs[c["id"]]["probe"]["exit_code"] == 0 and obs[c["id"]]["evidence_complete"] and obs[c["id"]]["claims_bounded"]
        out.append({"case_id": c["id"], "correct": ok})
    return out


if __name__ == "__main__": raise SystemExit(main())
