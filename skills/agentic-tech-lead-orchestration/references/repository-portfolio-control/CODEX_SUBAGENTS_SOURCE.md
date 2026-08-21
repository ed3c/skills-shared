# Codex Subagent Configuration Source Disposition

Observed: `2026-08-21`  
Canonical locator: `https://learn.chatgpt.com/docs/agent-configuration/subagents`  
Classification: `PRIMARY_SOURCE_CONFIRMED / MUTABLE_WEB_DOCUMENT`  
Immutable source bytes: `ABSENT`

The current official documentation confirms these bounded configuration facts:

- local Codex may delegate after a direct request or applicable `AGENTS.md` / Skill instruction;
- the main thread collects subagent results;
- parallel read-heavy work is the recommended starting point, while parallel writers require more care;
- project-scoped custom agents live under `.codex/agents/*.toml`;
- each custom-agent file requires `name`, `description`, and `developer_instructions`;
- `model`, `model_reasoning_effort`, and `sandbox_mode` are supported agent-file settings;
- global controls are under `[agents]`, including concurrency and default model/reasoning settings.

The source is a mutable web document. Its visibility is not an immutable source packet and
does not prove that any local Codex version supports these fields. Consumer bootstrap and
runtime admission must probe the installed Codex version, read back generated files, and
record unsupported or changed fields as `RUNTIME_DRIFT` / `NOT_EXERCISED`.
