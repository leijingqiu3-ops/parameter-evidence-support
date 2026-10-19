# Literature stack

The standard workflow is self-contained. External skills are optional accelerators, not prerequisites.

## Core path

| Need | Bundled tool | Output |
|---|---|---|
| Find candidate papers | `scripts/find_papers.py` | Europe PMC + OpenAlex CSV |
| Verify DOI/PMID identity | `scripts/verify_refs.py` | Crossref + PubMed metadata |
| Obtain an open-access PDF | `scripts/download_pdf.py` | PDF or classified access status |
| Find the exact passage and page | `scripts/locate_passage.py` | JSON + full-page PNG + crop PNG |
| Build the Word report | `scripts/build_evidence_docx.py` | DOCX in the fixed house style |

Install:

```bash
pip install -r requirements.txt
```

## Recommended sequence

1. **Discover** — build 2–4 queries from the parameter name, synonyms, cell type, and assay.
   Example: `GATA2 half-life P815 cycloheximide`, `GATA2 protein turnover proteasome`, `Gata2 t1/2 erythroid`.
2. **Triage** — prefer primary research articles with Methods and primary data; exclude reviews and conference abstracts unless no primary source exists.
3. **Verify metadata** — DOI, PMID, title, authors, journal, volume, pages. Do not merge two records merely because the titles look similar.
4. **Acquire PDF** — open-access first; for a subscription source, use the user's authorized browser session or a PDF the user already obtained.
5. **Extract** — page, verbatim sentence, figure/table, conditions, and screenshot.
6. **Record** — one entry in the spec; if any step fails, write `【找不到…】`.

## Commands

```bash
# Candidate discovery (Europe PMC + OpenAlex)
python scripts/find_papers.py "GATA2 half-life P815" --limit 12 --year-from 1990 --out candidates.csv

# Metadata verification
python scripts/verify_refs.py refs.csv

# Open-access PDF download
python scripts/download_pdf.py 10.1371/journal.pcbi.1000771 --out-dir pdfs --email you@example.org

# In-document passage search and screenshot
python scripts/locate_passage.py pdfs/paper.pdf "verbatim sentence" --out-dir shots --page 3

# DOCX build
python scripts/build_evidence_docx.py spec.json report.docx
```

`download_pdf.py` checks OpenAlex, Unpaywall, and Europe PMC and accepts only a valid `%PDF-` response. It never attempts a paywall bypass. Access failures are classified as `cloudflare_challenge`, `publisher_verification`, `institutional_access_required`, `rate_limited`, `response_not_pdf`, or `transport_error`; verification classes return exit code 4 for a manual browser handoff.

`locate_passage.py` uses an alphanumeric-only matching stream, so line breaks, PDF hyphenation, and variable spacing do not prevent a match. It returns the 1-based PDF page, bounding box, surrounding context, page PNG, and highlighted crop PNG.

## Optional integrations

| Need | Optional skill | When it helps |
|---|---|---|
| Broader multi-source search, publisher metadata, citation matching | `nature-academic-search` | MCP sources are mounted and a wider search is useful |
| Institutional/browser-session PDF access | `nature-downloader` | A lawful subscription copy requires the user's logged-in Chrome session |
| Hundreds of local PDFs → metadata inventory | `organize-research-literature` | The project starts with a large local PDF library |
| Full-paper reading or translation | `nature-reader` | A paper is hard to parse or needs a complete bilingual reader |

The core path must still work when none of these skills is installed.

## Division of labour

- This skill owns the evidence standard, page-level citation, screenshot record, entry format, and DOCX.
- `find_papers.py` proposes candidates; a candidate is not evidence.
- `verify_refs.py` checks identity; a matching DOI is not proof that the paper reports the claimed value.
- `locate_passage.py` proves location; the author must still check the experimental conditions and interpretation.

## Failure rules

- No MCP or discovery skill → use the bundled scripts; do not claim an external search was performed.
- No open-access PDF → mark `【找不到开放获取 PDF】`; do not scrape around a paywall.
- CAPTCHA, Cloudflare, or SSO → stop, ask the user to complete the authorized login, or mark `【找不到全文】`.
- No DOI/PMID match → keep records separate and flag `MISMATCH`.
- Review or abstract only → label it; do not promote it to primary evidence.
- Scanned PDF with no text layer → OCR first, or record that the screenshot cannot be located automatically.
