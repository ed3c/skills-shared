# Agent Host Procedural Grounding

> Dated adapter map: 2026-08-15. Host behavior is mutable external state; verify
> current official documentation before binding a production adapter.

## Trigger

Load this module when the task requires one or more of:

- searching/installing Agent Skills from an external catalog;
- running a Skill in Claude Code, Codex CLI/app, VS Code/Copilot, Gemini CLI, or
  another Agent host;
- isolating Skill analysis from the parent context;
- comparing no-Skill versus with-Skill task performance;
- observing whether procedures reached artifacts, commands, or runtime evidence.

This module extends the universal method and
[`../references/procedural-grounding-shadow-plane.md`](../references/procedural-grounding-shadow-plane.md).
It does not grant network, installation, script, tool, or private-data authority.

## Service and host roles

Do not treat discovery, installation, loading, execution, and evaluation as one
state machine.

| Surface | Useful role | Not evidence of |
|---|---|---|
| [Agent Skills standard](https://agentskills.io/specification) | portable `SKILL.md` format and progressive disclosure | host-specific isolation, runtime success, or capability lift |
| [Vercel `skills` / skills.sh](https://github.com/vercel-labs/skills) | cross-Agent search, install, and direct-use distribution | source trust, procedure execution, or semantic correctness |
| [Skillsmith](https://www.skillsmith.app/) | semantic discovery, quality/security/lifecycle metadata, stack-aware recommendations | a deterministic task outcome unless a separate execution/eval receipt exists |
| [Claude Code Skills](https://code.claude.com/docs/en/skills) | native Skill loading, dynamic context, hooks, and `context: fork` subagent execution | model independence or exact runtime proof without receipts |
| [VS Code Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills) | project/user Skills and experimental isolated execution | parity with every Claude-specific frontmatter field |
| [OpenAI Codex](https://openai.com/index/introducing-the-codex-app/) | Skills plus parallel Agents, worktrees, automations, and sandboxed execution | documented support for Claude's `context: fork` frontmatter semantics |
| [Gemini CLI Skills](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md) | metadata discovery, explicit activation, consent, and progressive disclosure | a native isolated Skill fork unless separately documented and observed |
| [Agent Skills evaluation guidance](https://agentskills.io/skill-creation/evaluating-skills) | clean-context with-Skill/no-Skill trials and concrete assertions | release/capability truth without real repeated runs |

An adapter must bind the exact source and host behavior it actually observed.
Never infer a host capability from another host's compatible file format.

## Discovery adapter

A discovery provider returns candidates, never executable truth.

Required normalized output:

```text
query identity
provider identity and observed API/CLI version
candidate Skill name and description
repository/ref/path
blob SHA and content SHA-256
license/use state
quality/security metadata with provenance
scripts/hooks/MCP/dynamic-context inventory
installation or direct-use command as an unexecuted proposal
```

The orchestrator then:

```text
candidate discovery
→ exact source fetch
→ provenance/license/script/dynamic-context review
→ procedure extraction
→ relevance selection
→ execution admission
```

Search ranking, popularity, quality score, or one-click installation cannot skip
source review.

### `skills.sh` / Vercel `skills`

Use as a distribution and discovery adapter. Pin the resulting repository/ref
and hash the selected Skill bytes. Direct-use mode is still a context/data
transition and must be represented in the source receipt.

Do not credit procedures merely because the CLI reports that a Skill was found,
installed, or used.

### Skillsmith

Use Skillsmith metadata to narrow candidate search and prioritize review. Keep
its documentation/security/maintenance scores separate from the repository's
verified-capability scorecard.

Unless Skillsmith or another connected adapter returns content-bound task-run
traces plus deterministic verifier receipts, classify task execution as
`NOT_EXERCISED`. For executable task evals, bind a separate harness adapter.

## Claude Code adapter

Claude Code documents native Skill execution in a forked subagent context using:

```yaml
context: fork
agent: <subagent-type>
```

Adapter mapping:

```text
host feature              Procedural Grounding field
context: fork             execution_mode=SEPARATE_CONTEXT
subagent/session identity context_provenance
model override            model_provenance when observed
skill invocation          fork checkpoint + input procedure IDs
subagent final result     proposed Context Capsule input
hooks                     deterministic pre/post enforcement receipts
```

Rules:

- bind the actual subagent/session identity;
- do not claim model independence when the fork inherits the same model;
- reject a full free-form subagent transcript as a capsule;
- summarize only source-grounded actionable deltas with procedure IDs;
- use hooks or an external checker for L3 conditions that prose cannot enforce;
- preserve dynamic context command output as untrusted runtime input with a
  digest and egress review.

## VS Code / Copilot adapter

Where experimental isolated Skill execution is enabled, map it to
`SEPARATE_CONTEXT` only after the final-result-only return and context provenance
are observed. Custom Agents, hooks, and MCP servers are separate capabilities
and supply-chain surfaces.

If the host merely injects `SKILL.md` into the main conversation, use
`IN_PROCESS_LOGICAL`; context independence remains `NOT_EXERCISED`.

## Codex CLI/app adapter

Codex supports Skills and multi-Agent/worktree/automation workflows, but the
adapter must not assume Claude-specific `context: fork` frontmatter behavior.

Use one of these admitted implementations:

```text
Codex child Agent/thread with bound identity
  → SEPARATE_CONTEXT

Codex child Agent using a separately bound model/config
  → SEPARATE_MODEL

Automation or orchestrator task with a content-addressed fork packet
  → SEPARATE_CONTEXT when provenance and isolation are observed

same Codex conversation analyzing the Skill
  → IN_PROCESS_LOGICAL; independence NOT_EXERCISED
```

The parent repository multi-Agent runtime contract owns Worker identity, base,
lease, budget, checkpoint, result, and stale-attempt rejection. The grounding
fork may be read-only and need not own a code branch when it returns only a
Context Capsule. Any implementation mutation still requires a normal Worker path
lease.

Codex-observable evidence should prefer repository files, terminal logs, test
reports, browser/DOM/screenshot artifacts, and exact worktree/commit identities
over model self-report.

## Gemini CLI adapter

Gemini CLI's documented lifecycle discovers metadata, explicitly activates a
Skill, requests consent, then injects the full instructions and resource access.
Map:

```text
metadata discovery       DISCOVERED
activate_skill           source/body loaded
user consent             host-owned authority receipt
injected instructions    parent-context input, not execution proof
resource/tool use        observation only when exact calls and results bind
```

Do not label it `SEPARATE_CONTEXT` without a separately observed fork mechanism.

## Eval harness adapter

Use the canonical condition matrix:

```text
NO_SKILL
METADATA_ONLY
FULL_SKILL
FULL_SKILL_PLUS_GROUNDING
```

For each trial bind:

```text
task/case identity
condition
Skill SHA and procedure-set digest
model/config
host/harness/environment
seed or nondeterminism policy
retry count
tool policy
context digest
run trace
artifact identities
verifier receipt
cost/tokens/duration
```

A suitable external harness may include a real Claude/Codex runner, an
Agent-Skills-compatible eval suite, or a consumer-owned Arena adapter. Normalize
all results into the repository's run-trace/evidence-bundle contracts; do not let
an external score become semantic authority by itself.

Minimum graders:

```text
code/deterministic grader
  for exact artifacts, commands, assertions, and negative controls

model grader
  only for semantic qualities that cannot be reduced to a stable code oracle

Human grader
  for Human-owned product, legal, security, or ambiguous acceptance boundaries
```

Prefer deterministic outcome verification for hard gates. Keep instruction
adherence and task outcome separate: a Skill can be followed faithfully and
still produce a poor result, or produce a good result while omitting a critical
procedure.

## Multimodal adapter contract

Each adapter normalizes observations to:

```text
procedure_id
modality
exact subject
content digest
oracle
expected
observed
exit code when applicable
timestamp/freshness
immutable reference
```

Examples:

| Host evidence | Strong use | Required companion |
|---|---|---|
| terminal stdout/stderr/exit | command execution | exact worktree/commit and semantic oracle |
| file diff/artifact | Harness encoding | content digest and owning assertion |
| test report | deterministic behavior | negative-control calibration |
| browser DOM/accessibility | semantic UI structure | route/session identity |
| screenshot/video | visual state | visual oracle; not database/auth proof |
| device trace | mobile lifecycle/runtime | app/build/device identity |
| provider/forge API | external state | exact object/run/head identity |

## Security and private-data boundary

External Skill catalogs and host extensions are supply-chain inputs.

Before execution inspect:

```text
scripts and inline shell
dynamic-context commands
hooks
MCP servers and tool schemas
network destinations
telemetry
filesystem/write scope
secret access
private repository/data egress
license and attribution
```

Run untrusted executable content with least privilege, bounded tools, denied
ambient secrets, and explicit network/egress policy. A compatible Skill format
is not a sandbox.

## Evidence boundary

```text
host/service adapter mapping                    IMPLEMENTED as dated guidance
live skills.sh or Skillsmith API/CLI integration NOT_EXERCISED
live Claude context:fork receipt                NOT_EXERCISED
live VS Code isolated Skill execution           NOT_EXERCISED
live Codex child-thread grounding adapter       NOT_EXERCISED
live Gemini activation receipt                  NOT_EXERCISED
real four-condition Claude/Codex eval matrix    NOT_EXERCISED
security/production acceptance                  HUMAN_ADMIT_REQUIRED
```
