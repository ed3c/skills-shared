#!/usr/bin/env python3
"""Controls for the authority-bound A/B composition.

Every case writes a real manifest over real files and runs both gates as
subprocesses, because the defect this composition exists for is a digest that
names bytes nobody hashed and an identity nobody produced. Mutating in memory
would skip exactly the step under test.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_ab_authority import GateUnavailable, Refused, Unusable, evaluate  # noqa: E402

SKILL_REL = "skills/controlled-technical-language-harness"


def digest_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def artifact(root: Path, relative: str) -> dict[str, Any]:
    return {"path": relative, "artifact_digest": digest_bytes((root / relative).read_bytes())}


def build(source_root: Path, work: Path) -> tuple[Path, Path]:
    """Copy the pieces into a disposable root and align the identities.

    The committed A/B fixture and the committed authority bundle name different
    evaluators. That mismatch is a control below, so the canonical case here
    aligns them deliberately rather than by accident.
    """
    root = work / "repo"
    (root / SKILL_REL / "scripts").mkdir(parents=True)
    (root / SKILL_REL / "tests" / "ab-canary" / "fixtures").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)

    shutil.copyfile(source_root / SKILL_REL / "scripts" / "score_ab.py",
                    root / SKILL_REL / "scripts" / "score_ab.py")
    shutil.copyfile(source_root / "scripts" / "check_intent_promotion_authority.py",
                    root / "scripts" / "check_intent_promotion_authority.py")
    shutil.copyfile(source_root / "scripts" / "intent_promotion_authority_selftest.py",
                    root / "scripts" / "intent_promotion_authority_selftest.py")
    shutil.copytree(source_root / "evals" / "fixtures" / "intent-promotion" / "authority",
                    root / "authority")

    evidence_path = root / "authority" / "evidence" / "evaluator.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    ab = json.loads((source_root / SKILL_REL / "tests" / "ab-canary" /
                     "fixtures" / "good-run.json").read_text(encoding="utf-8"))
    ab["evaluator_identities"] = [{
        "id": evidence["evaluator_id"],
        "version": evidence["evaluator_version"],
        "artifact_digest": evidence["evaluator_artifact_digest"],
    }]
    ab_path = root / SKILL_REL / "tests" / "ab-canary" / "fixtures" / "good-run.json"
    ab_path.write_text(json.dumps(ab, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        "schema_version": "controlled-language-ab-authority-manifest/v1",
        "ab_run": artifact(root, f"{SKILL_REL}/tests/ab-canary/fixtures/good-run.json"),
        "ab_scorer": artifact(root, f"{SKILL_REL}/scripts/score_ab.py"),
        "authority_checker": artifact(root, "scripts/check_intent_promotion_authority.py"),
        "authority_bundle": artifact(root, "authority/bundle.json"),
        "claimed_state": "VERIFIED",
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
    return root, manifest_path


def reseal(root: Path, manifest_path: Path, manifest: dict[str, Any]) -> None:
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")


def run_selftest(source_root: Path) -> int:
    survived: list[str] = []

    with tempfile.TemporaryDirectory(prefix="abauth-canonical.") as raw:
        root, manifest_path = build(source_root, Path(raw))
        try:
            receipt = evaluate(root, manifest_path)
        except RuntimeError as error:
            # The authority checker refuses to run without its validator, on
            # purpose. Say which it is, rather than emitting a traceback that
            # reads like a defect in the composition.
            print(f"SELFTEST RED: a required gate is unavailable: {error}",
                  file=sys.stderr)
            return 70
        except (Refused, Unusable, GateUnavailable) as error:
            print(f"SELFTEST RED: canonical composition refused: {error}", file=sys.stderr)
            return 2
        if receipt["status"] != "PASS":
            print(f"SELFTEST RED: canonical composition not PASS: {receipt}", file=sys.stderr)
            return 2
        if not receipt["evaluators_bound_to_external_evidence"]:
            print("SELFTEST RED: no evaluator was bound to external evidence",
                  file=sys.stderr)
            return 2
        if receipt["gate_order"] != ["authority", "ab_scorer"]:
            print("SELFTEST RED: gate order is not recorded", file=sys.stderr)
            return 2

    def case(name: str, mutate: Callable[[Path, Path, dict[str, Any]], None],
             expect: type[Exception] = Refused) -> None:
        with tempfile.TemporaryDirectory(prefix="abauth-mut.") as raw:
            root, manifest_path = build(source_root, Path(raw))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            mutate(root, manifest_path, manifest)
            reseal(root, manifest_path, manifest)
            try:
                evaluate(root, manifest_path)
            except expect:
                return
            except (Refused, Unusable, GateUnavailable):
                survived.append(f"{name} (wrong failure class)")
                return
            survived.append(name)

    # Manifest binding.
    case("A/B run digest does not match its bytes",
         lambda r, p, m: m["ab_run"].__setitem__("artifact_digest", "sha256:" + "9" * 64))
    case("A/B scorer byte drift",
         lambda r, p, m: (r / SKILL_REL / "scripts" / "score_ab.py").write_text(
             (r / SKILL_REL / "scripts" / "score_ab.py").read_text() + "\n# drift\n"))
    case("authority checker byte drift",
         lambda r, p, m: (r / "scripts" / "check_intent_promotion_authority.py").write_text(
             (r / "scripts" / "check_intent_promotion_authority.py").read_text() + "\n# drift\n"))
    case("authority bundle byte drift",
         lambda r, p, m: (r / "authority" / "bundle.json").write_text(
             json.dumps(json.loads((r / "authority" / "bundle.json").read_text()),
                        indent=4, sort_keys=True) + "\n"))
    case("manifest reference missing",
         lambda r, p, m: m.pop("authority_bundle"))
    case("extra unreferenced manifest entry",
         lambda r, p, m: m.__setitem__("spare", {"path": "manifest.json",
                                                 "artifact_digest": "sha256:" + "0" * 64}))
    case("escaping manifest path",
         lambda r, p, m: m["ab_run"].__setitem__("path", "../outside.json"))
    case("absolute manifest path",
         lambda r, p, m: m["ab_run"].__setitem__("path", "/etc/hosts"))
    case("manifest reference to an absent file",
         lambda r, p, m: (r / SKILL_REL / "tests" / "ab-canary" /
                          "fixtures" / "good-run.json").unlink(), Unusable)

    # Claim smuggling.
    case("claiming ADMITTED for an offline fixture comparison",
         lambda r, p, m: m.__setitem__("claimed_state", "ADMITTED"))
    case("claiming CANONICAL for an offline fixture comparison",
         lambda r, p, m: m.__setitem__("claimed_state", "CANONICAL"))
    case("claiming CERTIFIED",
         lambda r, p, m: m.__setitem__("claimed_state", "CERTIFIED"))

    def edit_ab(root: Path, manifest: dict[str, Any],
                mutate: Callable[[dict[str, Any]], None]) -> None:
        path = root / SKILL_REL / "tests" / "ab-canary" / "fixtures" / "good-run.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        mutate(body)
        path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest["ab_run"]["artifact_digest"] = digest_bytes(path.read_bytes())

    # The composition itself.
    case("evaluator identity exists only as caller-authored JSON",
         lambda r, p, m: edit_ab(r, m, lambda b: b.__setitem__(
             "evaluator_identities", [{"id": "invented", "version": "1.0.0",
                                       "artifact_digest": "sha256:" + "1" * 64}])))
    case("evaluator version does not match the external evidence",
         lambda r, p, m: edit_ab(r, m, lambda b: b["evaluator_identities"][0].__setitem__(
             "version", "9.9.9")))
    case("evaluator artifact digest does not match the external evidence",
         lambda r, p, m: edit_ab(r, m, lambda b: b["evaluator_identities"][0].__setitem__(
             "artifact_digest", "sha256:" + "2" * 64)))
    case("A/B declares no evaluator identity at all",
         lambda r, p, m: edit_ab(r, m, lambda b: b.__setitem__("evaluator_identities", [])))

    def edit_evidence(root: Path, manifest: dict[str, Any],
                      mutate: Callable[[dict[str, Any]], None]) -> None:
        """Change evidence and re-seal the bundle, so the authority layer still
        passes and only this composition can catch the change."""
        evidence_path = root / "authority" / "evidence" / "evaluator.json"
        body = json.loads(evidence_path.read_text(encoding="utf-8"))
        mutate(body)
        payload = json.dumps(body, indent=2, sort_keys=True) + "\n"
        evidence_path.write_text(payload, encoding="utf-8")
        digest = digest_bytes(payload.encode("utf-8"))

        bundle_path = root / "authority" / "bundle.json"
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        bundle["evidence"]["evaluator_receipts"][0]["artifact_digest"] = digest
        receipt_path = root / "authority" / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["evaluator_receipts"][0]["receipt_digest"] = digest
        for field in ("evaluator_id", "evaluator_version", "evaluator_artifact_digest",
                      "status", "output_digest", "execution_origin",
                      "subject_commit_sha", "subject_tree_sha"):
            if field in body:
                receipt["evaluator_receipts"][0][field] = body[field]
        receipt_payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        receipt_path.write_text(receipt_payload, encoding="utf-8")
        bundle["receipt"]["artifact_digest"] = digest_bytes(receipt_payload.encode("utf-8"))
        bundle_payload = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
        bundle_path.write_text(bundle_payload, encoding="utf-8")
        manifest["authority_bundle"]["artifact_digest"] = digest_bytes(
            bundle_payload.encode("utf-8"))

    case("external evidence reports a non-PASS status",
         lambda r, p, m: edit_evidence(r, m, lambda b: b.__setitem__("status", "SKIPPED")))

    if survived:
        for name in survived:
            print(f"SELFTEST RED: mutation survived: {name}", file=sys.stderr)
        return 2

    print("SELFTEST GREEN: authority-bound A/B admitted; 18 manifest, claim, "
          "composition and evidence mutations refused")
    return 0
