#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED = {
    "id", "title", "source_name", "source_type", "source_url", "canonical_url",
    "published_at", "monetization_score", "monetization_modes", "note_status",
    "note_version", "language", "technical_terms_language", "categories",
    "mapping_targets", "github_path", "legacy_google_doc_id",
    "legacy_google_doc_url", "citation_mapping_status",
}


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated YAML frontmatter")
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    note_root = root / "notes"
    errors: list[str] = []
    seen_ids: dict[str, Path] = {}
    seen_urls: dict[str, Path] = {}
    files = sorted(note_root.rglob("*.md"))
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
            meta = parse_frontmatter(text)
        except Exception as exc:
            errors.append(f"{path}: {exc}")
            continue
        missing = sorted(REQUIRED - set(meta))
        if missing:
            errors.append(f"{path}: missing {', '.join(missing)}")
        note_id = meta.get("id", "").strip('"')
        canonical = meta.get("canonical_url", "").strip('"')
        if note_id in seen_ids:
            errors.append(f"{path}: duplicate id with {seen_ids[note_id]}")
        else:
            seen_ids[note_id] = path
        if canonical in seen_urls:
            errors.append(f"{path}: duplicate canonical_url with {seen_urls[canonical]}")
        else:
            seen_urls[canonical] = path
        try:
            score = int(meta.get("monetization_score", "0"))
            if not 1 <= score <= 100:
                errors.append(f"{path}: monetization_score outside 1..100")
        except ValueError:
            errors.append(f"{path}: monetization_score is not an integer")
        expected = "ai-content-note/" + path.relative_to(root).as_posix()
        actual = meta.get("github_path", "").strip('"')
        if actual != expected:
            errors.append(f"{path}: github_path={actual!r}, expected {expected!r}")
        if meta.get("note_status") == "completed" and not text[text.find("\n---\n", 4) + 5:].strip():
            errors.append(f"{path}: completed note has empty body")
        if "docs.google.com" in actual:
            errors.append(f"{path}: primary github_path points to Google Docs")
    if errors:
        print("FAIL")
        print("\n".join(f"- {e}" for e in errors))
        return 1
    print(f"PASS: {len(files)} notes; unique IDs and canonical URLs; paths valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
