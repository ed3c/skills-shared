# Document routing module

## Trigger

Use when a repository has root context, a context map, ADRs, `docs/agents/` policy, nearest-directory READMEs, or an explicit multi-hop document route.

## Non-trigger

Do not load every document recursively. Skip this module when the task is fully bounded by an explicit source file and no repository policy or architectural decision can affect the answer.

## Inputs

```text
repository root
required route names from the task or binding
current working scope
context budget
```

## Process

Prefer the following route when present:

```text
README.md
→ AGENTS.md or host entrypoint
→ ARCHITECTURE.md
→ CONTEXT.md or CONTEXT-MAP.md
→ docs/README.md
→ docs/agents/domain.md
→ relevant docs/adr/
→ nearest directory README.md
→ machine contract/tests/receipts
→ exact issue/PR
```

`CONTEXT.md` supplies bounded domain vocabulary and stable context. `CONTEXT-MAP.md` is appropriate for a genuine multi-context repository and points to the relevant context files. `docs/agents/domain.md` explains how Agents consume these files; it does not replace them. ADR conflicts must be surfaced rather than silently overwritten.

Missing optional domain docs may be ignored when the repository policy says they are lazy. A route explicitly required by a task packet or repository contract is not optional and yields `REQUIRED_ROUTE_ABSENT` when missing.

## Outputs

```text
routes_read
routes_missing
route_authorities
applicable glossary terms
applicable ADRs and conflicts
nearest README and inherited rules
remaining source/test/receipt route
```

## Evidence ceiling

Documents establish declared intent, vocabulary, ownership, and decisions (`B`) unless the relevant behavior is independently established by source or execution. A document cannot turn a live provider or runtime state into `PASS`.

## Fallback

When no document route exists, record the absence and continue with deterministic source discovery only if no required route is missing. Do not replace missing repository context with chat history or memory.

## Authoritative laws

All Core laws in [`../SKILL.md`](../SKILL.md) remain authoritative, especially authority separation, source readback, and no self-admission.
