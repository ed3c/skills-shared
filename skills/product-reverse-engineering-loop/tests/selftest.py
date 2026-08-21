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
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "references"
EXAMPLES = ROOT / "examples"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CHECK = ROOT / "scripts/check_prel_contract.py"
COMPILE = ROOT / "scripts/compile_prel.py"
COMPILE_SESSION = ROOT / "scripts/compile_session_dispatch.py"
COMPILE_PROJECTION = ROOT / "scripts/compile_external_projection.py"

SIGNALS = "example-product-signal.json"
DOSSIER = "example-dossier.json"
MATRIX = "example-closure-matrix.json"
AUDIT = "example-closure-audit.json"
HANDOFF = "example-handoff.json"
PACKET = "example-prompt-packet.json"
CATALOGUE = "prompt-catalogue.md"

DISPATCH = "session-dispatch-request.example.json"
RECEIPT = "session-receipt.example.json"
REGISTRY = "external-projection-registry.example.json"

DISPATCH_DRAFT = "session-dispatch-input.json"
DISPATCH_COMPILED = "session-dispatch-request.compiled.json"
REGISTRY_DRAFT = "external-projection-input.json"
REGISTRY_COMPILED = "external-projection-registry.compiled.json"

# Every directory that may hold a committed artifact. Discovery reads these; no
# list of filenames exists anywhere in this suite, so an artifact added to the
# tree enters the denominator without an edit here, and one that is deleted
# takes its schema's coverage with it.
ARTIFACT_ROOTS = (REFERENCES, EXAMPLES, FIXTURES)

# Compiler-input schemas. These are staging documents, not contracts: they are
# consumed by a compiler and never validated against a frozen schema, so
# discovery records them as drafts rather than reporting them as unregistered.
DRAFT_SCHEMAS = {
    "prel/session-dispatch-input/v1",
    "prel/external-projection-input/v1",
}

# The artifact each projection was compiled from, for the stale-subject control.
UPSTREAM = {DOSSIER: SIGNALS, MATRIX: DOSSIER, HANDOFF: MATRIX}

# (compiler, draft, committed projection). Byte-stability is asserted on every
# entry, so a compiler whose output drifts from what is committed is red before
# any mutation runs.
PROJECTIONS = (
    (COMPILE, ["--stage", "dossier"], REFERENCES / SIGNALS, REFERENCES / DOSSIER),
    (COMPILE, ["--stage", "closure"], REFERENCES / DOSSIER, REFERENCES / MATRIX),
    (COMPILE, ["--stage", "handoff"], REFERENCES / MATRIX, REFERENCES / HANDOFF),
    (COMPILE_SESSION, [], FIXTURES / DISPATCH_DRAFT, FIXTURES / DISPATCH_COMPILED),
    (COMPILE_PROJECTION, [], FIXTURES / REGISTRY_DRAFT, FIXTURES / REGISTRY_COMPILED),
)


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


