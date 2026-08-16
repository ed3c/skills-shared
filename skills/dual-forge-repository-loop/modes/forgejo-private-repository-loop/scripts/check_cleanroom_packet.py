#!/usr/bin/env python3
"""Validate a one-way clean-room requirements packet without exposing denied text."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

PASS = 0
FAIL = 2
ERROR = 64
SCHEMA = "forgejo-private-cleanroom-packet/v1"
KINDS = {
    "capability-contract",
    "state-machine",
    "generalized-invariant",
    "synthetic-negative-control",
    "sanitized-receipt-schema",
    "approved-public-reference",
}
PACKET_KEYS = {"schema", "packet_id", "private_subject_digest", "items"}
ITEM_KEYS = {"id", "kind", "statement", "assertions", "public_references"}
REFERENCE_KEYS = {"label", "url"}
ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
TOKEN = re.compile(r"[\w-]+", re.UNICODE)
SUSPICIOUS = [
    ("absolute-unix-path", re.compile(r"(?:^|[\s'\"])/(?:Users|home|private|var|tmp)/[^\s'\"]+", re.I)),
    ("absolute-windows-path", re.compile(r"\b[A-Za-z]:\\[^\s]+")),
    ("home-path", re.compile(r"~/[^\s]+")),
    ("file-url", re.compile(r"\bfile://", re.I)),
    ("git-transport", re.compile(r"\b(?:git@|ssh://|git://)", re.I)),
    ("patch-payload", re.compile(r"(?:^|\n)(?:diff --git |@@ |From [0-9a-f]{40}\b)", re.I)),
    ("git-sha1", re.compile(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])", re.I)),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("email-address", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("encoded-payload", re.compile(r"(?:[A-Za-z0-9+/]{180,}={0,2})")),
]


def normalized_tokens(text: str) -> list[str]:
    value = unicodedata.normalize("NFKC", text).casefold()
    return [item for item in TOKEN.findall(value) if len(item) >= 2]


def fingerprint_set(texts: list[str], size: int) -> set[str]:
    result: set[str] = set()
    for text in texts:
        words = normalized_tokens(text)
        for index in range(max(0, len(words) - size + 1)):
            value = "\x1f".join(words[index : index + size]).encode("utf-8")
            result.add(hashlib.sha256(value).hexdigest())
    return result


def load_patterns(path: Path | None) -> list[bytes]:
    if path is None:
        return []
    values: list[bytes] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        value = raw.strip()
        if value and not value.startswith("#"):
            values.append(value.casefold().encode("utf-8"))
    if not values:
        raise ValueError("private pattern file has no active entries")
    return values


def load_fingerprints(path: Path | None) -> tuple[int, set[str]]:
    if path is None:
        return 9, set()
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("schema") != "private-text-fingerprints/v1":
        raise ValueError("private fingerprint file has the wrong schema")
    size = document.get("shingle_size")
    values = document.get("fingerprints")
    if not isinstance(size, int) or not isinstance(values, list) or any(
        not isinstance(item, str) or not HEX64.fullmatch(item) for item in values
    ):
        raise ValueError("private fingerprint file is malformed")
    return size, set(values)


def public_url(value: str) -> bool:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    host = parsed.hostname.casefold()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return False
    try:
        address = ipaddress.ip_address(host)
        if not address.is_global:
            return False
    except ValueError:
        pass
    sensitive = {"token", "key", "secret", "auth", "authorization", "signature", "sig"}
    return not any(name.casefold() in sensitive for name, _ in parse_qsl(parsed.query))


def inspect_text(text: str, label: str, patterns: list[bytes], problems: list[str]) -> None:
    encoded = unicodedata.normalize("NFKC", text).casefold().encode("utf-8")
    for index, pattern in enumerate(patterns, start=1):
        if pattern in encoded:
            problems.append(f"{label}: private rule index {index} matched")
    for name, expression in SUSPICIOUS:
        if expression.search(text):
            problems.append(f"{label}: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--private-patterns", type=Path)
    parser.add_argument("--private-fingerprints", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        raw = args.packet.read_bytes()
        document = json.loads(raw)
        patterns = load_patterns(args.private_patterns)
        shingle_size, private_fingerprints = load_fingerprints(args.private_fingerprints)
        problems: list[str] = []
        texts: list[str] = []

        if not isinstance(document, dict) or set(document) != PACKET_KEYS:
            problems.append("packet fields must be exactly schema, packet_id, private_subject_digest, items")
        else:
            if document.get("schema") != SCHEMA:
                problems.append(f"schema must be {SCHEMA}")
            packet_id = document.get("packet_id")
            if not isinstance(packet_id, str) or not ID.fullmatch(packet_id):
                problems.append("packet_id is invalid")
            digest = document.get("private_subject_digest")
            if not isinstance(digest, str) or not HEX64.fullmatch(digest):
                problems.append("private_subject_digest must be lowercase SHA-256")
            items = document.get("items")
            if not isinstance(items, list) or not items:
                problems.append("items must be a non-empty array")
            else:
                seen: set[str] = set()
                for index, item in enumerate(items):
                    prefix = f"items[{index}]"
                    if not isinstance(item, dict) or set(item) != ITEM_KEYS:
                        problems.append(f"{prefix}: fields differ from the clean-room contract")
                        continue
                    item_id = item.get("id")
                    if not isinstance(item_id, str) or not ID.fullmatch(item_id):
                        problems.append(f"{prefix}.id is invalid")
                    elif item_id in seen:
                        problems.append(f"{prefix}.id is duplicated")
                    else:
                        seen.add(item_id)
                    if item.get("kind") not in KINDS:
                        problems.append(f"{prefix}.kind is not admitted")
                    statement = item.get("statement")
                    if not isinstance(statement, str) or not 1 <= len(statement) <= 4000:
                        problems.append(f"{prefix}.statement has invalid length")
                    else:
                        texts.append(statement)
                        inspect_text(statement, f"{prefix}.statement", patterns, problems)
                    assertions = item.get("assertions")
                    if not isinstance(assertions, list) or any(
                        not isinstance(value, str) or not 1 <= len(value) <= 1000
                        for value in assertions
                    ):
                        problems.append(f"{prefix}.assertions is malformed")
                    else:
                        for assertion_index, value in enumerate(assertions):
                            texts.append(value)
                            inspect_text(
                                value,
                                f"{prefix}.assertions[{assertion_index}]",
                                patterns,
                                problems,
                            )
                    references = item.get("public_references")
                    if not isinstance(references, list):
                        problems.append(f"{prefix}.public_references is malformed")
                    else:
                        for ref_index, reference in enumerate(references):
                            label = f"{prefix}.public_references[{ref_index}]"
                            if not isinstance(reference, dict) or set(reference) != REFERENCE_KEYS:
                                problems.append(f"{label}: fields differ from contract")
                                continue
                            ref_label = reference.get("label")
                            url = reference.get("url")
                            if not isinstance(ref_label, str) or not 1 <= len(ref_label) <= 160:
                                problems.append(f"{label}.label is invalid")
                            else:
                                texts.append(ref_label)
                                inspect_text(ref_label, f"{label}.label", patterns, problems)
                            if not isinstance(url, str) or not public_url(url):
                                problems.append(f"{label}.url is not an admitted public HTTPS URL")

        if private_fingerprints:
            overlap = fingerprint_set(texts, shingle_size) & private_fingerprints
            if overlap:
                problems.append(f"distinctive private text fingerprints matched: count={len(overlap)}")

        packet_sha = hashlib.sha256(raw).hexdigest()
        receipt = {
            "schema": "cleanroom-packet-verification/v1",
            "packet_sha256": packet_sha,
            "private_patterns_sha256": hashlib.sha256(args.private_patterns.read_bytes()).hexdigest()
            if args.private_patterns
            else None,
            "private_fingerprints_sha256": hashlib.sha256(args.private_fingerprints.read_bytes()).hexdigest()
            if args.private_fingerprints
            else None,
            "problem_count": len(problems),
            "problems": problems,
            "verdict": "FAIL" if problems else "PASS",
        }
        if args.receipt:
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        for problem in problems:
            print(f"FAIL {problem}", file=sys.stderr)
        if problems:
            print(f"CLEANROOM RED problems={len(problems)}", file=sys.stderr)
            return FAIL
        print(f"CLEANROOM GREEN packet_sha256={packet_sha}")
        return PASS
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"CLEANROOM ERROR: {error}", file=sys.stderr)
        return ERROR


if __name__ == "__main__":
    raise SystemExit(main())
