# Source-proposal audit: the preparation branch

One branch was read as SOURCE_PROPOSAL for this freeze: the preparation branch
`docs/productization-operating-loop-preflight`, nine commits, head
`0be0d4d37869a4fa6eb2fe136d471d40a5eaddad`, tree
`faefdeecc69af4bbdd78481b5842b7c3608db5b3`.

It was read, not copied. A proposal is raw material: it records one way the
problem was framed by whoever framed it first, and its low cost to adopt is the
reason it would win an argument, not a reason it is right. This file records
what it contained, what this freeze admitted, and what it refused with the
reason, so that a later reader can tell a deliberate omission from an oversight.

## What the branch contained

Seven files, 925 added lines, none of them under `skills/`.

```text
docs/traceability/.../README.md                 method composition diagram, the
                                                fifteen-state target machine,
                                                start- and completion-readiness
                                                DAGs, planned directory
                                                ownership, parallel session
                                                division, data flow, per-atom
                                                current states, evidence ceiling

docs/traceability/.../AGENTS.md                 mandatory read order, authority
                                                boundary, thirteen worker laws,
                                                the evidence vocabulary, a
                                                block-on list, completion-packet
                                                shape

docs/traceability/.../implementation-preflight.json
                                                thirteen atoms, each with owner,
                                                state, relation, start and
                                                completion dependencies, planned
                                                paths, outputs, negative
                                                controls, evidence ceiling and
                                                next safe transition; ten laws;
                                                Human/external authority list;
                                                phase non-claims

docs/traceability/.../SESSION_PROMPTS.md        a common zero-context envelope
                                                plus one pasteable prompt per
                                                stage

scripts/check_productization_preflight.py       a deterministic graph checker
                                                over the preflight JSON:
                                                required atom ids, required
                                                fields, duplicate ids, owner
                                                presence

tests/test_productization_preflight.py          positive plus planted mutations
                                                for that checker

.github/workflows/productization-preflight.yml  hosted execution of the checker
```

## Admitted

```text
the twelve lane names                 taken as the lane set, and given the four
                                      -part treatment the vocabulary file uses:
                                      meaning, producer, consumer, and what the
                                      lane can never become

the fifteen-state machine             taken verbatim as the progression, with
                                      the four-valued disposition kept as one
                                      state rather than split into four

the ten-rung ladder                   taken verbatim, with one receipt kind
                                      bound to each rung so the substitution law
                                      has something to hold onto

the authority laws                    thirteen non-identities, of which the
                                      branch stated ten; three more were added
                                      from its own worker laws, where they were
                                      prose rather than law

the seven-state evidence vocabulary   extended to ten. UNKNOWN and BLOCKED were
                                      required by the contract spec and were
                                      absent from the branch's list; NOT_APPLIC-
                                      ABLE was taken from the sibling contract
                                      already on the tree, because a lane that
                                      cannot apply and a lane nobody entered are
                                      different facts

start / completion dependency split   admitted as the branch had it, and made
                                      structural: two fields with two different
                                      item shapes, so collapsing them is a
                                      validation error rather than a discipline

per-atom negative controls            the idea was admitted; the specific
                                      controls became the eleven inline refusal
                                      cases in the schema, each one naming the
                                      keyword that refuses it and each one
                                      checked to be refused by that keyword and
                                      no other
```

## Refused, with reasons

```text
the named external carrier atom       REFUSED for the portable core. The branch
                                      carried one specific consumer application
                                      as an atom with its own external issue.
                                      A portable contract that names one
                                      consumer makes every other consumer a
                                      special case of the first. Consumer
                                      binding belongs to the consumer's own
                                      repository; the core keeps a generic
                                      RUNTIME lane and no carrier identity.

the thirteen-atom preparation DAG     REFUSED as core content. It is a plan for
                                      this program's delivery, not portable
                                      vocabulary. Freezing a schedule inside a
                                      contract means every schedule change is a
                                      contract change, and it is the one part of
                                      the branch guaranteed to be stale first.

the preparation checker and its       REFUSED as a dependency. It validates the
tests                                 preparation JSON's graph shape, which is a
                                      different subject from this contract. The
                                      contract's own controls travel inside the
                                      schema instead, so removing a guard and
                                      leaving its control behind is visible in
                                      one diff.

the hosted workflow                   OUT OF LEASE. Not this atom's to write.

the stage session prompts             REFUSED as core content, and left with
                                      their later owner. A prompt is an instance
                                      of using the vocabulary; putting instances
                                      in the vocabulary is how the vocabulary
                                      stops being portable.

the branch's `base_state` field       REFUSED as a shape. It recorded a subject
                                      as "observed at branch creation", which is
                                      a description of when somebody looked
                                      rather than of what they looked at. Every
                                      identity in this freeze is a forty-hex
                                      commit and the schema refuses anything
                                      else.

the planned directory ownership map   ADMITTED AS ORIENTATION ONLY, not written
                                      into the core. It describes paths later
                                      atoms will own; a contract that lists them
                                      would be claiming a lease it does not
                                      hold.
```

## Predecessor ownership, unchanged

The reverse-engineering convergence, bootstrap and real-consumer evidence lines
keep their own independent owners. Nothing in this freeze closes, supersedes or
absorbs them, and no state or rung defined here should be read as evidence
about their subjects. This freeze consumed the preparation branch as a source
proposal and produced a vocabulary and a schema; that is the whole of its
effect.

## What this audit is not

It records what was read and what was decided. It does not establish that the
branch's framing was correct, that the atoms it names are the right atoms, or
that the states it reports were accurate when it reported them. A source
proposal read carefully is still a source proposal.
