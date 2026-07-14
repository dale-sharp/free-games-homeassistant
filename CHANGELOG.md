# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.9.3] - 2026-07-14

### Fixed

- `strings.json`/`translations/en.json` now translate the `base_url` and
  `scan_interval_minutes` config/options flow fields (previously only `platforms` was
  translated, so these two fields showed their raw key in the UI), and add an
  `error.cannot_connect` message for the feed-reachability check.
- Sensor icons are now provided via `icons.json` instead of hardcoded `_attr_icon` values in
  `sensor.py`, per Home Assistant's icon-translations convention. Icon values are unchanged.

---

## [0.9.2] - 2026-07-14

### Added

- `ty` strict type checking is now enforced in CI (`.github/workflows/lint.yml`), alongside
  the existing `ruff` job. `ty` is configured in `pyproject.toml` (`python-version = "3.12"`,
  `blanket-ignore-comment` promoted to error) and added as a pinned dev dependency, closing
  the gap where type-checking diagnostics were previously visible only via ad-hoc IDE
  integration and not actually enforced on pushes or pull requests.

### Fixed

- The Windows-only `socketpair` test shim in `tests/conftest.py` is now fully typed to
  match `socket.socketpair`'s real signature, resolving the one finding `ty` surfaced
  against the existing codebase. No behavior change — the shim still forwards to the real
  `socketpair`.

---

## [0.9.1] - 2026-07-14

### Fixed

- The `offers` attribute is now excluded from Home Assistant's recorder history
  (`_unrecorded_attributes`). Recorder enforces a 16,384-byte cap on serialized state
  attributes; `sensor.active_free_games` and the `amazon_game` per-platform sensor already
  exceed it at ordinary offer volumes, which silently dropped all attribute history for
  those sensors and logged recorder warnings on every recorded state change. The live
  `offers` attribute (dashboard cards, `state_attr()` templates, automations) is
  unaffected — only recorder-side history persistence changes.

---

## [0.9.0] - 2026-07-14

### Added

- Three new tracked platforms upstream LootScraper already scrapes but this integration never
  registered: `ubisoft_game` (Ubisoft Games), `fab_asset` (Fab Assets), and `steam_points`
  (Steam Points Shop). Their offers were previously silently dropped, including via the
  consolidated feed.

---

## [0.8.0] - 2026-07-13

### Changed

- Default polling interval raised from 15 minutes to 1 hour — proportional to how often
  upstream LootScraper data actually changes (Steam, the fastest-moving source, re-scrapes
  every 30 minutes). The interval is now configurable (config flow + options flow, 30–1440
  minutes).
- Config entry now reloads automatically when options change (platforms, base URL, or scan
  interval), instead of requiring a manual Home Assistant restart.

---

## [0.7.0] - 2026-07-13

### Added

- Configurable feed base URL (config flow + options flow) for self-hosted LootScraper
  instances, defaulting to `https://feed.eikowagenknecht.com` so existing installs are
  unaffected. The URL is validated for reachability before being saved.

---

## [0.6.0] - 2026-07-13

### Changed

- Reduced network calls: when 2 or more platforms are selected, the integration now fetches
  the LootScraper consolidated feed once instead of one feed per platform, using the
  `<category>` metadata added upstream to split entries back into per-platform groups
  locally. Falls back to per-platform fetches if the consolidated feed fetch fails.
- **Breaking:** the `platform` field on each offer now means the device platform (`PC`,
  `Android`, `iOS`) instead of the store name. The store name (e.g. `Steam`, `Epic Games`)
  is now under a new `store` field.

### Fixed

- Offer parsing now reads `source`/`platform`/`type` from the feed's `<category>` metadata
  tags instead of guessing from the entry title, which was fragile and (for `platform`) was
  actually returning the store name rather than a device platform.

---

## [0.5.0] - 2026-06-27

### Added

- Test suite with 21 tests covering the API parser, coordinator, config/options flow, and
  sensors. Uses `pytest-homeassistant-custom-component` with phase markers so Phase 1 and
  Phase 2 gates are independently verifiable.
- `pyproject.toml` as the single source of dev dependencies; `uv` manages the environment.

### Changed

- Coordinator now fetches only the platform feeds the user selected, instead of fetching
  all 12 feeds plus the merged feed on every poll cycle.
- When every selected platform feed fails to fetch, the coordinator now raises `UpdateFailed`
  so sensors correctly go unavailable rather than reporting 0 with stale data.
- Sensor attribute renamed: `unique_offer_count` → `total_offer_count` (the value was never
  deduplicated — the old name was misleading).

### Fixed

- `manifest.json` logger key corrected to `custom_components.free_games` (was `free_games`).
- `PLATFORMS` list updated to use `Platform.SENSOR` enum instead of the raw string `"sensor"`.
- Both sensors now declare `SensorStateClass.MEASUREMENT` and `native_unit_of_measurement = None`,
  making them eligible for long-term statistics in Home Assistant.
- `OptionsFlow.__init__` removed; the flow no longer stores a stale config-entry reference.
  `async_step_init` now retrieves the entry via `self.hass.config_entries.async_get_entry(self.handler)`.

### Removed

- Unused constants `CONF_SHOW_EXPIRED`, `OPTION_FEED_URL`, and `FEED_URL_MERGED` from `const.py`.

---

## [0.4.0] - 2026-06-24

### Changed

- Config flow now includes a multi-select list of stores during initial setup,
  so users pick which platforms to track before the integration is created.
- Options flow updated to use the same multi-select (replaces individual toggles).
- `config_flow.py` refactored to share a single `_platforms_schema()` helper
  between both flows.

---

## [0.3.0] - 2026-06-24

### Fixed

- Per-platform sensors now correctly show offer counts and game details. The coordinator
  now fetches each platform feed individually and tags offers with a `platform_key`, so
  matching is exact rather than relying on string mangling of the platform name.
- Fixed typo in `itch_game` feed URL (`loot_scraper_itch_game.xml` -> `lootscraper_itch_game.xml`).
- `Active Free Games` sensor now includes the `offers` list in its attributes.

---

## [0.2.0] - 2026-06-24

### Fixed

- Removed duplicate `hacs.json` from `custom_components/free_games/` - HACS only reads
  from the repository root.

### Changed

- `hacs.json` now declares `zip_release: true` and `filename: free_games.zip` so HACS
  installs from the release asset rather than the source tree.
- Lint workflow replaced `pip install homeassistant` with `astral-sh/ruff-action`,
  reducing CI run time from ~90s to ~5s.

---

## [0.1.0] - 2026-06-23

### Added

- Initial release of the Free Games - LootScraper integration.
- Polls the [LootScraper](https://feed.eikowagenknecht.com/) Atom XML feed every 15 minutes.
- `sensor.active_free_games` - total count of free game offers across all platforms.
- Per-platform sensors for 12 platforms: Steam Games, Epic Games, GOG Games, Humble Games,
  Itch.io Games, Amazon Games, Amazon In-Game Loot, Steam In-Game Loot, Epic (Android),
  Epic (iOS), Apple App Store, Google Play.
- Full offer details as sensor attributes: title, claim URL, image, description, genres,
  recommended price, and validity dates.
- Config flow setup - no YAML required.
- Options flow to enable or disable per-platform sensors individually.
- GitHub Actions workflows: HACS validation, hassfest, Ruff lint, and release packaging.
