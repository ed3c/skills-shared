# Specs-as-code output template

## Trigger

Use only after the source-anchored invariant pass when the caller explicitly requests durable or plan-scoped architecture/data-flow/security specifications.

## Non-trigger

Do not use as a standalone prompt that bypasses scope, routing, source readback, assertions, or repository ownership.

## Inputs

```text
subject identity and scope
confirmed invariants and source references
negative invariants and search boundaries
implicit dependencies and unresolved edges
repository document/output policy
```

## Template

```markdown
# <Specification title>

## Subject
- Repository/subtree: `<relative subject>`
- Immutable identity: `<commit/tree>`
- Scope: `<included>`
- Exclusions: `<excluded>`

## Authority and routes read
| Authority | Subject | State |
|---|---|---|

## Contract map
| ID | Owner | Public boundary | Inputs | Outputs | Effects | Exits | Evidence |
|---|---|---|---|---|---|---|---|

## State machine
```text
<states and transitions>
```

## Data flow
```text
<typed packets, artifacts, public ports, and receipts>
```

## Invariants
| ID | Claim | Level | Source refs | Falsifier |
|---|---|---|---|---|

## Negative invariants
| ID | Claim | Search boundary | Result | Limitation |
|---|---|---|---|---|

## Implicit dependencies
| ID | Known facts | Inference | Failure chain | Resolution |
|---|---|---|---|---|

## Security, limits, and cleanup
- Trust boundaries:
- Permission/effect boundaries:
- Time/output/retry limits:
- Cleanup/rollback:
- Current execution evidence:

## Unresolved evidence
| Question | Evidence needed | Owner | Blocking state |
|---|---|---|---|

## Assertions and handoff
- Commands and exits:
- Artifacts:
- Remaining evidence states:
- Human Admit:
- Rollback subject:
```

Replace placeholders with subject-bound facts. Preserve IDs and evidence levels from the analysis artifact.

## Outputs

One or more repository-approved specification files plus a link back to the machine-readable invariant artifact.

## Evidence ceiling

The template adds no evidence. Every populated claim inherits the evidence level and subject identity of its source record.

## Fallback

When a section lacks evidence, keep the section with an explicit unresolved state or omit it according to repository policy. Never invent content to make the template appear complete.

## Authoritative laws

The Core laws in [`../SKILL.md`](../SKILL.md) remain authoritative, especially no authority collapse, source references, and Human Admit for durable law.