def registered_schemas() -> dict[str, str]:
    """The checker's own schema registry, read from the checker.

    Copying the list into this file would let the two drift apart in the one
    direction that matters: a schema registered in production and exercised by
    nothing here would still look covered. There is one registry and this reads
    it.
    """
    spec = importlib.util.spec_from_file_location("prel_checker", CHECK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(module.SCHEMA_FILES)


def discover() -> tuple[list[tuple[Path, Path, str]], list[str]]:
    """Every committed artifact in the tree, as (root, path, schema id).

    Nothing is enumerated by name. A JSON file carrying a top-level `schema`
    string is an artifact and is validated; one carrying a compiler-input schema
    is a draft; one carrying anything else is reported rather than skipped,
    because a file the suite silently ignores is exactly how an unregistered
    schema arrives with no coverage.
    """
    found: list[tuple[Path, Path, str]] = []
    problems: list[str] = []
    known = set(registered_schemas())
    for root in ARTIFACT_ROOTS:
        if not root.is_dir():
            problems.append(f"artifact root {root} does not exist")
            continue
        for path in sorted(root.glob("*.json")):
            try:
                document = read(path)
            except json.JSONDecodeError as error:
                problems.append(f"{path.name} is not readable JSON: {error}")
                continue
            identity = document.get("schema") if isinstance(document, dict) else None
            if identity is None:
                continue  # a schema file or other non-artifact document
            if not isinstance(identity, str):
                problems.append(f"{path.name} carries a non-string schema {identity!r}")
                continue
            if identity in DRAFT_SCHEMAS:
                continue
            if identity not in known:
                problems.append(
                    f"{path.name} declares schema {identity!r}, which "
                    f"check_prel_contract.py does not register; an artifact whose "
                    f"schema is unknown to the checker is validated by nothing"
                )
                continue
            found.append((root, path, identity))
    return found, problems


def positive_control() -> tuple[list[str], dict[str, int]]:
    """Validate every discovered artifact and reconcile it against the registry."""
    failures: list[str] = []
    registered = registered_schemas()
    artifacts, failures_from_discovery = discover()
    failures.extend(failures_from_discovery)

    for root, path, _identity in artifacts:
        argv = [
            sys.executable, str(CHECK),
            "--artifact", str(path),
            "--resolve-subjects", str(root),
        ]
        upstream = UPSTREAM.get(path.name)
        if upstream:
            argv += ["--input", str(root / upstream)]
        code, output = run(argv)
        if code != 0:
            failures.append(f"positive control red for {path.name}: {output.strip()}")

    # Both directions. A registered schema nothing exercises is the failure the
    # #371 audit found by hand: three schemas landed, CI reached none of them,
    # and the suite stayed green because it enumerated six filenames.
    exercised = {identity for _root, _path, identity in artifacts}
    for identity in sorted(set(registered) - exercised):
        failures.append(
            f"registered schema {identity} has no committed artifact in "
            f"{[root.name for root in ARTIFACT_ROOTS]}, so no test exercises it"
        )

    code, output = run(
        [sys.executable, str(CHECK), "--catalogue", str(REFERENCES / CATALOGUE)]
    )
    if code != 0:
        failures.append(f"positive control red for the catalogue: {output.strip()}")

    for compiler, stage, source, target in PROJECTIONS:
        code, output = run([
            sys.executable, str(compiler), *stage,
            "--input", str(source),
            "--out", str(target),
            "--check",
        ])
        if code != 0:
            failures.append(
                f"committed projection {target.name} is not what {source.name} "
                f"compiles to: {output.strip()}"
            )

    counts = {
        "schemas": len(registered),
        "artifacts": len(artifacts),
        "projections": len(PROJECTIONS),
    }
    return failures, counts


class Controls:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.results: dict[str, bool] = {}

    def _copy(self, name: str, source: Path = REFERENCES) -> Path:
        target = self.workspace / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        return target

    def stage(
        self,
        name: str,
        source: Path,
        mutations: tuple[tuple[str, Callable[[Any], None]], ...] = (),
    ) -> Path:
        """A disposable copy of one artifact root carrying the planted defects."""
        root = self._copy(name, source)
        for filename, mutate in mutations:
            document = read(root / filename)
            mutate(document)
            write(root / filename, document)
        return root

    def expect(
        self,
        name: str,
        argv: list[str],
        code: str,
        *,
        status: int | None = None,
    ) -> None:
        """Record whether a command refused by its own code at its own status.

        `status` is the true exit code of the process, captured directly rather
        than through a pipeline: 2 is a refusal and 64 is "the tool could not
        run", and a suite that accepts any non-zero cannot tell a refused
        mutation from a crashed checker. Passing None keeps the weaker
        "non-zero" assertion for controls where either is honest.
        """
        got, output = run(argv)
        matched = got != 0 if status is None else got == status
        self.results[name] = matched and code in output

    def refuse_artifact(
        self,
        name: str,
        source: Path,
        filename: str,
        mutate: Callable[[Any], None],
        code: str,
    ) -> None:
        """Plant one defect in an artifact and require the checker to name it."""
        root = self.stage(name, source, ((filename, mutate),))
        self.expect(
            name,
            [
                sys.executable, str(CHECK),
                "--artifact", str(root / filename),
                "--resolve-subjects", str(root),
            ],
            code,
            status=2,
        )

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

    def refuse_draft(
        self, name: str, compiler: Path, draft: str,
        mutate: Callable[[Any], None], code: str, *, status: int,
    ) -> None:
        """Plant one defect in a compiler draft and require the named refusal."""
        root = self.stage(name, FIXTURES, ((draft, mutate),))
        self.expect(
            name,
            [sys.executable, str(compiler), "--input", str(root / draft)],
            code,
            status=status,
        )

    def refuse_projection(
        self, name: str, compiler: Path, draft: str, target: str,
        mutate: Callable[[Any], None], code: str,
    ) -> None:
        """Hand-edit a committed projection; `--check` must refuse to bless it."""
        root = self.stage(name, FIXTURES, ((target, mutate),))
        self.expect(
            name,
            [
                sys.executable, str(compiler),
                "--input", str(root / draft),
                "--out", str(root / target),
                "--check",
            ],
            code,
            status=2,
        )

    def pin(
        self, name: str, compiler: Path, draft: str,
        mutate: Callable[[Any], None], holds: Callable[[Any], bool],
    ) -> None:
        """A draft that claims more than it earned must compile to the pin anyway.

        This is the other half of a refusal: the compiler does not read these
        fields from the draft at all, so an adversarial draft asserting a
        running session or machine authority produces the same pinned bytes as
        an honest one. Asserting it here is what keeps that a property rather
        than an implementation detail nobody re-reads.
        """
        root = self.stage(name, FIXTURES, ((draft, mutate),))
        status, output = run(
            [sys.executable, str(compiler), "--input", str(root / draft)]
        )
        if status != 0:
            self.results[name] = False
            return
        try:
            compiled = json.loads(output)
        except json.JSONDecodeError:
            self.results[name] = False
            return
        self.results[name] = holds(compiled)


def request(document: Any, identifier: str) -> dict:
    return next(row for row in document["requests"] if row["id"] == identifier)


def entry(document: Any, identifier: str) -> dict:
    return next(row for row in document["entries"] if row["id"] == identifier)


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

    # --- session dispatch: DAG and lease shape ----------------------------
    def share_a_lease(doc: Any) -> None:
        request(doc, "SDR-002")["lease"]["paths"] = copy.deepcopy(
            request(doc, "SDR-001")["lease"]["paths"]
        )

    controls.refuse_artifact(
        "session_dispatch_overlapping_writer_lease", EXAMPLES, DISPATCH,
        share_a_lease, "C06_OVERLAPPING_WRITER_LEASE",
    )

    def share_a_resource(doc: Any) -> None:
        request(doc, "SDR-001")["lease"]["resources"] = [
            "the compiler byte-stability fixture"
        ]

    controls.refuse_artifact(
        "session_dispatch_shared_mutable_resource", EXAMPLES, DISPATCH,
        share_a_resource, "C06_OVERLAPPING_WRITER_LEASE",
    )

    def sibling_directories(doc: Any) -> None:
        """Two disjoint sibling directories, recorded as they behave today.

        `check_session_dispatch` compares lease paths with a bare `startswith`
        and no separator boundary, so `skills/example` and `skills/example-two`
        are reported as an overlap although neither contains the other. This
        control asserts the behavior that exists, not the behavior that is
        wanted: the checker lives in the read-only `scripts/` lease, and a
        control asserting the ideal would be red on arrival and tell nobody
        anything. It is fail-closed -- it over-refuses rather than
        under-refuses -- so the defect is noise, and this is the record that
        the noise is known and measured rather than undiscovered.
        """
        request(doc, "SDR-001")["lease"]["paths"] = ["skills/example"]
        request(doc, "SDR-002")["lease"]["paths"] = ["skills/example-two"]

    controls.refuse_artifact(
        "session_dispatch_lease_prefix_known_limitation", EXAMPLES, DISPATCH,
        sibling_directories, "C06_OVERLAPPING_WRITER_LEASE",
    )
    controls.refuse_artifact(
        "session_dispatch_child_is_its_own_parent", EXAMPLES, DISPATCH,
        lambda doc: request(doc, "SDR-003").__setitem__(
            "parent_request_id", "SDR-003"
        ),
        "C07_HIDDEN_MULTI_PARENT_CONVERGENCE",
    )
    controls.refuse_artifact(
        "session_dispatch_sibling_names_a_parent", EXAMPLES, DISPATCH,
        lambda doc: request(doc, "SDR-002").__setitem__(
            "parent_request_id", "SDR-001"
        ),
        "C07_HIDDEN_MULTI_PARENT_CONVERGENCE",
    )
    controls.refuse_artifact(
        "session_dispatch_rollback_equals_base_tree", EXAMPLES, DISPATCH,
        lambda doc: request(doc, "SDR-001")["rollback"].__setitem__(
            "commit", request(doc, "SDR-001")["base"]["tree"]
        ),
        "C13_ROLLBACK_SUBJECT_ABSENT_OR_EQUAL_TO_MUTABLE_ALIAS",
    )

    # --- session receipt: invented session state --------------------------
    controls.refuse_artifact(
        "session_receipt_running_without_session_observed", EXAMPLES, RECEIPT,
        lambda doc: doc["lifecycle"]["SESSION_OBSERVED"].__setitem__(
            "state", "NOT_EXERCISED"
        ),
        "C09_SESSION_REQUEST_PROMOTED_TO_RUNNING",
    )
    controls.refuse_artifact(
        "session_receipt_result_without_running", EXAMPLES, RECEIPT,
        lambda doc: doc["lifecycle"]["RUNNING"].__setitem__("state", "NOT_EXERCISED"),
        "C09_SESSION_REQUEST_PROMOTED_TO_RUNNING",
    )
    controls.refuse_artifact(
        "session_receipt_pass_without_evidence_ref", EXAMPLES, RECEIPT,
        lambda doc: doc["lifecycle"]["ARTIFACTS_READ_BACK"].__setitem__("state", "PASS"),
        "C05_MISSING_EXACT_RECEIPT",
    )

    # --- external projection: drift and widened authority -----------------
    controls.refuse_artifact(
        "projection_read_back_pass_on_digest_drift", EXAMPLES, REGISTRY,
        lambda doc: entry(doc, "PRJ-001")["read_back"].__setitem__(
            "compared_digest",
            "0" * 63 + "1",
        ),
        "C08_PROJECTION_USED_AS_MACHINE_AUTHORITY",
    )
    controls.refuse_artifact(
        "projection_subject_is_a_mutable_alias", EXAMPLES, REGISTRY,
        lambda doc: entry(doc, "PRJ-002")["canonical_subjects"][0].__setitem__(
            "commit", "main"
        ),
        "C01_MUTABLE_SUBJECT",
    )

    # --- the two compilers ------------------------------------------------
    def contradict_dispatch(doc: Any) -> None:
        request(doc, "SDR-001")["evidence_dispositions"].append(
            {
                "subject": "problem-closure-matrix.schema.json",
                "disposition": "CONTRADICTED",
            }
        )

    controls.refuse_draft(
        "session_dispatch_compiler_drops_contradiction", COMPILE_SESSION,
        DISPATCH_DRAFT, contradict_dispatch, "K09_CONTRADICTION_DROPPED", status=2,
    )

    def contradict_projection(doc: Any) -> None:
        entry(doc, "PRJ-001")["evidence_dispositions"].append(
            {
                "subject": "skills/product-reverse-engineering-loop/references/"
                           "example-closure-matrix.json",
                "disposition": "CONFIRMED",
            }
        )

    controls.refuse_draft(
        "external_projection_compiler_drops_contradiction", COMPILE_PROJECTION,
        REGISTRY_DRAFT, contradict_projection, "K09_CONTRADICTION_DROPPED", status=2,
    )
    controls.refuse_draft(
        "session_dispatch_compiler_refuses_malformed_draft", COMPILE_SESSION,
        DISPATCH_DRAFT, lambda doc: request(doc, "SDR-002").pop("lease"),
        "PREL-COMPILE-UNUSABLE", status=64,
    )
    controls.refuse_draft(
        "external_projection_compiler_refuses_malformed_draft", COMPILE_PROJECTION,
        REGISTRY_DRAFT, lambda doc: entry(doc, "PRJ-002").pop("read_back"),
        "PREL-COMPILE-UNUSABLE", status=64,
    )
    controls.refuse_draft(
        "session_dispatch_compiler_refuses_compiled_input", COMPILE_SESSION,
        DISPATCH_DRAFT,
        lambda doc: doc.__setitem__("schema", "prel/session-dispatch-request/v1"),
        "PREL-COMPILE-RED", status=2,
    )
    controls.refuse_draft(
        "external_projection_compiler_refuses_empty_registry", COMPILE_PROJECTION,
        REGISTRY_DRAFT, lambda doc: doc.__setitem__("entries", []),
        "PREL-COMPILE-RED", status=2,
    )
    controls.refuse_projection(
        "session_dispatch_hand_edited_projection", COMPILE_SESSION,
        DISPATCH_DRAFT, DISPATCH_COMPILED,
        lambda doc: request(doc, "SDR-001")["lease"]["paths"].append(
            "skills/product-reverse-engineering-loop/scripts/"
        ),
        "PREL-COMPILE-RED",
    )
    controls.refuse_projection(
        "external_projection_hand_edited_projection", COMPILE_PROJECTION,
        REGISTRY_DRAFT, REGISTRY_COMPILED,
        lambda doc: entry(doc, "PRJ-002")["read_back"].__setitem__("state", "PASS"),
        "PREL-COMPILE-RED",
    )

    def claim_a_running_session(doc: Any) -> None:
        doc["lifecycle_state"] = "RUNNING"
        doc["running_session"] = {"pid": 4242, "host": "a carrier nobody observed"}
        for row in doc["requests"]:
            row["requests_private_reasoning"] = True
            row["authority"] = {
                "merge": True, "permission": True, "secret": True, "production": True
            }

    def stayed_a_request(compiled: Any) -> bool:
        return (
            compiled["lifecycle_state"] == "LAUNCH_REQUESTED"
            and compiled["running_session"] is None
            and all(
                row["requests_private_reasoning"] is False
                and not any(row["authority"].values())
                for row in compiled["requests"]
            )
        )

    controls.pin(
        "session_dispatch_compiler_pins_launch_requested", COMPILE_SESSION,
        DISPATCH_DRAFT, claim_a_running_session, stayed_a_request,
    )

    def claim_machine_authority(doc: Any) -> None:
        doc["evidence_ceiling"] = "MACHINE_AUTHORITY"
        doc["authority"] = {
            "implementation": True, "completion": True, "product_truth": True,
            "merge": True, "release": True,
        }
        for row in doc["entries"]:
            row["authority"] = copy.deepcopy(doc["authority"])

    def stayed_a_projection(compiled: Any) -> bool:
        return (
            compiled["evidence_ceiling"] == "HUMAN_PROJECTION"
            and not any(compiled["authority"].values())
            and all(not any(row["authority"].values()) for row in compiled["entries"])
        )

    controls.pin(
        "external_projection_compiler_pins_human_projection", COMPILE_PROJECTION,
        REGISTRY_DRAFT, claim_machine_authority, stayed_a_projection,
    )


def main() -> int:
    failures, counts = positive_control()
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
        f"PREL-SELFTEST-GREEN {counts['artifacts']} committed artifact(s) covering "
        f"{counts['schemas']} registered schema(s), {counts['projections']} "
        f"byte-stable projection(s), "
        f"{len(controls.results)} planted defects refused by their own code"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
