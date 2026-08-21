# AGENTS.md — Codex repository-portfolio role bindings

These files are thin `.toml.template` bindings for Codex CLI subagents. The canonical procedure remains `../prompts/repository-portfolio-controller-v3.md` and `../REPOSITORY_PORTFOLIO_CONTROL.md`.

## Required route

```text
root AGENTS
→ Tech Lead AGENTS
→ prompts/AGENTS.md
→ Repository Portfolio Controller v3
→ exact dispatch schema and packet
→ this AGENTS.md
→ selected role template only
→ exact result and join contracts
```

## Role classes

```text
portfolio-explorer          READ_ONLY
acceptance-adversary        READ_ONLY
 dependency-auditor         READ_ONLY
runtime-admission-auditor   READ_ONLY
implementation-worker       WORKSPACE_WRITE / one exclusive lease
consolidation-verifier      READ_ONLY
release-auditor             READ_ONLY
```

A read-only role cannot receive an exclusive writer lease. An implementation Worker must receive exactly one bounded task/attempt/worktree/branch lease and may not edit frozen contracts, oracles, evidence ceilings or another Worker's paths.

## Identity and dispatch laws

- Resolve `${MODEL_ID}` and `${REASONING_EFFORT}` in consumer-local generated bindings; unresolved placeholders are not executable packets.
- Bind provider, carrier, exact model/version, configuration digest, sandbox, approvals and private-egress state.
- Fable/Opus/Sonnet names are aliases only; an alias is never an exact execution identity.
- Preserve all terminal states in the denominator.
- Keep the exact sentence below in every role:

```text
Use subagents. Wait for all agents and consolidate their findings.
```

- Do not recursively spawn unbounded agents.
- Do not persist transcripts, terminal screens, credentials, private source content or private chain of thought.
- Agent results remain candidate evidence until schema, lease, exact-subject, oracle, cleanup and all-agent join gates pass.

## Consumer projection

A consumer may generate `.codex/agents/*.toml` from these templates only when it pins the exact `skills-shared` commit/tree and template digest. Consumer policy may tighten sandbox, budgets, paths, tools, egress and authority. It may not weaken shared laws or copy the canonical prompt body into a divergent local authority.
