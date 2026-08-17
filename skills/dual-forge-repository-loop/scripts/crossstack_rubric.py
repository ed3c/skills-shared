#!/usr/bin/env python3
"""Score a stated rule against a paraphrase rubric instead of the checker's words.

The #229 run scored rule naming by loose token overlap with `check_multi_agent_
runtime.py`'s internal marker string, and its own audit showed what that measures:
one marker token anywhere in the answer scored full credit, while a precise
paraphrase that avoided the checker's vocabulary scored nothing. The candidate
prompt is 36KB of that vocabulary, so the metric separated arms by how many of
the checker's words each prompt happened to carry.

A rubric replaces the overlap test with an explicit conjunction of concept
groups. An answer scores when some accept path is satisfied -- every group in it
matched by at least one of its phrasings -- so a paraphrase in the model's own
words scores, and echoing a single marker token does not.

The rubric is only as good as its own examples, so `validate_rubric` executes
them: every declared accept phrasing must score, every declared reject phrasing
must not, at least one accepted phrasing must share no word with the marker, and
at least one rejected phrasing must contain a marker word. A rubric that cannot
tell those four apart is refused rather than shipped.

Importable; `--selftest` runs the module's own good-hollow check.
"""

from __future__ import annotations

import re
import sys
from typing import Any

WORD = re.compile(r"[a-z0-9]+")

LEXICAL = "LEXICAL_TOKEN_OVERLAP"
RUBRIC = "PARAPHRASE_RUBRIC"
MIXED = "MIXED"
NO_REFUSAL_CASES = "NO_REFUSAL_CASES"


def observed_metric(cases: list[dict[str, Any]]) -> str:
    """Name the metric a case set is scored by, from the cases and nothing else.

    Four outcomes, kept apart on purpose. A set where no refusal case carries a
    rubric is the lexical generation -- which is what the executed 2026-08 files
    say by having no rubric field, and reading that absence as anything else
    would be retro-fitting a metric onto a run that never used one. A set where
    only some carry one, and a set with nothing to name at all, are their own
    states rather than a shrug shared with either generation.
    """
    refusals = [case for case in cases if case["ground_truth"]["violated_rule"]]
    if not refusals:
        return NO_REFUSAL_CASES
    with_rubric = [case for case in refusals if isinstance(case.get("rule_rubric"), dict)]
    if not with_rubric:
        return LEXICAL
    return RUBRIC if len(with_rubric) == len(refusals) else MIXED


def words(text: str) -> list[str]:
    return WORD.findall((text or "").lower())


def matches_word(spoken: str, concept: str) -> bool:
    """Word-initial match: `depend` covers `depends`, and `self` never covers `itself`.

    Inflection is the reason. Requiring exact words would make a rubric fail on
    `depends` after admitting `depend`, which is the same "correct answer scores
    zero" defect the rubric exists to remove. Matching from the start of the word
    keeps that without letting a concept match inside an unrelated word. Concepts
    shorter than four characters match exactly, because `pr` or `one` as a prefix
    would swallow half the dictionary.
    """
    if len(concept) < 4:
        return spoken == concept
    return spoken.startswith(concept)


def contains_phrase(haystack: list[str], phrase: str) -> bool:
    """Contiguous word-initial match of every word in the phrase."""
    needle = words(phrase)
    if not needle:
        return False
    return any(all(matches_word(spoken, concept)
                   for spoken, concept in zip(haystack[i:i + len(needle)], needle))
               for i in range(len(haystack) - len(needle) + 1))


def score_rule(rubric: dict[str, Any], stated: str | None) -> bool:
    """True when the stated rule satisfies every concept group of some accept path."""
    haystack = words(stated or "")
    if not haystack:
        return False
    for path in rubric.get("accept_any", []):
        if path and all(group and any(contains_phrase(haystack, phrase) for phrase in group)
                        for group in path):
            return True
    return False


def marker_words(marker: str) -> list[str]:
    """The checker vocabulary a lexical metric would have rewarded."""
    return [token for token in marker.split("-") if len(token) > 3]


