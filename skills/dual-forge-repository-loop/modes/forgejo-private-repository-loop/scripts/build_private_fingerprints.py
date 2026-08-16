#!/usr/bin/env python3
"""Build a local-only hashed shingle set for clean-room copy detection."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

TOKEN = re.compile(r"[\w-]+", re.UNICODE)


def tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return [item for item in TOKEN.findall(normalized) if len(item) >= 2]


def shingles(words: list[str], size: int) -> set[str]:
    if len(words) < size:
        return set()
    return {
        hashlib.sha256("\x1f".join(words[index : index + size]).encode("utf-8")).hexdigest()
        for index in range(len(words) - size + 1)
    }


def source_files(root: Path, max_bytes: int) -> list[Path]:
    candidates = [root] if root.is_file() else sorted(root.rglob("*"))
    result: list[Path] = []
    for path in candidates:
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            if path.stat().st_size > max_bytes:
                continue
            data = path.read_bytes()
        except OSError:
            continue
        if b"\x00" in data:
            continue
        result.append(path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--shingle-size", type=int, default=9)
    parser.add_argument("--max-bytes", type=int, default=4 * 1024 * 1024)
    args = parser.parse_args()
    if args.shingle_size < 5 or args.shingle_size > 20:
        parser.error("--shingle-size must be between 5 and 20")
    root = args.source.resolve()
    files = source_files(root, args.max_bytes)
    all_fingerprints: set[str] = set()
    source_hash = hashlib.sha256()
    for path in files:
        data = path.read_bytes()
        source_hash.update(hashlib.sha256(data).digest())
        text = data.decode("utf-8", "replace")
        all_fingerprints.update(shingles(tokens(text), args.shingle_size))
    document = {
        "schema": "private-text-fingerprints/v1",
        "shingle_size": args.shingle_size,
        "source_file_count": len(files),
        "source_digest": source_hash.hexdigest(),
        "fingerprints": sorted(all_fingerprints),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"PRIVATE-FINGERPRINTS files={len(files)} count={len(all_fingerprints)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
