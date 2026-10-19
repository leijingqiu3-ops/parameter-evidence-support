# Local adapter protocol

Use an adapter only when the corresponding skill is already installed under the user's Codex skills directory. The adapter is a routing contract, not a copy of the other skill.

## Resolve the path

```bash
python scripts/lit_stack.py path <skill-name>
```

The resolver checks `CODEX_HOME/skills`, `~/.codex/skills`, and `~/.claude/skills`.

## Invoke it correctly

1. Read the installed skill's own `SKILL.md`.
2. Read only the fragments that its router or manifest tells you to load.
3. Keep the task inside that skill's stated scope.
4. Return the result to `parameter-evidence-support`; the evidence standard here still controls what enters the report.

Do not edit the installed skill, copy its source into this repository, or claim it was used when it is absent.

## If it is absent

Use the fallback named in `literature/integrations.json` or `literature/router.md`. Record that the adapter was unavailable only if that affects the user's requested deliverable.
