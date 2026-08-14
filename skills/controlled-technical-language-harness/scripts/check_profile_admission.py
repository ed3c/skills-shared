#!/usr/bin/env python3
"""Admission controls for controlled-language profiles.

The contract checker in `scripts/check_controlled_language_contracts.py` proves
a pack is *shaped* correctly. It cannot prove the pack is *honest*: a
proposal-derived approximation can satisfy every field while calling itself an
official standard edition, which is the one claim that would matter to a reader
deciding whether the output means compliance.

These controls sit above the schema and refuse that promotion.

Exits: 0 admitted, 2 refused, 64 usage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

# Designations that name a real external standard edition. A pack may use one
# only when it can produce that standard as a verified official source.
OFFICIAL_EDITION_MARKERS = (
    re.compile(r"\bASD[-\s]?STE\s?100\b", re.IGNORECASE),
    re.compile(r"\bissue\s+\d+\b", re.IGNORECASE),
    re.compile(r"\bASD\b"),
    re.compile(r"\bS1000D\b", re.IGNORECASE),
)

MUTABLE_EDITION_MARKERS = (
    re.compile(r"\blatest\b", re.IGNORECASE),
    re.compile(r"\bcurrent\b", re.IGNORECASE),
    re.compile(r"\bnewest\b", re.IGNORECASE),
    re.compile(r"\brolling\b", re.IGNORECASE),
    re.compile(r"\bHEAD\b"),
)


class Refused(Exception):
    pass


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise Refused(f"absent: {path}") from error
    except json.JSONDecodeError as error:
        raise Refused(f"unparseable JSON: {path}: {error}") from error


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def check_edition_identity(pack: dict[str, Any]) -> None:
    edition = pack["edition"]
    for marker in MUTABLE_EDITION_MARKERS:
        if marker.search(edition):
            raise Refused(
                f"edition {edition!r} is mutable; an edition must name one "
                f"immutable revision, or the pack silently changes meaning"
            )


def check_no_proposal_claiming_official(pack: dict[str, Any]) -> None:
    """The control this module exists for.

    A pack whose source is a proposal must not present itself as an official
    standard, in either its edition or its display name.
    """
    classification = pack["source"]["classification"]
    if classification == "OFFICIAL_STANDARD":
        return

    for field in ("edition", "display_name", "pack_id"):
        value = str(pack[field])
        for marker in OFFICIAL_EDITION_MARKERS:
            match = marker.search(value)
            if match:
                raise Refused(
                    f"{field} {value!r} names the official designation "
                    f"{match.group(0)!r}, but source.classification is "
                    f"{classification}. Obtain the official artifact and record "
                    f"its locator and digest, or keep the approximation's own name"
                )

    if pack["source"]["authority"].strip().upper() in {"ASD", "ASD-STE100"}:
        raise Refused(
            f"source.authority claims the standards body while "
            f"classification is {classification}"
        )


def check_official_pack_is_complete(pack: dict[str, Any]) -> None:
    """An OFFICIAL_STANDARD pack must carry what makes it official."""
    if pack["source"]["classification"] != "OFFICIAL_STANDARD":
        return
    source = pack["source"]
    if not source["locator"].startswith(("http://", "https://")):
        raise Refused(
            f"official pack locator {source['locator']!r} is not a resolvable "
            f"URL; an official claim needs a source a reader can reach"
        )
    license_policy = pack["license_policy"]
    if pack["content_mode"] == "VENDORED":
        if not license_policy["redistribution_allowed"]:
            raise Refused(
                "content_mode VENDORED commits the standard's bytes while "
                "redistribution_allowed is false"
            )
        if license_policy["human_legal_review"] != "ADMITTED":
            raise Refused(
                "content_mode VENDORED requires human_legal_review ADMITTED, "
                f"found {license_policy['human_legal_review']}"
            )
    if license_policy["classification"] == "UNKNOWN":
        raise Refused(
            "an official pack cannot leave license classification UNKNOWN"
        )


def check_human_boundaries(pack: dict[str, Any]) -> None:
    policy = pack["technical_terminology_policy"]
    if policy["technical_name_human_admit"] is not True:
        raise Refused("technical_name_human_admit must remain true")
    if policy["technical_verb_human_admit"] is not True:
        raise Refused("technical_verb_human_admit must remain true")
    if pack["compliance_claim_policy"] != "HUMAN_ADMIT_REQUIRED":
        raise Refused("compliance_claim_policy must remain HUMAN_ADMIT_REQUIRED")


def check_ruleset_binding(pack: dict[str, Any], root: Path) -> None:
    ruleset = root / "evals" / f"{pack['pack_id']}.rules.json"
    if not ruleset.is_file():
        raise Refused(
            f"pack {pack['pack_id']} declares a ruleset digest but "
            f"{ruleset.name} is absent; a digest of nothing proves nothing"
        )
    actual = sha256_of(ruleset)
    if actual != pack["ruleset_digest"]:
        raise Refused(
            f"ruleset_digest {pack['ruleset_digest']} does not match "
            f"{ruleset.name} ({actual}); the pack is bound to a ruleset it does "
            f"not have"
        )
    body = load(ruleset)
    if body.get("provenance") != pack["source"]["classification"]:
        raise Refused(
            f"ruleset provenance {body.get('provenance')!r} contradicts pack "
            f"source classification {pack['source']['classification']!r}"
        )


def check_profile_is_optional(root: Path) -> None:
    """A profile must stay trigger-selected, never a core dependency."""
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    if "PROFILE_ABSENT" not in skill:
        raise Refused(
            "SKILL.md does not name PROFILE_ABSENT; without it the core cannot "
            "report running with no profile and a profile becomes mandatory"
        )
    for module in sorted((root / "modules").glob("profile-*.md")):
        text = module.read_text(encoding="utf-8")
        if "## Trigger" not in text:
            raise Refused(
                f"{module.name} has no Trigger section, so nothing states when "
                f"it must not be loaded"
            )


def check_module_does_not_weaken_core(root: Path) -> None:
    """A module may add constraints; it may not relax the core's laws."""
    forbidden = (
        (re.compile(r"human[_\s-]?admit\s*(?:=|:)?\s*(?:false|not required)", re.IGNORECASE),
         "a module relaxes Human Admit"),
        (re.compile(r"skip\s+(?:the\s+)?deterministic", re.IGNORECASE),
         "a module skips the deterministic lane"),
        (re.compile(r"advisory\s+(?:result\s+)?overrides?\s+deterministic", re.IGNORECASE),
         "a module lets advisory output override a deterministic result"),
        (re.compile(r"send\s+(?:the\s+)?(?:full\s+)?document\s+to\s+(?:any|an?y)\s+provider", re.IGNORECASE),
         "a module widens the privacy lane"),
    )
    for module in sorted((root / "modules").glob("*.md")):
        text = module.read_text(encoding="utf-8")
        for pattern, why in forbidden:
            if pattern.search(text):
                raise Refused(f"{module.name}: {why}")


