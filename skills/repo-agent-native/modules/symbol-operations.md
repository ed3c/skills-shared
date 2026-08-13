# Symbol operations module

## Trigger

Use for symbol definitions, references, implementations, diagnostics, hierarchy, rename planning, or symbol-scoped edits where language-aware structure reduces text-surgery risk.

## Non-trigger

Do not use when the language/workspace backend is uninitialized, when generated code invalidates symbol ownership, or when a simple direct read is sufficient.

## Inputs

```text
repository and workspace identity
language/backend identity
symbol or file
operation: locate, references, diagnostics, edit-plan, or bounded edit
allowed paths and write policy
```

Concrete providers may use an LSP, compiler index, IDE backend, or another symbol service. The consumer binding owns provider configuration and write permissions.

## Process

1. Confirm the active project, workspace root, languages, backend, and read/write mode.
2. Retrieve symbol metadata or reference candidates.
3. Read back the relevant definitions and call sites from current source bytes.
4. For edit planning, enumerate public-contract and test impact before writing.
5. For an admitted edit, constrain paths, preserve named exits/effects, run diagnostics/tests, and record exact touched symbols.

## Outputs

```text
provider/workspace observation
symbol definition and reference candidates
source readback set
edit or impact plan
post-edit diagnostics and tests when exercised
```

## Evidence ceiling

Symbol metadata without source readback is at most `A-` candidate evidence. Diagnostics establish only the executed backend's declared checks. A successful rename or edit does not prove product behavior.

## Fallback

Use exact search plus direct source read. Refuse a symbol-level edit when reference completeness is required but the workspace/backend cannot provide it and deterministic search cannot bound the risk.

## Authoritative laws

The Core laws on source identity, scope, evidence separation, fail-closed fallback, assertions, and Human Admit remain authoritative.
