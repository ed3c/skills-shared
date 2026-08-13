# Code graph impact module

## Trigger

Use for cross-language, cross-package, or cross-module impact questions where calls, imports, inheritance, ownership, data flow, or configuration edges span more than a few files.

## Non-trigger

Do not load a graph for a local single-file question. Do not use graph absence as proof that a runtime dependency or reflection/configuration edge does not exist.

## Inputs

```text
subject commit/tree
provider and graph-build identity
included languages and paths
seed symbols/files/capabilities
edge kinds required
maximum traversal depth and result budget
```

Concrete providers may use AST/tree-sitter graphs, compiler indexes, code property graphs, or repository-specific dependency manifests.

## Process

1. Verify graph subject, parser versions, languages, included/excluded paths, and build freshness.
2. Traverse only declared edge kinds and depth.
3. Tag each edge by origin: parser, manifest, heuristic, generated summary, or runtime observation.
4. Read back load-bearing source declarations and call/configuration sites.
5. Search for dynamic dispatch, reflection, event, generated, environment, and data-store edges that static graph construction may miss.
6. Keep transitive impact candidates separate from confirmed direct dependencies.

## Outputs

```text
graph observation
seed and traversal policy
candidate edges with origin
source-readback references
confirmed and unverified impact sets
known blind spots
```

## Evidence ceiling

A graph edge is `B+` until its load-bearing source/manifest/test/runtime subject is read back. A parser-derived direct edge may become `A-` after readback. No graph result proves runtime success or absence by itself.

## Fallback

Use imports, manifests, exact search, symbol references, tests, and public contracts. Record `IMPACT_EDGE_UNVERIFIED` for edges that cannot be confirmed within budget.

## Authoritative laws

The Core laws on candidates, absence boundaries, observation versus attribution, source references, and no evidence overpromotion remain authoritative.
