# Shadow negative-control matrix

These controls are required before any deterministic graph checker may claim semantic closure.

| Control | Planted defect | Required result |
|---|---|---|
| NC-01 | duplicate/copy ICPG case truth into Knowledge Graph denominator | BLOCK duplicate authority |
| NC-02 | mutable PR projection reused after head changes | BLOCK stale decision subject |
| NC-03 | README/card says PASS while exact receipt says FAIL/NOT_EXERCISED | receipt/verifier wins; BLOCK promotion |
| NC-04 | `TRUE_CHILD` edge has no consumed unmerged artifact | BLOCK false Git ancestry |
| NC-05 | path-disjoint sibling serialized only because issue number is later | BLOCK false dependency |
| NC-06 | implementation artifact has no Intent/ICPG case lineage | BLOCK orphan implementation |
| NC-07 | forward Intent→implementation path exists but reverse path is absent | BLOCK incomplete trace |
| NC-08 | edge has no decision/causal/implementation/authority/evidence/retrieval utility | BLOCK connectivity inflation |
| NC-09 | L2/L3 artifact projected as L4/L5 because PR merged or models agree | BLOCK evidence laundering |
| NC-10 | AGENTS/README semantic match treated as permission to mutate governed path | BLOCK authority inversion |
| NC-11 | #418 static fixture represented as live GraphRAG/Shadow evidence | BLOCK live-evidence fabrication |
| NC-12 | historical issue/PR snapshot used as current mutable truth | BLOCK freshness violation |
| NC-13 | root/convergence docs copy and mutate a second full v7.2 prompt instead of routing to canonical `SYSTEM_PROMPT_V7_2.md` | BLOCK prompt-authority divergence |
| NC-14 | fresh Agent requires v7.1 + delta manual composition because standalone prompt is missing/stale | BLOCK incomplete prompt packaging |
| NC-15 | deterministic checker fails a prompt contract but Worker hides failure by rewriting only README prose | BLOCK evidence laundering; canonical prompt/checker contract must reconcile |
| NC-16 | a durable doc self-embeds the current mutable PR head and later treats it as current truth | BLOCK stale self-reference; refresh from GitHub authority |
| NC-17 | ArtifactProjection external identity is fabricated or does not match the observed repository/subject | BLOCK fabricated artifact identity |

## Executable ownership by stage

`#414/#438` owns the first deterministic subset because those controls are implied directly by the projection schemas rather than by later task/traversal semantics:

```text
NC-01  duplicate ICPG authority       EXECUTABLE_IN_#438
NC-02  stale mutable projection        EXECUTABLE_IN_#438
NC-03  prose over receipt              EXECUTABLE_IN_#438
NC-17  fabricated artifact identity    EXECUTABLE_IN_#438
```

The remaining controls retain their later owners:

```text
#415 ownership / Stack semantics      NC-04, NC-05, NC-06, NC-07
#416 traversal / authority semantics  NC-08, NC-09, NC-10, NC-12
#417 convergence / prompt routing     NC-13, NC-14, NC-15, NC-16
#418 live evidence lane               NC-11 plus live stale-head/reverse-trace canaries
```

A control is not `PASS` because it appears in this matrix. It becomes deterministic evidence only when its executable mutation runs on the exact candidate bytes and is rejected for the expected reason. Live #418 remains a separate evidence lane.
