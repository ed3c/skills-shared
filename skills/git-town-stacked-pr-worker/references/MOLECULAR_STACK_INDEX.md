# Molecular Stack index

A Stack index is the machine answer to "what is actually in this Stack, and what is missing?" It is derived from observed Issues, branches, PR heads, changed paths and Gates — never from the branch names or from the order the work happened to be written in.

Machine authority: [`molecular-stack-index.schema.json`](molecular-stack-index.schema.json), [`example-molecular-stack-index.json`](example-molecular-stack-index.json) and [`../scripts/assert_molecular_stack_index.py`](../scripts/assert_molecular_stack_index.py).

## Atom vocabulary

```text
C = contract/schema/interface lock
K = deterministic core
A = adapter/provider/substrate
E = Eval/mutation/fault controls
X = explicit multi-parent convergence/E2E
D = documentation/receipt/handoff
```

`required_atoms` is declared before the work starts. Deriving the required atoms and then indexing fewer of them is the failure this index exists to expose: an unindexed atom is not a smaller Stack, it is an unmeasured gap.

Only required atoms are derived. An atom with no paths, no oracle and no Gate is a ceremonial PR, and the checker refuses it.

## Index update algorithm

```text
read actual Issues, branches, PR heads, trees, parents, changed paths, Gates, directory inventory
→ classify each atom: root, sibling, true child, convergence
→ bind one purpose, one writer lease, one oracle, one exact parent set per atom
→ re-read open PR heads from the provider; mark exact-head drift stale
→ expose missing atoms, blocked atoms and Gates rather than smoothing them
→ receipt the index against its exact subject
```

## Structural laws

| Class | Parents | Base | Consumes |
|---|---|---|---|
| `root` | none | `main_branch` | nothing |
| `sibling` | none | `main_branch` | nothing |
| `child` | exactly one | that parent's branch | at least one path the parent owns |
| `convergence` | two or more | one parent's branch | its parents' paths |

Exactly one root and exactly one declared `convergence_owner`. Any other atom with more than one parent is a hidden convergence: the reader sees a chain, the graph is a lattice, and no single owner is responsible for reconciling it.

A child that consumes no parent path is a path-disjoint sibling serialized for no reason. False serialization is expensive in exactly the way it is invisible — the Stack looks ordered, and each atom waits on a parent it never reads.

Every atom's `owns_paths` is a writer lease. Two atoms whose leases overlap have two writers on the same bytes regardless of how the branches are drawn.

## PR head lifecycle

```text
NOT_CREATED  head_sha null           head_source ABSENT
DRAFT/READY  head_sha null           head_source LIVE_PROVIDER
MERGED       head_sha exact SHA-40   head_source IMMUTABLE_MERGED
```

An open PR head is mutable, so the index never embeds it: a self-embedded open head is stale the moment the branch is pushed again, and it reads as a receipt afterwards. A merged head is immutable and is recorded exactly.

## Evidence ceiling

The checker validates index bytes with zero network access. A green result proves the index is internally consistent for its declared subject. It does not read Git, call a provider, refresh a head, run a Gate, create a PR, merge, or admit anything. Reading back live heads and Gate results remains the delivery loop's job, and merge/release stay Human-owned.
