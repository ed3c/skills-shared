# Profile: Simplified Technical English (proposal-derived)

## What this profile is, and what it is not

This profile is **proposal-derived**. It is not ASD-STE100, and it must never be
presented as ASD-STE100.

```text
pack_id        ste-proposal-derived
profile_type   CONTROLLED_LANGUAGE
edition        0.1-proposal-derived
source         SOURCE_PROPOSAL
```

Its rules were reconstructed from the user-supplied architecture proposal that
`docs/architecture/CONTROLLED_TECHNICAL_LANGUAGE_HARNESS.md` records. That
proposal describes an approach to checking Simplified Technical English. It is
not the specification, not a rule set extracted from one, and not an authority.

## The official standard this approximates

Verified against the issuing authority on 2026-08-14:

```text
standard    ASD-STE100 Simplified Technical English
edition     Issue 9, 15 January 2025
authority   ASD (AeroSpace, Security and Defence Industries Association
            of Europe), Brussels
locator     https://asd-ste100.org/
access      free of charge, but only on request; not openly downloadable
```

The specification is therefore **not held by this repository**, and no digest of
it exists here. That is why this profile does not claim the edition above:

```text
official edition identity        VERIFIED (Issue 9 exists and is current)
official specification artifact  NOT_OBTAINED
official rule set                NOT_EXERCISED
official approved vocabulary     NOT_OBTAINED
```

Verifying that an edition *exists* is a different arrival from holding it. This
profile records the first and refuses to imply the second.

## Promoting this profile to an official pack

An official pack is a new pack, not an edit of this one. It requires all of:

1. an obtained copy of ASD-STE100 Issue 9 from ASD, with an exact locator and
   `sha256:` digest of the received artifact;
2. `source.classification` set to `OFFICIAL_STANDARD` with `authority` naming ASD;
3. an explicit `license_policy` — ASD grants the copy on request, which is not
   the same as a redistribution grant, so `redistribution_allowed` stays `false`
   and `human_legal_review` stays `REQUIRED` until a human records otherwise;
4. `content_mode` of `REFERENCE_ONLY` or `RUNTIME_INJECTED`. `VENDORED` requires
   an admitted redistribution grant, because it commits the bytes;
5. the approved vocabulary supplied at runtime, never committed, unless (4) is
   admitted.

Editing this profile's `edition` field to say `Issue 9` without (1) is the
defect the controls below exist to catch, not a shortcut.

## Technical Names and Technical Verbs

STE allows a project to admit its own Technical Names and Technical Verbs. That
admission is project-owned and Human-owned in both the standard and here:

```text
project termbase required     true
technical name human admit    true (contract-enforced constant)
technical verb human admit    true (contract-enforced constant)
```

A term is never promoted because it is frequent, because a model proposed it, or
because a rewrite needs it to pass.

## Trigger

Load this profile when the caller names Simplified Technical English or an
STE-style controlled language **and** accepts a proposal-derived approximation.
If the caller requires conformance to ASD-STE100 itself, the correct output is
`PROFILE_ABSENT` plus the promotion path above — not this profile with a
relabelled edition.

Do not load it for general prose editing, translation, or a document class that
selected no controlled-language profile.
