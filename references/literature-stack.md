# Literature stack

Use other installed skills as specialized layers; do not reimplement their whole workflows.

## Routing table

| Need | Use | Why |
|---|---|---|
| Find candidate papers by topic/author | `nature-academic-search` → `multi-source-search` | PubMed/CrossRef/arXiv plus Scopus/ScienceDirect when MCP is mounted |
| No-MCP discovery | `nature-academic-search/scripts/academic_search.py`, or this skill's `scripts/find_papers.py` | OpenAlex (and Europe PMC in `find_papers.py`), no API key |
| Verify a known DOI/PMID | this skill's `scripts/verify_refs.py` | Crossref + PubMed metadata, title-match check |
| Verify a citation extracted from a manuscript | `nature-academic-search` → `citation-verification` | parser + multi-source matching |
| Download a paywalled/institutional PDF | `nature-downloader` | reuses the user's logged-in Chrome session; stops at CAPTCHA/SSO |
| Batch local PDFs → metadata table | `organize-research-literature` | scans a local PDF folder, preserves Excel formatting |
| Read/translate a paper in full | `nature-reader` | not needed for parameter verification unless the PDF is hard to parse |

## Recommended sequence

1. **Discover** — build 2–4 queries from the parameter name, synonyms, cell type and assay. Example:
   `GATA2 half-life P815 cycloheximide`, `GATA2 protein turnover proteasome`, `Gata2 t1/2 erythroid`.
2. **Triage** — prefer primary research articles with a Methods section; exclude reviews, comments, conference abstracts unless no primary source exists.
3. **Verify metadata** — DOI, PMID, title, authors, journal, volume, pages. Use `verify_refs.py` or `nature-academic-search` citation verification.
4. **Acquire PDF** — open access first; then `nature-downloader` with the institutional session.
5. **Extract** — page, sentence, figure/table, conditions; screenshot.
6. **Record** — one entry in the spec; if any step fails, write `【找不到…】`.

## Commands

```bash
# Discovery without MCP (Europe PMC + OpenAlex)
python scripts/find_papers.py "GATA2 half-life P815" --limit 12 --year-from 1990 --out candidates.csv

# Discovery via nature-academic-search (MCP mounted)
# Use its multi-source-search workflow; do not call the MCP tools from this skill directly.

# Metadata verification
python scripts/verify_refs.py refs.csv

# Authorized PDF acquisition (run from the nature-downloader skill directory)
node scripts/batch_download.mjs --dois "10.1111/j.1365-2443.2005.00864.x,10.1074/jbc.275.13.9425" --out "<project>/01_文献PDF"
node scripts/batch_download.mjs --title "Rapid turnover of GATA-2" --open-access --out "<project>/01_文献PDF"
```

If `batch_download.mjs` reports that the institutional session is not authorized, stop and let the user log in; do not retry against a CAPTCHA or Cloudflare page.

## Division of labour

- `parameter-evidence-support` owns the **evidence standard, page-level citation, entry format and DOCX**.
- `nature-academic-search` owns **discovery and citation matching**.
- `nature-downloader` owns **authorized PDF acquisition**.
- `organize-research-literature` owns **bulk local-PDF inventory**.

Do not let a discovery tool decide what counts as evidence. A search hit is a candidate; only the PDF sentence + page + conditions makes it evidence.

## Failure rules

- MCP not mounted → use `find_papers.py` / `academic_search.py`; do not claim PubMed MCP was used.
- Publisher CAPTCHA/Cloudflare → stop, ask the user to complete it in Chrome, or mark `【找不到全文】`.
- No DOI/PMID match → do not merge records; keep them separate and flag `MISMATCH`.
- Review/abstract only → label it; do not promote it to primary evidence.

