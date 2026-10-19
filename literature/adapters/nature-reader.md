# Adapter: nature-reader

## Use for

- Full-paper Chinese-English reading and translation.
- Figure/table-aware Markdown readers with source anchors.
- Understanding a complex paper before deciding which passage is evidence.

## Detect and invoke

```bash
python scripts/lit_stack.py path nature-reader
```

Read the installed `SKILL.md` and its manifest. It may depend on the shared `_shared/core/terminology-ledger.md`; if that shared layer is missing, report the missing dependency instead of silently degrading the output.

## Boundary

A reader or translation is an aid to understanding, not a substitute for the evidence passage. The final report still needs the PDF page, verbatim source text, experimental conditions, and a screenshot when available. Do not cite a summary as if it were the paper's wording.

## Fallback

`scripts/locate_passage.py pdfs/paper.pdf "verbatim sentence"` for the exact passage, page, and screenshot.
