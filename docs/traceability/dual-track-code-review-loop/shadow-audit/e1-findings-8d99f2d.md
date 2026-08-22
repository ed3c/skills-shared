# E1 independent Shadow audit - findings

**Subject (frozen, re-verified at start and mid-audit):**
commit `8d99f2d95f06e18c4725fd506535f39d939fe679`, tree `4725c00693a146eba3c5084fe3b81f9f9c3967b1`,
worktree `/Users/neon/skills-shared/.claude/worktrees/dtcr-queue-tech-lead`.
`git rev-parse HEAD` did not move during the audit. No tracked file changed.

**Verdict: `BLOCK`** (equivalently `BLOCK_PORTABLE_METHOD`; machine `terminal_state = BLOCKED`).
Named blockers: F-01, F-02, F-03, F-04, F-05.

**Role compliance:** zero writes inside the repository; zero git mutations; zero `gh` calls; zero
pushes. Every replay and every knockout ran against a copy extracted outside the repository with
`git archive 8d99f2d | tar -x`, or against a throwaway per-knockout copy of that export.

**Note on the contract's own currency:** the repaired #525 body was written against `main`
`5341885f`. The audited head is 20 commits ahead and landed `#547`, `#549`, `#550` and `#524`.
Three classes the body fixed as `NOT_APPLICABLE_NO_SUBJECT` (`symbol`, `context`,
`expand-contract`) now have subjects and are re-scored upward with their ceilings stated. That is
denominator growth, not `DENOMINATOR_SHRINKAGE`.

---

## F-01 - BLOCKER - the committed suite is red in a clean checkout, and the absence has no typed exit

**Subject:** `skills/dual-track-code-review-loop/adapters/tree-sitter/selftest.py:435`
-> `skills/dual-track-code-review-loop/adapters/tree-sitter/adapter.py:679`

**Command + exit:**
`sh skills/dual-track-code-review-loop/tests/run-all.sh` -> **exit 0** in the audited worktree;
**exit 1** in a clean export of the same commit (`git archive 8d99f2d | tar -x`, no `.git`).

**Evidence:**

```
File ".../adapters/tree-sitter/selftest.py", line 435, in lane_live
    repo = Path(A.git(ADAPTER_DIR, "rev-parse", "--show-toplevel"))
subprocess.CalledProcessError: Command '['git', '-C', '.../adapters/tree-sitter',
'rev-parse', '--show-toplevel']' returned non-zero exit status 128.
```

The sibling lane landed in the *same wave* handles the identical absence correctly:

```
DTCR-SCIP ... live
  NOT_EXERCISED: this adapter is not inside a git checkout, so there is no exact subject to index
DTCR-SCIP denominators: ... live=NOT_EXERCISED (no checkout) failures=0
```

**Classification:** unhandled absence - an absent precondition surfaces as a traceback instead of a
named lane state, in direct contradiction of this Skill's own law that `NOT_EXERCISED` and `FAIL`
must not collapse (`AGENTS.md:138-149`). It is also a sibling-sweep miss: `#547` fixed this shape in
`scip` and the same wave's reconciliation commit did not carry the fix one directory over.

**Impact on the closure claim:** the repaired #525 admitted prerequisites state *"Full offline
replay is available (`set -eu`, five `python3` stdlib entrypoints, one exit code), so 'where
transport permits' is satisfied here."* That is falsified at this head - and the entrypoint count is
also stale (nine lanes, not five). The AGENTS.md denominator item *"clean checkout and offline
replay where transport permits"* does not pass.

**Ceiling on this finding:** in a scratch checkout that *does* carry `.git`, the lane is green
(exit 0). The defect is specific to a source export without a git directory - which is exactly the
shape `#527`'s consumer-bootstrap profile ships into a consumer repository.

**Disposition:** BLOCK. Repairable in one lane by giving `lane_live()` the typed absence `scip`
already has. E1 has no repair authority and performed none.

---

## F-02 - BLOCKER - the semantic-context lane never verifies the falsifier identity it reports

**Subject:** `skills/dual-track-code-review-loop/adapters/semantic-context/selftest.py:73-86`
and `:717-719`; `adapters/semantic-context/adapter.py:143-151`.

