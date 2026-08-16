# Selftest

`selftest.ts` proves that the assertion mechanism accepts known-good local fixtures and rejects independent planted defects. It creates a disposable Git repository, never uses the network, and deletes its temporary workspace on completion.

```bash
bun tests/selftest.ts
```

Positive controls cover the canonical Skill package, the admitted routing-case inventory, a subject-bound invariant report, and proof that uncommitted working-tree bytes cannot replace the recorded Git subject. Mutation controls cover host-only frontmatter, line budget, broken links, machine-local paths, absent provider modules, module-law override, missing/unknown routing controls, missing/escaping/invalid source references, stale digests, unsupported evidence, provider results without source readback, subject mismatch/absence, an undeclared negative-search boundary, and empty output falsely marked `PASS`. Separate controls assert exits `0`, `2`, and `64`.

`SELFTEST GREEN` means those exact controls behaved as expected. It does not mean Claude Code, Codex CLI, Serena, grepai, SCIP, Tree-sitter, SQLite, or mem0 was exercised. Code-Graph-RAG is no longer an active module and has no positive routing control.

## A/B mechanism selftest

`ab-selftest.ts` uses a disposable exact-subject repository to test the scorer and runner without contacting a model:

```bash
bun tests/ab-selftest.ts
```

Positive controls cover a source-matched structured report, a separated procedure receipt, the scoring CLI, a dry run that remains `NOT_EXERCISED`, and byte-identical fixture commits across fresh repositories. Mutations cover a forbidden phrase, missing source anchor, mem0 evidence promoted without read-back, wrong predicate value, missing required artifact group, and evaluator/subject mismatch.

Source-mutation sensitivity changes three independent semantics in fresh committed subjects: maximum attempts, fixed versus exponential delay, and absent versus present observability sink. For each mutation, the stale report must fail and the correspondingly adapted structured predicate must pass. Lexical wording is held out of admission, and a high alias score cannot rescue a lower structured/procedure score.

A green result proves only this offline mechanism and its planted mutations. It does not prove carrier-loaded Skill behavior, cross-task procedural generalization, provider integration, or candidate superiority; those require the repeated physical matrix in `../evals/README.md`.
