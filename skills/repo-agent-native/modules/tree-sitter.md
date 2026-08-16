# Tree-sitter Module

## Trigger

Use when the task needs fault-tolerant syntax structure, exact function/class ranges, imports, signatures, call-site snippets, or AST skeletonization for a supported grammar.

## Non-trigger

Do not use Tree-sitter alone to prove cross-file symbol identity, type inference, dynamic dispatch, macro expansion, or runtime behavior.

## Purpose

Convert source bytes into bounded structural slices so a Worker receives the target body, dependency signatures, downstream call sites, and tests instead of whole unrelated files.

## Assumptions

```text
grammar source/version known
language-to-grammar route declared
exact source bytes and subject identified
parse error policy declared
query files reviewed and bounded
```

## State machine

```text
STRUCTURAL SLICE REQUESTED
→ GRAMMAR/LANGUAGE IDENTIFIED
→ SOURCE SUBJECT VERIFIED
→ CST/AST PARSED
→ QUERY MATCHES BOUNDED
→ SKELETON/SNIPPETS EMITTED
→ SOURCE RANGE READ BACK
→ ACCEPT / DOWNGRADE / FALLBACK
```

Failure states:

```text
GRAMMAR_ABSENT
UNSUPPORTED_LANGUAGE
SOURCE_CHANGED
PARSE_ERROR_OUTSIDE_TOLERANCE
QUERY_PATTERN_INVALID
RANGE_ESCAPE
SKELETON_DROPS_PUBLIC_CONTRACT
RESULT_CONTRADICTS_SOURCE
```

## Inputs

Exact subject, repository-relative files, grammar identity, structural query, target symbol/range, retained node kinds, omitted-body marker, snippet radius, byte/token budget, and parse-error tolerance.

## Outputs and effects

AST/CST node ranges, signatures, imports, docstrings, skeletons, call-site snippets, parse warnings, and source references. Effects are read-only. Structural matches are candidates until any semantic claim is checked through source/compiler/test evidence.

## Evidence class and freshness

Tree-sitter provides deterministic structural `A-` evidence for the exact parsed bytes. It does not provide compiler semantics. Parse recovery, grammar gaps, and generated syntax must be visible in the receipt.

## Fallback

Use direct source ranges, repository parsers, language-native ASTs, Serena/native LSP, compiler diagnostics, and tests. Never invent a skeleton when parsing is outside the admitted tolerance.

## Core laws that remain authoritative

`../SKILL.md` remains authoritative for source truth, evidence ceilings, permissions, repair bounds, and completion.

## Consumer-owned values

Grammar binaries, query files, language routes, parser cache, generated/vendor exclusions, resource limits, and live parse receipts remain outside this module.
