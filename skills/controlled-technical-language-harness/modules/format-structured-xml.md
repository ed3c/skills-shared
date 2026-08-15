# Format: structured technical XML (S1000D-like and DITA-like)

## Trigger

Load when the caller declares `S1000D_LIKE_XML` or `DITA_LIKE_XML` **and** the
document is XML. The format is declared by the caller, never sniffed: a module
that guesses its own applicability has no failure state.

Do not load for prose, extracted text, Markdown, or a document whose structure
the caller has not declared. `check_document_preservation.py --format` refuses a
structured-XML declaration over non-XML content rather than proceeding.

## Why rewriting this is not a text operation

An output can be well-formed XML, read better than the original, and still be
wrong in a way no prose check notices:

```text
a warning node was dropped        → the technician is no longer told
two steps were reordered          → a different procedure, same words
an identifier was lost            → nothing can reference this step again
a cross-reference target vanished → a link now points at nothing
```

Each of those survives spell-checking, grammar-checking, readability scoring,
and a model's own confidence. So parser output stays a **candidate** until
readback proves the structure survived.

## Preservation contract

`scripts/check_document_preservation.py` compares source and output and refuses
the output if any of these changed:

| Preserved | Checked by |
|---|---|
| safety nodes — warning, caution, note, attention, danger | count per tag, per document |
| identifiers — `id`, `identNumber`, `applicRefId`, `chapnum` | set difference |
| cross-references — `xrefid`, `href`, `internalRefId`, `conref`, `keyref` | set difference |
| step order and identity | ordered comparison |

Reordering is reported separately from removal, because the same steps in a
different order is the case most likely to be read as harmless.

Prose inside a preserved node may change freely — that is the point of a
rewrite. Structure may not.

## Evidence boundary

```text
disposable XML fixtures              IMPLEMENTED
source-node readback                 IMPLEMENTED
real S1000D or DITA schema validation NOT_EXERCISED
proprietary manual                   NOT_EXERCISED
safety semantics                     HUMAN_ADMIT_REQUIRED
```

This module checks that structure survived. It does not check that the rewritten
instruction is still *correct*, which stays with a human.
