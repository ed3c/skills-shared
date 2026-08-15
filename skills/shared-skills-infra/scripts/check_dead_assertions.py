#!/usr/bin/env python3
"""Fail the build on shell assertions that physically cannot fail.

Every gate in this repo leans on a `verify.sh` as its only positive control, so
an assertion that can never go red is an unguarded gate that passes review under
the name "tests are green". Two instances of the same bash trap were found by
hand; this sweeps the whole class instead.

The class is `set -e` (and the ERR trap) declining to fire. Verified on bash
5.3.3 -- each row is a probe that kept running past a failure:

  ! grep -q Traceback <file-that-has-it>   STILL ALIVE   `!` inverts, so exempt
  test -e <missing> && test -e <missing>   STILL ALIVE   non-final `&&` operand
  test -e <missing>                        DIED          the live form
  grep X <no-match> > /dev/null            DIED          statement level is live

That last row is why this linter is narrower than a naive reading of the rules:
a bare redirected `grep` under `set -e` *does* fail the script, so calling it
dead would be a false claim. A linter that cries wolf gets switched off, which
is strictly worse than not having one -- the same reason `!` inside an
`if`/`while`/`until` CONDITION is exempt, where the inversion is both legitimate
and load-bearing.

Rules, each fired by its own predicate so it can be mutated independently:

  DEAD-NEGATION      `! cmd` in statement position (outside a condition)
  DEAD-AND-CHAIN     `test A && test B` -- every operand an assertion
  DEAD-SWALLOW       an assertion whose status is eaten by `|| true` / `|| :`
  DEAD-DISCARD       `grep >/dev/null` without `-q` where the status is provably
                     discarded (inside `set +e`, backgrounded, or no `set -e`)

Zero network, stdlib only.

Exit codes: 0 clean, 1 at least one dead assertion, 3 no shell test file matched
(absence is reported, never silently green).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterator, NamedTuple

REPO = Path(__file__).resolve().parents[3]

# The two shapes a gate takes in this repo. Kept explicit rather than "every
# *.sh": a helper library is not a positive control, and widening the net is how
# a linter starts reporting things nobody asked it about. `tests/**/verify.sh`
# already covers `tests/verify.sh`, because `**` also matches zero directories.
TEST_GLOBS = ("tests/**/verify.sh", "tests/run-all.sh")

# Commands that exist to assert, i.e. whose only product is an exit status.
ASSERTION_HEADS = frozenset({"test", "[", "[[", "cmp", "diff"})

# Commands run for their effect, where a non-zero status is routinely expected
# and `|| true` is the honest way to say so. Narrow and listed on purpose.
BEST_EFFORT_HEADS = frozenset({
    "mkdir", "mv", "cp", "rm", "rmdir", "unlink", "ln", "touch", "chmod",
    "chown", "kill", "pkill", "wait", "sync", "cd", "pushd", "popd", "unset",
    "export", "hash", "true", ":",
})

RESERVED_PUSH = frozenset({"if", "elif", "while", "until"})
RESERVED_POP = frozenset({"then", "do"})
# After these, the next word starts a fresh command rather than continuing one.
COMMAND_STARTERS = frozenset({
    "\n", ";", ";;", "&&", "||", "|", "|&", "&", "(", ")", "{", "}",
    "then", "do", "else", "elif", "if", "while", "until", "case", "esac",
    "fi", "done", "in", "!", "time",
})


class Finding(NamedTuple):
    path: Path
    line: int
    rule: str
    why: str
    found: str
    write: str

    def render(self, root: Path) -> str:
        try:
            where = self.path.relative_to(root)
        except ValueError:
            where = self.path
        return (
            f"{self.rule} {where}:{self.line}: {self.why}\n"
            f"      found: {self.found}\n"
            f"      write: {self.write}"
        )


# --------------------------------------------------------------------------
# tokenizer: enough bash to find command boundaries, not a bash implementation
# --------------------------------------------------------------------------


class Tok(NamedTuple):
    kind: str        # "word" | "op"
    text: str
    line: int


_OPS = ("&&", "||", ";;", "|&", "<<-", "<<", ">>", "&>", ";", "|", "&", "(", ")")


def _skip_quoted(text: str, i: int) -> int:
    """Return the index just past the quote/expansion starting at `i`."""
    ch = text[i]
    if ch == "'":
        end = text.find("'", i + 1)
        return len(text) if end < 0 else end + 1
    if ch == '"':
        i += 1
        while i < len(text):
            if text[i] == "\\":
                i += 2
                continue
            if text[i] == "$" and text[i:i + 2] == "$(":
                i = _skip_balanced(text, i + 1, "(", ")")
                continue
            if text[i] == "`":
                end = text.find("`", i + 1)
                i = len(text) if end < 0 else end + 1
                continue
            if text[i] == '"':
                return i + 1
            i += 1
        return len(text)
    if ch == "`":
        end = text.find("`", i + 1)
        return len(text) if end < 0 else end + 1
    if text[i:i + 2] == "$(":
        return _skip_balanced(text, i + 1, "(", ")")
    if text[i:i + 2] == "${":
        return _skip_balanced(text, i + 1, "{", "}")
    return i + 1


def _skip_balanced(text: str, i: int, opener: str, closer: str) -> int:
    depth = 0
    while i < len(text):
        ch = text[i]
        if ch in ("'", '"', "`"):
            i = _skip_quoted(text, i)
            continue
        if ch == "\\":
            i += 2
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(text)


def tokenize(text: str) -> list[Tok]:
    """Words and operators, with comments dropped and heredoc bodies skipped.

    Heredoc bodies matter: this repo writes fixture JSON and skill bodies through
    `<<'JSON'`, and a `!` on such a line is data, not a command.
    """
    tokens: list[Tok] = []
    pending: list[tuple[str, bool]] = []      # (delimiter, strip leading tabs)
    word: list[str] = []
    word_line = 1
    line = 1
    i, n = 0, len(text)

    def flush() -> None:
        nonlocal word
        if word:
            tokens.append(Tok("word", "".join(word), word_line))
            word = []

    while i < n:
        ch = text[i]

        if ch == "\\" and text[i:i + 2] == "\\\n":
            i += 2                             # continuation: one logical line
            line += 1
            continue

        if ch == "\n":
            flush()
            tokens.append(Tok("op", "\n", line))
            line += 1
            i += 1
            for delim, strip_tabs in pending:
                while i < n:
                    end = text.find("\n", i)
                    end = n if end < 0 else end
                    body = text[i:end]
                    i = end + 1
                    line += 1
                    if (body.lstrip("\t") if strip_tabs else body).strip() == delim:
                        break
            pending = []
            continue

        if ch in " \t":
            flush()
            i += 1
            continue

        if ch == "#" and not word:
            end = text.find("\n", i)
            i = n if end < 0 else end
            continue

        if ch in ("'", '"', "`") or text[i:i + 2] in ("$(", "${"):
            if not word:
                word_line = line
            end = _skip_quoted(text, i)
            chunk = text[i:end]
            word.append(chunk)
            line += chunk.count("\n")
            i = end
            continue

        if ch == "\\":
            if not word:
                word_line = line
            word.append(text[i:i + 2])
            i += 2
            continue

        matched = next((op for op in _OPS if text.startswith(op, i)), None)
        if matched:
            # `>&2`, `2>&1`, `>>file` are redirections, not list separators; only
            # a bare `&` ends a command, and `>` never does.
            if matched in ("<<", "<<-"):
                flush()
                j = i + len(matched)
                while j < n and text[j] in " \t":
                    j += 1
                start = j
                while j < n and text[j] not in " \t\n;&|<>":
                    j = _skip_quoted(text, j) if text[j] in ("'", '"') else j + 1
                delim = text[start:j].replace("'", "").replace('"', "").replace("\\", "")
                if delim:
                    pending.append((delim, matched == "<<-"))
                i = j
                continue
            if matched == "&" and text[i:i + 2] == "&>":
                word.append("&>")               # redirection, keep inside word
                i += 2
                continue
            if matched in (">>", "&>"):
                if not word:
                    word_line = line
                word.append(matched)
                i += len(matched)
                continue
            flush()
            tokens.append(Tok("op", matched, line))
            i += len(matched)
            continue

        if not word:
            word_line = line
        word.append(ch)
        i += 1

    flush()
    return tokens


# --------------------------------------------------------------------------
# parser: simple commands grouped into and-or lists, with condition context
# --------------------------------------------------------------------------


class Command(NamedTuple):
    words: list[str]
    negated: bool
    line: int
    raw: str

    @property
    def head(self) -> str:
        return self.words[0] if self.words else ""


class AndOr(NamedTuple):
    """One `a && b || c` list: its operands and where it sits."""
    operands: list[list[Command]]      # each operand is a pipeline
    connectors: list[str]
    line: int
    in_condition: bool
    in_set_e: bool
    raw: str


def errexit_effect(words: list[str]) -> bool | None:
    """Does this `set` command turn errexit on, off, or leave it alone?

    Written out rather than regexed at a glance because the first version read
    `set -eEuo pipefail` -- the ERR-trap form this repo actually uses -- as "no
    errexit", which silently suppressed every finding that depends on it. A
    linter that reports nothing looks exactly like a clean sweep.
    """
    state: bool | None = None
    index = 1
    while index < len(words):
        word = words[index]
        if word in ("-o", "+o"):
            if index + 1 < len(words) and words[index + 1] == "errexit":
                state = word.startswith("-")
                index += 2
                continue
        elif re.fullmatch(r"[-+][a-zA-Z]+", word) and "e" in word[1:]:
            state = word.startswith("-")
        index += 1
    return state


def parse(tokens: list[Tok], starts_set_e: bool = False) -> list[AndOr]:
    lists: list[AndOr] = []
    cond_stack: list[str] = []
    set_e = starts_set_e
    group_depth = 0

    operands: list[list[Command]] = []
    connectors: list[str] = []
    pipeline: list[Command] = []
    words: list[str] = []
    negated = False
    cmd_line = 0
    at_command_start = True

    def close_command() -> None:
        nonlocal words, negated, cmd_line
        if words:
            pipeline.append(Command(words, negated, cmd_line, " ".join(words)))
        words, negated, cmd_line = [], False, 0

    def close_pipeline() -> None:
        nonlocal pipeline
        close_command()
        if pipeline:
            operands.append(pipeline)
        pipeline = []

    def close_list() -> None:
        nonlocal operands, connectors, set_e
        close_pipeline()
        if operands:
            line = operands[0][0].line
            raw = f" {connectors[0]} ".join(
                " | ".join(c.raw for c in operand) for operand in operands
            ) if connectors else " | ".join(c.raw for c in operands[0])
            lists.append(AndOr(operands, connectors, line, bool(cond_stack), set_e, raw))
            # `set -e` / `set +e` take effect for everything after them -- but
            # only at top level. Inside a function body or a subshell the toggle
            # is scoped, and letting it leak would mark the rest of the file as
            # errexit-free and quietly stop reporting.
            first = operands[0][0]
            if group_depth == 0 and first.head == "set" and len(first.words) > 1:
                effect = errexit_effect(first.words)
                if effect is not None:
                    set_e = effect
        operands, connectors = [], []

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.kind == "op":
            if tok.text == "\n":
                # a list continues across a newline only if it ended on a connector
                if not (words or pipeline) and connectors and len(operands) == len(connectors):
                    i += 1
                    continue
                close_list()
                at_command_start = True
            elif tok.text in ("&&", "||"):
                close_pipeline()
                connectors.append(tok.text)
                at_command_start = True
            elif tok.text in ("|", "|&"):
                close_command()
                at_command_start = True
            else:                                   # ; ;; & ( ) and friends
                close_list()
                if tok.text == "(":
                    group_depth += 1
                elif tok.text == ")":
                    group_depth = max(0, group_depth - 1)
                at_command_start = True
            i += 1
            continue

        text = tok.text
        if at_command_start:
            if text == "!":
                negated = True
                cmd_line = tok.line
                i += 1
                continue
            if text in RESERVED_PUSH:
                close_list()
                cond_stack.append(text)
                i += 1
                continue
            if text in RESERVED_POP:
                close_list()
                if cond_stack:
                    cond_stack.pop()
                i += 1
                continue
            if text in ("else", "fi", "done", "esac", "{", "}", "time"):
                close_list()
                if text == "{":
                    group_depth += 1
                elif text == "}":
                    group_depth = max(0, group_depth - 1)
                i += 1
                continue
            if text == "[[":
                # `[[ ! -e x ]]` -- the `!` inside is a test operator, not command
                # negation, so the whole construct is consumed as one command.
                blob = [text]
                i += 1
                while i < len(tokens) and not (tokens[i].kind == "word" and tokens[i].text == "]]"):
                    blob.append(tokens[i].text)
                    i += 1
                if i < len(tokens):
                    blob.append("]]")
                    i += 1
                if not words:
                    cmd_line = tok.line
                words = blob
                at_command_start = False
                continue
            if not words:
                cmd_line = tok.line
        words.append(text)
        at_command_start = False
        i += 1

    close_list()
    return lists


# --------------------------------------------------------------------------
# rules -- one predicate each, so each can be mutated independently
# --------------------------------------------------------------------------


def _strip_redirects(words: list[str]) -> list[str]:
    kept: list[str] = []
    skip_next = False
    for word in words:
        if skip_next:
            skip_next = False
            continue
        if re.fullmatch(r"\d*(>>?|<)", word) or word in ("&>", "&>>"):
            skip_next = True
            continue
        if re.match(r"^\d*(>>?|<|&>)\S", word):
            continue
        kept.append(word)
    return kept


def is_assertion(cmd: Command) -> bool:
    """A command whose only product is an exit status."""
    words = _strip_redirects(cmd.words)
    if not words:
        return False
    head = words[0]
    if head in ASSERTION_HEADS:
        return True
    if head == "grep":
        return any(re.fullmatch(r"-[a-zA-Z]*q[a-zA-Z]*", w) for w in words[1:])
    return False


def rule_dead_negation(item: AndOr) -> list[tuple[Command, str, str]]:
    """`!` outside a condition: bash exempts inverted commands from `set -e`."""
    hits = []
    if item.in_condition:
        return hits                       # legitimate: the branch consumes it
    for operand in item.operands:
        for cmd in operand:
            if cmd.negated:
                inner = " ".join(_strip_redirects(cmd.words)) or "cmd"
                hits.append((
                    cmd,
                    "`!` inverts the status, and bash exempts inverted commands "
                    "from `set -e` and the ERR trap -- this line can never fail "
                    "the test",
                    f'if {inner}; then echo "FAIL: <what went wrong>" >&2; exit 1; fi',
                ))
    return hits


def rule_dead_and_chain(item: AndOr) -> list[tuple[Command, str, str]]:
    """`test A && test B`: only the final operand of an `&&` list is under set -e."""
    # Deliberately not gated on `in_set_e`: an all-assertion `&&` chain is wrong
    # with errexit (the left operand is exempt) and wrong without it (nothing is
    # checked at all), and gating it would let a mis-read `set` line silence the
    # rule instead of reporting.
    if item.in_condition:
        return []
    if not item.connectors or set(item.connectors) != {"&&"}:
        return []
    pipelines = item.operands
    if len(pipelines) < 2 or any(len(p) != 1 for p in pipelines):
        return []
    # Every operand must be an assertion. `test -d x && mv a b` is a guard, a
    # legitimate idiom, and flagging it is how a linter earns its way to /dev/null.
    if not all(is_assertion(p[0]) for p in pipelines):
        return []
    fixed = "; ".join(p[0].raw for p in pipelines).replace("; ", "\n")
    return [(
        pipelines[0][0],
        "only the command after the final `&&` is under `set -e`; if the left "
        "operand fails the list short-circuits and the script keeps going",
        "put each assertion on its own line:\n             "
        + fixed.replace("\n", "\n             "),
    )]


def rule_dead_swallow(item: AndOr, follower: AndOr | None) -> list[tuple[Command, str, str]]:
    """`|| true` discards the status; nothing downstream can bring it back."""
    if item.in_condition:
        return []
    if not item.connectors or item.connectors[-1] != "||":
        return []
    tail = item.operands[-1]
    if len(tail) != 1 or _strip_redirects(tail[0].words)[:1] not in (["true"], [":"]):
        return []
    victim = item.operands[-2][0]
    if is_assertion(victim):
        why = "an assertion whose failure is swallowed by `|| true` proves nothing"
    else:
        head = _strip_redirects(victim.words)[:1]
        if head and head[0] in BEST_EFFORT_HEADS:
            return []                     # run for effect; a bad status is expected
        inspected = follower is not None and re.search(r"\$\?|PIPESTATUS", follower.raw)
        if inspected:
            return []                     # the status was captured, not discarded
        why = ("`|| true` discards the exit status and the next statement never "
               "inspects `$?`, so the command cannot fail the test")
    return [(
        victim,
        why,
        "set +e; " + victim.raw + '; status=$?; set -e; test "${status}" -ne 0',
    )]


_REDIRECT_TO_NULL = re.compile(r"(^|\s)(\d*>|&>)\s*/dev/null")


def rule_dead_discard(item: AndOr) -> list[tuple[Command, str, str]]:
    """`grep >/dev/null` without `-q`, in a position where the status is dropped.

    Deliberately narrow. A bare redirected grep under `set -e` was probed and it
    *does* kill the script, so it is live and is not reported.
    """
    if item.in_condition:
        return []
    for index, operand in enumerate(item.operands):
        for position, cmd in enumerate(operand):
            words = _strip_redirects(cmd.words)
            if not words or words[0] != "grep" or is_assertion(cmd):
                continue
            if not _REDIRECT_TO_NULL.search(cmd.raw):
                continue
            reason = None
            if not item.in_set_e:
                reason = "`set -e` is not in effect here (inside a `set +e` region "
                reason += "or never enabled), so the status goes nowhere"
            elif position < len(operand) - 1:
                reason = "a non-final pipeline stage's status is dropped unless "
                reason += "`pipefail` is set"
            elif index < len(item.operands) - 1:
                reason = "a non-final `&&`/`||` operand is exempt from `set -e`"
            if reason is None:
                continue
            return [(
                cmd,
                f"the output is thrown away and there is no `-q`; {reason}",
                f'if ! {" ".join(w for w in words)} ; then '
                f'echo "FAIL: <what went wrong>" >&2; exit 1; fi',
            )]
    return []


RULES = ("DEAD-NEGATION", "DEAD-AND-CHAIN", "DEAD-SWALLOW", "DEAD-DISCARD")


def lint_text(text: str, path: Path) -> list[Finding]:
    lists = parse(tokenize(text))
    findings: list[Finding] = []
    for index, item in enumerate(lists):
        follower = lists[index + 1] if index + 1 < len(lists) else None
        for rule, hits in (
            ("DEAD-NEGATION", rule_dead_negation(item)),
            ("DEAD-AND-CHAIN", rule_dead_and_chain(item)),
            ("DEAD-SWALLOW", rule_dead_swallow(item, follower)),
            ("DEAD-DISCARD", rule_dead_discard(item)),
        ):
            for cmd, why, write in hits:
                found = ("! " if cmd.negated else "") + cmd.raw
                findings.append(Finding(path, cmd.line, rule, why, found, write))
    return sorted(findings, key=lambda f: (f.line, f.rule))


def lint_file(path: Path) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        # An unreadable gate is not a passing gate.
        return [Finding(path, 0, "UNREADABLE", str(error), "", "make the file readable")]
    return lint_text(text, path)


def shell_tests(root: Path) -> list[Path]:
    found: set[Path] = set()
    for pattern in TEST_GLOBS:
        found.update(p for p in root.glob(f"**/{pattern}") if p.is_file())
    return sorted(found)


def sweep(root: Path) -> tuple[list[Path], list[Finding]]:
    files = shell_tests(root)
    findings: list[Finding] = []
    for path in files:
        findings.extend(lint_file(path))
    return files, findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=REPO, help="repo to sweep")
    parser.add_argument("paths", nargs="*", type=Path, help="lint these files instead")
    args = parser.parse_args(argv)

    if args.paths:
        files = [p.resolve() for p in args.paths]
        findings = [f for p in files for f in lint_file(p)]
    else:
        files, findings = sweep(args.root.resolve())

    for finding in findings:
        print("FAIL " + finding.render(args.root.resolve()), file=sys.stderr)
    if findings:
        print(f"FAIL {len(findings)} dead assertion(s) in {len(files)} file(s)", file=sys.stderr)
        return 1
    if not files:
        # Absence is not success: a glob that matched nothing means the sweep
        # never ran, and that must not look like a clean sweep.
        print("NOTHING-TO-DO no shell test file matched", file=sys.stderr)
        return 3
    print(f"PASS no dead assertions ({len(files)} shell test file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
