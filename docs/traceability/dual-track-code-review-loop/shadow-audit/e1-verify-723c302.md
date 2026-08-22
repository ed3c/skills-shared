# E1 post-repair verification

## Post-repair verification - 723c302

**Subject:** `723c30238cf00839e6935b5358c7f844baf2124b`.
Confirmed identical for `origin/main`, `dtcr-wave-20260822` and worktree `HEAD`:

```
$ git rev-parse origin/main dtcr-wave-20260822 HEAD
723c30238cf00839e6935b5358c7f844baf2124b
723c30238cf00839e6935b5358c7f844baf2124b
723c30238cf00839e6935b5358c7f844baf2124b
```

`git merge-base --is-ancestor 8d99f2d 723c302` -> non-zero, consistent with the declared
history rebuild. The previously audited head is not an ancestor; content evolved from it.

**Role:** unchanged. Read-only in the repository; zero writes, zero git/gh mutations, zero pushes.
Replays ran against `git archive 723c302 | tar -x` and throwaway copies; in-worktree runs only where
a checkout is required by the lane under test.

**Independence: unchanged - `HUMAN_ADMIT_REQUIRED`.** Same dispatch relationship as the first pass:
a fresh-context subagent commissioned by the session that authored the repairs, sharing that
session's worktree. `SAME_CONTEXT_SHADOW_PROMOTED_TO_INDEPENDENT` stays OPEN. Nothing in this
verification sets that lane to `PASS`, and a clean re-verification does not make the reviewer more
independent than the dispatch made it.

---

### Blocker-by-blocker

| # | blocker | status |
|---|---|---|
| F-01 | clean-checkout replay crashes, absence untyped | **RESOLVED** |
| F-02 | semantic-context never verifies falsifier identity | **RESOLVED** |
| F-03 | traceability graph contradicts the tree; no closure packets | **PARTIALLY** |
| F-04 | `PRIVATE_URL_IN_PUBLIC_ARTIFACT` on committed bytes | **PARTIALLY** |
| F-05 | concurrent writer in the audited tree | **RESOLVED** |

---

#### F-01 - RESOLVED

`sh skills/dual-track-code-review-loop/tests/run-all.sh` in the clean export (no `.git`) -> **exit 0**
(was exit 1).

```
NOT_EXERCISED: this adapter is not inside a git checkout, so there is no exact subject to analyse
DTCR-TS denominators: fixtures=2 matches=5 schema_validations=9 falsifier_rows=14
                      live=NOT_EXERCISED (no checkout) failures=0
DTCR-TS SELFTEST GREEN
```

The traceback is gone and the absence is typed, in the same shape the `scip` sibling already used
(`...no exact subject to index`). All nine lanes green in the export. In the worktree checkout the
same suite is exit 0 with `live=EXERCISED` for both `tree-sitter` and `scip`, so the repair typed the
absence without disabling the live lane. Repo gates re-run on this head: `check_document_routes.py`
0, `check_guard_controls.py` 0, `agentic-tech-lead-orchestration/tests/run-all.sh` 0,
`shared-skills-infra/tests/run-all.sh` 0.

#### F-02 - RESOLVED

The three knockouts that were GREEN at `8d99f2d` are now RED for the reason they name, and the two
that were already RED stayed RED. Each ran on a throwaway copy of the export:

| knockout | 8d99f2d | 723c302 |
|---|---|---|
| **all 23 falsifier codes collapsed to one constant** | GREEN (exit 0) | **RED, exit 2** |
| single code swapped to a foreign code, prose intact | GREEN (exit 0) | **RED, exit 2** |
| a `REQUIRED_FALSIFIERS` entry renamed in the selftest itself | (tautology, could not fail) | **RED, exit 2** |
| mechanism prose mutated | RED | RED, exit 2 |
| guard removed entirely | RED | RED, exit 2 |

```
DTCR-SEMANTIC-CONTEXT-RED ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE was refused under the
falsifier code 'X', not the 'ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE' it names
```

Source confirms the mechanism rather than the wording: `refuses()` now compares both halves
(`if refusal.falsifier != falsifier`) and records the row *from the refusal the adapter actually
raised*, which is what converts the `REQUIRED_FALSIFIERS` accounting from a self-check into an
observation - my fourth knockout proves that, since renaming an entry in the selftest's own tuple now
goes red instead of silently passing.

