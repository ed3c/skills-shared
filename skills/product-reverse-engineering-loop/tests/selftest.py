#!/usr/bin/env python3
"""Positive, hollow, mutation and stale-subject controls for the PREL mechanisms.

Each control plants exactly one defect in a disposable copy of `references/`
and requires the checker to refuse it *by its own code*. Requiring the code and
not merely a non-zero exit is the point: a checker that fails everything for
one generic reason is indistinguishable from a working one when you only read
the exit status, and that is the failure this file exists to make impossible.

The positive control runs first and refuses to continue if it is red, so a
mutation is never credited to a suite that was already failing.
"""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"
CHECK = ROOT / "scripts/check_prel_contract.py"
COMPILE = ROOT / "scripts/compile_prel.py"

SIGNALS = "example-product-signal.json"
DOSSIER = "example-dossier.json"
MATRIX = "example-closure-matrix.json"
AUDIT = "example-closure-audit.json"
HANDOFF = "example-handoff.json"
PACKET = "example-prompt-packet.json"
CATALOGUE = "prompt-catalogue.md"


def run(argv: list[str]) -> tuple[int, str]:
    done = subprocess.run(argv, text=True, capture_output=True, check=False)
    return done.returncode, done.stdout + done.stderr


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def positive_control() -> list[str]:
    failures: list[str] = []
    checks = [
        [SIGNALS, None],
        [DOSSIER, SIGNALS],
        [MATRIX, DOSSIER],
        [AUDIT, None],
        [HANDOFF, MATRIX],
        [PACKET, None],
    ]
    for artifact, upstream in checks:
        argv = [
            sys.executable, str(CHECK),
            "--artifact", str(REFERENCES / artifact),
            "--resolve-subjects", str(REFERENCES),
        ]
        if upstream:
            argv += ["--input", str(REFERENCES / upstream)]
        code, output = run(argv)
        if code != 0:
            failures.append(f"positive control red for {artifact}: {output.strip()}")

    code, output = run(
        [sys.executable, str(CHECK), "--catalogue", str(REFERENCES / CATALOGUE)]
    )
    if code != 0:
        failures.append(f"positive control red for the catalogue: {output.strip()}")

    for stage, source, target in (
        ("dossier", SIGNALS, DOSSIER),
        ("closure", DOSSIER, MATRIX),
        ("handoff", MATRIX, HANDOFF),
    ):
        code, output = run([
            sys.executable, str(COMPILE),
            "--stage", stage,
            "--input", str(REFERENCES / source),
            "--out", str(REFERENCES / target),
            "--check",
        ])
        if code != 0:
            failures.append(f"committed {stage} projection is not current: {output.strip()}")
    return failures


class Controls:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.results: dict[str, bool] = {}

    def _copy(self, name: str) -> Path:
        target = self.workspace / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(REFERENCES, target)
        return target

    def refuse(
        self,
        name: str,
        filename: str,
        mutate: Callable[[Any], None],
        code: str,
        *,
        also_mutate: tuple[str, Callable[[Any], None]] | None = None,
        upstream: str | None = None,
    ) -> None:
        root = self._copy(name)
        document = read(root / filename)
        mutate(document)
        write(root / filename, document)
        if also_mutate is not None:
            other, change = also_mutate
            payload = read(root / other)
            change(payload)
            write(root / other, payload)
        argv = [
            sys.executable, str(CHECK),
            "--artifact", str(root / filename),
            "--resolve-subjects", str(root),
        ]
        if upstream:
            argv += ["--input", str(root / upstream)]
        status, output = run(argv)
        self.results[name] = status != 0 and code in output

    def refuse_catalogue(self, name: str, drop: str, code: str) -> None:
        root = self._copy(name)
        path = root / CATALOGUE
        path.write_text(
            path.read_text(encoding="utf-8").replace(drop, "STAGE_REMOVED"),
            encoding="utf-8",
        )
        status, output = run([sys.executable, str(CHECK), "--catalogue", str(path)])
        self.results[name] = status != 0 and code in output

    def refuse_compile(
        self, name: str, stage: str, source: str, target: str,
        mutate: Callable[[Any], None], code: str,
    ) -> None:
        root = self._copy(name)
        document = read(root / target)
        mutate(document)
        write(root / target, document)
        status, output = run([
            sys.executable, str(COMPILE),
            "--stage", stage,
            "--input", str(root / source),
            "--out", str(root / target),
            "--check",
        ])
        self.results[name] = status != 0 and code in output

    def refuse_compile_input(
        self, name: str, stage: str, source: str,
        mutate: Callable[[Any], None], code: str,
    ) -> None:
        root = self._copy(name)
        document = read(root / source)
        mutate(document)
        write(root / source, document)
        status, output = run([
            sys.executable, str(COMPILE),
            "--stage", stage,
            "--input", str(root / source),
        ])
        self.results[name] = status != 0 and code in output


