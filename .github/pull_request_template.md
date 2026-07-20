## Summary

<!-- What does this PR do and why? -->

## Test plan

<!--
Paste the actual output of the commands you ran below — not just a pass/fail summary.
If a command doesn't apply (e.g. a docs-only change), say so explicitly rather than
deleting the section.
-->

```
$ uv run pytest --cov=custom_components.free_games --cov-report=term-missing
<paste output>
```

```
$ uvx ruff format . --check
<paste output>

$ uvx ruff check .
<paste output>

$ uv run ty check
<paste output>
```

- [ ] Version bumped in `manifest.json` + `pyproject.toml` + `uv.lock`, and a `CHANGELOG.md` entry added (or explicitly note why this PR doesn't need one, e.g. docs-only)
