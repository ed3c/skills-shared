# Runtime Identity Contract

Runtime identity is an execution fact, not a model-name guess and not a forge identity.

Use this precedence before any repository mutation:

```text
1. trusted launcher override (`AGENT_RUNTIME`, `AGENT_HOST`) when explicitly supplied
2. `GITHUB_ACTIONS=true` + GitHub run/repository/head identity => GITHUB_ACTIONS
3. local checkout + executable process/shell/git + launcher identity =>
   CLAUDE_CODE_LOCAL | CODEX_CLI_LOCAL | CHATGPT_DESKTOP_WORKTREE
4. GitHub connector/API capability without local checkout/process capability => CHATGPT_GITHUB_CONNECTOR
5. otherwise => UNKNOWN
```

Admitted runtime values:

```text
CHATGPT_GITHUB_CONNECTOR
GITHUB_ACTIONS
CLAUDE_CODE_LOCAL
CODEX_CLI_LOCAL
CHATGPT_DESKTOP_WORKTREE
UNKNOWN
```

## Non-equivalence laws

- `CHATGPT_GITHUB_CONNECTOR` is not a GitHub Actions runner. Connector/API access proves only admitted GitHub observation/mutation capability.
- `GITHUB_ACTIONS` is a CI workspace, not a developer worktree and not local Forgejo authority.
- `CLAUDE_CODE_LOCAL` and `CODEX_CLI_LOCAL` may claim local git/worktree execution only after the checkout/path/remotes are observed in that process.
- `CHATGPT_DESKTOP_WORKTREE` requires an actually created Desktop worktree with bound path, branch, and HEAD. Opening the Desktop app or pre-filling a deep link is insufficient.
- Model family (`GPT`, `Claude`, `Gemini`, etc.) does not determine runtime identity.
- Forge authority (`GitHub`, `Forgejo`) does not determine runtime identity.
- `UNKNOWN` fails closed for irreversible delivery, merge, push, publication, or environment-specific claims.

## Required runtime receipt

Before mutating delivery state, record at least:

```text
runtime
host
repository identity
working-directory state: PRESENT | ABSENT | UNKNOWN
local git capability: PASS | ABSENT | NOT_EXERCISED
GitHub connector capability: PASS | ABSENT | NOT_EXERCISED
GitHub Actions identity: PASS | ABSENT | NOT_EXERCISED
Forgejo binding: PASS | ABSENT | NOT_EXERCISED
branch
HEAD SHA
writer lease / session identity when available
```

If the runtime changes, previous environment evidence does not automatically transfer. Rebind the relevant capabilities and exact HEAD.

## Delivery routing

```text
CHATGPT_GITHUB_CONNECTOR
  -> GitHub ingress/triage/publication operations only through admitted connector tools
  -> local shell/worktree/Forgejo claims forbidden without separate evidence

GITHUB_ACTIONS
  -> CI/test/evidence on exact checked-out SHA
  -> no developer-worktree or local-Forgejo inference

CLAUDE_CODE_LOCAL | CODEX_CLI_LOCAL
  -> local git/worktree execution after capability probes
  -> Forgejo only when consumer binding resolves

CHATGPT_DESKTOP_WORKTREE
  -> local worktree execution after actual Desktop worktree path/branch/HEAD is bound

UNKNOWN
  -> read/diagnose only; no irreversible delivery transition
```

One mutable branch has one writer regardless of runtime. Three qualifying failures against the same target enter the existing fresh-diagnosis/new-worktree escalation loop.
