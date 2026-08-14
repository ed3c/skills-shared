# Selftest

`selftest.ts` proves that the assertion mechanism accepts known-good local fixtures and rejects independent planted defects. It creates a disposable Git repository, never uses the network, and deletes its temporary workspace on completion.

```bash
bun tests/selftest.ts
```

Positive controls cover the canonical Skill package, the admitted routing-case inventory, a subject-bound invariant report, and proof that uncommitted working-tree bytes cannot replace the recorded Git subject. Mutation controls cover host-only frontmatter, line budget, broken links, machine-local paths, absent provider modules, module-law override, missing/unknown routing controls, missing/escaping/invalid source references, stale digests, unsupported evidence, provider results without source readback, subject mismatch/absence, an undeclared negative-search boundary, and empty output falsely marked `PASS`. Separate controls assert exits `0`, `2`, and `64`.

`SELFTEST GREEN` means those exact controls behaved as expected. It does not mean Claude Code, Codex CLI, Serena, grepai, Code-Graph-RAG, or mem0 was exercised.
