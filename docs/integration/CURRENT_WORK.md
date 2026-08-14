# Current Work

Snapshot date: 2026-08-13. Query GitHub for exact current heads.

## Completed control-plane stack

PRs #72, #73, #74, #75, #76, #77, #85, and #91 are merged.

The Skill Eval control-plane stack is implemented. Capability and release registries remain empty, so the first real capability unlock is still not exercised.

## Active repo-agent-native v2 work

Issue #89 is the canonical PRD.

```text
#91 contract and eval admission — merged
  -> #92 portable core and Bun assertions — active
     -> tool adapters and blind A/B — next child
        -> Bettor consumer migration — later cross-repository leaf
```

Active Phase 2 branch: `feat/repo-agent-native-v2-core`.

PR #87 is an older monolithic design branch. It overlaps the newer contract-first structure and should be treated as historical input rather than the active landing path.

## Physical evaluation boundary

Issue #37 remains open. The same admitted case still needs real execution through at least two harnesses before a capability unlock can be claimed.

## Other active debt

Issue #83 tracks the local verification relative-root selftest defect.

## Agent continuation

Read this file after `docs/AGENT_INTEGRATION_STATE.md`, then query GitHub metadata before changing a branch or PR. Keep one state transition per molecular PR when practical.
