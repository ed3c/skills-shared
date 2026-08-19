# Codex SDK Tech Lead Control Plane — admission record

Status: `STATIC_DETERMINISTIC_CONVERGENCE_ADMITTED_ON_MAIN`.

This record closes the static/deterministic publication phase of issues #375–#379. It is an admission/handoff record, not proof of live Codex, GitHub dependency mutation, Herdr, external source/provider closure, release, or production safety.

## Admitted subjects

```text
repository                 ed3c/skills-shared
admitted PR                #455
admitted candidate head    847e56c3418fce920c42d983e84ee44fdc6e8971
admitted candidate tree    8a75271851f2e9dd47dd3a019c93e4a0f9272d24
merge commit               ca31e0b1e640f0dba2c3d94da9d9786fbed32f2c
merge tree                 8a75271851f2e9dd47dd3a019c93e4a0f9272d24
pre-merge main             4ca9417b1da5ff32f1d4d3e7af64a15908749024
```

The merge commit has two parents: the pre-merge `main` subject and the exact admitted candidate head. Its tree equals the admitted candidate tree byte-for-byte. The merge therefore preserves the reviewed convergence bytes without squash/rebase flattening.

## Human Admit evidence

Before merge, Shadow re-read the exact candidate head, base, selected sibling subjects, review threads, and hosted evidence. The exact candidate head had these successful GitHub Actions runs:

```text
Skill Suites                  run 32270935750  SUCCESS
Shared Skills Infra           run 32270935738  SUCCESS
Skill Eval Contract           run 32270935693  SUCCESS
Git Town Stacked PR Worker    run 32270935970  SUCCESS
```

The deterministic denominator executed by the convergence includes:

```text
Codex SDK       4 positive / 14 mutations
GitHub DAG      6 positive / 17 mutations
Herdr           4 positive / 18 mutations
problem closure 6 positive / 22 mutations
```

A rejected Herdr integration epoch remains historical: `ed852502437570c7c86bae12c07c16a3f5d37ea8` failed the shared ATL suite because the selected Herdr source contained non-printable bytes. The owning #377 lane repaired it to `6a2ebcbe87078cecaf67f82f3c9c10643bcc9123`; #379 consumed the repair through `fc40cf833609328ded0141dd8d9629c9a727a159`. The failed subject is not erased or retroactively promoted.

## Consumed sibling publication state

The convergence consumed exact bytes from these closed-unmerged source PRs:

```text
#375 / PR #451  86f9e8d940b76cb71b713c098ff09cb68eb4e0c1
#376 / PR #452  426fb6f6f548f71572d4402e73e0b05ecf6f8aa8
#377 / PR #456  6a2ebcbe87078cecaf67f82f3c9c10643bcc9123
#378 / PR #457  ac5ddc0287eb4e4156a7c7eef178b7be8bbd1d34
#379 docs / PR #380  7a9d68fcd58b1ed78ed6d05595a8df7eae53f5a5
```

Their PR closure is publication lineage only. Their implementation bytes are present on `main` because #455 consumed them. They are not independently merged PRs and must not be presented as such.

## Current State Machine

```text
STATIC_MECHANISMS_IMPLEMENTED
→ EXACT_CANDIDATE_BYTES_CONVERGED
→ EXACT_HEAD_HOSTED_GATES_PASS
→ SHADOW_SAME_SUBJECT_PASS
→ HUMAN_ADMIT
→ MERGED_ON_MAIN
→ STATIC_DETERMINISTIC_PHASE_CLOSED
```

The next phases are independent evidence/process lanes; they do not reopen or rewrite this admission record.

## Remaining evidence owners

```text
#375 live Codex SDK execution                      NOT_EXERCISED
#376 live GitHub dependency mutation/readback      NOT_EXERCISED
#376 generic development-link ownership            RESIDUAL
#377 live Herdr observation                        NOT_EXERCISED
#378 real article/PDF/provider closure             EVIDENCE_DEPENDENT
release / production promotion                     NOT_PERFORMED
```

Issues #375–#378 remain the owners of those live/residual lanes. Closing or merging #455 does not convert them to PASS.

## Agent read order after admission

For #375–#379 work after this merge:

1. read this admission record;
2. read current `main` and GitHub issue/PR/workflow metadata;
3. use `CODEX_SDK_TECH_LEAD_CONTROL_PLANE.md` for the pre-admission design, State Machine, denominator, failure history, and evidence ceilings;
4. load the selected Agentic Tech Lead module/contracts only when their trigger matches;
5. keep #375–#378 live evidence in their owning issue/runtime lane.

If prose conflicts with current GitHub metadata, exact Git subjects, executable contracts, or runtime receipts, those machine/external subjects win. A later live receipt appends evidence; it does not mutate this historical static/deterministic admission.

Driven-By: human
Driven-On: chatgpt-github-connector