**Evidence - the mechanism:**

```python
def refuses(falsifier: str, mechanism: str, thunk: Callable[[], Any]) -> None:
    \"\"\"The planted case has to go red, and for the mechanism it names.\"\"\"
    ...
    except Refusal as refusal:
        if mechanism not in refusal.mechanism:
```

`Refusal.__init__(self, falsifier, mechanism, detail)` sets `self.falsifier` (adapter.py:148). The
selftest never reads it. The `falsifier` argument is used only for the failure message and for
bookkeeping. The required-falsifier check is self-referential:

```python
named = {falsifier for falsifier, _ in plants}      # selftest.py:717
for required in REQUIRED_FALSIFIERS:
    check(f"{required} is planted", required in named, ...)
```

`plants` is populated from the selftest's own string literals, so this compares the file's list
against the file's list. It cannot fail unless someone edits the selftest.

**Evidence - knockouts run (each in a throwaway copy, lane's own selftest re-run):**

| mutation | exit | result |
|---|---|---|
| mechanism prose the selftest asserts -> mutated | 2 | RED (discriminating) |
| the guard removed entirely | 2 | RED (discriminating) |
| `ORPHAN_CONTEXT_ROW_WITHOUT_SOURCE_BACK_REFERENCE` -> a foreign falsifier code | 0 | **GREEN** |
| **all 23 falsifier codes in the adapter collapsed to one constant `"X"`** | 0 | **GREEN** |

The same class of knockout is RED in every sibling lane:
`tree-sitter` -> `FAIL PARSE_ERROR_HIDDEN: refused, but by KNOCKED_OUT -- the planted defect never
reached its own guard`; `scip` -> same shape for three guards; `buf` -> same shape for three guards;
`expand-contract` -> same shape.

**Classification:** a green not supported by the mechanism it names - the precise collapse this
Skill exists to prevent, inside the Skill. `references/README.md:133` states the repo's own law:
*"A control also has to fail for the reason it claims."* Four of five adapters enforce it; this one
does not.

**Impact on the closure claim:** the printed line
`DTCR-SEMANTIC-CONTEXT-GREEN 90 cases, 41 planted falsifiers refused by the mechanism each names,
12 required falsifiers all planted` is accurate on the *mechanism* half and vacuous on the
*identity* half. `#550`'s exit terminal `DTCR_SEMANTIC_CONTEXT_ADAPTER_VERIFIED` rests partly on the
vacuous half.

**Disposition:** BLOCK. One comparison (`refusal.falsifier != falsifier`) closes it. Not repaired here.

---

## F-03 - BLOCKER - the traceability graph contradicts the tree it describes at this exact head

*(All bytes below read with `git show 8d99f2d:<path>`, never from the working tree - see the
methodological note under F-05.)*

**Subject:** `docs/traceability/dual-track-code-review-loop/ISSUE_DAG.json` and
`docs/traceability/dual-track-code-review-loop/LOCAL_HANDOFF_EXECUTION_QUEUE.json`.

**Evidence at the audited commit:**

```
DAG as_of.observed_main = 5341885f26b5e8e7baf5087a4d661e324f878242
DAG nodes:  524 OPEN exit=-   547 OPEN exit=-   549 OPEN exit=-   550 OPEN exit=-
QUEUE queue (active): 519, 521, 524, 525, 527, 547, 549, 550   all github_state=OPEN
QUEUE closed_lanes:   518, 522, 523, 526    -- and nothing else
```

At the very same commit, the Skill's own surfaces say the opposite:

- `skills/dual-track-code-review-loop/README.md:7` - `C0_CONTRACT_ADMITTED / FIVE_ADAPTERS_LANDED / ...`
- `README.md:312-317` - `SCIP adapter (#547) LANDED`, `Buf adapter (#549) LANDED`,
  `semantic-context adapter (#550) LANDED`, `R2 expand-contract compiler (#524) LANDED`
- `README.md:347` - *"the 2026-08-22 wave landed `#547`/`#549`/`#550`/`#524`"*
- `AGENTS.md:142-149` - *"SCIP on a real scip-python round-trip, Buf with landing-run outputs ...,
  semantic-context on a zero-network reference backend"*
- and the tree carries the bytes: `adapters/scip/`, `adapters/buf/`, `adapters/semantic-context/`
  and `expand-contract/` all exist and all pass their selftests.

**Three consequences, all at this head:**

1. **Audit item 8 fails.** The dependency graph is *not* consistent with the tree at this head. Four
   lanes whose implementation is committed are recorded OPEN, in the active queue, with no
   `exit_terminal`.
2. **No closure packet exists for any of the four.** `closed_lanes` names packets only for `#522`,
   `#523` and `#526` (all three committed, all three pass
   `assert_issue_closure_contract.py`, exit 0 each). `#524`, `#547`, `#549` and `#550` have no
   packet in the commit and are not claimed to have one. The Issue Closure Contract the wave applies
   to its earlier closures was not applied to its own four.
3. **`as_of.observed_main = 5341885f` predates every landing it would have to describe.**
   `git merge-base --is-ancestor fc12a345 5341885f` -> non-zero (same for the `#549`, `#550` and
   `#524` merges). The index's declared observation base is the wave's *base*, so it structurally
   cannot have observed the wave.

**Classification:** `STALE_BASE_OR_RECEIPT` on the traceability plane, plus a closure denominator
that omits exactly the four lanes this wave added.

**In flight, not fixed:** the reconciliation is being written *right now* by another actor - four
untracked packet files (`issue-524/547/549/550.json`, mtime 19:12:41-19:13:23) plus uncommitted
edits to both index files that flip these four to CLOSED with `exit_terminal` values and
`closure_packet` pointers. None of that is in the commit E1 was told to treat as frozen. A head was
dispatched for independent audit while its own closure reconciliation was still being authored.

**Disposition:** BLOCK. Either the four lanes are landed - in which case the graph, the exit
terminals and the closure packets belong in the commit - or they are open, in which case
`FIVE_ADAPTERS_LANDED` overstates the head.

---

## F-04 - BLOCKER - PRIVATE_URL_IN_PUBLIC_ARTIFACT fires on committed bytes

**Subject:** `skills/dual-track-code-review-loop/adapters/scip/fixtures/python-subject/index.scip`
(committed binary, `Metadata.project_root`, byte offset ~28).

**Evidence** (`git show 8d99f2d:<path> | strings`):

```
file:///[MACHINE-LOCAL-PREFIX-REDACTED-AT-PUBLICATION]/skills/dual-track-code-review-loop/adapters/scip/fixtures/python-subject/src
```

*(Redaction note: the machine-local prefix — an absolute home path with the account
name and the builder worktree id — was redacted from this published record on
2026-08-22 after the re-verification found the verbatim quote had become a new
carrier of the very locator it evidences; the unredacted record is retained on
the local forensic branch.)*

A `file://` URI carrying an absolute home path, the account name, the host repository name and the
builder's worktree identifier, in a committed public artifact.

**Why the existing controls did not catch it:**

- the committed leak scanner's denominator is `references/` only -
  `tests/selftest.py:66` `REFERENCES = Path(os.environ.get("DTCR_REFERENCES") or (SKILL / "references"))`,
  `:294` `files = sorted(path for path in REFERENCES.rglob("*") ...)`. Its pattern
  (`:73 LOCATOR_SHAPES = re.compile(r"/Users/|~/|Downloads|drive\.google|file://")`) **would** match
  this string; the path is simply outside its scan root. `leak_scan_files=38` counts only
  `references/`;
- `adapters/scip/selftest.py`, `adapters/buf/selftest.py` and `expand-contract/selftest.py` contain
  no leak-scan logic at all. Only `adapters/semantic-context/selftest.py:793` scans, and only its
  own directory.

**On the sibling precedent the audit brief asked about:** the precedent is *anti*-absolute-path and
this fixture violates it. Both live receipts carry the identical generic redaction -
`live-ac62c87f.json:32` and `live-ee9afe43.json:80`
`"executable_location": "resolved from DTCR_*_BIN or PATH; the install path is one machine and is
not part of the identity"` - and neither receipt leaks anything. The scip *receipt* was correctly
redacted (`"project_root_is_machine_local": true`, `"project_root_tail": "fixtures/python-subject/src"`,
built at `adapter.py:1406-1407`); the *fixture the receipt describes* was not. The builder knew: the
selftest prints `whole-index digest differs from the receipt, as it must from another directory:
Metadata.project_root is an absolute path and is inside the bytes`. The raw value was reasoned about
and left in the commit.

**Disposition:** BLOCK. Note that removing it is not a normal edit - the string is in committed
history, so purging it is a Human-owned history operation, recorded as such in the receipt.

---

## F-05 - BLOCKER - a concurrent writer mutated the audited working tree during the audit

**Evidence:** `git status --porcelain` at session start -> **empty**. Then, during the audit:

```
19:12-19:13  four UNTRACKED files appear, ~15 s apart:
             skills/agentic-tech-lead-orchestration/references/closure-audit/issue-{524,547,549,550}.json
later        five TRACKED files show uncommitted modifications:
             docs/traceability/TRACEABILITY_INDEX.md
             docs/traceability/dual-track-code-review-loop/ISSUE_DAG.json
             docs/traceability/dual-track-code-review-loop/LOCAL_HANDOFF_EXECUTION_QUEUE.json
             docs/traceability/dual-track-code-review-loop/README.md
             skills/git-town-stacked-pr-worker/molecular-indexes/dual-track-code-review-loop/README.md
```

None was written by this session (this session's only writes are two files under its scratchpad).
The repository's own suites do not write there -
`grep -rn "closure-audit" skills/agentic-tech-lead-orchestration/{tests,scripts}/` returns nothing.
`git rev-parse HEAD` and `git rev-parse HEAD^{tree}` were unchanged at start, mid-audit and at the
end, so the *commit* subject held; the *working tree* did not.

**Two of the modified files are inside this audit's own denominator** (item 8: `ISSUE_DAG.json` and
`LOCAL_HANDOFF_EXECUTION_QUEUE.json`). They were mutated *before* the audit first read them.

**Methodological consequence, and how it was handled:** an early pass read those two indexes from
the working tree and therefore observed the concurrent writer's in-flight edit rather than the
audited commit - it saw `as_of.observed_main = 674cfe14` and four `closed_lanes` rows that do not
exist at `8d99f2d`. That draft finding was **discarded and re-derived** with
`git show 8d99f2d:<path>`, which produced the materially different F-03 above. Every index claim in
this report is bound to committed blobs. The general rule this instantiates: in a shared tree, the
thing you observe and the thing you must prove are not the same bytes unless you name the commit.

**Classification:** the exactly-one-active-writer denominator item does not hold at audit time. The
repaired #525 lease is explicit: *"replay in a **separate** clean worktree at the exact audited
commit, never in the wave's shared working tree - otherwise the observation and the subject are the
same bytes."* This audit was dispatched into the wave's shared working tree, contrary to that
clause. It was mitigated by performing every replay against an out-of-repository export, which is
why F-01's clean-tree result is trustworthy - but the mitigation was the auditor's, not the
dispatch's.

**Disposition:** BLOCK, and it is the adverse evidence attached to the independence question below.

---

## F-06 - FINDING - the hollow-fixture rule is met in function for five of six lanes and unmet in the declared plane

Per-lane result for the repaired criterion 2 (*provider runs to exit 0, receipt must still report a
non-`PASS` lane state*), judged by reading each control rather than by its name:

| lane | hollow control | committed hollow *fixture* |
|---|---|---|
| `buf` | `NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE` + `fixtures/not-applicable/` + a **mechanised red proof** that disables the guard and observes the false pass appear | **yes** |
| `expand-contract` | `fixtures/two-repo-hollow.json` - every lane present and empty, exit 2, refused by `PROVIDER_COEXISTENCE_NOT_BOUND`, no artifact written | **yes** |
| `tree-sitter` | `EMPTY_QUERY_REPORTED_AS_EXERCISED` (`selftest.py:269-279`) - every query pattern removed, provider still runs, lane must not read EXERCISED | no |
| `sqlite-ledger` | `SEED_NOT_IN_LEDGER` (`selftest.py:518`) - *"an absent seed is not an empty blast radius"* | no |
| `semantic-context` | `AN_INDEX_WITH_NO_PROJECTIONS_IS_NOT_AN_INDEX` (`adapter.py:576`) - but F-02 applies to the code it raises | no |
| `scip` | **PARTIAL** - `PARTIAL_COVERAGE_PROMOTED_TO_COMPLETE`, `UNRESOLVED_SYMBOL_OMITTED_FROM_DENOMINATOR`, and a vacuous-denominator guard (`selftest.py:136`) - but no committed input on which the indexer exits 0 and the lane still refuses `PASS` | no |

**The declared plane is still empty.** `evals.json` `runnable[]` holds seven entries, all
`hollow_fixture: null`, and declares **no adapter lane at all** - its `_meta.scope` says it *"closes
nothing about a parser, an index, a retrieval adapter, an applied refactor or a consumer."* Five
adapters later, that scope was never widened. Under repair 2's literal oracle - *"a run reporting
PASS with a null hollow fixture is a red result, not a green one"* - this condition is unchanged
from the state the #525 body recorded against `5341885f`.

**Disposition:** FINDING, not an independent blocker: the controls exist in code. The gap is that
`evals.json` no longer describes the suite it belongs to.

---

## F-07 - FINDING - the R2 lane's only receipt binds a foreign subject and names a schema that does not exist

**Subject:** `skills/dual-track-code-review-loop/expand-contract/receipts/two-repo-fixture-670a3853.json`

**Evidence:**

- `subject.commit = 670a3853b5f9b72617630b9d45a8587f52c634b0` is
  `feat(#550): implement the rebuildable non-authoritative semantic-context adapter` - a **different
  lane's** commit;
- `git ls-tree --name-only 670a3853 skills/dual-track-code-review-loop/expand-contract/` returns
  **empty**: at the commit its own receipt names as the subject, the R2 compiler being receipted did
  not exist;
- `"schema": "dtcr/refactor-r2-fixture-receipt/v1"` (line 36) occurs **exactly once in the entire
  repository** - inside this file. The 33 committed schemas do not include it, and
  `references/README.md:100-106` makes `properties.schema.const` the identity *"a consumer binds"*;
- `grep -n "receipts" expand-contract/selftest.py` -> no match. Nothing reads or validates it. The
  file's own `_note` confirms: *"nothing reads it as an input"*.

**Classification:** `STALE_BASE_OR_RECEIPT` plus an artifact outside the schema denominator - an
unvalidated receipt, bound to a subject in which its own subject matter is absent, sitting inside a
lane whose green does not cover it.

**Disposition:** FINDING. Contained (nothing consumes it), so not scored as an independent blocker.

---

## F-08 - CONTRACT DEFECT - the repaired #525 receipt requirement is not satisfiable as written

**Subject:** `references/schemas/closure-record.schema.json:6-8` - root `"additionalProperties": false`
with a closed `required` list.

The repaired body requires *"one `closure-record/v1` document plus the two sidecar objects fixed
above (`session_identity`, `dissent`)"* **and** schema validity (repair 5's oracle is the schema's
`terminal_state` enum). A `closure-record/v1` instance cannot carry either sidecar: the root rejects
every additional key. The two requirements are jointly unsatisfiable in one document.

