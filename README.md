# Parameter Evidence Support

A self-contained Codex skill for turning a manuscript's parameter list into an auditable, page-cited evidence report.

It was built for computational-biology and systems-biology manuscripts, especially cases where a main text or SI mixes experimental measurements, derived rates, normalized Hill thresholds, fitted parameters, scan ranges, and code-set numerical constants.

## 给第一次使用的人（中文）

你不需要先懂代码，也不需要自己运行脚本。准备好这三样东西即可：

1. 正文：PDF 或 DOCX；
2. SI：PDF 或 DOCX；
3. 一个输出文件夹，例如 `D:\参数核验`。

把下面这段直接发给 Codex，并把路径换成你自己的：

```text
使用 parameter-evidence-support 技能，核对我正文和 SI 的全部参数，
找原始文献、下载 PDF、截取原文，按固定格式生成 Word；
找不到的写【找不到】。

正文：D:\我的论文\正文.pdf
SI：D:\我的论文\SI.pdf
输出到：D:\参数核验

如果某篇文献没有访问权限，不要绕过付费墙，直接标【找不到全文】。
```

技能会依次做：

1. 从正文和 SI 提取全部参数；
2. 判断哪些是实测值、换算值、模型设定或找不到；
3. 检索原始文献并核验 DOI/PMID；
4. 下载有权限的 PDF；
5. 定位原文句子并截图；
6. 生成固定格式 Word，并列出必须修改的地方。

你最后主要检查三个结果：

- `参数文献依据核验_完整版.docx`
- 同名 PDF 预览
- `【找不到】` 或 `【找不到全文】` 清单

详细步骤见：[`docs/TUTORIAL.zh-CN.md`](docs/TUTORIAL.zh-CN.md)

## What it does

- Extracts every numeric parameter from a manuscript, SI, parameter table, or code.
- Classifies each value as **A measured**, **B derived**, **C model/code-set**, or **D not found**.
- Searches Europe PMC and OpenAlex for candidate primary papers.
- Verifies DOI/PMID metadata through Crossref and PubMed.
- Downloads open-access PDFs through OpenAlex, Unpaywall, and Europe PMC.
- Distinguishes `cloudflare_challenge`, `publisher_verification`, `institutional_access_required`, and transport failures so the user can resume from an authorized browser session.
- Locates the exact sentence, figure, or table; records PDF page and journal page.
- Renders a full-page PNG and a highlighted crop of the source passage.
- Supports multiple screenshots per parameter, height caps, and automatic page breaks that keep each image with its caption.
- Checks experimental conditions such as species, cell type, assay, probe, construct, salt, and time window.
- Distinguishes a measurement from a normalized threshold or a code-derived value.
- Generates a fixed-format Chinese DOCX/PDF with a correction list and explicit `【找不到】` markers.
- Produces manuscript-ready English wording for supported values.

The core path does **not** require any other Codex skill. Optional integrations are listed below.

## Tutorial

- 中文使用教程：[`docs/TUTORIAL.zh-CN.md`](docs/TUTORIAL.zh-CN.md)
- 教程覆盖：准备文件、复制指令、回答追问、检查 Word 和常见问题。

## Requirements

- Python 3.10 or later
- Network access for metadata and open-access PDF lookup
- Microsoft Word or LibreOffice for PDF export (optional but recommended)

```bash
pip install -r requirements.txt
```

## Install

Copy this directory into your Codex skills directory:

```text
~/.codex/skills/parameter-evidence-support
```

On Windows:

```text
C:\Users\<you>\.codex\skills\parameter-evidence-support
```

The skill is loaded from `SKILL.md`.

## Quick start

```bash
# 1. Find candidate papers
python scripts/find_papers.py "GATA2 half-life P815" --limit 15 --out candidates.csv

# 2. Verify DOI/PMID metadata
python scripts/verify_refs.py 10.1111/j.1365-2443.2005.00864.x 15966900

# 3. Download an open-access PDF
python scripts/download_pdf.py 10.1371/journal.pcbi.1000771 --out-dir pdfs --email you@example.org

# 4. Locate a verbatim passage and make screenshots
python scripts/locate_passage.py pdfs/paper.pdf "verbatim sentence" --out-dir shots --page 3

# 5. Build the Word report
python scripts/build_evidence_docx.py spec.json report.docx
```

Example request:

```text
Use parameter-evidence-support to audit every parameter in my manuscript and SI.
Trace each value to a primary source, download authorized PDFs, locate exact
passages and screenshots, correct wrong citations or values, and build the Word
report in the established format. Mark anything unavailable as 【找不到】.
```

## Reproducibility

A second user can reproduce the same report structure when they have:

1. this repository;
2. Python and the packages in `requirements.txt`;
3. the same `spec.json`;
4. the same local PDFs and screenshot files referenced by the spec;
5. lawful access to the sources.

The builder is deterministic for the entry order, typography, colours, tables, and screenshot treatment. Screenshot entries accept `images` lists, per-image captions, width and height caps, and `page_break: true | false | auto`. Pagination can vary slightly across Word/LibreOffice versions or if the specified fonts are unavailable, so the exported PDF must still be inspected.

The evidence itself is reproducible only when the source PDF and the quoted page are available. Every entry should keep the local PDF filename and page. If a source is paywalled and the second user has no subscription, the correct result is `【找不到全文】`, not a fabricated screenshot.

## Repository layout

```text
SKILL.md
requirements.txt
docs/TUTORIAL.zh-CN.md
agents/openai.yaml
references/entry-spec.md
references/verification-playbook.md
references/literature-stack.md
scripts/find_papers.py
scripts/verify_refs.py
scripts/download_pdf.py
scripts/locate_passage.py
scripts/build_evidence_docx.py
assets/example_spec.json
assets/example_screenshot.png
```

## Evidence rules

- Never invent a citation, DOI, PMID, page, value, quote, or screenshot.
- A review is not a primary measurement.
- An abstract is not a full paper.
- A normalized threshold is not a molar Kd.
- A search hit is a candidate, not evidence.
- If a source is unavailable, state exactly what is missing and mark `【找不到】`.
- Do not bypass paywalls, CAPTCHAs, Cloudflare, or institutional login.

## Optional integrations

These are not required for the core path:

- `nature-academic-search` for broader MCP-based discovery.
- `nature-downloader` for authorized institutional/browser-session PDF access.
- `organize-research-literature` for bulk inventory of a large local PDF folder.
- `nature-reader` for full-paper reading or translation.

## Dependencies and licenses

- `python-docx` - MIT
- `PyMuPDF` - AGPL-3.0 or commercial license
- `Pillow` - HPND

Check dependency licenses before redistributing a modified bundle. This repository does not vendor those libraries and does not include manuscript data or downloaded copyrighted PDFs.

## Scope

This repository contains the workflow, report template, and helper scripts. It does not contain manuscript data or downloaded copyrighted PDFs.

## License

No license has been added yet. Add one before redistributing if appropriate.
