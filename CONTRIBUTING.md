# Contributing to Free Games - LootScraper

Contributions — bug reports, feature requests, and pull requests — are welcome.

## Quality bar

This integration targets the **Platinum tier of the Home Assistant Integration Quality
Scale**. Contributions are expected to conform to it, not just pass CI:

- [Integration Quality Scale rules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/)
- [#14](https://github.com/dale-sharp/free-games-homeassistant/issues/14) — this project's
  completed Platinum audit, rule by rule, with the reasoning behind each ruling

If a change touches entity behavior, config flow, or diagnostics, check whether it affects any
rule #14 already addressed before assuming it's fine.

## Reporting bugs and requesting features

Use the issue templates rather than a blank issue:

- **Bug report** — fill out the [bug report form](https://github.com/dale-sharp/free-games-homeassistant/issues/new?template=bug_report.yml). It asks for System Health details, reproduction steps, and debug logs — these aren't optional extras, they're what makes a bug reproducible.
- **Feature request** — fill out the [feature request form](https://github.com/dale-sharp/free-games-homeassistant/issues/new?template=feature_request.yml).

## Development setup

```bash
git clone https://github.com/dale-sharp/free-games-homeassistant.git
cd free-games-homeassistant
uv sync
```

[`uv`](https://docs.astral.sh/uv/) manages the environment and all dependencies (dev and
runtime) from `pyproject.toml`/`uv.lock` — there's no separate `pip install -r
requirements.txt` step and no devcontainer.

## Before opening a pull request

Run these locally — they're exactly what CI runs, so a clean local run means a clean CI run:

```bash
uv run pytest --cov=custom_components.free_games --cov-report=term-missing
uvx ruff format .
uvx ruff check .
uv run ty check
```

- **Coverage:** ≥95% overall, no module below ~90% (currently 100%). If your change drops a
  module below the floor, add a real test for the new code path — don't just accept the
  regression because it's still above the minimum.
- `ruff format`/`ruff check` and `ty check` are the two separate jobs `.github/workflows/lint.yml`
  runs in CI. Running them locally first catches a formatting-only CI failure before you push.
- `pytest` isn't run in CI — it's the local gate. Paste its actual output (not just
  pass/fail) into your PR's test plan.
- **Every PR bumps the version** — `manifest.json` + `pyproject.toml` + `uv.lock` (via `uv
  lock`) — and adds a `CHANGELOG.md` entry, regardless of scope. The only exception is a
  change that's genuinely docs/config-only with no functional effect — state that explicitly
  in the PR rather than silently skipping the bump.
- Use the [pull request template](https://github.com/dale-sharp/free-games-homeassistant/blob/main/.github/pull_request_template.md)
  — its test plan section expects pasted command output, not a checkbox.

## License

By contributing, you agree that your contributions will be licensed under this project's
[AGPL-3.0 license](LICENSE).
