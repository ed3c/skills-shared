# POSTMORTEM mode

Use POSTMORTEM after unexpected behavior, CI/runtime failure with architectural implications, repeated repair failure, or a completed/green implementation that may contain implicit assumptions.

Reverse-engineer the actual system rather than trusting the intended design:

```text
Observed implementation
→ Recover implicit architecture
→ Extract hidden assumptions
→ Reconstruct states/ownership/authority/side effects
→ Compare against intended invariants
→ Find violated or missing invariants
→ Design falsifying probes
→ Correct System Design
→ Re-enter MONITOR or PRECHECK
```

Evidence order is current code/runtime/receipts first, prose second. A failed test may reveal an implementation bug or a System Design defect; classify which before patching.

At `FIRST_GREEN`, POSTMORTEM may be used as a lightweight reverse review even without an observed failure. The goal is to identify what the green path did not prove.