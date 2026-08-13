# Repository document-routing reference

Use this reference when a continuity task spans multiple files, directories, or repositories.

## Route chain

```text
README.md
→ AGENTS.md / CLAUDE.md
→ CONTEXT.md + ARCHITECTURE.md
→ docs/INDEX.md
→ nearest directory README.md
→ machine authority
→ traceability/evidence
```

The route names and assertion IDs are defined in [`../../../docs/architecture/DOCUMENT_ROUTING.md`](../../../docs/architecture/DOCUMENT_ROUTING.md).

## Continuity requirements

1. Every hop leaves a local summary before linking away.
2. The nearest README names owner, purpose, inputs, outputs, transitions, evidence, and forbidden coupling.
3. The link lands on the source, not another unexplained index.
4. Current state and target design remain separate.
5. Missing evidence is named, never inferred.
6. Machine authority is explicit.
7. Cross-repository facts use immutable release/binding/receipt identity, not sibling filesystem paths.

## Skill-layer requirements

```text
SKILL.md      procedural method
references/   reusable generic contracts
modules/      domain instances on demand
```

If a domain example is needed to understand the procedure, summarize the relevant rule in the core and leave the detailed example in `modules/`.
