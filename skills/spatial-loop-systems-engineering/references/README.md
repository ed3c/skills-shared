# References

Reusable, host-neutral contracts selected by the procedural core.

| File | Purpose |
|---|---|
| [`system-prompt.md`](system-prompt.md) | Base copyable System / Spec Prompt for Claude Code, Codex CLI, and compatible coding agents |
| [`system-prompt-recovery-overlay.md`](system-prompt-recovery-overlay.md) | Mandatory repeated-failure recovery overlay: three-failure stop, fresh diagnosis, forge routing, worktree and publication gates |
| [`three-failure-escalation.md`](three-failure-escalation.md) | Full issue-packet, Forgejo/GitHub routing, ChatGPT Desktop handoff, isolated-worktree, commit/PR, and merge-boundary contract |
| [`spec-packet-template.md`](spec-packet-template.md) | Human-readable packet and `spatial-loop-system-contract/v1` field template |

Compose the **contents** of `system-prompt.md` followed by
`system-prompt-recovery-overlay.md` when installing the System / Spec Prompt.
The overlay is behavioral policy, not an optional worked example.

These files contain no consumer path, branch, credential, provider session, or
live evidence. Domain-specific interpretations belong under `../modules/`.
