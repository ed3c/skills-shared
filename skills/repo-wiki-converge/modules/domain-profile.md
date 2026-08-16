# Repository-wiki convergence domain profile

Historical provider- and consumer-specific operating detail was extracted from the pre-refactor `SKILL.md` blob `608d3a5a1474fd5de478171a8fe1974f75d3b0ce`.

## Trigger
Load this module when a concrete author model, judge model, wiki generator, knowledge-base ingest path, or consumer repository must be selected.

## Non-trigger
Do not load it for generic repository-grounding, author/judge separation, convergence criteria, claim verification, or handoff design.

## Assumptions
- Repository source is the primary ground truth for repository facts.
- Author and judge roles may be implemented by different models or deterministic tools.
- Wiki/KB publication is optional downstream transport, not completion authority.

## Specialization inventory
- Named author/judge model pairings belong here.
- openwiki-style generation, KB ingest, RepoDoc lanes, local runner paths, and consumer-specific artifacts belong here.
- Provider rate limits, credentials, model settings, and live runtime receipts stay runtime-owned.

## Evidence ceiling
A generated wiki, model verdict, or successful ingest is not sufficient for convergence `PASS`; exact source-bound verification and declared acceptance criteria remain required.

## Fallback
If an author/judge/provider/ingest capability is unavailable, preserve the repository fact packet and unresolved claim list and return the unavailable lane as `ABSENT`, `NOT_IMPLEMENTED`, or `NOT_EXERCISED`.

## Forbidden overrides
This module may not override `CORE-LAW-001` through `CORE-LAW-005`, weaken source-grounding or reviewer independence, or widen network/secret/merge/release authority.