**Resolution taken here (reported, not repaired):** `receipt.json` is a wrapper document whose
`closure_record` member is a `dtcr/closure-record/v1` instance validated against the committed
schema with `python3` + `jsonschema 4.26.0` `Draft202012Validator` (result: VALID, re-validated after
write), and whose siblings carry `session_identity`, `dissent`, the denominator inventory and the
falsifier disposition. No schema was weakened and nothing under the audited subject was touched.

---

## F-09 - FINDING - FALSE_SIBLING_SERIALIZATION is unrepaired since the #525 reconciliation

**Evidence at this head:**

- `LOCAL_HANDOFF_EXECUTION_QUEUE.json` gives `#525` `start_dependency: 519`;
- `ISSUE_DAG.json` `edges` gives the same pair as `{"from": 519, "to": 525, "kind": "COMPLETION_DEPENDENCY"}`.

Both read from committed blobs at `8d99f2d`. The same edge is a start dependency in one index and a
completion dependency in the other. The #525 body recorded this on `5341885f` and it survives
unchanged at `8d99f2d`. Both files disclaim GitHub-state currency in `_authority`, but no
disclaimer covers a self-contradiction between two committed files about the same edge.

**Disposition:** FINDING. Owned by another lane's lease; E1 has no repair authority over what it audits.