def check_no_official_bytes_committed(root: Path) -> None:
    """Official or proprietary content must not be committed unadmitted."""
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".pdf", ".doc", ".docx", ".xls", ".xlsx"}:
            raise Refused(
                f"{path.relative_to(root)} looks like a committed standard or "
                f"vocabulary artifact; official bytes require an admitted "
                f"redistribution grant"
            )


def admit(pack_path: Path, root: Path) -> None:
    pack = load(pack_path)
    for field in ("edition", "display_name", "pack_id", "source",
                  "license_policy", "content_mode", "ruleset_digest",
                  "technical_terminology_policy", "compliance_claim_policy"):
        if field not in pack:
            raise Refused(f"pack is missing required field {field!r}")
    check_edition_identity(pack)
    check_no_proposal_claiming_official(pack)
    check_official_pack_is_complete(pack)
    check_human_boundaries(pack)
    check_ruleset_binding(pack, root)
    check_profile_is_optional(root)
    check_module_does_not_weaken_core(root)
    check_no_official_bytes_committed(root)


def _mutations() -> list[tuple[str, Any]]:
    """(name, apply) pairs. Each must make admission refuse.

    One per control #118 requires, so a control that stops biting is visible
    here rather than only in review.
    """

    def edition(value: str):
        def apply(root: Path, pack: dict[str, Any]) -> None:
            pack["edition"] = value
        return apply

    def display_name(value: str):
        def apply(root: Path, pack: dict[str, Any]) -> None:
            pack["display_name"] = value
        return apply

    def authority(value: str):
        def apply(root: Path, pack: dict[str, Any]) -> None:
            pack["source"]["authority"] = value
        return apply

    def official_without_artifact(root: Path, pack: dict[str, Any]) -> None:
        pack["source"]["classification"] = "OFFICIAL_STANDARD"
        pack["source"]["locator"] = "google-drive:1vqFNBQmCwh9xgziZxlO0oYk6fZQg9rQ_"

    def vendored_without_grant(root: Path, pack: dict[str, Any]) -> None:
        pack["source"]["classification"] = "OFFICIAL_STANDARD"
        pack["source"]["locator"] = "https://asd-ste100.org/"
        pack["license_policy"]["classification"] = "RESTRICTED"
        pack["content_mode"] = "VENDORED"

    def relax_name_admit(root: Path, pack: dict[str, Any]) -> None:
        pack["technical_terminology_policy"]["technical_name_human_admit"] = False

    def relax_compliance(root: Path, pack: dict[str, Any]) -> None:
        pack["compliance_claim_policy"] = "AUTOMATIC"

    def ruleset_drift(root: Path, pack: dict[str, Any]) -> None:
        ruleset = root / "evals" / f"{pack['pack_id']}.rules.json"
        body = json.loads(ruleset.read_text(encoding="utf-8"))
        body["rules"].append({"id": "STE-P-99", "statement": "added quietly",
                              "lane": "deterministic", "implemented_by": None})
        ruleset.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")

    def ruleset_provenance_lie(root: Path, pack: dict[str, Any]) -> None:
        ruleset = root / "evals" / f"{pack['pack_id']}.rules.json"
        body = json.loads(ruleset.read_text(encoding="utf-8"))
        body["provenance"] = "OFFICIAL_STANDARD"
        payload = json.dumps(body, indent=2) + "\n"
        ruleset.write_text(payload, encoding="utf-8")
        pack["ruleset_digest"] = (
            "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
        )

    def profile_becomes_mandatory(root: Path, pack: dict[str, Any]) -> None:
        skill = root / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8").replace("PROFILE_ABSENT", "PROFILE_READY"),
            encoding="utf-8",
        )

    def module_loses_trigger(root: Path, pack: dict[str, Any]) -> None:
        module = root / "modules" / "profile-ste.md"
        module.write_text(
            module.read_text(encoding="utf-8").replace("## Trigger", "## Notes"),
            encoding="utf-8",
        )

    def module_relaxes_human_admit(root: Path, pack: dict[str, Any]) -> None:
        module = root / "modules" / "profile-ste.md"
        with module.open("a", encoding="utf-8") as handle:
            handle.write("\nFor speed, human admit = false on routine terms.\n")

    def module_widens_privacy(root: Path, pack: dict[str, Any]) -> None:
        module = root / "modules" / "profile-ste.md"
        with module.open("a", encoding="utf-8") as handle:
            handle.write("\nWhen in doubt, send the full document to any provider.\n")

    def official_bytes_committed(root: Path, pack: dict[str, Any]) -> None:
        (root / "references").mkdir(exist_ok=True)
        (root / "references" / "ASD-STE100-Issue9.pdf").write_bytes(b"%PDF-1.4 fake\n")

    return [
        ("mutable edition", edition("latest")),
        ("official designation in edition", edition("ASD-STE100 Issue 9")),
        ("official designation in display name",
         display_name("ASD-STE100 Simplified Technical English")),
        ("standards body claimed as authority", authority("ASD")),
        ("official claim without a resolvable source", official_without_artifact),
        ("vendored bytes without a redistribution grant", vendored_without_grant),
        ("technical name admit relaxed", relax_name_admit),
        ("compliance claim automated", relax_compliance),
        ("ruleset changed without rebinding the digest", ruleset_drift),
        ("ruleset provenance contradicts the pack", ruleset_provenance_lie),
        ("profile made a mandatory core dependency", profile_becomes_mandatory),
        ("profile module without a trigger boundary", module_loses_trigger),
        ("module relaxes Human Admit", module_relaxes_human_admit),
        ("module widens the privacy lane", module_widens_privacy),
        ("official bytes committed", official_bytes_committed),
    ]


