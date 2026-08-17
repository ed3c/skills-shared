# Consumer Bootstrap Contract

Contract ID: `CONSUMER-BOOTSTRAP-V1`  
Domain method: `DOMAIN-DECOUPLING-V1`  
Owner: `shared-skills-infra`

## Purpose

Attach a brand-new Git repository to the shared procedural control plane without copying shared Skill bodies or replacing the consumer's physical source layout.

```text
inspect consumer repository
→ bind exact skills-shared source
→ add standard managed route blocks
→ attach thin profile/requirements/binding
→ add read-only verification adapter
→ emit bootstrap receipt
→ read back exact bytes
```

## Command

From a clean, immutable `skills-shared` checkout:

```bash
python3 skills/shared-skills-infra/scripts/consumer_bootstrap.py \
  --consumer <consumer-worktree> \
  --repository-id <owner/repo> \
  --apply

python3 skills/shared-skills-infra/scripts/consumer_bootstrap.py \
  --consumer <consumer-worktree> \
  --repository-id <owner/repo> \
  --check
```

The consumer must already contain one initial commit. That commit/tree becomes the initial rollback subject.

## Generated surfaces

Managed-block documents:

```text
README.md
AGENTS.md
CLAUDE.md
CONTEXT.md
ARCHITECTURE.md
docs/INDEX.md
docs/architecture/{AGENTS,DOCUMENT_ROUTING,STATE_MACHINES,DOMAIN_DECOUPLING}.md
docs/integration/CROSS_REPO_INTEGRATION.md
docs/traceability/TRACEABILITY_INDEX.md
.agents/README.md
.agents/control-plane/README.md
```

Machine authorities:

```text
.agents/control-plane/source.json
.agents/control-plane/profile.json
.agents/control-plane/requirements.json
.agents/bindings/repository-control-plane.json
.agents/control-plane/bootstrap-receipt.json
.github/workflows/domain-decoupling-bootstrap.yml
```

The bootstrap replaces only its marked block in an existing Markdown document. It refuses malformed or duplicate markers. Machine authorities must be absent or carry an admitted generated schema/marker.

## State Machine

```text
REPOSITORY_INSPECTED
→ ROUTES_BOUND
→ SHARED_SOURCE_BOUND
→ PROFILE_AND_REQUIREMENTS_BOUND
→ CONSUMER_BINDING_GENERATED
→ WORKFLOW_ADAPTER_BOUND
→ RECEIPT_BOUND
→ VERIFIED
```

Failure terminals:

```text
BLOCKED_MISSING_INITIAL_SUBJECT
BLOCKED_SHADOW_COPY
BLOCKED_UNSAFE_OVERWRITE
BLOCKED_STALE_SOURCE
BLOCKED_STALE_BINDING
BLOCKED_STALE_RECEIPT
BLOCKED_POLICY
FAIL
HUMAN_ADMIT_REQUIRED
```

## Atomicity

Before mutation, snapshot every path owned by the bootstrap. If route generation, profile attachment, binding generation, byte readback, or receipt validation fails, restore all original bytes and remove newly created files/directories where safe.

An apply retry can update only recognized generated files and marked blocks. It cannot consume an unknown human-owned workflow or JSON authority.

## Shadow Architect controls

The owning test plants and refuses at least:

```text
missing or drifted route
malformed managed markers
human-owned workflow collision
mutable/stale source pin
stale generated binding
consumer-local copied Skill body
symlink used as machine authority
automatic merge/visibility/provider authority
projection promoted to runtime evidence
missing or non-ancestor rollback
private reasoning or secret-shaped fields
stale receipt artifact digest
downstream attach failure without full rollback
```

## Evidence boundary

A green bootstrap receipt establishes deterministic route scaffolding, immutable shared-source selection, thin binding generation, exact byte readback, and rollback identity for one consumer repository. It does not establish host Skill discovery, Agent/model execution, provider execution, confidential-data approval, Git Town execution, merge, release, or rollback execution.
