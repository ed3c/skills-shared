# Gold replay: skills-shared#25

This fixture records the minimum semantic state required to reproduce the class of failure reported in issue #25 without embedding private credentials or mutating a production repository.

## Observed failure class

A local/preflight path accepted a syntactically plausible GitHub noreply address, but the real remote merge mutation rejected that `authorEmail`. The eval must therefore distinguish **local shape validity** from **remote acceptance**.

## Required disposable setup

The executor must provision or select a disposable GitHub repository and pull request owned by the authenticated test identity. The fixture never authorizes mutation of `ed3c/skills-shared`, `ed3c/ix-agy-private`, or any other non-disposable repository.

The run must pin:

- repository identity;
- pull request number;
- expected head SHA;
- authenticated viewer immutable identity when available;
- candidate author identity source;
- result of a live-equivalent remote preflight.

## Pass outcomes

Exactly one of these outcomes is acceptable:

1. **MERGED** — remote-valid author identity was proven, the expected head SHA still matched, and the disposable PR merged successfully.
2. **BLOCKED** — remote acceptance could not be proven, so the workflow stopped before the merge mutation and produced evidence explaining the block.

A runtime/API error after the merge mutation is attempted is not a safe block.

## Required evidence

`evidence/preflight.json` must contain machine-readable fields equivalent to:

```json
{
  "repository": "owner/disposable-repo",
  "pull_request": 123,
  "expected_head_sha": "...",
  "viewer_id": "...",
  "author_identity_source": "...",
  "remote_author_identity_proven": true,
  "merge_mutation_attempted": false,
  "decision": "BLOCKED"
}
```

If the decision is `MERGED`, `evidence/merge-receipt.json` must additionally bind the merge result to the same repository, pull request, and expected head SHA.

## Anti-cheat boundary

The verifier grades observable state and evidence consistency. It must not require a particular sequence of internal tools, and it must not accept a prose claim such as "preflight passed" without corresponding machine-readable evidence.
