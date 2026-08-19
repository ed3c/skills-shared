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

The eventual checker/tests must bind each failure to an exact subject and deterministic terminal disposition. Presence of this matrix is preparation evidence only.
