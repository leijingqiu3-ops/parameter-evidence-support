# Integrated literature stack

This directory makes `parameter-evidence-support` a literature-capable skill rather than a DOCX builder that depends on tools the user may not have.

The integration has three layers:

| Layer | Location | What it means |
|---|---|---|
| Core fallback | `scripts/` | Always available; candidate search, DOI/PMID checks, open-access download, passage location, screenshots, and DOCX build |
| Bundled tools | `literature/vendor/` | Redistributable components copied with their licenses and executable code |
| Local adapters | `literature/adapters/` | Installed Codex skills that are detected and used in place, without redistributing their source |

Run the health check before a large job:

```bash
python scripts/lit_stack.py doctor
```

Bundled components:

- `nature-downloader` - MIT, Copyright (c) 2026 baihe26. Authorized institutional/browser-session PDF acquisition.
- `organize-research-literature` - MIT, Copyright (c) 2026 mao-yifan. Recursive local PDF inventory and Excel organization.

Local adapters are listed in `integrations.json`. They are optional accelerators. The core path must still work when none of them is installed.

See `router.md` for the routing rules and `adapters/local-skill-protocol.md` for the invocation contract.
