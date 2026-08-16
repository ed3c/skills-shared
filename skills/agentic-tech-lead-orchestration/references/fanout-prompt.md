# Standard Worker prompt packet

Populate every field. Do not send a Worker an unresolved placeholder.

```markdown
## Task identity
- task_id: <stable id>
- mode: <STACK | TOURNAMENT>
- base_commit: <immutable commit>
- base_tree: <immutable tree>
- branch: <head branch>
- parent_branch: <parent or main>
- branch_focus: <architecture | minimal-diff | defensive | named domain>

## Goal and non-goals
<one bounded behavior>

## Locked contracts
- interfaces: <path + digest + signatures>
- schemas/APIs: <exact version>
- state/dependency/style rules: <closed set>
- forbidden architectural substitutions: <closed set>

## Path lease
- write: <globs>
- read_only: <globs>
- forbidden: <globs>
- helper code must remain inside: <domain root>

## Deterministic context
- target source: <full files/ranges>
- dependency skeletons: <provenance>
- callers/tests: <provenance>
- index_subject: <SCIP commit/tree/indexer/coverage or BLOCKED>
- intent_candidates: <grepai/LanceDB candidates, not facts>

## Acceptance oracles
- commands: <argv arrays or repository-owned scripts>
- immutable assertions: <ids>
- required negative/mutation controls: <ids>
- artifact and cleanup checks: <ids>

## Budgets and stop states
- max_repairs_per_signature: 3
- time/token/tool budgets: <values>
- stop on: path escape, contract change, assertion mutation, missing exact precondition, repeated failure

## Output
Return changed paths, diff summary, commands/exits, test/control receipts, retries, unresolved assumptions, cleanup, and no merge/publication claim.
```
