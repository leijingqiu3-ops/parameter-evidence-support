# Adapter: nature-literature-pipeline

## Use for

- Recurring literature monitoring for a research area.
- Multi-source discovery, six-dimension scoring, daily/weekly digests, and archival.
- Keeping a literature watchlist separate from a one-off parameter audit.

## Detect and invoke

```bash
python scripts/lit_stack.py path nature-literature-pipeline
```

Read the installed `SKILL.md` and the relevant references for scoring, delivery format, cron setup, or archival. Configure keywords, delivery target, and archive path explicitly.

## Boundary

A monitoring digest is not an evidence report. Do not copy scores, one-line summaries, or metadata into the parameter report without reopening the source PDF and verifying the passage. Keep the daily pipeline's writes confined to its configured raw/archive directory.

## Fallback

Run `scripts/find_papers.py` manually on the desired schedule and triage the candidates yourself.