---

## F-10 - FINDING (minor) - stale prose contradicting the same file's own head

- `skills/dual-track-code-review-loop/README.md:54` - *"`adapters/` - the two landed
  deterministic-track adapters"* against `README.md:7` `FIVE_ADAPTERS_LANDED` and `README.md:10`
  *"Five adapters are landed"*.
- `README.md:159-163` - *"the first place in this tree where an external tool (`tree-sitter`) is
  actually invoked"* - `scip-python`, `buf` and `git` are now invoked too.
- `docs/traceability/dual-track-code-review-loop/README.md:90` - *"the two adapters"*.
- `AGENTS.md:94-101` still describes `#547`/`#549`/`#550` as *"a third adapter ... is a new disjoint
  lease"* in prospective voice; all three landed.

---

## F-11 - PASS WITH ONE NIT - evidence-ceiling honesty for the four new lanes

Every ceiling row matches what the selftests print. Verified token by token against the run:

| README row | printed |
|---|---|
| `SCIP adapter (#547) LANDED - selftest + live scip-python receipt` | `crosscheck=EXERCISED live=EXERCISED`, `ran scip-python 0.6.6 ... 76 facts, exit 0` |
| `Buf adapter (#549) ... live lane NOT_EXERCISED where buf absent` | `live=NOT_EXERCISED: no buf executable on PATH and DTCR_BUF_BIN unset` |
| `semantic-context (#550) ... LanceDB lane NOT_EXERCISED` | `lancedb=NOT_EXERCISED (PROVIDER_ABSENT)` |
| `R2 dual-run / telemetry observation NOT_OBSERVED` | `dual_run_observation=NOT_OBSERVED` |
| `applied refactor on a real codebase NOT_EXERCISED` | `applied_on_real_codebase=NOT_EXERCISED` in both R1 and R2 |
| `independent Shadow (#525) NOT_EXERCISED` | correct at dispatch; this audit does not set it to `PASS` |

