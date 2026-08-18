# Budgeted live-lane runbook (#228, #230, #235)

The exact commands a runner session executes for the three budgeted designs frozen beside this file:

- [`budgeted-matrix-228-preregistration.json`](budgeted-matrix-228-preregistration.json)
- [`budgeted-ablation-230-preregistration.json`](budgeted-ablation-230-preregistration.json)
- [`budgeted-canary-235-preregistration.json`](budgeted-canary-235-preregistration.json)

Section #235 window 1 has been executed; sections #228 and #230 have not. Running this file does not by
itself move a lane in [`live-evidence-state.json`](live-evidence-state.json): a lane moves only when a
receipt exists and verifies, which is why `235_production_like` now reads `INSUFFICIENT_SAMPLE` with the
shortfall counted, and `228_matrix` and `230_rule_ablation` are untouched.

Read the design before running its section. This file is the invocation, not the contract; where the two
disagree the design decides.

## Preconditions, checked once before any spend

```bash
command -v claude   # required by every section
command -v codex    # required even for a claude-only #228 slice: run_pilot_matrix.py validates
                    # every host in the preregistration it loads before filtering by --only-host
gh auth status      # the ground-truth resolver and the cell task both go through `gh api`
export PYTHONDONTWRITEBYTECODE=1
```

`gh` fails through a proxy on this machine and then reports the failure as an invalid token. Unset the
proxy for `gh` calls rather than believing the token message.

Confirm the Skill has not drifted from what the designs were frozen against:

```bash
shasum -a 256 skills/repository-capability-audit/SKILL.md
# must print 7cc59be07992119b0842a7f3ec1b41fcb93b08e74f3252a24efe08bc1ebc4d54
```

A different digest means the designs are stale. Re-freeze them or do not run them.

## Abort rule (all three sections)

Applies per cell, and it is a kill, not a retry:

1. A cell that exceeds its per-cell cap is killed.
2. It is recorded as a **failed cell in the denominator** with reason `BUDGET_EXCEEDED`.
3. It is **never re-run**. Every design forbids retries, so a re-run cell is a selected cell.
4. When cumulative spend passes the section's global cap, or when the section's abort-count trips,
   stop the whole section and report `PARTIAL` with the exact cells that ran.

| Section | Per-cell cap | Global cap | Section abort trips at |
|---|---|---|---|
| #228 | $4.00 / 600 s | $30.00 / 3600 s | 3 cells aborted in one slice |
| #230 | 600 s (cost not observable on this path) | 3600 s | 2 cells aborted |
| #235 | $6.00 / 900 s | $12.00 / 1800 s | both consumers aborted |

`claude -p` reports `total_cost_usd` per session; that is the cost signal for #228 and #235. On the
`run_agent_cell.py` path used by #230 no usage is collected at all, so cost, tokens and tool calls land
as zeros with `cost_observed=false`. Do not enforce a dollar cap against a recorded zero — every cap
would pass. Time is the only enforceable dimension there.

## Budget table

Per-cell figures are measured, not forecast: they come from the `claude-code` cells in
[`pilot-result.json`](pilot-result.json) and [`matrix-slice1-result.json`](matrix-slice1-result.json).
Token counts are provider-side, cache-read inclusive, and are billed to the spawned `claude -p`
subprocess rather than to the orchestrating session.

### #228 — 2 repositories x 3 arms x 2 repetitions x 1 host = 12 cells

| Repository | Arm | Cells | Cost/cell | In-tok/cell | Out-tok/cell | s/cell |
|---|---|---:|---:|---:|---:|---:|
| sindresorhus/slugify | candidate_trimmed_skill | 2 | $1.1549 | 679,731 | 4,932 | 100 |
| sindresorhus/slugify | current_full_composition | 2 | $1.5607 | 989,423 | 4,806 | 90 |
| sindresorhus/slugify | no_skill | 2 | $0.9998 | 644,770 | 5,167 | 98 |
| spf13/cobra | candidate_trimmed_skill | 2 | $1.7304 | 1,265,536 | 12,108 | 253 |
| spf13/cobra | current_full_composition | 2 | $2.2580 | 1,848,621 | 9,385 | 178 |
| spf13/cobra | no_skill | 2 | $2.0010 | 1,902,516 | 12,325 | 247 |
| **total** | | **12** | **$19.41** | **14,661,194** | **97,446** | **1,932** |

### #230 — 1 repository x 4 profiles x 2 repetitions x 1 host = 8 cells

| Profile | Cells | s/cell | Cost/cell |
|---|---:|---:|---|
| candidate_trimmed_skill | 2 | 287 | not observed |
| candidate_minus_RCA-001 | 2 | 287 | not observed |
| candidate_minus_RCA-003 | 2 | 287 | not observed |
| candidate_minus_RCA-007 | 2 | 287 | not observed |
| **total** | **8** | **2,296** | **~$19.46 unobserved reference** |

