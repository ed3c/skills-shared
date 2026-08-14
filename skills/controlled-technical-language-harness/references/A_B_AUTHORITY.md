# Authority-bound A/B

## The gap between two green gates

Two mechanisms landed separately, and each is sound on its own:

```text
score_ab.py          every arm graded by the same evaluator, no dropped
                     condition, no deterministic failure hidden by a pass
authority checker    external evidence bytes exist and hash to what the
                     receipt claimed
```

The A/B scorer reads its evaluator identity from a JSON field the caller wrote.
So a comparison can be perfectly fair between arms and still be measured by an
evaluator that never ran — every arm graded identically by nothing.

An A/B result does not acquire the authority layer's guarantee by being merged
after it. **Ancestry is not evidence.** A result produced before the layer
existed, or produced afterwards without consulting it, is the same artifact.

## What the composition requires

```text
exact A/B run bytes
+ exact A/B scorer bytes
+ exact authority checker bytes
+ exact authority bundle bytes
+ the authority gate passing first
+ every A/B evaluator identity matched in external evidence
→ authority-bound A/B receipt, state VERIFIED
```

Order matters and is recorded in the receipt. The authority gate runs first, and
a failure there stops the run before the scorer executes — if external evidence
does not hold, there is nothing for a fairness score to be a score *of*, and
producing the number anyway gives a reader something quotable.

An identity match is on id, version **and** artifact digest together. Matching
on id alone would let a different build of the same evaluator satisfy it.

## What it refuses to claim

```text
state                  VERIFIED, and only VERIFIED
physical runs          NOT_EXERCISED
generalization         NOT_EXERCISED
human approval         NOT_REQUIRED for fixture authority — and not claimed
merge / release        NOT_REQUIRED for fixture authority — and not claimed
compliance             NOT_CLAIMED
```

`ADMITTED`, `CANONICAL`, `RELEASED` and `CERTIFIED` are refused by name. An
offline fixture comparison has no merge, no release, no human approval and no
physical run behind it, so those states are unavailable rather than merely
unearned.

The wrapper also refuses an A/B receipt that carries `generalization_claimed`,
a non-zero `physical_runs`, or a compliance claim. Those cannot ride along on a
composition whose whole evidence base is offline fixtures.

## Exits

```text
0   composition admitted
2   read, and refused
64  input could not be read
70  a gate could not be executed at all
```

`70` is deliberately distinct from `2`: a gate that could not run has decided
nothing, and reporting that as a refusal would be as wrong as reporting it as a
pass.

## Running it

```bash
python3 skills/controlled-technical-language-harness/scripts/score_ab_authority.py \
  --repo-root . --manifest <manifest.json>

python3 skills/controlled-technical-language-harness/scripts/score_ab_authority.py \
  --repo-root . --selftest
```

`--selftest` builds a disposable repository, writes real manifests over real
files, and runs both gates as subprocesses for every case — the defect class
here is a digest naming bytes nobody hashed, so a control that mutated only in
memory would skip the step under test.
