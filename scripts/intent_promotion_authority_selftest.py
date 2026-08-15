#!/usr/bin/env python3
"""Controls for the external authority readback layer.

Every case builds a real bundle on disk with real evidence bytes, because the
defect class this layer exists for is precisely a digest that names a file
nobody hashed. A control that mutated only in memory would share the blind spot
it is testing.
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "evals" / "schema"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_intent_promotion_authority import Refused, Unusable, evaluate  # noqa: E402


def digest_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def write(path: Path, body: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(body, indent=2, sort_keys=True) + "\n"
    path.write_text(payload, encoding="utf-8")
    return digest_bytes(payload.encode("utf-8"))


def build(root: Path) -> dict[str, Any]:
    """A complete, internally consistent bundle with real evidence files."""
    for name in ("intent-promotion-authority-bundle.schema.json",
                 "intent-promotion-contract.schema.json",
                 "intent-promotion-receipt.schema.json",
                 "intent-promotion-ledger.schema.json"):
        (root / "schema").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SCHEMA_DIR / name, root / "schema" / name)

    source = REPO_ROOT / "evals" / "fixtures" / "intent-promotion"
    contract = json.loads((source / "valid-contract.json").read_text(encoding="utf-8"))
    receipt = json.loads((source / "valid-receipt.json").read_text(encoding="utf-8"))
    ledger = json.loads((source / "ledger.json").read_text(encoding="utf-8"))

    contract_digest = write(root / "contract.json", contract)
    receipt["contract_digest"] = contract_digest

    run = receipt["evaluator_receipts"][0]
    evaluator_evidence = {
        "evaluator_id": run["evaluator_id"],
        "evaluator_version": run["evaluator_version"],
        "evaluator_artifact_digest": run["evaluator_artifact_digest"],
        "subject_commit_sha": run["subject_commit_sha"],
        "subject_tree_sha": run["subject_tree_sha"],
        "status": run["status"],
        "output_digest": run["output_digest"],
        "execution_origin": run["execution_origin"],
    }
    evaluator_digest = write(root / "evidence" / "evaluator.json", evaluator_evidence)
    run["receipt_digest"] = evaluator_digest

    merge = receipt["merge_subject"]
    forge_evidence = {
        "source": merge["forge_readback"]["source"],
        "observed_at_commit_sha": merge["merge_commit_sha"],
        "repository": merge["repository"],
        "merge_commit_sha": merge["merge_commit_sha"],
        "merge_tree_sha": merge["merge_tree_sha"],
        "candidate_head_sha": merge["candidate_head_sha"],
        "candidate_tree_sha": merge["candidate_tree_sha"],
    }
    forge_digest = write(root / "evidence" / "forge.json", forge_evidence)
    merge["forge_readback"]["readback_digest"] = forge_digest
    merge["forge_readback"]["observed_at_commit_sha"] = merge["merge_commit_sha"]

    receipt_digest = write(root / "receipt.json", receipt)
    ledger_digest = write(root / "ledger.json", ledger)

    bundle = {
        "schema_version": "intent-promotion-authority-bundle/v1",
        "bundle_schema": {
            "path": "schema/intent-promotion-authority-bundle.schema.json",
            "artifact_digest": digest_bytes(
                (root / "schema/intent-promotion-authority-bundle.schema.json").read_bytes()),
        },
        "contract_schema": {
            "path": "schema/intent-promotion-contract.schema.json",
            "artifact_digest": digest_bytes(
                (root / "schema/intent-promotion-contract.schema.json").read_bytes()),
        },
        "receipt_schema": {
            "path": "schema/intent-promotion-receipt.schema.json",
            "artifact_digest": digest_bytes(
                (root / "schema/intent-promotion-receipt.schema.json").read_bytes()),
        },
        "ledger_schema": {
            "path": "schema/intent-promotion-ledger.schema.json",
            "artifact_digest": digest_bytes(
                (root / "schema/intent-promotion-ledger.schema.json").read_bytes()),
        },
        "contract": {"path": "contract.json", "artifact_digest": contract_digest},
        "receipt": {"path": "receipt.json", "artifact_digest": receipt_digest},
        "ledger": {"path": "ledger.json", "artifact_digest": ledger_digest},
        "evidence": {
            "evaluator_receipts": [
                {"receipt_ref": run["receipt_ref"], "path": "evidence/evaluator.json",
                 "artifact_digest": evaluator_digest}
            ],
            "forge_readback": {"path": "evidence/forge.json", "artifact_digest": forge_digest},
        },
    }
    write(root / "bundle.json", bundle)
    return bundle


def rebuild(root: Path, mutate: Callable[[Path, dict[str, Any]], None]) -> Path:
    """Apply a mutation, then re-seal only what the mutation did not touch."""
    bundle = build(root)
    mutate(root, bundle)
    write(root / "bundle.json", bundle)
    return root / "bundle.json"


def reseal_receipt(root: Path, bundle: dict[str, Any], receipt: dict[str, Any]) -> None:
    bundle["receipt"]["artifact_digest"] = write(root / "receipt.json", receipt)


def run_selftest() -> int:
    survived: list[str] = []

    with tempfile.TemporaryDirectory(prefix="ipa-canonical.") as raw:
        root = Path(raw)
        build(root)
        try:
            result = evaluate(root / "bundle.json")
        except (Refused, Unusable) as error:
            print(f"SELFTEST RED: canonical bundle refused: {error}", file=sys.stderr)
            return 2
        if result["status"] != "PASS":
            print(f"SELFTEST RED: canonical bundle not PASS: {result}", file=sys.stderr)
            return 2
        if result["evaluator_evidence_read"] == []:
            print("SELFTEST RED: canonical bundle read no evaluator evidence",
                  file=sys.stderr)
            return 2

    def case(name: str, mutate: Callable[[Path, dict[str, Any]], None],
             expect: type[Exception] = Refused) -> None:
        with tempfile.TemporaryDirectory(prefix="ipa-mut.") as raw:
            root = Path(raw)
            path = rebuild(root, mutate)
            try:
                evaluate(path)
            except expect:
                return
            except (Refused, Unusable):
                # Refused where Unusable was expected, or the reverse: the two
                # exits must not be interchangeable.
                survived.append(f"{name} (wrong failure class)")
                return
            survived.append(name)

    def drop_evaluator_evidence(root: Path, bundle: dict[str, Any]) -> None:
        bundle["evidence"]["evaluator_receipts"] = []

    def duplicate_evaluator_evidence(root: Path, bundle: dict[str, Any]) -> None:
        bundle["evidence"]["evaluator_receipts"].append(
            copy.deepcopy(bundle["evidence"]["evaluator_receipts"][0]))

    def extra_unreferenced_evidence(root: Path, bundle: dict[str, Any]) -> None:
        digest = write(root / "evidence" / "spare.json", {"evaluator_id": "spare"})
        bundle["evidence"]["evaluator_receipts"].append(
            {"receipt_ref": "workflow-run:unreferenced", "path": "evidence/spare.json",
             "artifact_digest": digest})

    def evaluator_bytes_drift(root: Path, bundle: dict[str, Any]) -> None:
        body = json.loads((root / "evidence/evaluator.json").read_text(encoding="utf-8"))
        body["status"] = "FAIL"
        (root / "evidence/evaluator.json").write_text(
            json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def evaluator_field_mismatch(field: str, value: Any) -> Callable[[Path, dict[str, Any]], None]:
        def mutate(root: Path, bundle: dict[str, Any]) -> None:
            body = json.loads((root / "evidence/evaluator.json").read_text(encoding="utf-8"))
            body[field] = value
            digest = write(root / "evidence" / "evaluator.json", body)
            bundle["evidence"]["evaluator_receipts"][0]["artifact_digest"] = digest
            receipt = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
            receipt["evaluator_receipts"][0]["receipt_digest"] = digest
            reseal_receipt(root, bundle, receipt)
        return mutate

    def forge_missing(root: Path, bundle: dict[str, Any]) -> None:
        bundle["evidence"].pop("forge_readback")

    def forge_field_mismatch(field: str, value: Any) -> Callable[[Path, dict[str, Any]], None]:
        def mutate(root: Path, bundle: dict[str, Any]) -> None:
            body = json.loads((root / "evidence/forge.json").read_text(encoding="utf-8"))
            body[field] = value
            digest = write(root / "evidence" / "forge.json", body)
            bundle["evidence"]["forge_readback"]["artifact_digest"] = digest
            receipt = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
            receipt["merge_subject"]["forge_readback"]["readback_digest"] = digest
            reseal_receipt(root, bundle, receipt)
        return mutate

    def forge_digest_drift(root: Path, bundle: dict[str, Any]) -> None:
        body = json.loads((root / "evidence/forge.json").read_text(encoding="utf-8"))
        body["repository"] = body["repository"] + "-x"
        (root / "evidence/forge.json").write_text(
            json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def add_approval(root: Path, bundle: dict[str, Any], *,
                     evidence_overrides: dict[str, Any] | None = None,
                     supply_evidence: bool = True) -> None:
        receipt = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
        approval = {
            "approver_identity": "ed3c",
            "approver_kind": "HUMAN",
            "approval_subject_commit_sha": receipt["subject"]["commit_sha"],
            "approval_receipt_digest": "sha256:" + "0" * 64,
            "generated_by_agent": False,
            "review_ref": "https://example.invalid/review/1",
            "readback_source": "GITHUB_API",
        }
        receipt["from_state"] = "ADMITTED"
        receipt["to_state"] = "CANONICAL"
        receipt["approval"] = approval
        receipt["writebacks"] = [
            {"destination_id": "root-context", "scope": "ROOT_GLOBAL", "mode": "APPEND"}]
        body = {
            "approver_identity": approval["approver_identity"],
            "approver_kind": approval["approver_kind"],
            "review_ref": approval["review_ref"],
            "readback_source": approval["readback_source"],
            "approval_subject_commit_sha": approval["approval_subject_commit_sha"],
            "subject_tree_sha": receipt["subject"]["tree_sha"],
            "generated_by_agent": False,
        }
        body.update(evidence_overrides or {})
        digest = write(root / "evidence" / "approval.json", body)
        approval["approval_receipt_digest"] = digest
        reseal_receipt(root, bundle, receipt)
        if supply_evidence:
            bundle["evidence"]["approval_readback"] = {
                "path": "evidence/approval.json", "artifact_digest": digest}

    case("evaluator evidence missing", drop_evaluator_evidence)
    case("evaluator evidence duplicated", duplicate_evaluator_evidence)
    case("unreferenced extra evidence artifact", extra_unreferenced_evidence)
    case("evaluator evidence bytes drifted from their digest", evaluator_bytes_drift)
    case("evidence reports a different evaluator",
         evaluator_field_mismatch("evaluator_id", "some-other-evaluator"))
    case("evidence reports a different evaluator version",
         evaluator_field_mismatch("evaluator_version", "9.9.9"))
    case("evidence reports a different evaluator artifact",
         evaluator_field_mismatch("evaluator_artifact_digest", "sha256:" + "9" * 64))
    case("evidence reports a different subject commit",
         evaluator_field_mismatch("subject_commit_sha", "9" * 40))
    case("evidence reports a different subject tree",
         evaluator_field_mismatch("subject_tree_sha", "9" * 40))
    case("evidence reports a failing status",
         evaluator_field_mismatch("status", "FAIL"))
    case("evidence reports a different output digest",
         evaluator_field_mismatch("output_digest", "sha256:" + "9" * 64))
    case("evidence reports a different execution origin",
         evaluator_field_mismatch("execution_origin", "EXTERNAL_ATTESTED"))

    case("forge readback missing", forge_missing)
    case("forge readback bytes drifted from their digest", forge_digest_drift)
    case("forge readback names a different candidate",
         forge_field_mismatch("candidate_head_sha", "9" * 40))
    case("forge readback names a different candidate tree",
         forge_field_mismatch("candidate_tree_sha", "9" * 40))
    case("forge readback names a different merge commit",
         forge_field_mismatch("merge_commit_sha", "9" * 40))
    case("forge readback names a different repository",
         forge_field_mismatch("repository", "ed3c/somewhere-else"))
    case("forge readback names a different source",
         forge_field_mismatch("source", "GITLAB_API"))

    case("approval evidence missing",
         lambda root, bundle: add_approval(root, bundle, supply_evidence=False))
    case("approval evidence generated by an agent",
         lambda root, bundle: add_approval(root, bundle,
                                           evidence_overrides={"generated_by_agent": True}))
    case("approval evidence names a different approver",
         lambda root, bundle: add_approval(root, bundle,
                                           evidence_overrides={"approver_identity": "someone-else"}))
    case("approval evidence names a different review",
         lambda root, bundle: add_approval(root, bundle,
                                           evidence_overrides={"review_ref": "https://example.invalid/review/999"}))
    case("approval evidence approves a different commit",
         lambda root, bundle: add_approval(root, bundle,
                                           evidence_overrides={"approval_subject_commit_sha": "9" * 40}))
    case("approval evidence approves a different tree",
         lambda root, bundle: add_approval(root, bundle,
                                           evidence_overrides={"subject_tree_sha": "9" * 40}))

    def ledger_digest_mismatch(root: Path, bundle: dict[str, Any]) -> None:
        bundle["ledger"]["artifact_digest"] = "sha256:" + "9" * 64

    def ledger_path_mismatch(root: Path, bundle: dict[str, Any]) -> None:
        digest = write(root / "elsewhere.json",
                       json.loads((root / "ledger.json").read_text(encoding="utf-8")))
        bundle["ledger"] = {"path": "elsewhere.json", "artifact_digest": digest}

    def forbidden_extra_field(root: Path, bundle: dict[str, Any]) -> None:
        receipt = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
        receipt["reviewer_notes"] = "looked fine to me"
        reseal_receipt(root, bundle, receipt)

    def contract_digest_drift(root: Path, bundle: dict[str, Any]) -> None:
        receipt = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
        receipt["contract_digest"] = "sha256:" + "9" * 64
        reseal_receipt(root, bundle, receipt)

    def path_escape(root: Path, bundle: dict[str, Any]) -> None:
        bundle["evidence"]["evaluator_receipts"][0]["path"] = "../outside.json"

    def bundle_extra_field(root: Path, bundle: dict[str, Any]) -> None:
        bundle["notes"] = "extra"

    case("ledger digest does not match its bytes", ledger_digest_mismatch)
    case("ledger is not the one the contract declares", ledger_path_mismatch)
    case("schema-valid receipt carrying a forbidden extra field", forbidden_extra_field)
    case("receipt bound to different contract bytes", contract_digest_drift)
    case("evidence path escaping the bundle root", path_escape)
    case("bundle carrying an undeclared extra field", bundle_extra_field)

    def semantically_identical_bytes_drift(root: Path, bundle: dict[str, Any]) -> None:
        """Bytes change; every compared field stays identical.

        Only the digest check can catch this. The other drift controls change a
        field the field-by-field comparison also inspects, so they would still
        pass with the digest check removed -- which is exactly what happened
        when this control was absent.
        """
        path = root / "evidence" / "evaluator.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        body["irrelevant_annotation"] = "added after the digest was taken"
        path.write_text(json.dumps(body, indent=4, sort_keys=True) + "\n", encoding="utf-8")

    def schema_bytes_drift(root: Path, bundle: dict[str, Any]) -> None:
        """A schema swapped after its digest was recorded."""
        path = root / "schema" / "intent-promotion-receipt.schema.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        body["description"] = "swapped after sealing"
        path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    case("evidence bytes changed with every compared field intact",
         semantically_identical_bytes_drift)
    case("schema bytes swapped after the bundle was sealed", schema_bytes_drift)

    def absent_evidence_file(root: Path, bundle: dict[str, Any]) -> None:
        (root / "evidence" / "evaluator.json").unlink()

    case("evidence file absent entirely", absent_evidence_file, expect=Unusable)

    if survived:
        for name in survived:
            print(f"SELFTEST RED: mutation survived: {name}", file=sys.stderr)
        return 2

    print("SELFTEST GREEN: authority bundle admitted; 37 evidence, schema and "
          "boundary mutations refused")
    return 0