**Shallow-`/tmp` guard:** selftest with `TMPDIR=/tmp` -> **exit 0**, no crash.
Denominator moved 90 -> 92 cases and the printed claim changed from "refused by the mechanism each
names / 12 required falsifiers all planted" to "refused **under the code and** by the mechanism each
names / 12 required falsifiers **all raised**" - the wording now matches what the code checks.

#### F-03 - PARTIALLY

Everything the repair was asked to do is done. All bytes read with `git show 723c302:<path>`.

- all four packets committed: `issue-524.json`, `issue-547.json`, `issue-549.json`, `issue-550.json`;
- `assert_issue_closure_contract.py` -> **exit 0** on each (`ISSUE CLOSURE CONTRACT PASS`);
- all four **VALID** against `references/issue-closure-contract.schema.json` (3961 bytes, committed,
  `Draft202012Validator`);
- `ISSUE_DAG.json` records all four `CLOSED` with exit terminals, e.g.
  `#547 exit_terminal='DTCR_SCIP_ADAPTER_VERIFIED (exercised python scope)'`,
  `#524 exit_terminal='DTCR_CROSS_REPO_EXPAND_CONTRACT_READY: NOT_ADMITTED (protocol_ready pinned false)'`;
- `LOCAL_HANDOFF_EXECUTION_QUEUE.json` `closed_lanes` = `[518, 522, 523, 524, 526, 547, 549, 550]`,
  active queue = `[519, 521, 525, 527]`, each closed lane carrying its `closure_packet` pointer;
- `as_of.observed_main` = `674cfe14`, now a genuine ancestor of the head (it was the wave *base*
  before), so the "observation base predates every landing" half of the original finding is gone.

**Residual, and it is new.** The `landing.commit` pointers were not re-pointed after the history
rebuild. All four name pre-rebuild SHAs that do not exist in published history:

```
#547: fc12a3457b5d  ancestor_of_head=False  ancestor_of_as_of=False
#549: e1d867f70b97  ancestor_of_head=False  ancestor_of_as_of=False
#550: 8972c788eb7a  ancestor_of_head=False  ancestor_of_as_of=False
#524: 9b59e55f6b86  ancestor_of_head=False  ancestor_of_as_of=False

$ git merge-base --is-ancestor fc12a345... origin/main ; echo $?
1
```

The published history squashed the per-lane merges into
`a3f87ac feat(#524,#547,#549,#550): land the SCIP, Buf and semantic-context adapters and the R2
expand-contract compiler`. The four merge commits survive locally only because the pre-rebuild branch
is still checked out in this repository; on a fresh clone of `origin/main` every one of those SHAs is
unresolvable. That is `STALE_BASE_OR_RECEIPT` in its ordinary post-rebase form: a committed receipt
pointing at a commit the published history does not contain.

Low severity - the packets, the exit terminals and the evidence are all correct and the pointers are
repairable by naming `a3f87ac` (and `197d3cc` for the docs lane) - but it is exactly the class of
defect this method exists to catch, so it is recorded rather than waived.

#### F-04 - PARTIALLY

**The named blob is clean.** `git cat-file` on `index.scip` at this head (6727 bytes):

```
/Users/            occurrences=0
.claude/worktrees  occurrences=0
wf_                occurrences=0
neon               occurrences=0
file://            occurrences=1  ->  'file:///dtcr-fixture/skills/.../python-subject/src'
```

The one remaining `file://` is the SCIP format's mandatory `Metadata.project_root` URI, now pointing
at the synthetic root `/dtcr-fixture`, which names no account, host or checkout. Every criterion
given (`no /Users/`, `no .claude/worktrees`, `no wf_`) is met. Across the pushed range
`674cfe1..723c302` there is exactly **one** distinct blob at that path and it is this clean one, so
no earlier version of the fixture survives in the published history.

**The leak-scan lane is real and load-bearing.** `adapters/scip/selftest.py:795-868` scans every file
under the adapter *as bytes, binaries included* - the exact gap that let the original F-04 through -
and its red proof runs on every host, observed in the export run rather than asserted:

```
(red proof) same scan, throwaway copy carrying the shape this lane exists to catch:
fixtures/python-subject/index.scip: machine-local locator shape b'file://' is not on the permitted
list, in b'file:///Users/example/checkout/.claude/worktrees/wf_0/src'
python-subject: project_root is file:///dtcr-fixture/..., and re-neutralizing it changes nothing
12 files under adapters/scip scanned as bytes, binaries included: no machine-local locator outside
the 2 declared literals
```

