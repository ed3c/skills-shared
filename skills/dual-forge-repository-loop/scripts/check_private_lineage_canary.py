#!/usr/bin/env python3
"""Validate a #262 private-lineage live canary receipt. Zero network, no forge.

The producer runs against a live Forgejo; this runs against what it wrote. Three
laws carry the weight, and each exists because the honest receipt and the
flattering one are otherwise the same document:

* A provider lane may only be PASS with the wire evidence that proves it. A
  deletion is PASS when the receipt holds both the 204 and the follow-up 404;
  without the 404 the receipt claims erasure it never observed, which is the one
  thing `check_provider_retention.py` refuses on the provider side.
* Every provider mutation must name a repository this canary created. A receipt
  that certifies a mutation of an existing repository is not a stricter receipt,
  it is a different and forbidden run.
* Every mutation must reach a terminal cleanup before the cleanup lane may be
  PASS. Created-and-forgotten and created-and-deleted otherwise read alike.

Exit codes: 0 pass, 2 receipt failure, 64 unusable input, 70 evaluator defect.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "dual-forge-repository-loop/private-lineage-canary-receipt/v1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
# The throwaway namespace this canary is allowed to create and destroy.
THROWAWAY = re.compile(r"^[A-Za-z0-9_.-]+/canary-\d+-private-\d+(@refs/heads/[\w./-]+)?$")
STATES = {"PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED",
          "SKIPPED_BY_POLICY", "HUMAN_ADMIT_REQUIRED"}
OBSERVED = {"PASS", "FAIL", "ABSENT"}
PROVIDER_LANES = {"private-repository-created", "private-main-sealed",
                  "provider-cleanup-disposition"}
SECRET = re.compile(r"(gh[pousr]_[A-Za-z0-9]{16,}|sk-[A-Za-z0-9]{20,}"
                    r"|://[^/\s:]+:[^/\s@]+@)")


class Refused(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def refuse(code: str, detail: str) -> None:
    raise Refused(code, detail)


def check_shape(body: Any) -> None:
    if not isinstance(body, dict) or body.get("schema") != SCHEMA:
        refuse("RECEIPT_MALFORMED", f"schema must be {SCHEMA}")
    for section in ("forge", "subject", "chain", "chain_declared", "coverage",
                    "mutations_performed", "declared_non_claims", "dry_run"):
        if section not in body:
            refuse("RECEIPT_MALFORMED", f"receipt has no {section}")
    forge = body["forge"]
    if not isinstance(forge, dict) or not forge.get("url") or not forge.get("version"):
        refuse("RECEIPT_MALFORMED", "forge identity needs both a URL and an observed version")
    subject = body["subject"]
    if not isinstance(subject, dict) or not SHA40.fullmatch(str(subject.get("head", ""))):
        refuse("RECEIPT_MALFORMED", "subject.head must be an exact 40-hex commit")
    if not SHA256.fullmatch(str(subject.get("identity_digest", ""))):
        refuse("RECEIPT_MALFORMED", "subject.identity_digest must be lowercase SHA-256")


def check_links(body: dict[str, Any]) -> None:
    declared = body["chain_declared"]
    if not isinstance(declared, list) or not declared:
        refuse("RECEIPT_MALFORMED", "chain_declared is empty")
    seen: dict[str, str] = {}
    for entry in body["chain"]:
        name = entry.get("link")
        if name not in declared:
            refuse("LINK_COVERAGE_INCOMPLETE", f"chain records unknown link {name!r}")
        if name in seen:
            refuse("LINK_COVERAGE_INCOMPLETE", f"link {name} recorded twice")
        if entry.get("state") not in STATES:
            refuse("LINK_COVERAGE_INCOMPLETE",
                   f"link {name} state {entry.get('state')!r} is not admitted")
        if not str(entry.get("detail", "")).strip():
            refuse("LINK_COVERAGE_INCOMPLETE", f"link {name} carries no detail")
        seen[name] = entry["state"]
    missing = [name for name in declared if name not in seen]
    if missing:
        refuse("LINK_COVERAGE_INCOMPLETE",
               f"the chain declares {len(declared)} links and the receipt states "
               f"{len(seen)}; unstated: {missing}")
    if "FAIL" in seen.values():
        refuse("LINK_FAILED",
               f"link(s) reported FAIL: {sorted(k for k, v in seen.items() if v == 'FAIL')}")


def check_coverage(body: dict[str, Any]) -> None:
    chain = body["chain"]
    computed = {
        "pass": sorted(item["link"] for item in chain if item["state"] == "PASS"),
        "not_exercised": sorted(item["link"] for item in chain
                                if item["state"] == "NOT_EXERCISED"),
    }
    for key, value in computed.items():
        if body["coverage"].get(key) != value:
            refuse("COVERAGE_MISREPORTED",
                   f"coverage.{key} does not match the chain; the chain gives {value}")


def check_observed_evidence(body: dict[str, Any]) -> None:
    """An observed state needs a replay pointer; a bare assertion is not evidence."""
    for entry in body["chain"]:
        if entry["state"] not in OBSERVED:
            continue
        evidence = {k: v for k, v in entry.items()
                    if k not in {"link", "state", "detail"} and v not in (None, "", [], {})}
        if not evidence:
            refuse("OBSERVED_WITHOUT_EVIDENCE",
                   f"{entry['link']} is {entry['state']} with no recorded observation")
        for record in entry.get("commands", []):
            if not isinstance(record, dict) or not isinstance(record.get("exit_code"), int):
                refuse("OBSERVED_WITHOUT_EVIDENCE",
                       f"{entry['link']} records a command with no exit code")
            if not record.get("argv"):
                refuse("OBSERVED_WITHOUT_EVIDENCE",
                       f"{entry['link']} records an exit code with no command behind it")


def link_of(body: dict[str, Any], name: str) -> dict[str, Any]:
    for entry in body["chain"]:
        if entry["link"] == name:
            return entry
    return {}


def check_wire_evidence(body: dict[str, Any]) -> None:
    """The provider lanes are PASS only with the exact wire result behind them."""
    if body["dry_run"]:
        claimed = [name for name in PROVIDER_LANES if link_of(body, name).get("state") == "PASS"]
        if claimed:
            refuse("DRY_RUN_CLAIMS_MUTATION",
                   f"dry_run receipt claims PASS on provider lane(s) {sorted(claimed)}")
        return

    created = link_of(body, "private-repository-created")
    if created.get("state") == "PASS":
        request = created.get("request") or {}
        if request.get("method") != "POST" or request.get("http_status") != 201:
            refuse("WIRE_EVIDENCE_MISSING",
                   "repository creation is PASS without an observed 201 POST")
        if body["subject"].get("private") is not True:
            refuse("WIRE_EVIDENCE_MISSING", "the canary subject is not recorded as private")

    sealed = link_of(body, "private-main-sealed")
    if sealed.get("state") == "PASS":
        request = sealed.get("request") or {}
        if request.get("http_status") != 200:
            refuse("WIRE_EVIDENCE_MISSING",
                   "the sealed main lane is PASS without an authenticated 200 readback")
        if sealed.get("head") != body["subject"]["head"]:
            refuse("WIRE_EVIDENCE_MISSING",
                   "the readback head differs from the receipted subject head")

    cleanup = link_of(body, "provider-cleanup-disposition")
    if cleanup.get("state") == "PASS":
        statuses = [item.get("http_status") for item in cleanup.get("requests", [])]
        if 204 not in statuses:
            refuse("DELETION_NOT_OBSERVED",
                   "cleanup is PASS without an observed 204 deletion")
        if 404 not in statuses:
            refuse("DELETION_NOT_OBSERVED",
                   "cleanup is PASS without the follow-up 404; deleting and confirming "
                   "the absence are two different observations")


def check_mutations(body: dict[str, Any]) -> None:
    mutations = body["mutations_performed"]
    if not isinstance(mutations, list):
        refuse("RECEIPT_MALFORMED", "mutations_performed must be a list")
    for record in mutations:
        if not isinstance(record, dict) or not record.get("subject") or not record.get("purpose"):
            refuse("MUTATION_UNACCOUNTED", "a mutation carries no subject or no purpose")
        if not THROWAWAY.fullmatch(str(record["subject"])):
            refuse("MUTATION_OUTSIDE_THROWAWAY_NAMESPACE",
                   f"{record['subject']!r} is not a repository this canary created; "
                   "existing repositories are never this run's to mutate")
        if not record.get("cleanup"):
            refuse("MUTATION_UNACCOUNTED", f"{record['subject']} records no cleanup disposition")

    if link_of(body, "provider-cleanup-disposition").get("state") == "PASS":
        outstanding = [item["subject"] for item in mutations if item.get("cleanup") != "DELETED"]
        if outstanding:
            refuse("CLEANUP_INCOMPLETE",
                   f"cleanup is PASS while {outstanding} are still owed deletion")
    created = link_of(body, "private-repository-created").get("state")
    if created == "PASS" and not mutations:
        refuse("MUTATION_UNACCOUNTED",
               "a repository was created and the mutation ledger is empty")


def check_lineage(body: dict[str, Any]) -> None:
    entry = link_of(body, "fresh-root-verified")
    if entry.get("state") != "PASS":
        return
    fresh = entry.get("fresh_root_head")
    if not SHA40.fullmatch(str(fresh or "")):
        refuse("LINEAGE_UNPROVEN", "the fresh root lane records no exact root commit")
    if fresh == body["subject"]["head"]:
        refuse("LINEAGE_UNPROVEN",
               "the fresh root head equals the private head; that is one lineage, not two")
    if not entry.get("commands"):
        refuse("LINEAGE_UNPROVEN", "the fresh root lane records no executed assertion")


def check_secrets(body: Any, path: str = "") -> None:
    if isinstance(body, dict):
        for key, value in body.items():
            check_secrets(value, f"{path}.{key}")
    elif isinstance(body, list):
        for index, value in enumerate(body):
            check_secrets(value, f"{path}[{index}]")
    elif isinstance(body, str) and SECRET.search(body):
        refuse("SECRET_IN_RECEIPT", f"credential-shaped value at {path}")


CHECKS = (check_links, check_coverage, check_observed_evidence, check_wire_evidence,
          check_mutations, check_lineage)


def validate(body: Any) -> None:
    check_shape(body)
    check_secrets(body)
    for check in CHECKS:
        check(body)


def recompute_coverage(doc: dict[str, Any]) -> None:
    chain = doc["chain"]
    doc["coverage"]["pass"] = sorted(i["link"] for i in chain if i["state"] == "PASS")
    doc["coverage"]["not_exercised"] = sorted(
        i["link"] for i in chain if i["state"] == "NOT_EXERCISED")


def selftest(body: dict[str, Any]) -> int:
    try:
        validate(body)
    except Refused as failure:
        print(f"SELFTEST RED: committed receipt already refused -- {failure}", file=sys.stderr)
        return 2

    def mutate(fn: Any) -> dict[str, Any]:
        copied = copy.deepcopy(body)
        fn(copied)
        return copied

    def drop_link(doc: dict[str, Any]) -> None:
        doc["chain"] = [i for i in doc["chain"] if i["link"] != "fresh-root-verified"]
        recompute_coverage(doc)

    def drop_404(doc: dict[str, Any]) -> None:
        entry = link_of(doc, "provider-cleanup-disposition")
        entry["requests"] = [r for r in entry.get("requests", []) if r.get("http_status") != 404]

    def forget_deletion(doc: dict[str, Any]) -> None:
        for record in doc["mutations_performed"]:
            record["cleanup"] = "delete-in-this-run"

    def mutate_existing_repository(doc: dict[str, Any]) -> None:
        doc["mutations_performed"][0]["subject"] = "neon/skills-shared"

    def strip_evidence(doc: dict[str, Any]) -> None:
        entry = link_of(doc, "private-main-sealed")
        for key in list(entry):
            if key not in {"link", "state", "detail"}:
                entry.pop(key)

    def same_lineage(doc: dict[str, Any]) -> None:
        link_of(doc, "fresh-root-verified")["fresh_root_head"] = doc["subject"]["head"]

    def dry_run_claim(doc: dict[str, Any]) -> None:
        doc["dry_run"] = True

    controls = [
        ("link-omitted", "LINK_COVERAGE_INCOMPLETE", mutate(drop_link)),
        ("link-state-invented", "LINK_COVERAGE_INCOMPLETE",
         mutate(lambda d: d["chain"][0].update({"state": "MOSTLY_DONE"}))),
        ("coverage-inflated", "COVERAGE_MISREPORTED",
         mutate(lambda d: d["coverage"].update({"pass": d["chain_declared"]}))),
        ("sealed-without-evidence", "OBSERVED_WITHOUT_EVIDENCE", mutate(strip_evidence)),
        ("creation-without-201", "WIRE_EVIDENCE_MISSING",
         mutate(lambda d: link_of(d, "private-repository-created")["request"]
                .update({"http_status": 200}))),
        ("readback-head-substituted", "WIRE_EVIDENCE_MISSING",
         mutate(lambda d: link_of(d, "private-main-sealed")
                .update({"head": "0" * 40}))),
        ("deletion-unconfirmed", "DELETION_NOT_OBSERVED", mutate(drop_404)),
        ("cleanup-claimed-while-owed", "CLEANUP_INCOMPLETE", mutate(forget_deletion)),
        ("existing-repository-mutated", "MUTATION_OUTSIDE_THROWAWAY_NAMESPACE",
         mutate(mutate_existing_repository)),
        ("fresh-root-is-private-head", "LINEAGE_UNPROVEN", mutate(same_lineage)),
        ("dry-run-claims-provider-pass", "DRY_RUN_CLAIMS_MUTATION", mutate(dry_run_claim)),
        ("credential-in-receipt", "SECRET_IN_RECEIPT",
         mutate(lambda d: d["forge"].update(
             {"url": "http://user:hunter2@127.0.0.1:3000"}))),
    ]

    failed = 0
    for name, code, doc in controls:
        try:
            validate(doc)
        except Refused as failure:
            if failure.code == code:
                print(f"REFUSED {code} ({name})")
                continue
            print(f"CONTROL FAILED {name}: expected {code}, got {failure.code}", file=sys.stderr)
            failed += 1
            continue
        print(f"CONTROL FAILED {name}: expected {code}, nothing was refused", file=sys.stderr)
        failed += 1

    if failed:
        return 2
    print(f"SELFTEST GREEN: committed private-lineage canary admitted; "
          f"{len(controls)} planted defects refused")
    return 0


def main(argv: list[str] | None = None) -> int:
    default = (Path(__file__).resolve().parent.parent / "evals" / "receipts"
               / "private-lineage-canary.receipt.json")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", nargs="?", default="check", choices=["check", "selftest"])
    parser.add_argument("--receipt", type=Path, default=default)
    args = parser.parse_args(argv)

    try:
        body = json.loads(args.receipt.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"USAGE: {error}", file=sys.stderr)
        return 64
    except json.JSONDecodeError as error:
        print(f"USAGE: unparseable receipt: {error}", file=sys.stderr)
        return 64

    if args.mode == "selftest":
        return selftest(body)

    try:
        validate(body)
    except Refused as failure:
        print(f"PRIVATE-LINEAGE CANARY REFUSED {failure.code}: {failure.detail}", file=sys.stderr)
        return 2
    except Exception as error:  # noqa: BLE001 - an evaluator defect is not a receipt defect
        print(f"EVALUATOR FAILURE: {error!r}", file=sys.stderr)
        return 70

    coverage = body["coverage"]
    print(f"PRIVATE-LINEAGE CANARY GREEN: {body['subject']['repository']} on "
          f"Forgejo {body['forge']['version']}; {len(coverage['pass'])} of "
          f"{len(body['chain_declared'])} links PASS, "
          f"{len(body['mutations_performed'])} provider mutation(s) all deleted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
