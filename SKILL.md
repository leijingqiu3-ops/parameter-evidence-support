---
name: parameter-evidence-support
description: Build a page-cited, screenshot-backed parameter-evidence Word report for computational-biology and systems-biology manuscripts. Use when the user supplies a main text, SI, parameter table, model, or code and asks to verify each parameter against primary literature, distinguish measured versus derived versus model-set values, find candidate papers, download authorized open-access PDFs, locate the exact passage, figure, or table, capture an original-text screenshot, correct wrong values or citations, and deliver a fixed-format DOCX/PDF with explicit 【找不到】 markers. Triggers include 参数文献支撑, 参数文献核验, 参数依据, 参数出处, SI 参数溯源, 原文截图 Word, 审稿前参数审计, parameter provenance, parameter evidence report, and parameter citation audit. Do not use for ordinary manuscript writing, general literature reviews without a parameter list, or GEO/expression-matrix import tasks unless the user explicitly asks to combine them.
metadata:
  short-description: Self-contained, page-cited parameter evidence reports
---

# Parameter Evidence Support

Turn a manuscript's parameter list into an auditable Word report: every numerical value is classified, traced to a source when one exists, quoted at the exact location, illustrated with an original-text screenshot when available, and marked `【找不到】` when it is not.

The core workflow is self-contained. A user who downloads this skill can run the bundled search, open-access download, PDF passage locator, metadata verifier, and DOCX builder without installing the other Codex skills referenced below.

## When to use

Use this skill when the user wants to:

- audit every parameter in a main text or SI before submission;
- verify whether a cited paper actually reports a stated value;
- find primary literature for an unsupported parameter;
- distinguish an experimental measurement from a derived, normalized, fitted, or code-set value;
- correct a wrong DOI, PMID, journal, value, unit, or experimental condition;
- download an authorized PDF and capture the sentence, figure, or table that supports a value;
- produce a Chinese Word report with manuscript-ready English wording and page-level provenance.

Typical requests: `参数文献支撑`, `每个参数找到原始文献`, `这句参数出处在哪里`, `把参数核验做成 Word`, `找 PDF 并截原文`, `审稿前参数审计`.

## Inputs

Required:

- Main manuscript and SI, preferably as PDF or DOCX.
- A parameter list, or permission to extract one from the manuscript and SI.
- Output directory and desired report name.

Useful but optional:

- Model equations or source code, to identify normalized and operational constants.
- A local literature folder, to reuse PDFs already downloaded.
- A logged-in institutional browser session, for authorized PDF access.
- Existing reference style or a sample report whose layout must be retained.

Input contract:

1. Freeze the scope before searching. Parameter evidence and unrelated data-import work must remain separate unless the user explicitly requests one combined deliverable.
2. Treat the manuscript's own definitions as claims to verify, not as evidence.
3. If a value, range, or citation is ambiguous, keep the ambiguity visible in the report instead of silently choosing a number.

## Self-contained core

These files are enough for the standard path:

| File | Role |
|---|---|
| `scripts/find_papers.py` | Europe PMC + OpenAlex candidate search, no MCP or API key |
| `scripts/verify_refs.py` | Crossref + PubMed DOI/PMID metadata checks |
| `scripts/download_pdf.py` | OpenAlex + Unpaywall + Europe PMC open-access PDF download |
| `scripts/locate_passage.py` | Locate a verbatim passage, report its PDF page, and render page/crop screenshots |
| `scripts/build_evidence_docx.py` | JSON-driven DOCX builder with the fixed house style |
| `assets/example_spec.json` | Minimal working report specification |

Install the Python dependencies once:

```bash
pip install -r requirements.txt
```

The only unavoidable external dependency is lawful access to a paywalled PDF. The bundled downloader handles open-access copies only and never bypasses a paywall, CAPTCHA, Cloudflare check, or institutional login.

## Workflow

### 1. Build the parameter inventory

Read the main text and SI completely. Record one row for every numeric value, including:

- symbol, value, unit, and equation or table location;
- whether it is measured, derived, fitted, scanned, or hard-coded;
- the experimental system or normalization that the manuscript claims;
- the citation the manuscript currently attaches to it.

