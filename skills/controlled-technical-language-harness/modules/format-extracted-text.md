# Format: plain text and extracted text

## Trigger

Load when the caller declares `PLAIN_TEXT` or `PDF_EXTRACTED_TEXT` and the
content is not XML. `check_document_preservation.py --format` refuses a
plain-text declaration over XML content, because structure processed as prose is
lost silently rather than loudly.

## Plain text

There is no structure to preserve, so the deterministic lane in
`scripts/lint_deterministic.py` is the whole contract: sentence splitting, word
budgets, admitted terms, forbidden tokens.

## Extracted text

Text recovered from a PDF is a **measurement of a document**, not the document.
Extraction commonly loses exactly the parts that carry the most risk — tables,
warning boxes, figure callouts, and column order — and it loses them silently,
producing fluent prose that simply omits them.

So an extraction declares its own quality, and an undeclared quality is not the
same as a good one:

```text
COMPLETE   structure recovered; semantic PASS is available
PARTIAL    something known is missing; semantic PASS is blocked
GARBLED    the text is not a reliable measurement; semantic PASS is blocked
```

`structures_recovered.tables` and `structures_recovered.warnings` must each be
declared true or false. An unreported structure reads as a recovered one, which
is why the absence of the field is refused rather than defaulted. Declaring
`COMPLETE` while a structure is `false` is refused as a contradiction.

## Evidence boundary

```text
extraction quality contract     IMPLEMENTED
deterministic text lane         IMPLEMENTED
PDF extraction itself           NOT_EXERCISED — the caller supplies extracted text
table and figure recovery       NOT_EXERCISED
document completeness           HUMAN_ADMIT_REQUIRED
```

This module never claims a PDF was read correctly. It only refuses to let an
unmeasured extraction support a semantic pass.
