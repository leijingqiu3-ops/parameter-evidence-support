# Adapter: nature-academic-search

## Use for

- Broader multi-source discovery when MCP tools are mounted.
- Citation verification and deduplication.
- MeSH/PubMed search strategy.
- `.nbib`/`.ris`/`.bib` conversion and reference management.

## Detect and invoke

```bash
python scripts/lit_stack.py path nature-academic-search
```

Read the installed `SKILL.md`, follow its router, and load only the workflow fragment needed for the current task. It is particularly useful for PubMed/CrossRef/Scopus/ScienceDirect searches and citation-file work.

## Boundary

A search hit remains a candidate. Do not use an abstract, a citation-manager record, or a matching title as proof that a paper reports a parameter. Verify the DOI/PMID, obtain the PDF, and quote the exact passage before adding an evidence entry.

## Fallback

`scripts/find_papers.py` plus `scripts/verify_refs.py`.
