# Integrated literature stack

The standard workflow is self-contained. The bundled tools add institutional access and local-corpus organization; local adapters add search, reading, citation, monitoring, and note-taking layers when they are installed. None of them is allowed to weaken the evidence standard.

## Layer map

| Layer | Bundled or local | Purpose | Primary entry point |
|---|---|---|---|
| Core fallback | Bundled | Search, metadata checks, open-access PDF, passage location, screenshots, DOCX | `scripts/` |
| Institutional downloader | Bundled | Authorized Chrome/CARSI/SSO PDF acquisition and status reporting | `literature/vendor/nature-downloader/` |
| Local-corpus organizer | Bundled | Recursive PDF inventory and Excel organization | `literature/vendor/organize-research-literature/` |
| Multi-source search | Local adapter | MCP-backed PubMed/CrossRef/arXiv/Scopus/ScienceDirect workflows | installed `nature-academic-search` |
| Full-paper reader | Local adapter | Bilingual, figure/table-aware reading | installed `nature-reader` |
| Citation writer | Local adapter | Segment prose, find CNS support, export reference files | installed `nature-citation` |
| Monitoring pipeline | Local adapter | Recurring discovery, scoring, digest, archive | installed `nature-literature-pipeline` |
| Literature mapper | Local adapter | arXiv + OpenAlex title/abstract mapping | installed `literature-mapper` |
| Zotero note curator | Local adapter | Zotero-to-Obsidian close-reading notes | installed `zotero-taxonomy-curator` |

Run `python scripts/lit_stack.py doctor` to see which layers are ready. `python scripts/lit_stack.py list` prints the resolved paths. The machine-readable inventory is `literature/integrations.json`.

## Recommended sequence

1. **Discover** - use `nature-academic-search` when MCP is configured; otherwise run `scripts/find_papers.py`. Build 2-4 queries from the parameter name, synonyms, cell type, and assay. Example: `GATA2 half-life P815 cycloheximide`, `GATA2 protein turnover proteasome`.
2. **Triage** - prefer primary research articles with Methods and primary data. Reviews, conference abstracts, and database records are context, not automatic proof.
3. **Verify metadata** - use `scripts/verify_refs.py` for DOI/PMID/title/authors/journal/pages. Do not merge two records because their titles look alike.
4. **Acquire PDF** - try open access first with `scripts/download_pdf.py`. For a subscription source, use the bundled `nature-downloader` with the user's logged-in Chrome session, or a PDF the user already obtained.
5. **Extract** - use `scripts/locate_passage.py` to record the PDF page, verbatim sentence, conditions, and screenshot. Use `nature-reader` only to understand the paper, not to replace the source quote.
6. **Record** - one entry in the spec. If a step fails, write `【找不到】` or `【找不到全文】` and state exactly what is missing.
7. **Build** - run `scripts/build_evidence_docx.py` and inspect the Word/PDF output.

## Commands

```bash
# Environment and component check
python scripts/lit_stack.py doctor
python scripts/lit_stack.py list
python scripts/lit_stack.py path nature-downloader

# Candidate discovery (core fallback)
python scripts/lit_stack.py search "GATA2 half-life P815" --limit 12 --out candidates.csv

# Metadata verification
python scripts/verify_refs.py refs.csv

# Open-access PDF
python scripts/download_pdf.py 10.1371/journal.pcbi.1000771 --out-dir pdfs --email you@example.org

# Authorized institutional route through the bundled downloader
python scripts/lit_stack.py school preset "上海交通大学"   # or: school url "<library resource URL>"
python scripts/lit_stack.py school health --force
python scripts/lit_stack.py download --doi 10.1371/journal.pcbi.1000771 --out-dir pdfs --si

# In-document passage search and screenshot
python scripts/locate_passage.py pdfs/paper.pdf "verbatim sentence" --out-dir shots --page 3

# DOCX build
python scripts/build_evidence_docx.py spec.json report.docx
```

`download_pdf.py` checks OpenAlex, Unpaywall, and Europe PMC and accepts only a valid `%PDF-` response. It never attempts a paywall bypass. Access failures are classified as `cloudflare_challenge`, `publisher_verification`, `institutional_access_required`, `rate_limited`, `response_not_pdf`, or `transport_error`; verification classes return exit code 4 for a manual browser handoff.

`locate_passage.py` uses an alphanumeric-only matching stream, so line breaks, PDF hyphenation, and variable spacing do not prevent a match. It returns the 1-based PDF page, bounding box, surrounding context, page PNG, and highlighted crop PNG.

## Adapter rules

- Read the installed adapter's own `SKILL.md`; do not copy its source into this repository.
- Resolve its path with `python scripts/lit_stack.py path <name>`.
- If it is absent, use the named fallback and say so.
- An adapter may propose, download, read, or organize; the final evidence entry still requires a source PDF, page, verbatim quote, conditions, and screenshot when available.

## Division of labour

- This skill owns the evidence standard, page-level citation, screenshot record, entry format, and DOCX.
- `find_papers.py` proposes candidates; a candidate is not evidence.
- `verify_refs.py` checks identity; a matching DOI is not proof that the paper reports the claimed value.
- `locate_passage.py` proves location; the author must still check experimental conditions and interpretation.
- `nature-downloader` proves lawful access; it does not prove that a passage exists or that the paper supports the claim.
- `organize-research-literature` helps find and summarize local papers; a summary is not a source quote.

## Failure rules

- No MCP or discovery skill -> use the bundled scripts; do not claim an external search was performed.
- No open-access PDF -> mark `【找不到开放获取 PDF】`; do not scrape around a paywall.
- CAPTCHA, Cloudflare, SSO, or CARSI -> stop, ask the user to complete the authorized login in Chrome, or mark `【找不到全文】`.
- No DOI/PMID match -> keep records separate and flag `MISMATCH`.
- Review or abstract only -> label it; do not promote it to primary evidence.
- Scanned PDF with no text layer -> OCR first, or record that the screenshot cannot be located automatically.
- Adapter absent -> use the core fallback; never claim the adapter was used.
