# E1 final verdict - f2e3edf

**Subject:** commit `f2e3edf8bf10cfa43ef7a0917de4bb8180af29b6`,
tree `b9bc76f635fdd73a7a9cdada9489d3ba790b2360`.
`origin/main` == `dtcr-wave-20260822` == worktree `HEAD`, all three at that SHA.
`git status --porcelain` empty at start and end.

**Role:** read-only; zero repository writes, zero git/gh mutations, zero pushes. Replays ran against a
`git archive f2e3edf` export and throwaway copies; one in-worktree suite run where a checkout is needed.

**Verdict: `ADMIT_FOR_DOWNSTREAM`** (≙ `ADMIT_PORTABLE_METHOD`; machine `terminal_state =
PASS_WITH_STATED_CEILING`).

---

## Check rows

| # | check | command | exit / result |
|---|---|---|---|
| 1 | subject pinned | `git rev-parse origin/main dtcr-wave-20260822 HEAD` | three identical SHAs |
| 2 | worktree clean | `git status --porcelain` | empty (F-05) |
| 3 | DTCR suite, in-worktree | `sh skills/dual-track-code-review-loop/tests/run-all.sh` | **0**, nine lanes green |
| 4 | tree-sitter, clean export no `.git` | `python3 adapters/tree-sitter/selftest.py` | **0**, typed `NOT_EXERCISED` (F-01) |
| 5 | scip, clean export no `.git` | `python3 adapters/scip/selftest.py` | **0** (F-01) |
| 6 | falsifier identity still enforced | knockout: all 23 codes → one constant | **2**, RED for its named reason (F-02) |
| 7 | leak lane still load-bearing | knockout: `leak_scan()` gutted | **2**, `a planted machine-local locator was not found…` (F-04) |
| 8 | closure gate | `assert_issue_closure_contract.py` × `issue-{524,547,549,550}.json` | **0** each |
| 9 | closure schema | `issue-closure-contract.schema.json` × same four | **VALID** × 4 |

## Residual A (F-03 tail) - RESOLVED

```
a3f87ac724ab56e78c6fe40967397f64038afffa  ancestor_of_head=True   feat(#524,#547,#549,#550): land the SCIP, Buf and semantic-context adapters…
81f2f20d63…                                ancestor_of_head=True   feat(#527): add the dual-track-code-review-loop consumer bootstrap…
```

- `#524`, `#547`, `#549`, `#550` each now carry `landing.commit = a3f87ac724ab`, `ancestor_of_head=True`.
- **Unresolved landing pointers across the whole queue: `NONE`.**
- The four pre-rebuild SHAs (`fc12a345`, `e1d867f7`, `8972c788`, `9b59e55f`) are all
  `ancestor_of_head=False` and appear **only inside `landing.note` prose** as forensic history — no
  machine-resolvable pointer names them.
- Each packet names `a3f87ac` and passes gate + schema.
- `closed_lanes = [518, 522, 523, 524, 526, 547, 549, 550]`, active queue `= [519, 521, 525, 527]`.

## Residual B (F-04 tail) - RESOLVED

Committed `index.scip` at this head: `/Users/`=0, `.claude/worktrees`=0, `wf_`=0, `neon`=0;
`project_root = file:///dtcr-fixture/skills/.../python-subject/src`.

The redaction is in place with its note stated, at the exact site that carried the locator:

```
:192 file:///[MACHINE-LOCAL-PREFIX-REDACTED-AT-PUBLICATION]/skills/dual-track-code-review-loop/adapters/scip/fixtures/python-subject/src
:195 *(Redaction note: the machine-local prefix — an absolute home path with the account
:196 name and the builder worktree id — was redacted from this published record on …
```

`e1-verify-723c302.md`: `/Users/neon` = **0**. Its five `/Users/` tokens are all pattern names or
synthetic examples (`/Users/example/checkout/.claude/worktrees/wf_0/src`, `/Users/<user>/.../wf_<id>/…`,
and scanner output literally reading `occurrences=0`).

### Explicit statement on real machine-local locators

Oracle: bytes grep over the full `git ls-files` denominator (**2320 tracked files**) at this head,
counting the real account path `/Users/neon` and the real builder worktree id `wf_5779055d`, and
excluding synthetic examples and declared scanner literals.

