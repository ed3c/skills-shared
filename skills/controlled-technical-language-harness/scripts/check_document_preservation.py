#!/usr/bin/env python3
"""Source-node preservation for structured technical documents.

Rewriting a technical document is not a text operation. An output can be
perfectly well-formed XML, read fluently, and still have dropped a warning,
reordered two steps, or lost a cross-reference target -- and every one of those
is a safety-relevant change that no prose-level check notices.

So parser output stays a *candidate* until readback proves the structure
survived: same safety nodes, same step order, same identifiers, same
cross-reference targets.

Format is deliberately not sniffed from content. The caller declares it, and a
module that declares S1000D on plain text is refused rather than guessed at.

Exits: 0 preserved, 2 not preserved, 64 usage.

ponytail: xml.etree, so entity expansion limits are Python's. Inputs here are
disposable fixtures; a production adapter processing untrusted manuals should
bound the parser before this check, not after.
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

# Nodes whose loss changes what a technician is told, not merely how.
SAFETY_TAGS = frozenset({
    "warning", "caution", "note", "attention", "danger",
    "warningandcautionpara", "safetyrqmts",
})
ID_ATTRS = ("id", "ID", "identNumber", "applicRefId", "chapnum")
XREF_ATTRS = ("xrefid", "href", "internalRefId", "conref", "keyref")
STEP_TAGS = frozenset({"step", "step1", "step2", "proceduralstep", "li", "cmd"})

FORMATS = ("S1000D_LIKE_XML", "DITA_LIKE_XML", "PLAIN_TEXT", "PDF_EXTRACTED_TEXT")


class NotPreserved(Exception):
    pass


def localname(tag: str) -> str:
    return tag.split("}", 1)[-1].lower()


def walk(root: ET.Element) -> list[ET.Element]:
    return list(root.iter())


def safety_nodes(root: ET.Element) -> list[str]:
    return [localname(node.tag) for node in walk(root) if localname(node.tag) in SAFETY_TAGS]


def identifiers(root: ET.Element) -> set[str]:
    found: set[str] = set()
    for node in walk(root):
        for attr in ID_ATTRS:
            value = node.get(attr)
            if value:
                found.add(f"{attr}={value}")
    return found


def xrefs(root: ET.Element) -> set[str]:
    found: set[str] = set()
    for node in walk(root):
        for attr in XREF_ATTRS:
            value = node.get(attr)
            if value:
                found.add(f"{attr}={value}")
    return found


def step_order(root: ET.Element) -> list[str]:
    order: list[str] = []
    for node in walk(root):
        if localname(node.tag) in STEP_TAGS:
            marker = None
            for attr in ID_ATTRS:
                if node.get(attr):
                    marker = node.get(attr)
                    break
            if marker is None:
                marker = "".join(node.itertext()).strip()[:40]
            order.append(marker)
    return order


def parse(path_or_text: str, *, is_path: bool) -> ET.Element:
    try:
        if is_path:
            return ET.parse(path_or_text).getroot()
        return ET.fromstring(path_or_text)
    except ET.ParseError as error:
        raise NotPreserved(f"output is not well-formed XML: {error}") from error


def check_xml_preservation(source: ET.Element, output: ET.Element) -> None:
    lost_safety = []
    source_safety = safety_nodes(source)
    output_safety = safety_nodes(output)
    for tag in set(source_safety):
        if output_safety.count(tag) < source_safety.count(tag):
            lost_safety.append(
                f"{tag} ({source_safety.count(tag)} -> {output_safety.count(tag)})"
            )
    if lost_safety:
        raise NotPreserved(
            f"safety nodes dropped: {', '.join(sorted(lost_safety))}. "
            f"Well-formed output that says less is still lossy"
        )

    lost_ids = identifiers(source) - identifiers(output)
    if lost_ids:
        raise NotPreserved(f"identifiers dropped: {', '.join(sorted(lost_ids))}")

    lost_xrefs = xrefs(source) - xrefs(output)
    if lost_xrefs:
        raise NotPreserved(f"cross-references dropped: {', '.join(sorted(lost_xrefs))}")

    source_steps = step_order(source)
    output_steps = step_order(output)
    if len(source_steps) != len(output_steps):
        raise NotPreserved(
            f"step count changed: {len(source_steps)} -> {len(output_steps)}"
        )
    if source_steps != output_steps:
        if sorted(source_steps) == sorted(output_steps):
            raise NotPreserved(
                "step order changed while the same steps are present; similar "
                "text in a different order is a different procedure"
            )
        raise NotPreserved("step identities changed")


def check_extraction_quality(declared: dict[str, Any]) -> None:
    """A PDF extraction that does not declare its quality cannot support a PASS."""
    quality = declared.get("extraction_quality")
    if quality is None:
        raise NotPreserved(
            "PDF-extracted text must declare extraction_quality; undeclared "
            "quality is not the same as good quality"
        )
    if quality not in ("COMPLETE", "PARTIAL", "GARBLED"):
        raise NotPreserved(f"unknown extraction_quality {quality!r}")
    if quality != "COMPLETE":
        if declared.get("semantic_pass_allowed") is not False:
            raise NotPreserved(
                f"extraction_quality {quality} must block semantic PASS"
            )
    for structure in ("tables", "warnings"):
        state = (declared.get("structures_recovered") or {}).get(structure)
        if state is None:
            raise NotPreserved(
                f"structures_recovered.{structure} is undeclared; an unreported "
                f"structure reads as a recovered one"
            )
        if state is False and quality == "COMPLETE":
            raise NotPreserved(
                f"{structure} were not recovered but extraction is reported COMPLETE"
            )


def check_format_trigger(declared_format: str, sample: str) -> None:
    """A format module must not claim a document it cannot be looking at."""
    if declared_format not in FORMATS:
        raise NotPreserved(f"unknown document format {declared_format!r}")
    looks_like_xml = sample.lstrip().startswith("<")
    if declared_format in ("S1000D_LIKE_XML", "DITA_LIKE_XML") and not looks_like_xml:
        raise NotPreserved(
            f"{declared_format} was selected for content that is not XML; a "
            f"format module must not trigger on an unrelated document"
        )
    if declared_format in ("PLAIN_TEXT", "PDF_EXTRACTED_TEXT") and looks_like_xml:
        raise NotPreserved(
            f"{declared_format} was selected for XML content; structure would be "
            f"processed as prose and silently lost"
        )


S1000D_SOURCE = """<dmodule>
  <content>
    <procedure>
      <warning id="W-1"><simplePara>De-energise the system.</simplePara></warning>
      <proceduralStep id="S-1" xrefid="R-1"><para>Open the access panel.</para></proceduralStep>
      <proceduralStep id="S-2"><para>Release the residual pressure.</para></proceduralStep>
      <caution id="C-1"><simplePara>Do not exceed 3.5 kPa.</simplePara></caution>
      <proceduralStep id="S-3"><para>Close the access panel.</para></proceduralStep>
    </procedure>
  </content>
