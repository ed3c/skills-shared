# Conversation-research domain profile

This module owns provider-, browser-, storage-, and consumer-specific interpretations that were previously embedded in the canonical procedure. Historical operational detail remains recoverable from the pre-refactor `SKILL.md` blob `2abd9551aea24d6d246006f1fb0369f0bbed0276`.

## Trigger

Load this module only when a concrete conversation provider, browser carrier, deep-research engine, knowledge store, or consumer repository must be bound for execution.

## Non-trigger

Do not load it for provider-neutral conversation analysis, gap classification, evidence planning, coverage calculation, or handoff design.

## Assumptions

- Provider sessions, browser tabs, credentials, local paths, and live research engines are runtime-owned.
- Long source conversations may require file-based isolation before model analysis.
- A deep-research engine is an optional capability, not the procedural authority.

## Specialization inventory

- Gemini and AI Studio URL/session handling belongs here.
- Chrome/CDP extraction, browser adapters, `automate.js`, deep-research launch/extract mechanics, and content-isolation recipes belong here.
- Provider-specific knowledge-ingest/KG mappings and consumer repository paths belong here.
- Cross-Skill provider bindings may route to `external-verify` or other admitted capabilities, but those bindings remain explicit.

## Evidence ceiling

This module can describe or bind a concrete provider path. It cannot turn an installed browser, reachable session, provider response, or static fixture into runtime `PASS`; only an exact-subject receipt may do that.

## Fallback

When provider/browser/deep-research capabilities are absent, preserve the portable analysis/gap packet and return `ABSENT`, `NOT_IMPLEMENTED`, or `NOT_EXERCISED` for the unavailable lane instead of fabricating completion.

## Forbidden overrides

This module may not override `CORE-LAW-001` through `CORE-LAW-005`, weaken content-isolation or evidence rules, widen filesystem/network/secret authority, or create merge/release authority.
