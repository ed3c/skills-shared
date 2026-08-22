#!/usr/bin/env python3
"""Compile an exact-PR CADG admission receipt from a durable PR template.

CADG is causal observability, not an execution graph. The default OBSERVE mode
never blocks a reversible material PR merely because its full causal packet is
late or absent. WARN surfaces that omission without creating an execution edge.
GATE requires a complete packet only at a named transition boundary; the legacy
strict-material policy remains an explicit opt-in profile.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

HEX40 = __import__("re").compile(r"^[0-9a-f]{40}$")
DIGEST = __import__("re").compile(r"^sha256:[0-9a-f]{64}$")
OPERATING_MODES = {"OFF", "OBSERVE", "WARN", "GATE"}
FI_BLOCKER_MAP = {
    "CADG001": "CADG-FI-001",  # stale/wrong immutable subject
    "CADG013": "CADG-FI-001",
    "CADG014": "CADG-FI-001",
    "CADG008": "CADG-FI-002",  # duplicate canonical writer
    "CADG009": "CADG-FI-003",  # authority/effect widening
    "CADG003": "CADG-FI-004",  # blocking assumption unresolved
}


class AdmissionError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def canonical_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AdmissionError("CADG001", f"{path} root must be an object")
    return value


def under(root: Path, rel: str) -> Path:
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        raise AdmissionError("CADG012", f"unsafe repository path: {rel!r}")
    target = (root / rel).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise AdmissionError("CADG012", f"path escapes repository: {rel}") from exc
    return target


def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def load_lines(path: Path) -> list[str]:
    return sorted({line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()})


def manifest(root: Path, paths: list[str], excluded: list[str]) -> tuple[str, list[dict[str, str]]]:
    records: list[dict[str, str]] = []
    for rel in sorted(set(paths)):
        if matches(rel, excluded):
            continue
        target = under(root, rel)
        if not target.is_file():
            raise AdmissionError("CADG013", f"declared delta path is absent or not a file: {rel}")
        records.append({"path": rel, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    if not records:
        raise AdmissionError("CADG013", "code manifest has no non-metadata paths")
    return canonical_digest(records), records


def git(root: Path, *args: str) -> str:
    run = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True)
    if run.returncode:
        raise AdmissionError("CADG001", f"git {' '.join(args)} failed: {run.stderr.strip()}")
    return run.stdout.strip()


def exact40(value: str, label: str) -> None:
    if not HEX40.fullmatch(value):
        raise AdmissionError("CADG001", f"{label} must be immutable 40-hex")


def material_paths(paths: list[str], policy: dict[str, Any]) -> list[str]:
    metadata = [str(x) for x in policy.get("metadata_globs", [])]
    probes = [str(x) for x in policy.get("material_path_globs", [])]
    return [path for path in paths if not matches(path, metadata) and matches(path, probes)]


def operating_mode(policy: dict[str, Any]) -> str:
    mode = str(policy.get("operating_mode", "OBSERVE")).upper()
    if mode not in OPERATING_MODES:
        raise AdmissionError("CADG016", f"unknown CADG operating mode: {mode}")
    return mode


def transition_boundary(args: argparse.Namespace, policy: dict[str, Any]) -> str:
    return args.transition_boundary or str(policy.get("transition_boundary", "PR_IMPLEMENTATION_REVERSIBLE"))


def missing_packet_action(args: argparse.Namespace, policy: dict[str, Any], material_hits: list[str]) -> None:
    mode = operating_mode(policy)
    boundary = transition_boundary(args, policy)
    strict = bool(policy.get("strict_missing_packet", False))
    gate_boundaries = {str(x) for x in policy.get("gate_boundaries", [])}
    details = ", ".join(material_hits)

    if mode == "OFF":
        print(f"CADG-PR-OFF boundary={boundary} material={details}")
        return
    if mode == "OBSERVE":
        print(f"CADG-PR-OBSERVE PARTIAL_CAUSAL_CHAIN boundary={boundary} material={details}")
        return
    if mode == "WARN":
        print(f"CADG-PR-WARN PARTIAL_CAUSAL_CHAIN boundary={boundary} material={details}", file=sys.stderr)
        return
    if strict or boundary in gate_boundaries:
        raise AdmissionError("CADG018", f"GATE boundary {boundary} requires a CADG packet: {details}")
    print(f"CADG-PR-GATE-NOT-AT-BOUNDARY boundary={boundary} material={details}")


def map_checker_failure(detail: str) -> str:
    for cadg_code, fi_code in FI_BLOCKER_MAP.items():
        if cadg_code in detail:
            return fi_code
    return "CADG016"


def run_checker(checker: Path, packet: Path) -> None:
    run = subprocess.run([sys.executable, str(checker), "--packet", str(packet)], text=True, capture_output=True)
    if run.returncode:
        detail = "\n".join(line for line in (run.stdout + run.stderr).splitlines() if line.strip())
        raise AdmissionError(map_checker_failure(detail), f"CADG checker rejected packet: {detail}")


def validate_shadow(path: Path, exact: dict[str, str]) -> dict[str, Any]:
    shadow = read_json(path)
    if shadow.get("builder_identity") == shadow.get("reviewer_identity"):
        raise AdmissionError("CADG016", "Builder self-review cannot become independent Shadow")
    if shadow.get("subject") != exact:
        raise AdmissionError("CADG-FI-001", "Shadow receipt is bound to another PR subject")
    if not DIGEST.fullmatch(str(shadow.get("receipt_digest", ""))):
        raise AdmissionError("CADG010", "Shadow receipt digest is absent")
    return shadow


def admit(args: argparse.Namespace) -> dict[str, Any] | None:
    root = args.repo_root.resolve()
    policy = read_json(args.policy)
    changed = load_lines(args.changed_files)
    metadata = [str(x) for x in policy.get("metadata_globs", [])]
    changed_code = [path for path in changed if not matches(path, metadata)]
    material_hits = material_paths(changed, policy)
    if args.packet is None:
        if material_hits:
            missing_packet_action(args, policy, material_hits)
            return None
        print("CADG-PR-NOT-APPLICABLE no material trigger and no packet")
        return None

    packet = read_json(args.packet)
    run_checker(args.checker, args.packet)
    subject = packet.get("subject", {})
    pr = packet.get("pr", {})
    if packet.get("mode") != "FORWARD_PROVENANCE" or packet.get("stage") != "PR_TEMPLATE":
        raise AdmissionError("CADG002", "PR admission requires FORWARD_PROVENANCE/PR_TEMPLATE")
    if subject.get("repository") != args.repository or subject.get("base_commit") != args.base_commit or subject.get("base_tree") != args.base_tree:
        raise AdmissionError("CADG-FI-001", "packet repository/base does not match PR event")
    if pr.get("repository") != args.repository or pr.get("number") != args.pr_number or pr.get("head_branch") != args.head_branch:
        raise AdmissionError("CADG-FI-001", "packet PR identity does not match event")

    declared = sorted(set(str(x) for x in packet.get("delta", {}).get("paths", [])))
    undeclared = sorted(set(changed_code) - set(declared))
    stale_declared = sorted(set(declared) - set(changed_code))
    if undeclared or stale_declared:
        raise AdmissionError("CADG-FI-001", f"delta paths differ from PR code paths; undeclared={undeclared} stale={stale_declared}")
    excluded = [str(x) for x in subject.get("binding", {}).get("excluded_paths", [])]
    current_manifest, records = manifest(root, declared, excluded)
    expected_manifest = subject.get("binding", {}).get("code_manifest_digest")
    if current_manifest != expected_manifest:
        raise AdmissionError("CADG-FI-001", f"code manifest stale: expected={expected_manifest} actual={current_manifest}")

    for value, label in ((args.base_commit, "base commit"), (args.base_tree, "base tree"),
                         (args.head_commit, "head commit"), (args.head_tree, "head tree")):
        exact40(value, label)
    observed_head = git(root, "rev-parse", "HEAD")
    observed_tree = git(root, "rev-parse", "HEAD^{tree}")
    if (observed_head, observed_tree) != (args.head_commit, args.head_tree):
        raise AdmissionError("CADG-FI-001", "checked-out HEAD/tree differs from PR event")

    exact = {"repository": args.repository, "base_commit": args.base_commit, "base_tree": args.base_tree,
             "branch": args.head_branch, "head_commit": args.head_commit, "head_tree": args.head_tree}
    shadow_state = "NOT_EXERCISED"
    shadow_evidence = None
    if args.shadow_receipt:
        shadow_evidence = validate_shadow(args.shadow_receipt, exact)
        shadow_state = str(shadow_evidence.get("verdict", "HOLD"))
        if shadow_state not in {"READY_FOR_HUMAN_ADMIT", "HOLD", "REJECT"}:
            raise AdmissionError("CADG010", f"unknown Shadow verdict: {shadow_state}")

    human_state = "HUMAN_ADMIT_REQUIRED"
    if args.human_admission_ref:
        human_state = "HUMAN_ADMITTED"
    ceiling = packet.get("evidence_ceiling", {})
    expected_ceiling = {"deterministic": "PASS", "live": "NOT_EXERCISED",
                        "human": human_state, "release": "NOT_RELEASED"}
    if ceiling != expected_ceiling:
        raise AdmissionError("CADG010", f"packet evidence ceiling is not supported by this run: {ceiling}")

    receipt: dict[str, Any] = {
        "schema": "cadg-admission-receipt/v1",
        "receipt_id": f"CADG_PR_{args.pr_number}_{args.head_commit[:12].upper()}",
        "packet_id": packet["packet_id"],
        "packet_digest": canonical_digest(packet),
        "subject": exact,
        "code_manifest_digest": current_manifest,
        "validator": {"path": str(args.checker), "content_digest": file_digest(args.checker), "exit_code": 0},
        "operating_mode": operating_mode(policy),
        "transition_boundary": transition_boundary(args, policy),
        "code": args.code_state,
        "cadg": "PASS",
        "shadow": shadow_state,
        "human": human_state,
        "refusal_ids": [],
        "evidence_ceiling": ceiling,
        "manifest_records": records,
    }
    if shadow_evidence is not None:
        receipt["shadow_evidence"] = {key: shadow_evidence[key] for key in ("builder_identity", "reviewer_identity", "subject", "receipt_digest")}
    if args.human_admission_ref:
        receipt["human_admission_ref"] = args.human_admission_ref
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_bytes(canonical_bytes(receipt) + b"\n")
    print(f"CADG-PR-GREEN packet={packet['packet_id']} head={args.head_commit} mode={operating_mode(policy)} code={args.code_state} shadow={shadow_state} human={human_state}")
    return receipt


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, required=True)
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--changed-files", type=Path, required=True)
    p.add_argument("--checker", type=Path, required=True)
    p.add_argument("--packet", type=Path)
    p.add_argument("--shadow-receipt", type=Path)
    p.add_argument("--human-admission-ref")
    p.add_argument("--transition-boundary")
    p.add_argument("--repository", required=True)
    p.add_argument("--pr-number", type=int, required=True)
    p.add_argument("--base-commit", required=True)
    p.add_argument("--base-tree", required=True)
    p.add_argument("--head-commit", required=True)
    p.add_argument("--head-tree", required=True)
    p.add_argument("--head-branch", required=True)
    p.add_argument("--code-state", choices=["PASS", "FAIL", "NOT_EXERCISED"], default="NOT_EXERCISED")
    p.add_argument("--receipt-out", type=Path, required=True)
    return p


def main() -> int:
    try:
        admit(parser().parse_args())
        return 0
    except AdmissionError as exc:
        print(f"CADG-PR-RED {exc.code} {exc}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"CADG-PR-INVALID {exc}", file=sys.stderr)
        return 64
    except Exception as exc:
        print(f"CADG-PR-ERROR {exc}", file=sys.stderr)
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