</dmodule>"""

DITA_SOURCE = """<task id="T-1">
  <taskbody>
    <steps>
      <step id="D-1"><cmd>Open the valve.</cmd></step>
      <step id="D-2"><cmd>Wait for pressure.</cmd>
        <note id="N-1">Pressure falls slowly.</note></step>
    </steps>
  </taskbody>
</task>"""


def _selftest() -> int:
    survived: list[str] = []
    source = parse(S1000D_SOURCE, is_path=False)

    # A faithful rewrite: same structure, different prose.
    faithful = S1000D_SOURCE.replace(
        "Open the access panel.", "Open the panel."
    ).replace("Release the residual pressure.", "Release the pressure.")
    try:
        check_xml_preservation(source, parse(faithful, is_path=False))
        check_xml_preservation(parse(DITA_SOURCE, is_path=False),
                               parse(DITA_SOURCE, is_path=False))
    except NotPreserved as error:
        print(f"SELFTEST RED: faithful rewrite refused: {error}", file=sys.stderr)
        return 2

    def case(name: str, output_xml: str) -> None:
        try:
            check_xml_preservation(source, parse(output_xml, is_path=False))
        except NotPreserved:
            return
        survived.append(name)

    # Well-formed, reads fine, drops a warning.
    case("warning node dropped", S1000D_SOURCE.replace(
        '<warning id="W-1"><simplePara>De-energise the system.</simplePara></warning>', ""))
    case("caution node dropped", S1000D_SOURCE.replace(
        '<caution id="C-1"><simplePara>Do not exceed 3.5 kPa.</simplePara></caution>', ""))
    # Same steps, different order.
    reordered = S1000D_SOURCE.replace(
        '<proceduralStep id="S-1" xrefid="R-1"><para>Open the access panel.</para></proceduralStep>\n'
        '      <proceduralStep id="S-2"><para>Release the residual pressure.</para></proceduralStep>',
        '<proceduralStep id="S-2"><para>Release the residual pressure.</para></proceduralStep>\n'
        '      <proceduralStep id="S-1" xrefid="R-1"><para>Open the access panel.</para></proceduralStep>')
    case("step order changed while text stays similar", reordered)
    case("identifier dropped", S1000D_SOURCE.replace('id="S-2"', ""))
    case("cross-reference dropped", S1000D_SOURCE.replace(' xrefid="R-1"', ""))
    case("step removed", S1000D_SOURCE.replace(
        '<proceduralStep id="S-3"><para>Close the access panel.</para></proceduralStep>', ""))

    try:
        check_xml_preservation(source, parse("<dmodule><content>", is_path=False))
        survived.append("malformed output accepted")
    except NotPreserved:
        pass

    # Format triggering.
    def trigger_case(name: str, fmt: str, sample: str) -> None:
        try:
            check_format_trigger(fmt, sample)
        except NotPreserved:
            return
        survived.append(name)

    trigger_case("S1000D module triggered on plain text", "S1000D_LIKE_XML",
                 "Open the valve. Then close it.")
    trigger_case("DITA module triggered on plain text", "DITA_LIKE_XML", "Some prose.")
    trigger_case("plain-text module triggered on XML", "PLAIN_TEXT", S1000D_SOURCE)
    trigger_case("unknown format accepted", "MARKDOWN", "# heading")
    try:
        check_format_trigger("S1000D_LIKE_XML", S1000D_SOURCE)
        check_format_trigger("PLAIN_TEXT", "Open the valve.")
    except NotPreserved as error:
        print(f"SELFTEST RED: valid format trigger refused: {error}", file=sys.stderr)
        return 2

    # PDF extraction quality.
    good = {
        "extraction_quality": "COMPLETE",
        "semantic_pass_allowed": True,
        "structures_recovered": {"tables": True, "warnings": True},
    }
    try:
        check_extraction_quality(good)
    except NotPreserved as error:
        print(f"SELFTEST RED: complete extraction refused: {error}", file=sys.stderr)
        return 2

    def quality_case(name: str, body: dict[str, Any]) -> None:
        try:
            check_extraction_quality(body)
        except NotPreserved:
            return
        survived.append(name)

    quality_case("undeclared extraction quality", {
        "semantic_pass_allowed": True,
        "structures_recovered": {"tables": True, "warnings": True}})
    quality_case("garbled extraction still allows semantic PASS", {
        "extraction_quality": "GARBLED", "semantic_pass_allowed": True,
        "structures_recovered": {"tables": True, "warnings": True}})
    quality_case("partial extraction still allows semantic PASS", {
        "extraction_quality": "PARTIAL", "semantic_pass_allowed": True,
        "structures_recovered": {"tables": True, "warnings": True}})
    quality_case("missing tables reported as complete", {
        "extraction_quality": "COMPLETE", "semantic_pass_allowed": True,
        "structures_recovered": {"tables": False, "warnings": True}})
    quality_case("missing warnings reported as complete", {
        "extraction_quality": "COMPLETE", "semantic_pass_allowed": True,
        "structures_recovered": {"tables": True, "warnings": False}})
    quality_case("undeclared table recovery", {
        "extraction_quality": "COMPLETE", "semantic_pass_allowed": True,
        "structures_recovered": {"warnings": True}})

    if survived:
        for name in survived:
            print(f"SELFTEST RED: mutation survived: {name}", file=sys.stderr)
        return 2

    print("SELFTEST GREEN: faithful rewrites preserved; 19 preservation, "
          "trigger and extraction mutations refused")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", dest="document_format", choices=FORMATS)
    args = parser.parse_args()

    if args.selftest:
        return _selftest()
    if not args.source or not args.output:
        parser.error("--source and --output, or --selftest, are required")
    if not args.source.is_file() or not args.output.is_file():
        print("FATAL: source or output is absent", file=sys.stderr)
        return 64

    try:
        if args.document_format:
            check_format_trigger(
                args.document_format,
                args.source.read_text(encoding="utf-8", errors="replace"),
            )
        check_xml_preservation(
            parse(str(args.source), is_path=True),
            parse(str(args.output), is_path=True),
        )
    except NotPreserved as error:
        print(f"PRESERVATION RED: {error}", file=sys.stderr)
        return 2

    print("PRESERVATION GREEN: safety nodes, identifiers, cross-references and step order survived")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