I tried four ways to neuter it. All four turn the lane red for the reason they name:

| knockout | exit | failure |
|---|---|---|
| `leak_scan()` returns no findings | 2 | `a planted machine-local locator was not found, so a green on this tree means nothing` |
| `file://` dropped from `LEAK_SHAPES` | 2 | `the probe carries no locator shape, so the red proof below would prove nothing` |
| `PERMITTED_LOCATORS` widened to swallow `/Users/` | 2 | four `machine-local locator shape ... is not on the permitted list` findings |
| machine-local `project_root` re-planted in the committed fixture | 1 | red |

`file:///dtcr-fixture` is permitted by an **explicit two-literal allowlist**, not by a pattern gap,
and the lane additionally asserts the committed index is the fixed point of the neutralizer that
produced it, so a hand-edited fixture is caught. This meets the standard I set in F-13.

**Residual: the same locator is still in the published tree, in a different carrier.** The
`rev-list --objects` scan over the pushed range finds six blobs containing `[REDACTED-HOME]`, and two of
them are my own first-round audit artifacts, committed into the repository by the wave owner:

```
cad25efa8355 docs/traceability/dual-track-code-review-loop/shadow-audit/e1-findings-8d99f2d.md
882b982a1633 docs/traceability/dual-track-code-review-loop/shadow-audit/e1-receipt-8d99f2d.json
```

`e1-findings-8d99f2d.md:192` carries the original locator **verbatim**, because F-04's evidence quote
reproduced it in full:

```
file:///[MACHINE-LOCAL-PREFIX-REDACTED-AT-PUBLICATION]/skills/dual-track-code-review-loop/adapters/scip/fixtures/python-subject/src
```

So the history was rebuilt to excise this exact string from a binary fixture, and then the report
naming it was published into the same history. Net effect on `origin/main`: the string is still
there. `PRIVATE_URL_IN_PUBLIC_ARTIFACT` still fires; only its carrier moved.

Two further occurrences (`e1-findings-8d99f2d.md:5,464`, `e1-receipt-8d99f2d.json:76`) are the
auditor's `worktree_path`, which the repaired #525 contract explicitly *requires* in
`session_identity` for human adjudication. Those are contract-mandated and I do not score them
against the repair. The line-192 quote is not mandated and could have been redacted
(`file:///Users/<user>/.../wf_<id>/...`) without losing any evidentiary value.

The remaining four (`data/handoff/**` receipts) arrived with the concurrently merged `#599` lane, are
outside the DTCR lanes and outside this audit's denominator; noted, not scored.

**Consequence:** the scip lane's own leak scan cannot see this, because its root is `adapters/scip`,
and the C0 scanner's root is `references/`. `docs/traceability/**` is covered by neither. The
denominator gap that produced F-04 was narrowed, not closed.

#### F-05 - RESOLVED

```
$ git status --porcelain
(empty)
$ git rev-parse HEAD
723c30238cf00839e6935b5358c7f844baf2124b
```

Clean at the start of this verification, clean at the end, `HEAD` unchanged throughout. No untracked
files, no modified tracked files, and no writer activity observed in the tree during the check -
unlike the first pass, where four untracked files and five modified tracked files appeared mid-audit.
The subject was genuinely frozen this time, which is also why every index claim above could be taken
from `git show` and the working tree agreed with it.

---

### Residual blockers carried forward

1. **F-03 residual** - four `landing.commit` pointers in `LOCAL_HANDOFF_EXECUTION_QUEUE.json` name
   pre-rebuild SHAs that are unreachable from `origin/main`.
2. **F-04 residual** - `docs/traceability/dual-track-code-review-loop/shadow-audit/e1-findings-8d99f2d.md:192`
   reproduces the excised locator verbatim in published history; no leak scan covers
   `docs/traceability/**`.

Neither is a defect in the five landed lanes; both are in the traceability plane, both are one-line
repairs, and both are instances of the falsifiers this wave declared. Because
`PRIVATE_URL_IN_PUBLIC_ARTIFACT` was the falsifier that produced F-04 and it still fires on the
published head, the verdict cannot be `ALL_RESOLVED`.

**E1_REVERIFY: BLOCK_REMAINS**
