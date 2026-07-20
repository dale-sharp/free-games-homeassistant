# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.1] - 2026-07-21

### Changed

- Upgraded the dev/test dependency chain off the old `homeassistant==2024.11.0b7` beta pin
  to `homeassistant==2025.2.5` / `pytest-homeassistant-custom-component==0.13.215` /
  `aiohttp==3.11.12` — the latest stable pairing available before `homeassistant` started
  unconditionally depending on `pymicro-vad`/`pyspeex-noise`, which have no published Windows
  wheels. Raised `requires-python` to `>=3.13,<3.14` to match the new test harness's floor. No
  runtime/functional change to the integration itself.
- Worked around an upstream Windows incompatibility in
  `pytest-homeassistant-custom-component`'s `mock_zeroconf_resolver` fixture (present in every
  release from 0.13.181 through the latest 0.13.346): it eagerly constructs a real
  `aiodns.DNSResolver`, which requires a `SelectorEventLoop` on Windows, but the harness also
  installs `homeassistant.runner.HassEventLoopPolicy` and neuters
  `asyncio.set_event_loop_policy`, so the usual pytest-asyncio override has no effect. Patched
  `HassEventLoopPolicy._loop_factory` directly in `tests/conftest.py` instead.
- Grouped `homeassistant`, `pytest-homeassistant-custom-component`, `aiohttp`,
  `pytest-asyncio`, `pytest`, and `josepy` in `.github/dependabot.yml` so future Dependabot
  updates propose one resolvable bump instead of several that each fail independently (#58,
  #55) — `pytest-homeassistant-custom-component` pins exact versions of the first four, and
  `homeassistant` transitively requires `josepy>=1.13.0,<2` via `hass-nabucasa`/`acme`, so
  isolated single-package bumps are structurally unsatisfiable.
- Capped `requires-python` to `<3.14` after a Dependabot run failed resolving a
  `python_full_version >= '3.14.2'` split: an open-ended floor forces `uv lock` to also find a
  resolution valid for hypothetical future Python versions, and for 3.14+ that meant jumping to
  `homeassistant==2026.2.3` (which reintroduces the `pymicro-vad` Windows problem and pulls in
  `hass-nabucasa==1.12.0`'s `josepy>=2,<3`, conflicting with our `josepy<2.0.0` pin). Capping
  the floor to the Python version we actually pin (`.python-version` = `3.13`) removes the
  multi-version fork at the root instead of chasing each conflict it produces.
- Added `constraint-dependencies = ["homeassistant<2025.4.0"]` under `[tool.uv]` after a
  Dependabot "uv group" bump (#62) crossed the `pymicro-vad`/`pyspeex-noise` boundary anyway,
  breaking `uv sync` on Windows on `main` — the Dependabot grouping only bundles PRs together,
  it doesn't constrain what the resolver picks. A follow-up single-package security PR (#65,
  targeting a `zeroconf` mDNS cache-poisoning fix, GHSA-qc2x-6f54-m6h9) then swung the other
  way, resolving an older `pytest-homeassistant-custom-component==0.13.195` than our intended
  pin and silently dropping `zeroconf` from the graph entirely rather than patching it — because
  `homeassistant==2025.2.5` pins `zeroconf==0.144.1` exactly, that CVE can't be fixed
  independently while under the Windows ceiling; it's dev/test-only exposure, since `zeroconf`
  isn't a runtime dependency of the shipped integration (`manifest.json` only requires
  `beautifulsoup4`/`lxml`). The explicit ceiling makes future resolutions land back on the
  known-good pin (`pytest-homeassistant-custom-component==0.13.215` /
  `homeassistant==2025.2.5`) deterministically instead of wherever an unconstrained resolver
  happens to swing. Revisit alongside #64.
- Moved local dev/test onto a devcontainer (`.devcontainer/`) and dropped the `homeassistant<2025.4.0`
  constraint and `requires-python` upper-bound history above — both turned out to be about native Windows
  being unable to import `homeassistant.runner`'s unconditional, unguarded `fcntl`/`resource` stdlib usage
  (no Windows equivalent, present in every current release), not about the pinned dependency versions
  themselves. `pyproject.toml` now only pins `requires-python` to the Python line the devcontainer's base
  image actually provides (`>=3.13.2,<3.14`) for resolution stability, with no Windows-specific constraint at
  all. Dev/test now tracks current `homeassistant` (`2026.2.3` as of this change) again. Native Windows
  `uv sync`/`pytest` is no longer a supported path — see `CONTRIBUTING.md`.

---

## [1.0.0] - 2026-07-15

First stable release — semver guarantees begin here. Highlights since 0.1.0: Ubisoft/Fab/Steam
Points platform support, a configurable feed base URL and scan interval, automatic entry
reload on options changes, diagnostics, repair issues, config-flow translations and icon
translations, a reconfigure flow, a Platinum-targeted Home Assistant Quality Scale pass
(including an adversarial re-review that fixed a per-platform availability gap and log spam),
and two new optional entity platforms — a calendar showing offer expiry windows and per-platform
event entities for reliable new-offer notifications. See the entries below for full detail on
every 0.x release. The one breaking change across the 0.x series was in 0.6.0 (the `platform`
attribute's meaning changed from store name to device platform, with the store name moving to
a new `store` field).

### Added

- A **Requirements** section in the README documenting the minimum supported Home Assistant
  version (2024.6.0), and documentation for the calendar and new-offer event entities
  (previously undocumented after #27/#28 landed).

### Changed

- Replaced the placeholder brand icon/logo assets with real "Free Games - LootScraper"
  branding (light and dark variants).

---

## [0.9.10] - 2026-07-15

### Added

- A new `event.free_games_<platform>_new_offer` entity is now available per selected
  platform (e.g. `event.free_games_steam_games_new_offer`), firing a `new_offer` event
  exactly once per newly-seen offer, with the full offer as event attributes. This replaces
  the fragile `offers[0]`-templated notification pattern in the README's automation example,
  which could miss offers arriving in the same poll or misfire when the feed reordered
  existing offers without any new one appearing.

---

## [0.9.9] - 2026-07-15

### Added

- A `calendar.free_games` entity now surfaces offer expiry windows (`offer_from`/`offer_to`)
  across all selected platforms, enabling the calendar dashboard card and calendar
  event-start/event-end automation triggers. Offers missing an end date are omitted from the
  calendar (they still appear normally in the existing `offers` attribute); offers missing a
  start date fall back to the date this integration first saw them.

---

## [0.9.8] - 2026-07-15

### Fixed

- A per-platform sensor now correctly goes unavailable when only that platform's own feed
  fetch fails during per-platform fallback, instead of silently reporting a count of 0
  (indistinguishable from "no free games today"). Found by #23's adversarial re-review of
  the `entity-unavailable` quality-scale rule.
- The integration no longer logs a full traceback and a fallback warning on every failed
  poll on top of Home Assistant's own once-per-outage/once-on-recovery coordinator logging —
  both are now debug-level, eliminating redundant log spam during a sustained outage. Found
  by #23's adversarial re-review of the `log-when-unavailable` quality-scale rule.

---

## [0.9.7] - 2026-07-15

### Added

- A dedicated "Reconfigure" flow is now available (alongside the existing "Configure"
  options flow), satisfying Home Assistant's `reconfiguration-flow` quality-scale rule.
  Both flows edit the same settings (stores to track, feed base URL, scan interval) since
  this integration stores all of its configuration in options rather than splitting
  required connection data from optional settings.

---

## [0.9.6] - 2026-07-14

### Added

- A repair issue is now created when the Free Games feed fails to fetch for 3 consecutive
  polls, appearing in Home Assistant's Settings > System > Repairs. The message differs
  depending on whether `base_url` is the public default (suggesting a possible temporary
  outage or local network issue) or a custom self-hosted value (suggesting the self-hosted
  instance or the configured URL should be checked). The issue clears automatically on the
  next successful fetch.

---

## [0.9.5] - 2026-07-14

### Added

- A diagnostics platform (`diagnostics.py`) is now implemented, letting users download
  structured debugging state from Home Assistant's UI: configured options, coordinator
  health (`last_update_success`, `last_exception`), and per-platform offer counts (not full
  offer payloads). A custom (self-hosted) `base_url` is redacted, since it could reveal a
  private network address or hostname; the public default URL is shown in full.

---

## [0.9.4] - 2026-07-14

### Added

- Test coverage raised from 93% to 95%+ overall: added tests for the options flow's
  reachability-failure path, sensor behavior before the coordinator's first refresh,
  several genuine `api.py` parsing edge cases (titles without a separator, categories
  without a platform tag, unparseable titles, category-tag-derived genres, bytes input to
  `parse_feed`), and both of `api.py`'s defensive exception-handling branches (verified
  unreachable via real input; tested via forced failures instead). Replaced the one test
  that had been silently skipped on Windows (this project's only dev platform) since it
  relied on `aioresponses`, which is incompatible with Windows' `ProactorEventLoop` — direct
  `session.get()` mocking now covers the same paths cross-platform, and the now-unused
  `aioresponses` dev dependency is removed.

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
