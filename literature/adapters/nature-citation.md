# Adapter: nature-citation

## Use for

- Splitting manuscript prose into citable segments.
- Finding Nature/CNS-family support for a statement.
- Exporting RIS, EndNote, ENW, or Zotero RDF files.

## Detect and invoke

```bash
python scripts/lit_stack.py path nature-citation
```

Read the installed `SKILL.md`, then its core static files and the relevant script-usage reference. Keep the requested journal scope and date limits explicit.

## Boundary

This is a citation-writing aid, not a parameter-verification source. A metadata-only candidate must be checked against the abstract or publisher page before it is cited. For a numerical parameter, prefer the primary measurement and the exact passage over a citation-shaped match.

## Fallback

`scripts/find_papers.py` + `scripts/verify_refs.py` + manual citation assembly.
