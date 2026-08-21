# Portfolio Control Tests

`run-all.sh` is the bounded deterministic denominator for the prompt and contract
foundation. It validates the positive fixture set and 21 mutation controls covering:

```text
prompt digest drift
mixed snapshot epochs
duplicate repository subjects
missing acceptance oracles
runtime ABSENT versus NOT_EXERCISED
path-lease overlap
false parallelism and false serialization
TRUE_CHILD without consumed parent bytes
incomplete joins and dropped failed agents
read-only agent writes
model alias identity laundering
private-repository dispatch without egress admission
multiple pushes, stale heads, empty green jobs, and blind reruns
```

Exit contract:

```text
0   full deterministic denominator PASS
2   checked semantic or mutation failure
64  malformed or unreadable input at an individual CLI boundary
```

A green result proves only the exact fixture-bound mechanism. It does not prove a live
Codex session, local worktree, private egress, GitHub Actions run, merge, release, or
production behavior.