def echoes_marker(marker: str, stated: str) -> bool:
    return bool(set(marker_words(marker)) & set(words(stated)))


def validate_rubric(marker: str, rubric: Any) -> list[str]:
    """Return every reason this rubric may not be used as a metric. Empty means usable."""
    problems: list[str] = []
    if not isinstance(rubric, dict):
        return [f"{marker}: no rubric"]

    paths = rubric.get("accept_any")
    if not isinstance(paths, list) or not paths:
        problems.append(f"{marker}: accept_any is empty, so nothing can score")
    else:
        for index, path in enumerate(paths):
            if not isinstance(path, list) or not path or not all(
                    isinstance(group, list) and group for group in path):
                problems.append(f"{marker}: accept path {index} is not a non-empty "
                                f"conjunction of non-empty concept groups")

    examples = rubric.get("examples")
    if not isinstance(examples, dict):
        return problems + [f"{marker}: rubric declares no examples, so it is unexecuted"]
    accept = examples.get("accept") or []
    reject = examples.get("reject") or []

    if len(accept) < 3:
        problems.append(f"{marker}: {len(accept)} accepted phrasings; a rubric claiming "
                        f"multiple acceptable phrasings needs at least three")
    if len(reject) < 2:
        problems.append(f"{marker}: {len(reject)} rejected phrasings; without them the "
                        f"rubric is never shown to refuse anything")

    for phrasing in accept:
        if not score_rule(rubric, phrasing):
            problems.append(f"{marker}: declared-correct phrasing scores zero: {phrasing!r}")
    for phrasing in reject:
        if score_rule(rubric, phrasing):
            problems.append(f"{marker}: declared-wrong phrasing scores: {phrasing!r}")

    if not any(not echoes_marker(marker, phrasing) for phrasing in accept):
        problems.append(f"{marker}: every accepted phrasing repeats a marker word, so the "
                        f"rubric is the lexical metric under another name")
    if not any(echoes_marker(marker, phrasing) for phrasing in reject):
        problems.append(f"{marker}: no rejected phrasing echoes a marker word, so marker "
                        f"echo was never shown to be insufficient")
    return problems


def selftest() -> int:
    """Prove the scorer can go red: a rubric that only its own marker satisfies."""
    good = {
        "accept_any": [[["task", "slice"], ["itself", "its own"], ["depend", "prerequisite"]]],
        "examples": {
            "accept": ["a slice waits on its own prerequisite",
                       "the task depends on itself",
                       "self-dependency: the task lists itself as a prerequisite"],
            "reject": ["dependency", "the task depends on another slice"],
        },
    }
    problems = validate_rubric("self-dependency", good)
    if problems:
        print(f"SELFTEST RED: a sound rubric was refused -- {problems}", file=sys.stderr)
        return 2

    lexical = {
        "accept_any": [[["self dependency"]]],
        "examples": {"accept": ["self dependency", "self-dependency", "self  dependency"],
                     "reject": ["dependency", "self"]},
    }
    if not validate_rubric("self-dependency", lexical):
        print("SELFTEST RED: a marker-only rubric was admitted; the keyword-independence "
              "control does not fire", file=sys.stderr)
        return 2

    unsound = {
        "accept_any": [[["task"]]],
        "examples": {"accept": ["the task waits on itself", "a task cycle", "task loop"],
                     "reject": ["the task depends on another slice", "self dependency"]},
    }
    if not validate_rubric("self-dependency", unsound):
        print("SELFTEST RED: a rubric that scores its own reject example was admitted",
              file=sys.stderr)
        return 2

    if contains_phrase(words("the task depends on itself"), "self"):
        print("SELFTEST RED: 'self' matched inside 'itself'; matching is not whole-word",
              file=sys.stderr)
        return 2

    print("SELFTEST GREEN: rubric scorer admits paraphrase, refuses marker-only and "
          "self-contradicting rubrics, and matches whole words only")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] != ["--selftest"]:
        print("USAGE: crossstack_rubric.py --selftest", file=sys.stderr)
        raise SystemExit(64)
    raise SystemExit(selftest())