- **`wf_5779055d`: 0 occurrences repo-wide.** The locator F-04 was raised about no longer exists in
  the published tree.
- **`skills/dual-track-code-review-loop/**` (132 files): 0 real-locator hits.** The audited subject
  is clean.
- **DTCR traceability plane (11 files): 3 hits**, all the same string — the *auditor's own*
  `worktree_path` at `e1-findings-8d99f2d.md:5,470` and `e1-receipt-8d99f2d.json:76`. Repaired #525
  repair 3 **requires** `worktree_path` inside `session_identity` so a person can adjudicate
  independence. Contract-mandated evidence, not a leak, and not scored against this verdict.
- **No DTCR lane introduced any real locator.** Of the 122 files this wave touched, six contain one:
  the two audit records above (contract-mandated), and four `data/handoff/**` receipts that arrived
  with the concurrently merged `#599` lane.

**Out-of-scope observation for the Human, not a blocker on #525:** real machine-local locators do
exist elsewhere in tracked bytes — `data/handoff/**` (4 files, `#599` lane) and, pre-dating this
work, `migration/superseded/**` and `docs/traceability/github-portfolio-control/**`. They are outside
the #525 denominator and no DTCR lane produced them. Worth a separate lane; the DTCR leak scanners'
roots (`references/`, `adapters/scip`, `adapters/semantic-context`) cover none of those paths.

## Five original blockers at this head

| blocker | status |
|---|---|
| F-01 clean-checkout replay crashed, absence untyped | **RESOLVED** |
| F-02 semantic-context never verified falsifier identity | **RESOLVED** |
| F-03 traceability graph contradicted the tree; no closure packets | **RESOLVED** |
| F-04 `PRIVATE_URL_IN_PUBLIC_ARTIFACT` on committed bytes | **RESOLVED** |
| F-05 concurrent writer in the audited tree | **RESOLVED** |

## Stated ceiling

`PASS_WITH_STATED_CEILING` is legal here because every denominator class is `PASS` and the ceiling
enumerates each one:

- **syntax** — tree-sitter, live receipt; live lane typed `NOT_EXERCISED` outside a checkout.
- **symbol** — scip on a real scip-python 0.6.6 round-trip; **python scope only**, other indexer
  scopes ride `#519`.
- **graph** — sqlite-ledger, real database created and traversed.
- **context** — zero-network reference backend; **LanceDB lane `NOT_EXERCISED` (PROVIDER_ABSENT)**.
- **contract compatibility** — buf on committed landing-run outputs; **live buf lane `NOT_EXERCISED`**.
- **review** — X1 synthesis compilers, **fixture level only**.
- **refactor** — R1; **every request self-declared synthetic**, `applied_on_real_codebase` pinned false.
- **expand-contract** — R2 over a two-repository git fixture; `dual_run_observation=NOT_OBSERVED`,
  `live_canary=NOT_EXERCISED`, `contraction_authorization=HUMAN_ADMIT_REQUIRED`.
- **closure** — closure rows plus four Issue Closure Contract packets, gate exit 0 and schema-VALID.

Not reached by anything here, and not reachable by accumulating more of it: an applied refactor on a
real codebase, a live consumer, registry admission, legal clearance, merge, release, production.

## Independence - unchanged

`HUMAN_ADMIT_REQUIRED`, exactly as in both prior passes. Not machine-decidable;
`references/contracts/controlled-vocabulary.md:170-181` places independent-review identity permanently
under Human admission. The dispatch relationship is unchanged and is the weakest form of the property:
this session shares the authoring session's worktree and was commissioned by it.

The Human's standing directive pre-admitting prerequisite requirements is noted. **Recording that
admission is the Tech Lead's and the Human's act; this receipt does not record it.** What this receipt
carries is the session-identity evidence and a verdict on the audited bytes. `ADMIT_FOR_DOWNSTREAM` is
prose, never a `terminal_state`, and every `authority.*` field stays `false`.

## Dissent

**Empty list.** One Shadow ran across all three passes. Stated explicitly: an empty dissent list is not
evidence of agreement — it is evidence that agreement was never tested.

**E1_FINAL: ADMIT_FOR_DOWNSTREAM**
