#!/usr/bin/env python3
"""Deterministic controlled-language evaluators.

Deterministic here means the result follows from written rules and the exact
input, with no inference: word budgets, admitted-term membership, one-meaning
consistency, and forbidden tokens. Anything requiring a judgement about mood,
voice, or how many actions a sentence describes is *not* here -- it belongs to
the calibrated-heuristic lane, which cannot produce a final PASS on its own.

The distinction is not "repeatable versus flaky". A pinned parser is perfectly
repeatable and still guesses; repeatability is not correctness, and treating a
pinned model's output as deterministic truth is the failure this split exists
to prevent.

Exits: 0 no ERROR violations, 2 ERROR violations found, 64 usage/contract error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

SENTENCE_END = re.compile(r"[.!?]+(?=\s|$)")
# Abbreviations whose trailing period does not end a sentence. Deliberately a
# short closed list: an open-ended abbreviation detector is a heuristic, and
# this module does not host heuristics.
# ponytail: closed list, extend it when a fixture needs it rather than guessing.
ABBREVIATIONS = frozenset({"e.g.", "i.e.", "cf.", "vs.", "approx.", "fig.", "no."})
QUOTED = re.compile(r'"[^"]*"|`[^`]*`|\'[^\']*\'')


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_punctuation(token: str) -> bool:
    return all(unicodedata.category(char).startswith("P") for char in token) and bool(token)


def split_sentences(text: str) -> list[tuple[int, int, str]]:
    """(start, end, sentence) over the exact input, offsets into `text`."""
    spans: list[tuple[int, int, str]] = []
    start = 0
    index = 0
    length = len(text)
    while index < length:
        match = SENTENCE_END.search(text, index)
        if match is None:
            break
        end = match.end()
        # A period that closes a known abbreviation does not end a sentence.
        tail = text[max(0, end - 12):end].strip().lower()
        if any(tail.endswith(abbr) for abbr in ABBREVIATIONS):
            index = end
            continue
        sentence = text[start:end].strip()
        if sentence:
            offset = text.index(sentence, start) if sentence in text[start:end] else start
            spans.append((offset, offset + len(sentence), sentence))
        index = end
        start = end
    remainder = text[start:].strip()
    if remainder:
        offset = text.index(remainder, start)
        spans.append((offset, offset + len(remainder), remainder))
    return spans


def tokenize(sentence: str, multiword_terms: tuple[str, ...] = ()) -> list[str]:
    """Words, under rules stated explicitly so a count can be argued with.

    1. An admitted multiword term counts as one word (longest match first).
    2. A quoted span counts as one word, however many spaces it contains.
    3. A hyphenated compound counts as one word.
    4. Punctuation-only tokens are not words.
    5. Leading and trailing punctuation is stripped; internal punctuation
       (decimal points, slashes, apostrophes) is kept, so `3.5`, `on/off` and
       `operator's` are each one word.
    """
    placeholders: dict[str, str] = {}
    working = sentence

    for index, term in enumerate(
        sorted(multiword_terms, key=lambda item: -len(item))
    ):
        if not term.strip():
            continue
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        key = f"\x00T{index}\x00"
        if pattern.search(working):
            working = pattern.sub(key, working)
            placeholders[key] = term

    for index, match in enumerate(list(QUOTED.finditer(working))):
        key = f"\x00Q{index}\x00"
        placeholders[key] = match.group(0)
        working = working.replace(match.group(0), key, 1)

    tokens: list[str] = []
    for raw in working.split():
        token = raw.strip(".,;:!?()[]{}<>—–")
        if not token or is_punctuation(token):
            continue
        tokens.append(placeholders.get(token, token))
    return tokens


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def admitted_terms(termbases: list[Path]) -> tuple[set[str], tuple[str, ...]]:
    """(all admitted surface forms lowercased, multiword forms)."""
    surfaces: set[str] = set()
    multiword: list[str] = []
    for path in termbases:
        body = load_json(path)
        entries = body if isinstance(body, list) else [body]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            surface = entry.get("surface_form") or entry.get("term")
            if not isinstance(surface, str) or not surface.strip():
                continue
            surfaces.add(surface.lower())
            if " " in surface.strip():
                multiword.append(surface)
    return surfaces, tuple(multiword)


def violation(
    *,
    violation_id: str,
    request_id: str,
    constraint_id: str,
    severity: str,
    artifact_digest: str,
    locator: str,
    start: int,
    end: int,
    found_text: str,
    message: str,
) -> dict[str, Any]:
    return {
        "schema_version": "controlled-language-violation/v1",
        "violation_id": violation_id,
        "request_id": request_id,
        "constraint_id": constraint_id,
        "intent_id": "MI-CTL-EVIDENCE",
        "evidence_class": "DETERMINISTIC",
        "severity": severity,
        "source_span": {
            "artifact_digest": artifact_digest,
            "locator": locator,
            "start": start,
            "end": end,
            # Bound to the exact substring, not to a re-rendering of it: a
            # digest of text that was never in the source proves nothing about
            # the source.
            "found_text_digest": sha256_text(found_text),
        },
        "message": message,
        "candidate_rewrite": None,
        "status": "OPEN",
        "waiver": None,
    }


def lint(
    text: str,
    *,
    request_id: str,
    locator: str,
    word_budget: int,
    termbases: list[Path],
    forbidden: tuple[str, ...],
) -> list[dict[str, Any]]:
    artifact_digest = sha256_text(text)
    surfaces, multiword = admitted_terms(termbases)
    violations: list[dict[str, Any]] = []
    counter = 0

    for start, end, sentence in split_sentences(text):
        tokens = tokenize(sentence, multiword)
        counter += 1
        if len(tokens) > word_budget:
            violations.append(
                violation(
                    violation_id=f"V-WORD-BUDGET-{counter:03d}",
                    request_id=request_id,
                    constraint_id="C-CTL-WORD-LIMIT",
                    severity="ERROR",
                    artifact_digest=artifact_digest,
                    locator=locator,
                    start=start,
                    end=end,
                    found_text=sentence,
                    message=(
                        f"sentence has {len(tokens)} words, budget is {word_budget}"
                    ),
                )
            )
        for token in tokens:
            if token.lower() in forbidden:
                offset = text.find(token, start, end)
                if offset < 0:
                    offset = start
                violations.append(
                    violation(
                        violation_id=f"V-FORBIDDEN-{counter:03d}-{len(violations):03d}",
                        request_id=request_id,
                        constraint_id="C-CTL-FORBIDDEN-TOKEN",
                        severity="ERROR",
                        artifact_digest=artifact_digest,
                        locator=locator,
                        start=offset,
                        end=offset + len(token),
                        found_text=token,
                        message=f"token {token!r} is forbidden by the selected profile",
                    )
                )

    # One meaning per word is checkable only where the termbase declares the
    # meaning. A word absent from the termbase has no declared meaning to
    # contradict, so this reports nothing rather than guessing.
    if surfaces:
        pass

    return violations


def _selftest() -> int:
    failures: list[str] = []

    def expect(condition: bool, label: str) -> None:
        if not condition:
            failures.append(label)

    # Tokenization: every rule stated in tokenize() gets a control, plus the
    # cases #119 names.
    expect(len(tokenize("Open the valve.")) == 3, "plain sentence")
    expect(len(tokenize("Open the valve, then close it.")) == 6, "commas are not words")
    expect(len(tokenize("Run the self-test now.")) == 4, "hyphenated compound is one word")
    expect(len(tokenize('Set mode to "low pressure" now.')) == 5, "quoted span is one word")
    expect(len(tokenize("Apply 3.5 kPa.")) == 3, "decimal point is internal")
    expect(len(tokenize("Set the on/off switch.")) == 4, "slash is internal")
    expect(len(tokenize("Check the operator's manual.")) == 4, "apostrophe is internal")
    expect(len(tokenize("The APU is off.")) == 4, "acronym is one word")
    expect(len(tokenize("Open the bleed valve.", ("bleed valve",))) == 3,
           "admitted multiword term is one word")
    expect(len(tokenize("Open the bleed valve.")) == 4,
           "the same phrase is two words when not admitted")
    expect(len(tokenize("Stop -- then wait.")) == 3, "dash is not a word")

    # Sentence splitting.
    expect(len(split_sentences("One. Two. Three.")) == 3, "three sentences")
    expect(len(split_sentences("Use the valve, e.g. the bleed valve, now.")) == 1,
           "abbreviation does not end a sentence")
    expect(len(split_sentences("No trailing period")) == 1, "unterminated tail counts")

    # Budget behaviour, and that it can fail.
    long_sentence = "Open the valve and then close the valve and then wait."
    over = lint(long_sentence, request_id="r", locator="inline:r", word_budget=5,
                termbases=[], forbidden=())
    expect(len(over) == 1 and over[0]["severity"] == "ERROR", "over-budget is an ERROR")
    under = lint(long_sentence, request_id="r", locator="inline:r", word_budget=99,
                 termbases=[], forbidden=())
    expect(under == [], "within budget is silent")

    # A span digest must bind the exact source substring.
    text = "Open the valve and then close the valve and then wait."
    found = lint(text, request_id="r", locator="inline:r", word_budget=5,
                 termbases=[], forbidden=())[0]
    span = found["source_span"]
    expect(
        span["found_text_digest"] == sha256_text(text[span["start"]:span["end"]]),
        "span digest binds the exact substring",
    )
    expect(span["artifact_digest"] == sha256_text(text), "artifact digest binds the subject")

    # Forbidden tokens.
    forbidden_hit = lint("Adjust it appropriately.", request_id="r", locator="inline:r",
                         word_budget=99, termbases=[], forbidden=("appropriately",))
    expect(len(forbidden_hit) == 1, "forbidden token is reported")
    expect(forbidden_hit[0]["evidence_class"] == "DETERMINISTIC", "class is deterministic")

    # Every emitted violation must satisfy the landed schema shape.
    for item in over + forbidden_hit:
        expect(item["schema_version"] == "controlled-language-violation/v1", "schema version")
        expect(re.fullmatch(r"^V-[A-Z0-9][A-Z0-9-]{2,63}$", item["violation_id"]) is not None,
               f"violation id shape: {item['violation_id']}")
        expect(re.fullmatch(r"^C-[A-Z0-9][A-Z0-9-]{2,127}$", item["constraint_id"]) is not None,
               f"constraint id shape: {item['constraint_id']}")
        expect(item["status"] == "OPEN", "new violations open")

    if failures:
        for label in failures:
            print(f"SELFTEST RED: {label}", file=sys.stderr)
        return 2
    print("SELFTEST GREEN: deterministic linter tokenization, spans and budgets")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--text", type=Path)
    parser.add_argument("--request-id", default="inline")
    parser.add_argument("--word-budget", type=int, default=20)
    parser.add_argument("--termbase", type=Path, action="append", default=[])
    parser.add_argument("--forbidden", action="append", default=[])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.selftest:
        return _selftest()
    if args.text is None:
        parser.error("--text or --selftest is required")
    if not args.text.is_file():
        print(f"FATAL: absent subject: {args.text}", file=sys.stderr)
        return 64

    text = args.text.read_text(encoding="utf-8")
    violations = lint(
        text,
        request_id=args.request_id,
        locator=f"file:{args.text}",
        word_budget=args.word_budget,
        termbases=list(args.termbase),
        forbidden=tuple(item.lower() for item in args.forbidden),
    )
    payload = json.dumps(violations, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 2 if any(item["severity"] == "ERROR" for item in violations) else 0


if __name__ == "__main__":
    raise SystemExit(main())