def selftest(root: Path) -> int:
    import shutil
    import tempfile

    packs = sorted((root / "evals").glob("standard-pack-*.json"))
    if not packs:
        print("SELFTEST RED: no pack to mutate", file=sys.stderr)
        return 2

    try:
        for pack_path in packs:
            admit(pack_path, root)
    except Refused as error:
        print(f"SELFTEST RED: canonical pack is refused: {error}", file=sys.stderr)
        return 2

    survived: list[str] = []
    for name, apply in _mutations():
        with tempfile.TemporaryDirectory(prefix="ctl-profile.") as raw:
            sandbox = Path(raw) / "skill"
            shutil.copytree(root, sandbox)
            target = sandbox / "evals" / packs[0].name
            pack = json.loads(target.read_text(encoding="utf-8"))
            apply(sandbox, pack)
            target.write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
            try:
                admit(target, sandbox)
            except Refused:
                continue
            survived.append(name)

    if survived:
        for name in survived:
            print(f"SELFTEST RED: mutation survived: {name}", file=sys.stderr)
        return 2

    print(
        f"SELFTEST GREEN: canonical pack admitted; "
        f"{len(_mutations())} mutations refused"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True,
                        help="the Skill directory")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--pack", type=Path, action="append", default=None,
                        help="pack reference to admit; repeatable")
    args = parser.parse_args()

    root = args.root.resolve()
    if not (root / "SKILL.md").is_file():
        print(f"PROFILE ADMISSION RED: no SKILL.md under {root}", file=sys.stderr)
        return 64

    if args.selftest:
        return selftest(root)

    packs = args.pack or sorted((root / "evals").glob("standard-pack-*.json"))
    if not packs:
        print("PROFILE ADMISSION RED: no pack references found", file=sys.stderr)
        return 2

    failed = False
    for pack_path in packs:
        try:
            admit(Path(pack_path), root)
        except Refused as error:
            failed = True
            print(f"PROFILE ADMISSION RED: {Path(pack_path).name}: {error}",
                  file=sys.stderr)
    if failed:
        return 2
    print(f"PROFILE ADMISSION GREEN: {len(packs)} pack(s) admitted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
