# Repository Document Routes

The Skill follows repository-local documents before extracting code facts. It never substitutes a machine-local sibling checkout or chat history for a missing route.

## Compatible multi-hop route

```text
README.md
→ AGENTS.md / CLAUDE.md
→ ARCHITECTURE.md
→ CONTEXT.md or CONTEXT-MAP.md
→ docs/README.md
→ docs/DOCUMENT_ROUTING.md
→ docs/INTEGRATION_STATE.md
→ docs/STATE_MACHINES.md
→ docs/TRACEABILITY_INDEX.md
→ nearest [folder]/README.md
→ selected machine contract/schema/lock/eval/receipt
→ exact issue/PR task packet
→ source body
```

Not every repository needs every optional document. A required route declared by the repository or task packet that is missing is `ABSENT`.

## Matt Pocock setup pattern

The `setup-matt-pocock-skills` reference Skill contributes a useful repository configuration layer:

```text
docs/agents/issue-tracker.md
  where admitted work lives and how it is created/read

docs/agents/domain.md
  single-context or multi-context layout and consumer rules

docs/agents/triage-labels.md
  optional label mapping when triage is installed
```

Default domain layout:

```text
single-context
  CONTEXT.md
  docs/adr/
```

Use multi-context only for a real large monorepo:

```text
CONTEXT-MAP.md
→ root CONTEXT.md and/or per-context CONTEXT.md
→ context-local docs/adr/
```

The setup pattern edits the repository's existing Agent entrypoint rather than creating a conflicting second file. In this project family, both `AGENTS.md` and a thin `CLAUDE.md` may exist because they are deliberate host projections of one canonical routing contract; neither may fork repository rules.

## Route state machine

```text
TARGET REPOSITORY IDENTIFIED
→ ROOT ENTRYPOINTS DISCOVERED
→ CONTEXT LAYOUT CLASSIFIED
→ DOCUMENT INDEX FOLLOWED
→ NEAREST README OWNER FOUND
→ MACHINE SUBJECT FOUND
→ TASK/EVIDENCE SUBJECT FOUND
→ SOURCE SCOPE ADMITTED
```

Failure states:

```text
ROUTE_ABSENT
ROUTE_AMBIGUOUS
CURRENT_STATE_DUPLICATED
BROKEN_RELATIVE_LINK
MACHINE_LOCAL_PATH
STALE_CONTEXT
NO_PATH_OWNER
TASK_PACKET_ABSENT
```

## Context budget

Load only what the task needs:

```text
global laws
+ current state for the selected subject
+ nearest directory ownership
+ selected module/interface/eval
+ exact source scope
```

Do not preload every ADR, module, graph, memory, or prior plan. Follow one-hop links when a claim or decision needs them.

## Assertion requirements

A document route assertion checks:

- the path exists relative to the repository root;
- symlinks remain inside the admitted source/bundle boundary;
- required headings or explicit canonical redirects exist;
- only one current-state authority exists for the subject;
- no machine-local path or secret-shaped value is required;
- the source commit/tree used by the task is recorded.

Document presence is not source-code fact evidence. It provides scope, intent, ownership, and expected contracts that must be checked against implementation.
