# MONITOR mode

`MONITOR` is the default mode.

Allow the Builder to explore, design, implement, test, and refactor normally. Do not require the complete A–L packet before harmless reversible work. In parallel, run the Shadow Architecture Watch Loop from [`../references/architecture-watch-loop.md`](../references/architecture-watch-loop.md).

The monitor observes architecture deltas rather than line-by-line edits. It becomes more intrusive only as risk rises:

```text
L0 OBSERVE
→ L1 WARN
→ L2 REVIEW
→ L3 BLOCK
```

Material deltas must be reconciled by the next mandatory checkpoint. Level C/D work may never use MONITOR as an excuse to behave like Level A; the full applicable architecture model must exist by `BEFORE_PR_OR_PUBLICATION`.

The Builder remains the sole implementation writer unless the repository explicitly assigns a different writer. The Shadow Architect owns critique, falsifiers, and architecture/evidence reconciliation, not implementation mutation.