def signal(document: Any, identifier: str) -> dict:
    return next(row for row in document["signals"] if row["id"] == identifier)


def row(document: Any, identifier: str) -> dict:
    return next(item for item in document["rows"] if item["id"] == identifier)


def packet(document: Any, identifier: str) -> dict:
    return next(item for item in document["packets"] if item["id"] == identifier)


def audited(document: Any, identifier: str) -> dict:
    return next(item for item in document["problems"] if item["id"] == identifier)


def rung(document: Any, identifier: str, level: str) -> dict:
    return next(
        item for item in audited(document, identifier)["levels"] if item["level"] == level
    )


def anchor(kind: str, artifact: str, digest: str) -> dict:
    return {
        "kind": kind,
        "locator": "planted control",
        "observed": "a planted anchor whose kind may not close the level it was filed under",
        "exact_subject": {"artifact": artifact, "digest": digest},
    }


def subject_of(document: Any, identifier: str, level: str) -> dict:
    """Reuse an already-correct exact subject so only the kind is the defect."""
    return copy.deepcopy(rung(document, identifier, level)["anchors"][0]["exact_subject"])


def plant(controls: Controls) -> None:
    # --- product signal intake -------------------------------------------
    controls.refuse(
        "source_statement_as_observed_architecture", SIGNALS,
        lambda doc: signal(doc, "SIG-008").__setitem__(
            "observation",
            {
                "method": "read the vendor page and treated it as a system trace",
                "artifact_ref": "VENDOR-PAGE-A",
                "repeatable": True,
            },
        ),
        "SOURCE_STATEMENT_AS_OBSERVED_ARCHITECTURE",
    )
    controls.refuse(
        "market_attention_as_demand", SIGNALS,
        lambda doc: signal(doc, "SIG-013").__setitem__("slot", "PAIN"),
        "MARKET_ATTENTION_AS_DEMAND",
    )
    controls.refuse(
        "mechanism_without_oracle_at_intake", SIGNALS,
        lambda doc: signal(doc, "SIG-006").__setitem__("oracle", None),
        "MECHANISM_WITHOUT_OBSERVABLE_ORACLE",
    )
    controls.refuse(
        "hollow_signal_evidence", SIGNALS,
        lambda doc: signal(doc, "SIG-002").__setitem__("source_ref", "TBD"),
        "HOLLOW_EVIDENCE",
    )
    controls.refuse(
        "observed_kind_without_observation", SIGNALS,
        lambda doc: signal(doc, "SIG-002").__setitem__("observation", None),
        "HOLLOW_EVIDENCE",
    )
    controls.refuse(
        "compatibility_field_unknown", SIGNALS,
        lambda doc: doc["compatibility"]["consumed_fields"].append("confidence"),
        "COMPATIBILITY_FIELD_UNKNOWN",
    )
    controls.refuse(
        "signal_dependency_unbound", SIGNALS,
        lambda doc: signal(doc, "SIG-011").__setitem__("depends_on", ["SIG-901"]),
        "SIGNAL_DEPENDENCY_UNBOUND",
    )

    # --- dossier ----------------------------------------------------------
    def blank_job(doc: Any) -> None:
        doc["job"] = {"grade": "ABSENT", "statement": "", "signal_ids": []}

    controls.refuse(
        "feature_clone_without_job_hypothesis", DOSSIER, blank_job,
        "FEATURE_CLONE_WITHOUT_JOB_HYPOTHESIS",
    )
    controls.refuse(
        "observable_mechanism_without_oracle", DOSSIER,
        lambda doc: doc["mechanism_hypotheses"][0].__setitem__("oracle_id", None),
        "MECHANISM_WITHOUT_OBSERVABLE_ORACLE",
    )
    controls.refuse(
        "vendor_claim_graded_as_observed", DOSSIER,
        lambda doc: next(
            row for row in doc["mechanism_hypotheses"]
            if row["classification"] == "VENDOR_CLAIMED_MECHANISM"
        ).__setitem__("grade", "OBSERVED"),
        "SOURCE_STATEMENT_AS_OBSERVED_ARCHITECTURE",
    )
    controls.refuse(
        "graded_slot_citing_no_signal", DOSSIER,
        lambda doc: doc["pain"].__setitem__("signal_ids", []),
        "UNGRADED_SLOT",
    )
    controls.refuse(
        "dossier_ceiling_overclaim", DOSSIER,
        lambda doc: doc["evidence_ceiling"].__setitem__("product_market_fit", "PASS"),
        "CEILING_OVERCLAIM",
    )
    controls.refuse(
        "capability_edge_unbound", DOSSIER,
        lambda doc: doc["capability_graph"]["edges"][0].__setitem__("from", "CAP-901"),
        "CAPABILITY_EDGE_UNBOUND",
    )
    controls.refuse(
        "usage_right_self_admitted", DOSSIER,
        lambda doc: doc["rights"][0].__setitem__("state", "PASS"),
        "CEILING_OVERCLAIM",
    )

    # --- closure matrix ---------------------------------------------------
    def close_user_lane_with_technical_oracle(doc: Any) -> None:
        target = next(item for item in doc["rows"] if item["lane"] == "USER")
        target.update(
            {
                "oracle_id": "ORC-001",
                "oracle_lane": "DETERMINISTIC",
                "closure_state": "CLOSED_BY_ORACLE",
                "evidence_state": "PASS",
            }
        )

    controls.refuse(
        "technical_pass_as_user_validation", MATRIX,
        close_user_lane_with_technical_oracle,
        "TECHNICAL_PASS_AS_USER_VALIDATION",
    )
    controls.refuse(
        "closure_claimed_without_oracle", MATRIX,
        lambda doc: next(
            item for item in doc["rows"] if item["oracle_id"] is None
        ).__setitem__("closure_state", "OPEN_WITH_ORACLE"),
        "CLOSURE_STATE_UNSUPPORTED",
    )
    controls.refuse(
        "blocked_row_marked_pass", MATRIX,
        lambda doc: next(
            item for item in doc["rows"]
            if item["closure_state"] == "BLOCKED_NO_ORACLE"
        ).__setitem__("evidence_state", "PASS"),
        "CLOSURE_STATE_UNSUPPORTED",
    )
    controls.refuse(
        "matrix_ceiling_overclaim", MATRIX,
        lambda doc: doc["evidence_ceiling"].__setitem__("live_provider_execution", "PASS"),
        "CEILING_OVERCLAIM",
    )

    # --- product closure audit -------------------------------------------
    def planted_anchor(doc: Any, kind: str) -> dict:
        subject = subject_of(doc, "PRB-001", "SOURCE_ANCHORED")
        return anchor(kind, subject["artifact"], subject["digest"])

    def green_ci_as_live_closure(doc: Any) -> None:
        target = rung(doc, "PRB-001", "LIVE_WORKFLOW_VERIFIED")
        target["state"] = "PASS"
        target["anchors"] = [planted_anchor(doc, "CI_RUN")]

    controls.refuse(
        "green_ci_as_live_closure", AUDIT, green_ci_as_live_closure,
        "EVIDENCE_LANE_PROMOTION",
    )

    def model_judgment_as_user_evidence(doc: Any) -> None:
        target = rung(doc, "PRB-002", "USER_VALIDATED")
        target["state"] = "PASS"
        target["anchors"] = [planted_anchor(doc, "MODEL_JUDGMENT")]

    controls.refuse(
        "model_judgment_as_user_evidence", AUDIT, model_judgment_as_user_evidence,
        "MODEL_JUDGE_OVERRIDE",
    )
    controls.refuse(
        "audit_level_set_drift", AUDIT,
        lambda doc: audited(doc, "PRB-001")["levels"].pop(4),
        "AUDIT_LEVEL_SET_DRIFT",
    )
    controls.refuse(
        "closure_level_ladder_skip", AUDIT,
        lambda doc: audited(doc, "PRB-002").__setitem__(
            "highest_earned_level", "TECH_VERIFIED"
        ),
        "LEVEL_LADDER_SKIP",
    )
    controls.refuse(
        "missing_lane_undeclared", AUDIT,
        lambda doc: audited(doc, "PRB-001")["missing_lanes"].remove("USER"),
        "MISSING_LANE_UNDECLARED",
    )
    controls.refuse(
        "contradictory_closure_status", AUDIT,
        lambda doc: audited(doc, "PRB-002")["findings"][0].__setitem__(
            "code", "EVIDENCE_ABSENT"
        ),
        "CONTRADICTORY_CLOSURE_STATUS",
    )
    controls.refuse(
        "unanchored_finding", AUDIT,
        lambda doc: audited(doc, "PRB-001")["findings"][0].__setitem__("anchors", []),
        "UNANCHORED_FINDING",
    )
    controls.refuse(
        "shadow_writes_implementation", AUDIT,
        lambda doc: doc["reviewer"].__setitem__("writes_implementation", True),
        "SHADOW_WRITE_AUTHORITY",
    )
    controls.refuse(
        "issue_delta_claims_write_authority", AUDIT,
        lambda doc: doc["issue_delta"][0].__setitem__("write_authority", "BUILDER_WRITE"),
        "SHADOW_WRITE_AUTHORITY",
    )
    controls.refuse(
        "first_green_obligation_skipped", AUDIT,
        lambda doc: doc.__setitem__("reopened_obligations", []),
        "FIRST_GREEN_OBLIGATION_SKIPPED",
    )
    controls.refuse(
        "reopened_obligation_on_closed_rung", AUDIT,
        lambda doc: doc["reopened_obligations"].append(
            {
                "problem_id": "PRB-001",
                "level": "SOURCE_ANCHORED",
                "state": "NOT_EXERCISED",
                "reason": "a closed rung listed as reopened work, which hides which lane is open",
            }
        ),
        "FIRST_GREEN_OBLIGATION_SKIPPED",
    )
    controls.refuse(
        "dissent_omitted_from_denominator", AUDIT,
        lambda doc: doc["review_denominator"].__setitem__("findings_withdrawn", []),
        "DISSENT_OMITTED_FROM_DENOMINATOR",
    )
    controls.refuse(
        "private_reasoning_in_public_snapshot", AUDIT,
        lambda doc: doc["public_snapshot"]["excluded_from_snapshot"].append(
            "the reviewer keeps the private reasoning that produced each verdict"
        ),
        "PRIVATE_REASONING_IN_PUBLIC_SNAPSHOT",
    )
    controls.refuse(
        "snapshot_requires_prior_conversation", AUDIT,
        lambda doc: audited(doc, "PRB-001")["findings"][0].__setitem__(
            "proposed_repair", "apply the repair agreed in the earlier message"
        ),
        "SNAPSHOT_REQUIRES_PRIOR_CONVERSATION",
    )
    controls.refuse(
        "merge_authority_assumed", AUDIT,
        lambda doc: doc["external_authority"].__setitem__("merge", "SHADOW_REVIEWER"),
        "MERGE_OR_RELEASE_AUTHORITY_ASSUMED",
    )
    controls.refuse(
        "audit_ceiling_overclaim", AUDIT,
        lambda doc: doc["evidence_ceiling"].__setitem__("live_provider_execution", "PASS"),
        "CEILING_OVERCLAIM",
    )
    controls.refuse(
        "stale_audit_anchor", AUDIT,
        lambda doc: None,
        "STALE_SUBJECT",
        also_mutate=(
            DOSSIER,
            lambda doc: doc["mvp"]["excluded"].append("a requirement the audit never saw"),
        ),
    )

    # --- executable handoff ----------------------------------------------
    controls.refuse(
        "false_serialization_of_independent_leaves", HANDOFF,
        lambda doc: packet(doc, "PKT-002").__setitem__(
            "depends_on",
            [{"packet_id": "PKT-001", "consumes": ["prel/CLR-909/output.json"]}],
        ),
        "FALSE_SERIALIZATION_OF_INDEPENDENT_LEAVES",
    )
    controls.refuse(
        "overlapping_writer_lease", HANDOFF,
        lambda doc: packet(doc, "PKT-002").__setitem__("paths_lease", ["prel/CLR-001/"]),
        "HIDDEN_CONVERGENCE_OR_OVERLAPPING_LEASE",
    )
    controls.refuse(
        "convergence_owner_without_convergence", HANDOFF,
        lambda doc: packet(doc, "PKT-001").__setitem__("convergence_owner", "PKT-001"),
        "HIDDEN_CONVERGENCE_OR_OVERLAPPING_LEASE",
    )
    def make_cycle(doc: Any) -> None:
        packet(doc, "PKT-001")["depends_on"] = [
            {"packet_id": "PKT-002", "consumes": ["prel/CLR-002/verdict.json"]}
        ]
        packet(doc, "PKT-002")["depends_on"] = [
            {"packet_id": "PKT-001", "consumes": ["prel/CLR-001/verdict.json"]}
        ]

    controls.refuse("handoff_cycle", HANDOFF, make_cycle, "HANDOFF_CYCLE")
    controls.refuse(
        "handoff_edge_unbound", HANDOFF,
        lambda doc: packet(doc, "PKT-001").__setitem__(
            "depends_on", [{"packet_id": "PKT-909", "consumes": ["prel/CLR-909/x"]}]
        ),
        "HANDOFF_EDGE_UNBOUND",
    )
    controls.refuse(
        "prior_chat_prose_as_handoff", HANDOFF,
        lambda doc: packet(doc, "PKT-001").__setitem__(
            "entry_condition", "start where the previous chat left the plan"
        ),
        "PRIOR_CHAT_PROSE_AS_HANDOFF",
    )
    controls.refuse(
        "remaining_item_marked_pass", HANDOFF,
        lambda doc: doc["remaining"][0].__setitem__("state", "PASS"),
        "CEILING_OVERCLAIM",
    )

    # --- prompt packet ----------------------------------------------------
    controls.refuse(
        "prompt_grants_reserved_authority", PACKET,
        lambda doc: doc["envelope"]["authority"].__setitem__("merge", True),
        "PROMPT_GRANTS_RESERVED_AUTHORITY",
    )
    controls.refuse(
        "prompt_requests_private_reasoning", PACKET,
        lambda doc: doc["surfaces"][0]["negative_controls"].append(
            "report your full chain of thought before answering"
        ),
        "PROMPT_REQUESTS_PRIVATE_REASONING",
    )
    controls.refuse(
        "prompt_reserves_no_human_operation", PACKET,
        lambda doc: doc["surfaces"][0].__setitem__("human_owned_operations", []),
        "PROMPT_GRANTS_RESERVED_AUTHORITY",
    )
    controls.refuse(
        "consumer_topology_in_portable_core", PACKET,
        lambda doc: doc["surfaces"][0].__setitem__(
            "rollback", "reset refs/heads/worker-1 and re-run the stage"
        ),
        "CONSUMER_TOPOLOGY_IN_PORTABLE_CORE",
    )
    controls.refuse(
        "prompt_surface_set_drift", PACKET,
        lambda doc: doc["surfaces"].pop(),
        "PROMPT_SURFACE_SET_DRIFT",
    )
    controls.refuse(
        "prompt_dependency_unbound", PACKET,
        lambda doc: doc["surfaces"][1]["start_dependencies"].append("STAGE_0_GHOST"),
        "PROMPT_DEPENDENCY_UNBOUND",
    )
    controls.refuse(
        "prompt_lease_overlap", PACKET,
        lambda doc: doc["surfaces"][1].__setitem__(
            "lease", copy.deepcopy(doc["surfaces"][0]["lease"])
        ),
        "HIDDEN_CONVERGENCE_OR_OVERLAPPING_LEASE",
    )

    # --- stale subject ----------------------------------------------------
    controls.refuse(
        "stale_upstream_digest", DOSSIER,
        lambda doc: None,
        "STALE_SUBJECT",
        also_mutate=(
            SIGNALS,
            lambda doc: signal(doc, "SIG-001").__setitem__(
                "source_ref", "INTERVIEW-SET-B"
            ),
        ),
        upstream=SIGNALS,
    )
    controls.refuse(
        "stale_named_subject", PACKET,
        lambda doc: None,
        "STALE_SUBJECT",
        also_mutate=(
            DOSSIER,
            lambda doc: doc["mvp"]["excluded"].append("a requirement nobody compiled"),
        ),
    )
    controls.refuse(
        "vanished_named_subject", PACKET,
        lambda doc: doc["surfaces"][0]["exact_subject"].__setitem__(
            "artifact", "example-signals-that-were-deleted.json"
        ),
        "STALE_SUBJECT",
    )

    # --- catalogue and compiler ------------------------------------------
    controls.refuse_catalogue(
        "catalogue_surface_drift", "STAGE_6_SHADOW_MONITOR", "PROMPT_SURFACE_SET_DRIFT"
    )
    controls.refuse_compile(
        "hand_edited_projection", "closure", DOSSIER, MATRIX,
        lambda doc: doc["rows"][0].__setitem__("closure_state", "CLOSED_BY_ORACLE"),
        "PREL-COMPILE-RED",
    )

    def strip_scope(doc: Any) -> None:
        keep = {"SIG-001", "SIG-002", "SIG-008", "SIG-009", "SIG-012", "SIG-013"}
        doc["signals"] = [row for row in doc["signals"] if row["id"] in keep]

    controls.refuse_compile_input(
        "compiler_refuses_empty_mvp", "dossier", SIGNALS, strip_scope,
        "PREL-COMPILE-RED",
    )


def main() -> int:
    failures = positive_control()
    if failures:
        for failure in failures:
            print(f"PREL-SELFTEST-RED {failure}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="prel-selftest-") as workspace:
        controls = Controls(Path(workspace))
        plant(controls)

    survived = sorted(name for name, refused in controls.results.items() if not refused)
    if survived:
        for name in survived:
            print(f"PREL-SELFTEST-RED planted defect survived: {name}", file=sys.stderr)
        return 2

    # The inventory in cases.json is only worth reading if it cannot drift from
    # what actually ran. A control added here and never registered there, or a
    # registered control that quietly stopped running, are both defects.
    declared = set(read(ROOT / "cases.json")["planted_controls"])
    executed = set(controls.results)
    if declared != executed:
        for name in sorted(declared - executed):
            print(f"PREL-SELFTEST-RED cases.json declares an unrun control: {name}", file=sys.stderr)
        for name in sorted(executed - declared):
            print(f"PREL-SELFTEST-RED control is unregistered in cases.json: {name}", file=sys.stderr)
        return 2
    print(
        f"PREL-SELFTEST-GREEN positive control clean, "
        f"{len(controls.results)} planted defects refused by their own code"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
