# Verification playbook

## 1. Metadata first

PubMed (no API key required):

```text
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term=<query>
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=<pmid>
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=text&rettype=abstract&id=<pmid>
```

Crossref:

```text
https://api.crossref.org/works/<doi>
https://api.crossref.org/works?rows=3&query.bibliographic=<title+author>
```

Accept a reference only when DOI, title, journal, volume, pages and first author all match. A PMID can point to a different paper; never copy a PMID from a secondary source without checking the title.

## 2. Find a legal PDF

Bundled open-access attempt:

```bash
python scripts/download_pdf.py <DOI-or-PMID> --out-dir pdfs --email you@example.org
```

Order of preference:

1. publisher PDF via the institution's logged-in browser;
2. PMC / Europe PMC (`https://europepmc.org/articles/PMCxxxx?pdf=render`);
3. Unpaywall (`https://api.unpaywall.org/v2/<doi>?email=...`);
4. Semantic Scholar `openAccessPdf`;
5. author/institutional repository.

If the publisher shows a CAPTCHA or Cloudflare challenge, do not bypass it. Try the institutional session once, then mark `【找不到全文】` and use the abstract only. Record that decision in the entry.

## 3. Locate the sentence

Bundled locator:

```bash
python scripts/locate_passage.py paper.pdf "verbatim sentence" --out-dir shots --page 2
```

It writes a JSON record, a full-page PNG, and a highlighted crop. It tolerates line breaks, PDF hyphenation, and variable spacing.

Manual fallback: dump text page by page and search for the number.

```python
import fitz
doc = fitz.open(path)
for i, page in enumerate(doc):
    print(i + 1, page.get_text())
```

Search for the number first (`27.7`, `5.5`, `0.94`), then read the surrounding paragraph. Record:

- **PDF page** (`p.2`) — the page in the file;
- **journal page** (`p.694`) — printed page number;
- **Fig/Table** (`Fig. 1C`, `Table S4`) when the value is in a panel or table.

If the number appears only in a figure axis or table image, say so; do not invent a sentence.

## 4. Screenshot rules

- Capture the sentence plus at least one line above and below.
- Include the running head or journal logo when possible so the source is identifiable.
- Highlight the parameter sentence in yellow if the tool allows it; otherwise crop tightly around the paragraph.
- Do not crop off `±`, units, superscripts or the figure panel label.
- Name files `NN_parameter_value_firstauthor_page.png`.
- If no screenshot can be produced, write `【找不到截图】`; never insert an unrelated figure.

## 5. Conditions that must be recorded

For half-lives:

- species, cell line/primary cells;
- chase method (cycloheximide, pulse-chase), antibody, normalization;
- isoform (e.g. FLI1 p51 vs p48).

For Kd:

- protein construct (full-length, DBD, zinc fingers);
- DNA probe sequence and flanking bases;
- assay (EMSA, SPR, ITC, fluorescence);
- salt concentration and temperature;
- whether the value is apparent or equilibrium.

Two Kd values may be combined only if the probe and construct are the same. If they are not, use them as an ordering constraint, not as a ratio.

## 6. Common traps

| Trap | Check |
|---|---|
| Review cited as primary | Does the paper report the measurement, or cite another paper? |
| Abstract cited as full paper | Is there a PDF with Methods/Figures? If not, label it. |
| Conference abstract | `Blood 128:1479` style; no full paper; label `abstract`. |
| Internal contradiction | Search the same PDF for the value again (e.g. 70 h vs 50 h in one SI). |
| Wrong author list | PubMed/Crossref may differ from the manuscript's reference list. |
| Wrong DOI | Resolve it; a plausible-looking DOI can point to an unrelated paper. |
| Normalized vs molar | `K_norm = 0.30` is dimensionless; `Kd = 0.10 nM` is molar. Never equate them. |
| Code-derived value | `x*`, `2μK`, `α = μC*`, `ΔT` from pseudotime are outputs, not measurements. |
| Different cell state | 5.5 h in splenocytes ≠ 70 h in early progenitors. State both. |

## 7. Wording for missing evidence

Use one of these, and leave the unsupported fields empty:

```text
【找不到全文】出版社全文无法获取（原因）；仅 PubMed 摘要可核对，图和实验条件未核对。
【找不到原文】未检索到报告该数值的原始论文；当前数值来自模型设定/代码，不能写成实验值。
【找不到截图】已核对原文，但无法截取包含该句的页面；原句与页码见上。
【找不到 full paper】该文献本身只有会议摘要，没有全文。
```

Do not write “approximately”, “probably”, or a substitute citation to fill the gap.

## 8. Separation of tasks

A parameter-provenance report is not a GEO/expression-data report. Do not add:

- cell counts, gene counts, matrix dimensions;
- pseudotime values;
- dataset QC metrics;
- GEO accession descriptions,

unless the user explicitly asks for them in the same document. Keep the parameter report focused on values that enter the model.
