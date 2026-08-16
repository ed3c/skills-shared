# Private-lineage routing gate

Before entering the normal dual-forge state machine, classify the Git-lineage boundary:

```text
GitHub and Forgejo may share the admitted Git object graph
  -> use the normal dual-forge-repository-loop

Any source object, document, executable, fixture, generated knowledge, or runtime evidence must never enter GitHub
  -> stop the normal state machine
  -> use modes/forgejo-private-repository-loop/SKILL.md
```

The two procedures are non-interchangeable. The private-lineage mode keeps source Git objects local, permits only a checked clean-room requirements packet to cross the boundary, and requires an independently authored fresh root before returning to normal publication delivery.

A GitHub connector can inspect this routing contract but cannot establish local checkout, Forgejo, worktree, remote-sealing, fresh-root, provider-cleanup, or local receipt evidence.
