# Adapter: zotero-taxonomy-curator

## Use for

- Turning Zotero items, collections, annotations, or local PDFs into structured Obsidian notes.
- Mapping original tags to a controlled taxonomy.
- Maintaining a literature index and close-reading notes.

## Detect and invoke

```bash
python scripts/lit_stack.py path zotero-taxonomy-curator
```

Read the installed `SKILL.md`; initialize its local configuration and taxonomy first if the project has not been set up.

## Boundary

Notes are not primary evidence. A Zotero annotation or Obsidian summary may point you to a page, but the report still requires the PDF, page, verbatim text, conditions, and screenshot. Do not copy its source into this repository; no license file was found in the installed copy.

## Fallback

Extract the relevant page with `scripts/locate_passage.py` and keep personal notes outside the evidence report.