The dollar figure is the slice-1 candidate-arm mean carried over from the other harness so the owner can
size the spend. It is not observed on this path and must not be written into a receipt as an observation.

### #235 — 2 consumers x 1 window = 2 cells

| Consumer | Cells | Cap/cell | Window 1, measured |
|---|---:|---:|---|
| `consumer_selection.selected[0]` | 1 | $6.00 / 900 s | $0.6870 / 76.6 s |
| `consumer_selection.selected[1]` | 1 | $6.00 / 900 s | $0.8571 / 72.5 s |
| **total** | **2** | **$12.00 / 1800 s** | **$1.5442 / 149.1 s, plus $0.4835 / 7.7 s of preflight** |

The two consumer paths, their pinned commits and their pinned trees live in
`budgeted-canary-235-preregistration.json` under `consumer_selection.selected`. That file is the single
source for them; this runbook reads them rather than restating them, so a repinned subject cannot end up
recorded in two places with two values.

The cap was set with no prior observation to extrapolate from and window 1 came in at 17% of it. These
figures are window 2's estimate, and they are two sessions on two consumers — not a per-consumer cost
model, and not transferable to a consumer whose tree is a different size.

### Total across all three sections

**22 cells. 2 of them (#235 window 1) have run, for $2.03 including preflight; the remaining 20 are the
~$38.87 observed-basis estimate for #228 and #230, so the whole set is bounded at $40.90.** Wall clock
roughly 70 minutes serial for what remains; the canary section took 157 seconds.

## Section #228

Two slices, one per repository. A slice whose result file already exists is skipped; that is how an
interrupted run resumes without any cell running twice.

```bash
REPO=$(git rev-parse --show-toplevel)
OUT=$HOME/rca-228-budgeted
RUNNER=$REPO/skills/repository-capability-audit/scripts/run_pilot_matrix.py

for repository in sindresorhus/slugify spf13/cobra; do
  slug=$(printf '%s' "$repository" | tr '/' '_')__claude-code
  [ -f "$OUT/$slug/pilot-result.json" ] && { echo "SKIP $slug"; continue; }
  python3 "$RUNNER" \
    --output "$OUT/$slug" \
    --repetitions 2 \
    --only-repository "$repository" \
    --only-host claude-code \
    --timeout 600
done
```

Each slice is 6 cells. Expect roughly 10 minutes for slugify and 23 for cobra.

**Required after each slice.** The runner hardcodes its preregistration path and will stamp
`preregistration_id: rca-pilot-2026-08`, which is the wrong design. Write the binding sidecar or the
slice is not this design's evidence:

```bash
for slug in sindresorhus_slugify__claude-code spf13_cobra__claude-code; do
  python3 - "$OUT/$slug" <<'PY'
import hashlib, json, pathlib, sys
design = pathlib.Path("skills/repository-capability-audit/evals/budgeted-matrix-228-preregistration.json")
(pathlib.Path(sys.argv[1]) / "budgeted-binding.json").write_text(json.dumps({
    "preregistration_id": "rca-228-budgeted-2026-08",
    "preregistration_path": str(design),
    "preregistration_sha256": hashlib.sha256(design.read_bytes()).hexdigest(),
    "result_preregistration_id_is_wrong_because":
        "run_pilot_matrix.py hardcodes PREREG = evals/pilot-preregistration.json",
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
done
```

Merge and score:

```bash
python3 $REPO/skills/repository-capability-audit/scripts/merge_matrix_slices.py \
  --input "$OUT" --output "$OUT/matrix-result.json"
python3 $REPO/skills/repository-capability-audit/scripts/analyze_arm_separation.py \
  --result "$OUT/matrix-result.json"
```

Report per repository. Never pool the two. `spf13/cobra` recorded `false_pass_rate` 1.000 in all three
pilot arms; if that reproduces, cobra's contribution is a fully saturated cell set and reads as a
case-set fact, not a treatment fact.

## Section #230

Prepare the shared inputs first. None of this spends model time.

```bash
REPO=$(git rev-parse --show-toplevel)
SKILL=$REPO/skills/repository-capability-audit
OUT=$HOME/rca-230-budgeted
mkdir -p "$OUT"

python3 "$SKILL/scripts/generate_ablation_treatment.py" \
  --skill-file "$SKILL/SKILL.md" --output-dir "$OUT/treatments"
cp "$SKILL/SKILL.md" "$OUT/treatments/candidate_trimmed_skill.md"

for emit in task ground-truth; do
  python3 "$SKILL/scripts/resolve_holdout_ground_truth.py" \
    --repository psf/requests \
    --tree-sha 271ed3be81c5d263a4293f30924c0ee95484511d \
    --family real-capability-with-evidence \
    --emit "$emit" | python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin)[0], indent=2, sort_keys=True))' \
    > "$OUT/$emit.json"
done

printf '%s\n' '{"tool_calls":0,"input_tokens":0,"output_tokens":0,"duration_ms":0,"cost_usd":0.0,"cost_observed":false}' \
  > "$OUT/usage.json"
```

Then eight cells. `arm_order` is the frozen permutation from the design, not a value invented here.

```bash
VERSION=$(claude --version)
TOOLS=Bash,Read,Write,Glob,Grep
TOOLSET=418c900a87809d45f7220dfb2c3e54b33bf6c7c223764cc5ea3b9b895cbf1b4b
TASK='Audit the pinned repository subject named in your task file and report only what its tree supports. Inspect it through the GitHub API, for example `gh api /repos/OWNER/NAME/git/trees/TREE?recursive=1`. Write agent-output.json in the current directory with exactly this shape: {{"tree_sha": "...", "evidence_paths": [...], "claims": [...], "non_claims": [...], "escalate": true|false}}. Cite only paths you actually resolved. Your task file is {task_file}.'

cell () {  # cell <profile> <repetition> <arm_order>
  profile=$1; rep=$2; order=$3
  receipt="$OUT/${profile}__rep${rep}.receipt.json"
  [ -f "$receipt" ] && { echo "SKIP $profile rep$rep"; return; }
  python3 "$SKILL/scripts/run_agent_cell.py" \
    --agent-class language_model_agent \
    --profile "$profile" \
    --case-id real-capability-with-evidence \
    --repository-id psf/requests \
    --commit 8068356288978c4f54661ae6f95afe0e0831885e \
    --tree 271ed3be81c5d263a4293f30924c0ee95484511d \
    --repetition "$rep" \
    --arm-order "$order" \
    --task-file "$OUT/task.json" \
    --treatment-file "$OUT/treatments/${profile}.md" \
    --evaluator-file "$OUT/ground-truth.json" \
    --agent-command-json "$(python3 -c 'import json,os,sys; print(json.dumps(["claude","-p",os.environ["TASK"],"--allowedTools",os.environ["TOOLS"],"--model","opus","--output-format","json","--append-system-prompt-file","{treatment_file}"]))')" \
    --evaluator-command-json "$(python3 -c 'import json,os,sys; print(json.dumps([sys.executable,os.environ["SKILL"]+"/scripts/pilot_evaluator.py","--ground-truth",os.environ["OUT"]+"/ground-truth.json","--usage",os.environ["OUT"]+"/usage.json"]))')" \
    --agent-provider anthropic \
    --agent-family claude-code \
    --agent-model opus \
    --agent-version "$VERSION" \
    --agent-harness claude-code \
    --agent-harness-version "$VERSION" \
    --runtime-identity CLAUDE_CODE_LOCAL \
    --runtime-version "$VERSION" \
    --toolset-digest "$TOOLSET" \
    --evaluator-identity holdout-deterministic-evaluator \
    --evaluator-version 1.0.0 \
    --evaluator-owner independent \
    --timeout-seconds 600 \
    --allow-env PATH --allow-env HOME --allow-env GH_TOKEN \
    --workspace "$OUT/ws/${profile}__rep${rep}" \
    --output "$receipt"
}

export TASK TOOLS SKILL OUT

# repetition 1, in frozen order
cell candidate_minus_RCA-003 1 0
cell candidate_minus_RCA-007 1 1
cell candidate_trimmed_skill 1 2
cell candidate_minus_RCA-001 1 3

# repetition 2, in frozen order
cell candidate_minus_RCA-007 2 0
cell candidate_minus_RCA-003 2 1
cell candidate_trimmed_skill 2 2
cell candidate_minus_RCA-001 2 3
```

Score the pairs:

```bash
python3 "$SKILL/scripts/score_agent_ab.py" --receipts "$OUT" --output "$OUT/agent-effectiveness.json"
```

Expect `admission_state: INSUFFICIENT_SAMPLE` — the sample gate wants 5 repetitions, 2 model families and
3 repositories, and this design supplies 2, 1 and 2. That is not a failure of the run; it is the gate
refusing to let a budgeted run be read as the full matrix. The per-rule block is the part that carries
information, and only for RCA-001, RCA-003 and RCA-007. The other ten stay `NOT_EXERCISED`.

Only bind a rule into [`live-evidence-state.json`](live-evidence-state.json) when its receipts exist and
their recomputed digests match. `publish_source_contribution.py` refuses the file otherwise, which is the
intended outcome for an edit that promotes a state without adding evidence.

## Section #235

Read-only against both consumers. Confirm the subjects have not moved before spending anything:

```bash
DESIGN=$SKILL/evals/budgeted-canary-235-preregistration.json
python3 - "$DESIGN" <<'PY'
import json, subprocess, sys
design = json.load(open(sys.argv[1]))
for consumer in design["consumer_selection"]["selected"]:
    path = consumer["consumer_path"]
    head, tree = subprocess.run(
        ["git", "-C", path, "rev-parse", "HEAD", "HEAD^{tree}"],
        capture_output=True, text=True, check=True).stdout.split()
    moved = head != consumer["commit_sha"] or tree != consumer["tree_sha"]
    print(f"{path} {'MOVED' if moved else 'pinned'} head={head} tree={tree}")
PY
```

A moved head is not a blocker — it is the subject. Re-pin the design or record the new SHAs in the
receipt; what is forbidden is running against a moved subject while reporting the frozen one.

Run each consumer audit under the caps. One invocation is one cell: it recomputes the boundary ground
truth from `git ls-files` with the design's own frozen markers, spawns one bounded `claude -p` audit
under the candidate Skill body, scores it deterministically, and emits the `canary-receipt/v1` object.
`$OUT` is this section's own directory — the `$OUT` above belongs to #230 — and it must be outside every
consumer checkout, because the design forbids writing inside one.

```bash
OUT=${TMPDIR:-/tmp}/rca-235-budgeted
V=$(claude --version)
for index in 0 1; do
  python3 "$SKILL/scripts/run_canary_cell.py" \
    --consumer-index "$index" \
    --output "$OUT" \
    --claude-bin "$(command -v claude)" \
    --harness-version "$V"
done
```

Exit 0 is a completed cell, 2 an aborted or blocked one, 64 a cell that never started (subject drift,
unreadable consumer). All three write what they know; a cell that produced no valid receipt is a cell
that ran and failed, not a cell that did not run. Rehearse the whole chain first with `--selftest` and
`--dry-run`, which stub the session and spend nothing.

Then validate before recording anything:

```bash
for receipt in "$OUT"/*.canary.json; do
  python3 "$SKILL/scripts/check_canary_receipt.py" "$receipt"
done
```

Exit 0 admits the receipt. A non-zero exit is a refusal with a named reason; fix the binding rather than
the checker, and do not spend the second consumer's budget on a refusal the first already showed you.

`rollback_subject_digest` must stay `32aa3043b4a7c0b7e1dc829294c3555898997b2603185429600f1d232d568ba2`
(the committed prior Skill body) and must never equal the candidate digest — that equality is one of the
eight controls and the checker refuses it.

A receipt cannot name the design it was run under: `canary-receipt/v1` sets `additionalProperties: false`
and has no field for one. The binding therefore lives beside the receipts in
[`receipts/rca-235-w1-run-ledger.json`](receipts/rca-235-w1-run-ledger.json), which is this section's
equivalent of #228's `budgeted-binding.json` sidecar — needed for the opposite reason, since #228's
runner stamps the wrong id and this one can stamp none at all.

Window 2 is not scheduled. It becomes runnable when either 14 days have passed since window 1's
`run_window.ended_at` or any `revalidation_triggers` identity changes, whichever comes first. Until one
of those is true there is no second window and no longitudinal claim.

### What window 1 recorded

Two cells, both completed, no retries and no aborts. $2.03 of the $12.00 global cap and 157 s of the
1800 s, including a preflight probe that is not a canary and is counted anyway because it spent money.
Both receipts were admitted — the first real objects this contract has ever accepted, having until then
only ever seen ones synthesized inside its own test.

The two consumers split. `local/ix-agy` passed all 11 probes. `local/bettor-arena` passed 4 of 11: its
audit gave all six present boundaries a row-level `PASS` while nothing had been executed, which
[`../SKILL.md`](../SKILL.md)'s terminal-state section forbids in those words, and said so itself in the
same message — *"PASS here means only that a tracked path matching the boundary's marker pattern was
resolved … it is a STATIC path-presence observation"*. That is a live false PASS on a real consumer, and
the design's `must_report_even_if_adverse` makes it the result rather than a reason to re-run. At n=2
with no repetition and no matched control arm it is one observation, not a rate, and it is attributed to
nothing.

Four discrepancies between this runbook and what running it required, recorded in the run ledger and
repaired above where they were repairable: `gh auth status` fails on this machine (blocking #228 and
#230, not #235, which needs no GitHub access); `--append-system-prompt-file` works but is absent from
`claude --help` on 2.1.233; this section named no cell invocation and inherited #230's `$OUT`; and
`/Users/neon/ix-agy` had moved off its pinned commit, so its receipt binds the observed SHAs and records
the revalidation rather than reporting the frozen ones.

## After any section

```bash
bash skills/repository-capability-audit/tests/run-all.sh
python3 scripts/check_skill_evals.py
python3 scripts/check_skill_eval_plane.py
```

Green means the committed contracts still hold. It does not mean a live lane moved; that is what the
receipts are for.
