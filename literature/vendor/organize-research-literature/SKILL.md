---
name: organize-research-literature
description: Batch organize and deeply review local PDF research papers for any research topic into an existing Excel literature-summary workbook. Use when Codex must recursively scan local PDFs offline, apply a user-provided or inferred research profile, extract metadata and body evidence, deduplicate against Excel, preserve workbook formatting, append new literature rows, fill blank cells only, process only newly added PDFs, restrict to high-relevance papers, write Chinese or user-specified academic summaries, translate English residues in summary columns, mark relevance/read-priority labels with colors, sort by relevance, or generate a processing log.
---

# Organize Research Literature

Use this skill to turn a local folder of PDF papers into a structured literature-summary Excel workbook for any research topic. The topic-specific part must come from a **research profile**, not from hard-coded domain assumptions.

## Core Contract

- Work from local files only unless the user explicitly permits web search. Never use filenames alone to invent paper content.
- Start by reading the workbook structure: sheet names, headers, existing rows, formatting, widths, row heights, freeze panes, filters, wrapping, and any relevance/remarks columns.
- Preserve the input workbook. Save to a separate output path unless the user explicitly asks to update it in place; for in-place work, create a timestamped backup first.
- Recursively scan PDFs, extract metadata/body text, identify non-paper files, and deduplicate the whole batch before adding new rows.
- Never overwrite non-empty human-written cells unless the user explicitly asks for overwrite. For existing papers, fill blank cells only.
- Use the workbook’s existing columns when possible; map semantically by header names instead of assuming only one fixed template.
- Write summaries in the requested language. For Chinese workbooks, B and summary/remarks columns must be Chinese-only prose unless the user explicitly requests bilingual output.
- Write a CSV log with parse status, duplicate status, Excel action, relevance level, evidence notes, and failure reason.

## Research Profile

Before judging relevance or writing remarks, establish the research profile from the user prompt, a supplied profile file, the workbook notes, or a concise inference that you state in the report.

Read `references/research_profile_template.md` when the user supplies a new topic, changes topics, or asks for deep review. The profile should include:

- research topic and current project goal;
- target objects/materials/populations/systems;
- methods, instruments, models, theories, datasets, variables, and metrics that matter;
- key terms and synonyms in the paper language and output language;
- high/medium/low relevance criteria;
- output workbook path, target sheet, column schema, language, and any forbidden actions.

If a profile is missing but the task is otherwise clear, infer a minimal profile and proceed; log that it was inferred.

## Default Workflow

1. Confirm or infer `ROOT_DIR`, `INPUT_EXCEL`, `OUTPUT_EXCEL`, `LOG_CSV`, and optional `RESEARCH_PROFILE`.
2. Load the Excel workbook with `openpyxl`; record headers, data rows, formatting, and relevance/remarks column usage.
3. Scan only PDF files recursively. Skip temporary Excel files, logs, images, compressed files, blank/corrupted PDFs, covers, table-of-contents files, journal information pages, and supplements without a reliable title.
4. Extract text with local tools in this order when available: PyMuPDF/fitz, `pypdf`, `pdfplumber`. Use fallbacks and log failures.
5. Extract title, DOI, first author, journal/conference/source, year, abstract, keywords, methods, results, conclusions, figure/table captions, formulas, limitations, and topic-specific evidence.
6. Deduplicate using DOI, normalized title, title similarity plus first author, and existing Excel rows.
7. Classify relevance using the research profile:
   - `high`: directly supports the user’s current research object, method, model, measurement, dataset, experiment, theory, design, or writing argument.
   - `medium`: adjacent theory, method, background, benchmark, parameter definition, application context, or transferable analysis idea.
   - `low`: broad background or weakly related material that should not drive core design or argumentation.
   - `unreadable_or_manual_review`: insufficient readable evidence; do not force a weak label.
8. Write or fill workbook cells according to `references/column_schema.md` and the workbook’s existing headers.
9. If relevance labels are requested or a relevance column already exists, write only the approved labels and apply the requested colors.
10. Reopen the output workbook and verify row counts, duplicate titles, blank titles, wrapping, relevance labels/colors, column alignment, and language cleanup.

## Use The Script

Prefer the bundled script for repeatable scanning, extraction, deduplication, conservative drafting, relevance labeling, and validation:

```powershell
python scripts/research_literature_excel.py `
  --root "C:\path\to\papers" `
  --input-excel "C:\path\to\论文总结.xlsx" `
  --output-excel "C:\path\to\论文总结_整理完成.xlsx" `
  --log-csv "C:\path\to\research_literature_processing_log.csv" `
  --profile "C:\path\to\research_profile.md"
