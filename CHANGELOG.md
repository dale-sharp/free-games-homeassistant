# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