Include scan ranges and numerical-protocol constants, not only biological parameters.

### 2. Classify before searching

| Grade | Meaning | Test |
|---|---|---|
| A | Direct experimental measurement | A primary study reports the value under relevant conditions |
| B | Derived from an experimental input | The conversion formula and input value are both documented |
| C | Model, normalized, fitted, scanned, or code-set value | No primary measurement should be cited as if it were the source |
| D | Not found | No accessible source or no verifiable passage; write `【找不到】` |

For B and C values, search for the input or the modelling rationale, not for a paper that happens to contain the final number. Example: search the protein half-life before deriving a degradation rate; search the Kd ratio before explaining a normalized Hill threshold.

### 3. Find candidate papers and verify identity

```bash
python scripts/find_papers.py "GATA2 half-life P815" --limit 15 --year-from 1990 --out candidates.csv
python scripts/verify_refs.py 10.1111/j.1365-2443.2005.00864.x 15966900
```

Prefer primary research articles with Methods and primary data. Reviews, conference abstracts, and database records are candidates or context, not automatic proof. A DOI that resolves is not enough: it must resolve to the paper that actually contains the claim.

### 4. Acquire the PDF lawfully

```bash
python scripts/download_pdf.py 10.1371/journal.pcbi.1000771 --out-dir pdfs --email you@example.org
```

The downloader checks OpenAlex, Unpaywall, and Europe PMC, accepts only a response with a valid `%PDF-` header, and reports `【找不到开放获取 PDF】` when no authorized copy is available. For an institutional subscription, use the user's logged-in browser or `nature-downloader` as an optional accelerator. If access is not authorized, stop and mark the source `【找不到全文】`.

### 5. Locate the exact passage and screenshot it

```bash
python scripts/locate_passage.py pdfs/paper.pdf "verbatim sentence from the paper" --out-dir shots --page 3
```

The locator tolerates line breaks, PDF hyphenation, and different spacing. It writes:

- a JSON record with PDF page number, bounding box, context, and occurrence count;
- a full-page PNG;
- a cropped PNG with the matched lines highlighted.

Record both the PDF page and the journal page or figure/table number. If the passage spans a page break or the PDF has no text layer, shorten the quote, inspect adjacent pages, or OCR the PDF. Do not infer a screenshot from an abstract.

### 6. Diagnose and correct

For each entry, issue one verdict:

- keep: the value and citation are supportable as written;
- relabel: the number is usable but is not the kind of quantity claimed;
- re-derive: keep the experimental input but recalculate the model value;
- remove: no defensible source or derivation;
- not found: evidence is unavailable.

Prioritize corrections as must-fix, should-fix, or acceptable. Never change a value merely to make the narrative smoother.

### 7. Build and QA the report

Create a JSON specification from `assets/example_spec.json`, then run:

```bash
python scripts/build_evidence_docx.py spec.json output.docx
```

Export the DOCX to PDF and inspect the rendered pages. Check that every inventory row appears once, every A entry has a page, quote, and screenshot, every B/C entry is labelled, every missing item states what is missing, and the DOCX and PDF contain the same entries.

## Outputs

The primary deliverable is a Chinese DOCX plus a PDF preview, using the established house style:

- A4; Microsoft YaHei plus Cambria; 10.5 pt body;
- heading colour `#174A6E`; quote block `#F4F8FA`;
- screenshot width 16.4 cm with caption below;
- footer containing the document title and page number;
- revision colours: red `#AE3A3A` must change, orange `#915E0F` needs relabelling, green `#236C4D` usable.

Each entry follows this fixed order:

1. parameter, formula, value, unit;
2. cited literature;
3. journal, year, volume, pages, DOI/PMID;
4. paper title;
5. authors;
6. links;
7. verbatim English passage;
8. Chinese verification note;
9. web link;
10. verdict;
11. manuscript-ready English sentence;
12. local PDF filename and page;
13. original-text screenshot.