**Nit:** `README.md:284` claims *"Nothing else is reworded - run the suite and the tokens above
appear in its output."* The block does drop `failures=0` (all three adapter lanes),
`schema_controls=28`, `git_arrivals=10` and `live_canary=NOT_EXERCISED` (expand-contract), and
rewrites each line's prefix. The tokens quoted are real; the "nothing else" is not.

**Second nit, honestly disclosed by the file itself:** `scip: live=EXERCISED` is
checkout-dependent - the same commit reports `live=NOT_EXERCISED (no checkout)` from an export.
`README.md:264` does scope the block to *"this worktree's exact head"*, so this is disclosed, not
overclaimed.

---

## F-12 - CEILING - nothing in this wave has converged to main

`git rev-parse main` = `git rev-parse origin/main` = `674cfe1435c4bd1c29e8f07308266fe5c6284973`.
`git merge-base --is-ancestor 8d99f2d main` -> non-zero. All 20 commits sit on branch
`worktree-dtcr-queue-tech-lead`. The word "landed" throughout the wave's artifacts means
"committed on a worktree branch", not "on `main`" - and `main` is three commits behind even the
`674cfe1` the in-flight edit names.

At the commit, both indexes declare `as_of.observed_main = 5341885f`, the wave's *base*. So the
recorded observation base predates all four landings (F-03, consequence 3) *and* is itself two
commits behind the current `main`. No index in this head observed a state in which the wave exists.

