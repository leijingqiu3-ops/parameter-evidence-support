# Literature stack router

Use this router before a literature step. The evidence standard in the parent skill always wins over a convenience tool.

## Route by task

| Task | First choice | If unavailable | Do not |
|---|---|---|---|
| Find candidate papers for a parameter | Installed `nature-academic-search`, if its MCP tools are available | `scripts/find_papers.py` | Treat search ranking or citation count as evidence |
| Verify a DOI/PMID/title/authors | `scripts/verify_refs.py`; optionally `nature-academic-search` citation-verification | Crossref + PubMed through the bundled verifier | Merge two records because their titles look alike |
| Obtain an open-access PDF | `scripts/download_pdf.py` | Direct lawful publisher/archive URL supplied by the user | Scrape around a paywall or rename HTML to PDF |
| Obtain an authorized subscription PDF | Bundled `nature-downloader` with the user's logged-in Chrome session | Ask for a user-supplied PDF; mark `【找不到全文】` | Ask for passwords, cookies, or OTP; bypass CAPTCHA/Cloudflare |
| Inventory a large local PDF folder | Bundled `organize-research-literature` | Use the supplied file list and run core scripts only on papers selected for evidence | Infer paper content from filenames |
| Read/translate a whole paper | Installed `nature-reader` | `scripts/locate_passage.py` for the exact evidence passage | Replace page-level evidence with a summary |
| Add citations to manuscript prose | Installed `nature-citation` | `scripts/find_papers.py` + `scripts/verify_refs.py` + manual assembly | Cite a metadata-only candidate without checking the claim |
| Run recurring literature monitoring | Installed `nature-literature-pipeline` | Schedule `scripts/find_papers.py` manually | Let a monitoring digest become the evidence report |
| Scope a field or build a title/abstract map | Installed `literature-mapper` | `scripts/find_papers.py` | Treat abstract-level mapping as full-text proof |
| Turn Zotero items into close-reading notes | Installed `zotero-taxonomy-curator` | Keep notes outside the evidence report | Treat an Obsidian note as the primary source |

## Route by source state

1. **No PDF yet** -> search and verify identity, then try open access, then authorized browser access.
2. **PDF available** -> `scripts/locate_passage.py` and retain the PDF page, quote, and screenshot.
3. **Paywalled and no authorized session** -> stop at `【找不到全文】`; do not substitute a review or abstract.
4. **Scanned PDF** -> OCR first; record that automatic text location was unavailable if OCR is not possible.
5. **Only abstract/metadata** -> label it as such; never use it as a measured-value source.

## Execution invariants

- The final report is built from verified entries, not from a search result table.
- Every entry keeps local PDF filename, page, verbatim source text, and screenshot when available.
- A bundled or adapter tool may propose, download, read, or organize; it does not get to waive the evidence rules.
- If an adapter is absent, say so and use the fallback. Never claim an external skill was used when it was not.
- Do not copy an unlicensed adapter's source into this repository. Detect it with `python scripts/lit_stack.py path <name>` and read its own `SKILL.md` in place.

## Useful commands

```bash
# Fresh-machine bootstrap for missing adapters
python scripts/install_literature_skills.py --check
python scripts/install_literature_skills.py --install

python scripts/lit_stack.py doctor
python scripts/lit_stack.py list
python scripts/lit_stack.py path nature-downloader

# Open-access route
python scripts/download_pdf.py 10.1371/journal.pcbi.1000771 --out-dir pdfs --email you@example.org

# Authorized institutional route through the bundled downloader
python scripts/lit_stack.py school preset "上海交通大学"
python scripts/lit_stack.py school health --force
python scripts/lit_stack.py download --doi 10.1371/journal.pcbi.1000771 --out-dir pdfs --si

# Search and verify through the core fallback
python scripts/lit_stack.py search "GATA2 half-life P815" --limit 15 --out candidates.csv
python scripts/verify_refs.py candidates.csv
```

For first-run institutional setup, read `literature/vendor/nature-downloader/SKILL.md` and use the user's actual library resource URL rather than guessing from a school name.
