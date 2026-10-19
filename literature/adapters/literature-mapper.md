# Adapter: literature-mapper

## Use for

- arXiv + OpenAlex scoping and title/abstract-level literature maps.
- Journal-tier or CCF-level filtering.
- Early field exploration before choosing papers for full-text verification.

## Detect and invoke

```bash
python scripts/lit_stack.py path literature-mapper
```

Read the installed `SKILL.md`. It uses Plan-mode checkpoints and a whitelist-driven search; follow those choices when the user wants a scoping map rather than a parameter audit.

## Boundary

It explicitly analyzes titles and abstracts, not full PDFs. Never use its output as proof of a measured parameter or as a substitute for a page-level quote. Its license is custom/non-commercial; do not copy its source into this repository.

## Fallback

`scripts/find_papers.py` for candidate discovery, followed by PDF verification.