The report also includes an evidence-grade summary, a prioritised correction list, a `【找不到】` section, and a list of PDFs actually obtained.

Supporting outputs may include a candidate-search CSV, a verified-reference CSV, page-mapped PDFs, and cropped screenshots. A search hit is only a candidate; it becomes evidence only after the passage, page, and conditions are verified.

## Reproducibility contract

A second user can reproduce the same report structure on another machine when they have:

1. this skill directory;
2. Python 3.10 or later and `pip install -r requirements.txt`;
3. the same `spec.json`;
4. the same local PDFs and screenshot files referenced by the spec;
5. lawful access to the sources.

Given those inputs, `build_evidence_docx.py` produces the same entry order, typography, colours, tables, and screenshot treatment. Word/LibreOffice versions and missing fonts can change pagination slightly, so the PDF preview must be checked rather than assumed byte-identical.

The evidence itself is reproducible only when the source PDF and the quoted page are available. Keep the local PDF filename in every entry. If a source is paywalled and the second user has no subscription, the correct result is `【找不到全文】`, not a fabricated screenshot.

## Evidence rules

- Never invent a citation, DOI, PMID, page, value, quote, or screenshot.
- Never present a code output, fitted value, normalized threshold, or steady-state inverse as an experimental measurement.
- A review article is not a primary measurement. An abstract is not a full paper. A conference abstract must be labelled as such.
- Kd values are comparable only when probe, construct, salt, temperature, and assay match. Record those conditions.
- A normalized threshold such as `K_G2norm` is dimensionless; do not call it a molar Kd.
- If a source cannot be obtained, leave the unsupported fields empty and write `【找不到】` or `【找不到全文】` plus exactly what is missing.
- Quote the source verbatim; keep gene symbols, superscripts, `±`, and units intact.
- The report is Chinese, but quoted source text remains in the original language.
- Do not merge a parameter-evidence task with an unrelated GEO/expression-matrix import task.

## Optional integrations

The core path does not require other skills. These are optional accelerators:

| Need | Optional tool | Core fallback |
|---|---|---|
| Broader multi-source discovery or citation matching | `nature-academic-search` | `scripts/find_papers.py` + `scripts/verify_refs.py` |
| Institutional or browser-session PDF access | `nature-downloader` | `scripts/download_pdf.py`; manual PDF when authorized |
| Bulk inventory of hundreds of local PDFs | `organize-research-literature` | use a local file list or the supplied PDFs directly |
| Full-paper reading or translation | `nature-reader` | `scripts/locate_passage.py` for the evidence passage |

Routing and failure rules are in `references/literature-stack.md`. If another skill is absent, the core scripts must still run; never claim that an external tool was used when it was not.

## Resources

- `references/entry-spec.md` - exact field order, table widths, colours, and JSON schema.
- `references/verification-playbook.md` - queries, PDF acquisition, page mapping, screenshots, and common traps.
- `references/literature-stack.md` - core scripts versus optional integrations.
- `scripts/find_papers.py` - candidate search without MCP or API keys.
- `scripts/verify_refs.py` - batch DOI/PMID metadata checker.
- `scripts/download_pdf.py` - open-access PDF acquisition with explicit failure status.
- `scripts/locate_passage.py` - page-level passage search and screenshot rendering.
- `scripts/build_evidence_docx.py` - JSON-driven DOCX builder.
- `assets/example_spec.json` - minimal working specification.
- `assets/example_screenshot.png` - placeholder screenshot for the example.

## Limits

- The skill cannot bypass a paywall, CAPTCHA, Cloudflare check, or institutional login. It stops and asks for a lawful manual handoff.
- It cannot guarantee that every paper has an accessible PDF or a reportable page-level passage.
- It does not treat search ranking, citation counts, or a matching title as proof of a parameter.
- It does not invent a screenshot when no PDF is available.
- Scanned PDFs without a text layer require OCR before `locate_passage.py` can find a quote.
- It does not perform parameter fitting, model selection, or GEO/expression-matrix import as part of this workflow.
- Ambiguous values, units, or experimental conditions remain flagged for author confirmation.