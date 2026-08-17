# Tool Routing

The procedural core works with deterministic source tools alone. Optional tools are selected by capability, exact subject and health—not installation popularity.

## Routing order

```text
Tier 0  git + rg + repository-relative direct read
Tier 1  semantic intent candidates
Tier 2a interactive symbol/LSP diagnostics
Tier 2b compiler-derived semantic index
Tier 3  syntax structure and skeletonization
Tier 4  subject-bound normalized projection
Tier M  episodic/project memory
Tier X  compiler/tests/public-port/runtime controls
```

Tier X is a behavioral evidence lane, not a later retrieval tier.

## Tool health state machine

```text
CAPABILITY REQUESTED
→ PRODUCER/PROVIDER DISCOVERED
→ EXACT IDENTITY RECORDED
→ PROJECT + SUBJECT + COVERAGE MATCHED
→ FRESHNESS/SCOPE CHECKED
→ QUERY/PARSE EXECUTED
→ RESULT READ BACK AGAINST SOURCE
→ RESULT ACCEPTED OR DOWNGRADED
```

Failure states:

```text
PROVIDER_ABSENT
PROVIDER_UNREACHABLE
WRONG_PROJECT
STALE_SUBJECT
PARTIAL_LANGUAGE_COVERAGE
UNSUPPORTED_LANGUAGE
NAMESPACE_MISMATCH
SOURCE_CHANGED
RESULT_CONTRADICTS_SOURCE
OUTPUT_LIMIT
```

Every failure has a Tier-0 fallback unless the task specifically requires the missing relation class.

## Current capability routes

| Capability | Current route | Strength | Cost/risk | Default role |
|---|---|---|---|---|
| semantic intent search | grepai | local concept search, watcher, MCP | embedding/index freshness; negative results incomplete | optional seed lane |
| interactive symbols/diagnostics | Serena/LSP | definitions, references, diagnostics, edit planning | project/server health and language variance | optional interactive lane |
| compiler semantic relations | SCIP indexers | stable global symbols, Def/Ref/type edges | build/config/language coverage; batch index cost | preferred impact-edge lane when healthy |
| syntax/skeletons | Tree-sitter | tolerant AST/CST ranges and structural queries | no cross-file type inference | structural slicing lane |
| normalized graph/projection | SQLite | embedded, inspectable, transactional, rebuildable | schema/subject/producer drift | deterministic storage/query lane |
| episodic context | mem0 or admitted memory provider | prior decisions and incident context | privacy, freshness and conflicts | optional memory lane |
| cross-lane absence | Blindspot Hybrid ledger | turns lane disagreement and missing coverage into a stated verdict | only as complete as the lanes feeding it | the lane that decides what absence means |

The composed route is [`../modules/compiler-truth-context-funnel.md`](../modules/compiler-truth-context-funnel.md). The Code-Graph-RAG retirement decision is [`CODE_GRAPH_RAG_RETIREMENT.md`](CODE_GRAPH_RAG_RETIREMENT.md).

## Selection rules

### grepai

Use to turn fuzzy intent into a small candidate set. Record exact workspace/index identity, cap results, and read every promoted result from current source.

### Serena

Use for interactive symbol/reference/diagnostic operations when the exact project and language backend are healthy. Treat edit output as a proposal unless the host separately grants mutation authority.

### SCIP

Use for compiler-derived cross-file relations when the exact commit/tree, indexer and language/path coverage are known. Do not describe partial coverage as 100% completeness.

### Tree-sitter

Use for exact-byte ranges, signatures, imports, snippets and skeletons. Do not infer type identity or runtime behavior from syntax alone.

### Blindspot Hybrid

Use when a question is about *absence* — nothing calls this, no handler exists,
this path is unreachable. Every other lane answers "I did not find it", and the
routing table above already says why that is not the same claim: an embedding
miss, a partial-coverage index, a parse hole and an unsupported language all
look identical from the caller's side.

[`BLINDSPOT_HYBRID_CONTRACT.md`](BLINDSPOT_HYBRID_CONTRACT.md) makes the
difference decidable. Lane events land in a subject-bound SQLite ledger with a
declared kind, the ledger moves `INITIALIZED → INGESTED → PASS`, and `PASS` is
reachable only when no blindspot assertion holds:

```text
SOURCE_READBACK_MISSING     a candidate was never confirmed against current source
AST_COVERAGE_MISSING        the structural lane never covered the range in question
LINK_TARGET_MISSING         an event points at something the ledger does not contain
READBACK_TARGET_INVALID     the read-back names a target the source does not have
VECTOR_PROJECTION_ORPHAN    a similarity row with no source lane behind it
VECTOR_PROJECTION_CHAINED   a projection built on another projection
TEST_OBSERVATION_FAILED     the behavioural lane contradicts the claim
PROVIDER_SELF_ADMISSION     a provider admitted its own output as truth
EVENT_ID_DRIFT              the same logical event under two identities
EVENT_SUBJECT_MISMATCH      an event bound to a different subject than the ledger
```