Per-candidate workflow identity is `ABSENT` - structurally, because no push has happened, and no run
id is inferred anywhere.

---

## F-13 - POSITIVE - recorded because it is the standard the other lanes should be held to

`adapters/buf/selftest.py:293` `prove_no_protobuf_guard_disabled_is_red()` does not assert that a
guard exists; it disables the guard at a verified source anchor, runs the input again, and observes
the false pass appear:

```
NO_PROTOBUF_TASK_FORCED_TO_PASS_INSTEAD_OF_NOT_APPLICABLE (red proof): refused with the guard
disabled, a zero-source compare emitted outcome='NO_BREAKING_CHANGE_DETECTED' -- proving the guard
is what stood between this input and a false pass
```

It also fails closed if the anchor moves (`selftest.py:349-352`). This is the only lane in the tree
that proves its own control is load-bearing rather than asserting it. F-02 is exactly what its
absence looks like.

---

## Replayed denominator - commands and exits

| command | exit |
|---|---|
| `sh skills/dual-track-code-review-loop/tests/run-all.sh` (audited worktree) | 0 |
| `sh skills/dual-track-code-review-loop/tests/run-all.sh` (clean export, no `.git`) | **1** (F-01) |
| `bash skills/shared-skills-infra/tests/run-all.sh` | 0 |
| `bash skills/agentic-tech-lead-orchestration/tests/run-all.sh` | 0 |
| `python3 scripts/check_document_routes.py` | 0 |
| `python3 scripts/check_guard_controls.py` | 0 |
| `python3 scripts/check_commit_roles.py --repo-root . --range origin/main..HEAD` (20 commits) | 0 |
| `assert_issue_closure_contract.py issue-522.json` | 0 |
| `assert_issue_closure_contract.py issue-523.json` | 0 |
| `assert_issue_closure_contract.py issue-526.json` | 0 |
| `assert_issue_closure_contract.py issue-547.json` | 0 - but the file is **not in the commit**; it was read from an untracked in-flight artifact and its green says nothing about `8d99f2d` (F-03, F-05) |