```

Useful modes:

- “只处理新增文献”: add `--only-new`.
- “只整理高相关论文”: add `--high-only`.
- “补全空白单元格”: add `--fill-blanks-only`.
- “中低相关也写入”: add `--include-medium-low`.
- “写回原 Excel / 整理到原文件”: add `--in-place` after making sure a backup will be created.
- “给 K 列/相关度列标阅读优先级”: add `--mark-relevance`.
- “按相关度排序”: add `--sort-by-relevance`.
- “确保中文/翻译英文残留”: run the script and then scan summary columns for `[A-Za-z]{3,}`; rewrite remaining cells manually if needed.

The script is conservative. It can draft and validate, but high-stakes summaries should be inspected and polished by Codex using the profile and extracted evidence.

## Deep Review Mode

Use deep review mode when the user asks for 精读, full reading, doctoral-level summaries, research-plan support, or detailed relevance ranking.

For each readable paper, extract evidence from:

- title page, abstract, keywords, introduction;
- methods/experiment/numerical setup/theory/data section;
- results, discussion, conclusions, limitations;
- figures, tables, captions, formulas, appendices, and supplementary evidence available in the PDF.

For every topic, adapt the evidence matrix to the profile. Typical dimensions include:

- research object/system/material/population and boundary conditions;
- apparatus, instrument, dataset, sample, geometry, protocol, intervention, or algorithm;
- variables, parameters, metrics, uncertainty, error, validation, and reproducibility;
- theoretical model, empirical correlation, statistical method, numerical method, or evaluation benchmark;
- quantitative ranges, thresholds, effect sizes, model errors, performance gains, and failure cases;
- author-stated limitations and agent-inferred migration risks, clearly separated.

Use `文中未明确给出` for missing evidence. Do not make the user’s future plan sound like the paper’s completed work.

## Relevance Labels

When a relevance/read-priority column is requested or already present:

- Use existing relevance-like headers if present: `相关度`, `阅读优先级`, `优先级`, `Relevance`, `Priority`.
- If no such column exists and K is blank, set K1 to `相关度（阅读优先级）`; otherwise add a new column after existing data columns.
- Write only `强相关`, `中等相关`, `弱相关`, or blank for manual review.
- Map log values as `high -> 强相关`, `medium -> 中等相关`, `low -> 弱相关`, `unreadable_or_manual_review -> blank`.
- Default colors:
  - `强相关`: fill `#C00000`, white bold centered text.
  - `中等相关`: fill `#4472C4`, white bold centered text.
  - `弱相关`: fill `#7F7F7F`, white bold centered text.
- If sorting is requested, move whole rows across all populated columns, preserving style and row integrity. Stable order inside each relevance group.

## Writing Quality

Write for the user’s research use case, not as abstract translation.

- `创新点/主要贡献`: identify concrete novelty, solved limitation, new range, method, model, dataset, validation, or insight.
- `全文概要`: cover background, object, core problem, route, conditions/data, findings, conclusions, and limitations.
- `研究重点`: name the key questions, parameters, variables, methods, models, comparisons, and sections/figures/formulas worth rereading.
- `研究意义`: explain academic and engineering/clinical/social/design value without repeating action remarks.
- `研究方法`: describe experimental, theoretical, computational, statistical, field, archival, or design methods specifically.
- `备注/与课题关联`: state why the paper matters to the current profile, what can be borrowed, what cannot be transferred, and 1-3 executable next actions for high-relevance papers.

## Language Cleanup

For Chinese deliverables, scan title-translation and summary/remarks columns for English residues with `[A-Za-z]{3,}`.

- Translate or rewrite copied English sentences and section labels.
- Allow original English in original-title, author, journal/source, DOI, file paths, and unavoidable formulas only.
- Prefer translated technical terms; keep bilingual terms only when the user asks.

## Validation Checklist

Before final response:

- Confirm backup/output paths.
- Confirm workbook opens with `openpyxl`.
- Confirm sheet names, max row/column, freeze panes, column widths, and formatting are preserved.
- Confirm no blank original-title cells in data rows.
- Confirm duplicate titles are removed, pre-existing, or logged.
- Confirm summary/remarks columns wrap and align correctly.
- Confirm requested language cleanup passes.
- Confirm relevance labels and colors are valid if used.
- Confirm log CSV exists and includes skipped/failure reasons.
- Report counts: scanned PDFs, identified papers, text extracted, added rows, updated rows, duplicates, suspected duplicates, relevance counts, unreadable/manual-review files, output paths, and top 5 most relevant papers with reasons tied to the profile.
