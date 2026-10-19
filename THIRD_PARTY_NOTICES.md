# Third-party notices

`parameter-evidence-support` bundles two MIT-licensed components and uses several other installed skills through local adapters.

## Bundled source

### nature-downloader

- Path: `literature/vendor/nature-downloader/`
- License: MIT
- Copyright: Copyright (c) 2026 baihe26
- License text: `literature/vendor/nature-downloader/LICENSE`

### organize-research-literature

- Path: `literature/vendor/organize-research-literature/`
- License: MIT
- Copyright: Copyright (c) 2026 mao-yifan
- License text: `literature/vendor/organize-research-literature/LICENSE`

## Local-only adapters

The following skills are detected in the user's Codex skills directory and invoked in place. Their source is not copied into this repository. The adapter files describe the supported use and the fallback.

| Skill | Recorded license/origin | Adapter |
|---|---|---|
| `nature-academic-search` | Apache-2.0 upstream (`Yuan1z0825/nature-skills`); installed copy may omit a LICENSE file | `literature/adapters/nature-academic-search.md` |
| `nature-reader` | Apache-2.0 upstream (`Yuan1z0825/nature-skills`); installed copy may omit a LICENSE file | `literature/adapters/nature-reader.md` |
| `nature-citation` | Apache-2.0 upstream (`Yuan1z0825/nature-skills`); installed copy may omit a LICENSE file | `literature/adapters/nature-citation.md` |
| `nature-literature-pipeline` | Apache-2.0 upstream repository; installed `SKILL.md` declares MIT | `literature/adapters/nature-literature-pipeline.md` |
| `literature-mapper` | Custom non-commercial terms in the installed README; not bundled | `literature/adapters/literature-mapper.md` |
| `zotero-taxonomy-curator` | No license file found in the installed copy; not bundled | `literature/adapters/zotero-taxonomy-curator.md` |

Before redistributing an adapter's source or using it commercially, verify the upstream license and obtain permission where required.

## Python dependencies

Dependencies are installed by the user and are not vendored here:

- `python-docx` - MIT
- `PyMuPDF` - AGPL-3.0 or commercial license
- `Pillow` - HPND
- optional `PyYAML`, `pdfplumber`, `pypdf`, `jsonschema`, `openpyxl` - see their package metadata

## No manuscript or PDF content

This repository does not include manuscript data or downloaded copyrighted PDFs. The bundled downloader only uses sources the user is authorized to access.