`issue-52*.json` at the audited commit resolves to exactly three packets (`522`, `523`, `526`). No
packet exists at this head for `#524`, `#547`, `#549` or `#550`.

Per-lane in the clean export: `sqlite-ledger`, `scip`, `buf`, `semantic-context`, `synthesis`,
`refactor`, `expand-contract` and the C0 contract all exit 0; `tree-sitter` exits 1 (F-01).

---

## Independence - HUMAN_ADMIT_REQUIRED, not self-certified

Recorded verbatim for a person to adjudicate; no combination of it sets the lane to `PASS`:

```text
host                : claude-code
role                : fresh-context subagent commissioned via the Agent tool by the wave's own session
model               : claude-opus-5[1m]
base_sha            : 8d99f2d95f06e18c4725fd506535f39d939fe679
head_sha            : 8d99f2d95f06e18c4725fd506535f39d939fe679
subject_tree        : 4725c00693a146eba3c5084fe3b81f9f9c3967b1
worktree_path       : /Users/neon/skills-shared/.claude/worktrees/dtcr-queue-tech-lead
replay_path         : out-of-repository export of 8d99f2d + per-knockout throwaway copies
dirty_before        : clean
dirty_after         : four untracked files appeared, written by another actor (F-05)
authored_artifacts  : none - this session built nothing it audited
writes_in_repository: zero
```

`SAME_CONTEXT_SHADOW_PROMOTED_TO_INDEPENDENT` is left **OPEN**. Per the repaired contract it is not
machine-decidable and `references/contracts/controlled-vocabulary.md:170-181` places independent
review identity permanently under `HUMAN_ADMIT_REQUIRED`. The adverse facts a person should weigh:
this session shares the parent session's worktree, was dispatched by the actor that built the
audited artifacts, and F-05 shows that actor writing into the same tree while the audit ran. That is
the weakest form of the property, not the strongest.

---

## Dissent

**Empty list.** There is no recorded dissent, because exactly one Shadow ran and no second reviewer
existed to disagree.

```json
"dissent": []
```

Stated explicitly per repair 4: an empty dissent list is **not** evidence of agreement. It is
evidence that agreement was never tested.