Exit `0` accepts the closure, `2` means an assertion failed or blindspots
remain, `64` unusable input, `70` a mechanism failure.

The inversion is the point. Every other lane reports what it found; this one
refuses to close while a reason for not-finding is still standing. An absence
survives only when none of the above explains it. Method:
[`../modules/blindspot-hybrid.md`](../modules/blindspot-hybrid.md). Checker:
[`../scripts/blindspot_contract.py`](../scripts/blindspot_contract.py). Controls:
[`../tests/blindspot-hybrid/verify.sh`](../tests/blindspot-hybrid/verify.sh).

A LanceDB projection may be rebuilt over the ledger; it is never the authority
and the contract refuses a vector projection with no source lane behind it.

### SQLite

Use only as a subject-bound projection of normalized observations. Database integrity proves the projection shape, not repository semantics. Refuse subject mismatch and rebuild stale stores.

### Memory

Use only for prior decisions, preferences, incident history or continuity. Current repository authority wins conflicts; writes require a separate policy.

## Commercial exclusion

GitNexus is not admitted for the commercial core while the upstream repository is licensed under PolyForm Noncommercial. Popularity does not override license policy.

## Tool receipt

A run records:

```text
producer/provider version or commit
capability requested
repository/commit/tree
project/index/grammar/schema identity
language and path coverage
freshness observation
query/depth/byte budget
result count
source read-back count
fallback taken
warnings and exclusions
```

Provider presence, query success, parse success and database integrity are not source-truth PASS.

### Producing and checking one

This section described a receipt for as long as nothing produced one, which is
indistinguishable from a routed lane that never ran. Two scripts close that gap,
and they deliberately share no code path:

```bash
# the only lane that starts a process or opens a socket
python3 skills/repo-agent-native/scripts/capture_adapter_receipt.py \
  --repo-root . --out skills/repo-agent-native/evals/receipts

# zero network, zero provider execution; runnable where no provider exists
python3 skills/repo-agent-native/scripts/check_adapter_receipts.py check
python3 skills/repo-agent-native/scripts/check_adapter_receipts.py selftest

# bind another subject's receipt as a reference, never as a lane: this prints
# CROSS_SUBJECT_BINDING only while the two subjects are different commits, and
# refuses SUBJECT_COLLAPSED when they are the same
python3 skills/repo-agent-native/scripts/check_adapter_receipts.py check \
  --bind-scheduler skills/dual-forge-repository-loop/evals/receipts/scheduler-run.receipt.json
```

Captured receipts live in [`../evals/receipts/`](../evals/receipts/), one file per
lane. A lane whose provider is absent still gets a receipt: omitting it reads
exactly like a lane that passed.

The checker refuses, each with its own code: an unbound or dirty subject, an
unidentified provider, an undeclared network/filesystem/secret policy, an
unbounded budget, a state laundered against its own execution record (an
`ABSENT` lane carrying a duration, or `PASS` on a non-zero exit), an evidence
level the read-back does not support, a missing read-back record, undeclared
residue, a credential-shaped value, and — the one that matters most — a `PASS`
whose controls all agreed with it.

### A lane that starts an admitted external artifact

The `git-town` lane runs a binary this repository deliberately does not install.
It is gated by a Human admission record,
[`../evals/git-town-darwin-admission.json`](../evals/git-town-darwin-admission.json),
and the gate compares SHA-256 rather than version strings: one release version
ships as several artifacts, so a version match would admit whichever file
happened to be on the host.

```bash
python3 skills/repo-agent-native/scripts/capture_adapter_receipt.py \
  --repo-root . --out <capture directory> --lane git-town \
  --git-town-bin <path to the extracted artifact>
```

Three outcomes, three states. No binary is `ABSENT` — the provider is not here.
A binary whose digest is not the admitted one is `SKIPPED_BY_POLICY` and nothing
starts. Only an exact digest match runs. The lane then builds its own repository
and bare remote under `TMPDIR`, runs `hack`, `append` and
`sync --stack --no-push` there, and reads the resulting stack back out of
`git config` and `git merge-base` rather than out of git-town's own output — a
provider confirming its own claim is `PROVIDER_SELF_ADMISSION`. Nothing it does
touches this checkout, and the refusal path is exercised inside the receipt by
flipping one byte of a copy of the admitted binary.

`A` and `A-` contain a read-back clause in their own definition in
[`EVIDENCE_MODEL.md`](EVIDENCE_MODEL.md), so claiming either with zero confirmed
read-backs is refused. That rule caught its own author: the Serena lane was
written as `A-` and is recorded as `B`, because the CLI surface builds an index
and lists tools without answering a symbol query, and so produces no fact.
