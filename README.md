# Parameter Evidence Support

A Codex skill for turning a manuscript's parameter list into an auditable, page-cited evidence report.

It was built for computational-biology and systems-biology manuscripts, especially cases where a main text or SI mixes experimental measurements, derived rates, normalized Hill thresholds, fitted parameters, scan ranges, and code-set numerical constants.

## What it does

- Extracts every numeric parameter from a manuscript, SI, parameter table, or code.
- Classifies each value as **A measured**, **B derived**, **C model/code-set**, or **D not found**.
- Searches primary literature and verifies DOI/PMID metadata.
- Downloads authorized PDFs through the user's logged-in institutional browser session.
- Locates the exact sentence, figure, or table; records PDF page and journal page.
- Captures an original-text screenshot when a PDF is available.
- Checks experimental conditions such as species, cell type, assay, probe, construct, salt, and time window.
- Distinguishes a measurement from a normalized threshold or a code-derived value.
- Generates a fixed-format Chinese DOCX/PDF with a correction list and explicit `【找不到】` markers.
- Produces manuscript-ready English wording for supported values.

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

## Use

Example request:

```text
Use parameter-evidence-support to audit every parameter in my manuscript and SI.
Trace each value to a primary source, download authorized PDFs, capture exact
passages and screenshots, correct wrong citations or values, and build the Word
report in the established format. Mark anything unavailable as 【找不到】.
```

## Scripts

```bash
# Build a DOCX from a JSON specification
python scripts/build_evidence_docx.py spec.json output.docx

# Find candidate papers without MCP or an API key
python scripts/find_papers.py "GATA2 half-life P815" --limit 12 --out candidates.csv

# Verify DOI/PMID metadata
python scripts/verify_refs.py 10.1111/j.1365-2443.2005.00864.x 15966900
```

Python dependency:

```bash
pip install python-docx
```

## Repository layout

```text
SKILL.md
agents/openai.yaml
references/entry-spec.md
references/verification-playbook.md
references/literature-stack.md
scripts/build_evidence_docx.py
scripts/find_papers.py
scripts/verify_refs.py
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

## Scope

This repository contains the workflow, report template, and helper scripts. It does not contain manuscript data or downloaded copyrighted PDFs.

## License

No license has been added yet. Add one before redistributing if appropriate.