# Blindspot Hybrid Event Contract

This reference defines the host-neutral normalized event and storage boundary for the active `modules/blindspot-hybrid.md` route. It does not install or invoke a provider.

## Subject

Every run binds one immutable repository subject:

```json
{
  "schema": "blindspot-hybrid/subject/v1",
  "repository": "owner/repository",
  "commit": "40-hex commit",
  "tree": "40-hex tree"
}
```

One SQLite ledger stores one subject. Mixing commits, trees, forks, indexes, grammars, or project identities without a new ledger is invalid.

## Event bundle

```json
{
  "schema": "blindspot-hybrid/events/v1",
  "subject": {
    "schema": "blindspot-hybrid/subject/v1",
    "repository": "owner/repository",
    "commit": "40-hex commit",
    "tree": "40-hex tree"
  },
  "events": []
}
```

Each event has a stable `id`, `lane`, `kind`, optional repository-relative path/symbol fields, zero or more `links`, an `admitted` boolean, and provider-specific `payload` metadata.

```json
{
  "id": "scip-auth-reference",
  "lane": "scip",
  "kind": "reference",
  "path": "src/auth.py",
  "symbol": "authenticate",
  "links": ["intent-auth"],
  "admitted": false,
  "payload": {
    "indexer": "consumer-owned",
    "relation": "reference"
  }
}
```

## Lane and kind inventory

```text
grepai
  intent_anchor
  runtime_exploration

scip
  declaration
  reference
  implementation
  relation

tree-sitter
  ast_skeleton
  syntax_capture

serena
  symbol_read
  reference_read
  diagnostic
  edit_proposal
  execution_observation

source-readback
  source_readback

test
  test_observation

lancedb
  similarity_projection
```

## Admission law

Provider lanes are candidates and must use `admitted=false`:

```text
grepai / scip / tree-sitter / serena / lancedb
```

Only direct source read-back and passing targeted test/runtime observations may be admitted by this contract. A source-readback event links to each candidate it directly checks. A test event links to the claim/readback it exercises and carries `payload.passed`.

```text
provider event
→ source-readback event links provider ID
→ optional passing test links readback/claim
→ verifier admits the closure for the exact subject
```

A provider cannot set its own truth state. A model statement, index hit, AST node, LSP result, or vector hit cannot rescue missing read-back.

## Structural coverage law

SCIP declarations/references/implementations/relations and Serena edit/execution events require Tree-sitter coverage for every involved path. The Tree-sitter event proves only that the path was structurally represented under the recorded grammar/input; a consumer adapter still records grammar identity and error nodes in payload metadata.

## SQLite authority

The deterministic checker stores:

```text
subject digest
normalized canonical event bytes and digest
event lane/kind/path/admission state
ordered event links
```

Replaying the same event ID with identical canonical bytes is idempotent. Reusing an event ID with changed bytes is a mechanism error because it would rewrite evidence identity.

## LanceDB projection law

A LanceDB event:

- has exactly one source link;
- links to an existing non-LanceDB event;
- is never admitted;
- carries only projection metadata, never secret vectors in portable receipts;
- can be deleted and rebuilt without changing SQLite admission.

Chained vector-to-vector projection and orphan source IDs are blindspots.

## Blindspot assertions

The shared checker reports stable failures including:

```text
SOURCE_READBACK_MISSING
AST_COVERAGE_MISSING
LINK_TARGET_MISSING
READBACK_TARGET_INVALID
VECTOR_PROJECTION_ORPHAN
VECTOR_PROJECTION_CHAINED
TEST_OBSERVATION_FAILED
PROVIDER_SELF_ADMISSION
EVENT_ID_DRIFT
EVENT_SUBJECT_MISMATCH
```

Exit semantics:

```text
0   accepted closure / report PASS
2   contract assertion failed or blindspots remain
64  invalid or absent input
70  SQLite/filesystem/mechanism failure or event-ID drift
```

## Provider adapter boundary

A consumer adapter owns:

- exact executable/container/version/checksum;
- repository/index/grammar/project/namespace identity;
- freshness and language coverage;
- network/privacy policy;
- query arguments and bounded outputs;
- normalization into this event format;
- provider stderr/exit and raw-output digest;
- secrets and credentials outside the repository.

The shared checker consumes only normalized events. It does not claim that a live provider ran.

## Minimal command sequence

```bash
python3 scripts/blindspot_contract.py init \
  --db /consumer-owned/run.sqlite \
  --subject /consumer-owned/subject.json

python3 scripts/blindspot_contract.py ingest \
  --db /consumer-owned/run.sqlite \
  --input /consumer-owned/events.json

python3 scripts/blindspot_contract.py verify \
  --db /consumer-owned/run.sqlite

python3 scripts/blindspot_contract.py report \
  --db /consumer-owned/run.sqlite \
  --output /consumer-owned/report.json
```

Static fixtures prove the checker and failure controls. They do not prove provider health, live index accuracy, Agent execution, Git Town branches, Forgejo, remote publication, or Human Admit.
