# Host Compatibility

## Portable authoring profile

The canonical `SKILL.md` targets the intersection of the open Agent Skills format, Codex CLI, and Claude Code.

```text
required portable frontmatter
  name
  description

portable optional frontmatter
  license
  compatibility
  metadata

portable resources
  scripts/
  references/
  assets/
  additional directories with explicit relative links
```

`allowed-tools` exists in the open specification as experimental and has host-specific semantics. The portable core does not rely on it for security or correctness.

## Host matrix

| Capability | Open Agent Skills | Codex CLI | Claude Code | repo-agent-native rule |
|---|---|---|---|---|
| Required entry | `SKILL.md` | `SKILL.md` | `SKILL.md` | one canonical file |
| Required metadata | `name`, `description` | `name`, `description` | fields are more permissive | use stricter open/Codex requirements |
| Executable resources | `scripts/` | supported through Agent tools/sandbox | supported through Agent tools/permissions | explicit I/O and stable exits |
| Reference docs | `references/` | on demand | on demand | one-hop links from `SKILL.md` |
| Assets/templates | `assets/` | supported | supporting files supported | optional |
| OpenAI metadata | not standard | `agents/openai.yaml` | ignored | UI/invocation metadata only |
| Explicit invocation | host-defined | `/skills` or `$repo-agent-native` | `/repo-agent-native` | document both; do not assume one syntax |
| Automatic invocation | description match | description match | description/when-to-use match | concise front-loaded description |
| Claude task controls | not standard | ignored | e.g. `disable-model-invocation`, `context`, `agent` | keep out of canonical core; use a host projection only when needed |
| Claude dynamic shell injection | not standard | unsupported | `!` command expansion | forbidden in portable core |

## Codex discovery

Codex scans `.agents/skills` from the working directory up to the repository root, plus user/admin/system locations. Symlinked skill directories are supported, but an immutable run must not depend on a machine-local absolute target.

## Claude discovery

Claude project Skills live under `.claude/skills`. User-only Skills do not automatically appear in remote/cloud sessions; a cloud-capable project must commit or install the selected Skill through a reproducible project/plugin route.

## Code execution

A script is not executed merely because it exists. The active Agent must invoke it through the host's shell/tool layer, subject to sandbox, trust, and permission policy.

Portable scripts must:

- accept explicit input and output paths;
- avoid implicit current-working-directory assumptions;
- default to no network;
- bound runtime, output, and retries;
- emit useful stderr and stable named exits;
- avoid secret/session values and owner-checkout dependency borrowing;
- be re-runnable on a fresh clone or immutable bundle.

Planned exit contract:

```text
0   assertion passed
2   subject was evaluated and failed a domain assertion
64  usage, schema, required input, or evidence subject is absent/invalid
70  internal mechanism error
124 timeout
```

## Assertion layers

```text
natural-language checklist     guidance only
Bun/TypeScript assertion       deterministic mechanism
compiler/test/public control   behavioral observation
receipt                         subject-bound claim
Human Admit                     merge/promotion authority
```

A checklist may guide the Agent, but only executable assertions and relevant controls can produce a machine PASS.

## Sources

- Open Agent Skills specification: `https://agentskills.io/specification`
- OpenAI build-skills documentation: `https://developers.openai.com/codex/skills/`
- Claude Code skills documentation: `https://code.claude.com/docs/en/skills`
- Reference setup pattern: `https://github.com/mattpocock/skills/tree/main/skills/engineering/setup-matt-pocock-skills`
