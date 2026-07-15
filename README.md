# Free Games - LootScraper

[![HACS Action](https://github.com/dale-sharp/free-games-homeassistant/actions/workflows/validate.yml/badge.svg)](https://github.com/dale-sharp/free-games-homeassistant/actions/workflows/validate.yml)

A [Home Assistant](https://www.home-assistant.io/) custom integration that tracks free game offers across all major gaming platforms using the [LootScraper](https://eikowagenknecht.com/lootscraper/) feeds.

Never miss a free game again - get sensor states and attributes showing every currently free game on Steam, Epic, GOG, Amazon Prime, Humble Bundle, itch.io, and more, directly in your Home Assistant dashboard.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dale-sharp&repository=free-games-homeassistant&category=integration)

---

## Features

- **One sensor per platform** showing the count of currently free games
- **Total count sensor** aggregating all platforms
- **Full offer details as attributes** - title, claim URL, image, description, genres, price, validity dates
- **Polls hourly by default** (configurable, 30 min–1 day) using the LootScraper Atom XML feed
- **Config flow setup** - no YAML required
- **Options flow** - choose which platform sensors to enable

---

## Supported Platforms

| Platform Key | Sensor Name |
|---|---|
| `steam_game` | Steam Games |
| `epic_game` | Epic Games |
| `gog_game` | GOG Games |
| `humble_game` | Humble Games |
| `itch_game` | Itch.io Games |
| `amazon_game` | Amazon Games |
| `amazon_loot` | Amazon In-Game Loot |
| `steam_loot` | Steam In-Game Loot |
| `epic_android` | Epic (Android) |
| `epic_ios` | Epic (iOS) |
| `apple_game` | Apple App Store |
| `google_game` | Google Play |
| `ubisoft_game` | Ubisoft Games |
| `fab_asset` | Fab Assets |
| `steam_points` | Steam Points Shop |

---

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance.
2. Click the three-dot menu in the top-right corner and select **Custom repositories**.
3. Add `https://github.com/dale-sharp/free-games-homeassistant` as an **Integration**.
4. Search for **Free Games** in HACS and click **Download**.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/free_games/` directory into your `<config>/custom_components/` directory.
2. Restart Home Assistant.

---

## Setup

1. Go to **Settings > Devices & Services > Add Integration**.
2. Search for **Free Games**.
3. Click **Submit** - no credentials required.
4. The integration will create sensors immediately.

---

## Configuration

After setup, click **Configure** on the integration card to open the options flow. Three
options are available (also present on the initial setup form):

| Option | Description | Default |
|---|---|---|
| **Stores to track** | Enable or disable per-platform sensors. Toggle any platform on or off. | All platforms enabled |
| **Feed Base URL** | URL of the LootScraper feed server. Change this only if you run your own self-hosted instance (see [Self-Hosting LootScraper](#self-hosting-lootscraper) below). Checked for reachability before saving. | `https://feed.eikowagenknecht.com` |
| **Scan Interval** | How often to poll for new offers, in minutes. | `60` (30-1440 allowed) |

---

## How Data Updates

Each poll, the integration fetches offers using one of two strategies depending on how many
platforms are selected:

- **2 or more platforms selected:** a single request is made to the consolidated feed
  (`lootscraper.xml`), and entries are split locally by their `<category>`-derived platform
  tag. If that request fails, the integration falls back to fetching each selected platform's
  own feed individually.
- **1 platform selected:** the platform's own feed (`lootscraper_<platform>.xml`) is fetched
  directly - there's no consolidated-feed benefit for a single platform.

This means logs may show one request or several per poll, depending on platform count and feed
health - both are expected, not a bug.

---

## Sensors

### `sensor.active_free_games`

Total count of free game offers across all platforms.

| Attribute | Description |
|---|---|
| `feed_title` | Title of the feed source |
| `feed_updated` | When the feed was last updated |
| `total_offer_count` | Total number of offers across all selected platforms |

### Per-platform sensors (e.g. `sensor.steam_games_active_free_games`)

Count of free game offers for that specific platform.

| Attribute | Description |
|---|---|
| `offers` | List of up to 20 current offers (see offer object below) |

### Offer object

Each item in the `offers` list contains:

| Field | Description |
|---|---|
| `id` | Unique offer ID |
| `title` | Full title (e.g. `Steam (Game, PC) - Tell Me Why`) |
| `game_name` | Just the game name portion |
| `store` | Store name (e.g. `Steam`, `Epic Games`, `Amazon Prime`) |
| `platform` | Device platform (`PC`, `Android`, or `iOS`) |
| `type` | Offer type (`Game` or `Loot`) |
| `claim_url` | Direct link to claim the offer |
| `published` | When this offer was first seen |
| `image_url` | Cover art URL |
| `description` | Short game description |
| `genres` | List of genre tags |
| `recommended_price` | Normal retail price |
| `offer_from` | Offer start date/time |
| `offer_to` | Offer end date/time |

Offer history is not persisted to Home Assistant's recorder database (the `offers`
attribute is excluded to stay under HA's per-state attribute size limit) — the live
attribute is always current via `state_attr()` or the dashboard card above.

---

## Known Limitations

- **Data freshness** is bounded by both this integration's poll interval (configurable,
  30-1440 minutes) *and* LootScraper's own upstream re-scrape cadence per source - lowering
  the scan interval below a source's own cadence cannot surface data any sooner:

  | Source | Cadence |
  |---|---|
  | Steam (games + loot) | every 30 min (fastest) |
  | Amazon, GOG | every hour |
  | Humble, Itch, Ubisoft | every 3 hours |
  | Epic, Fab | ~2x/day at fixed times |
  | Mobile aggregators (App Store, Google Play) | 1x/day |

- **Self-hosted `base_url` instances** must expose the same path structure as the public feed:
  `lootscraper.xml` (consolidated) and `lootscraper_<platform>.xml` (per-platform, e.g.
  `lootscraper_steam_game.xml`) at the same base URL.
- **Only one config entry is supported.** Attempting to add a second instance aborts with
  "Free Games is already configured."

---

## Dashboard

The per-platform sensors expose up to 20 offers as a list in their `offers` attribute. The easiest way to display this in a dashboard card is the [list-card](https://github.com/iantrich/list-card) custom card, available through HACS.

Example card configuration to show all current Steam free games:

```yaml
type: custom:list-card
entity: sensor.steam_games_active_free_games
title: Free Steam Games
feed_attribute: offers
columns:
  - title: Game
    field: game_name
  - title: Until
    field: offer_to
  - title: Claim
    field: claim_url
```

---

## Example Automation

Send a notification when a new free Steam game appears:

```yaml
automation:
  - alias: "Notify on new free Steam game"
    trigger:
      - platform: state
        entity_id: event.free_games_steam_games_new_offer
    action:
      - service: notify.mobile_app_my_phone
        data:
          title: "New free Steam game!"
          message: >
            {{ trigger.to_state.attributes.game_name }}
            is free until {{ trigger.to_state.attributes.offer_to }}.
            Claim: {{ trigger.to_state.attributes.claim_url }}
```

The `event.free_games_steam_games_new_offer` entity (and one per other selected platform)
fires exactly once per newly-seen offer — unlike templating off `offers[0]`, this can't
mis-fire when multiple offers arrive in the same poll, and it can't be triggered by the feed
simply reordering existing offers.

---

## Data Source

All data comes from the [LootScraper](https://github.com/eikowagenknecht/lootscraper) project by [Eiko Wagenknecht](https://eikowagenknecht.com/), published at `https://feed.eikowagenknecht.com/`.

---

## Self-Hosting LootScraper

By default, this integration polls the public LootScraper feed at
`https://feed.eikowagenknecht.com/`. If you run your own
[LootScraper](https://github.com/eikowagenknecht/lootscraper) instance, set **Feed Base URL**
in [Configuration](#configuration) to your instance's base URL (e.g.
`https://lootscraper.example.com`) — a trailing slash is fine, it's stripped automatically.

Your self-hosted instance must expose the same feed path structure as the public feed; see
[Known Limitations](#known-limitations) for details.

---

## Removal

**Via the UI:** go to **Settings > Devices & Services > Free Games**, click the three-dot menu
on the integration card, and select **Delete**.

**Manual installs:** UI removal only deletes the config entry, not the integration files copied
in during a manual install. Also delete the `custom_components/free_games/` directory from your
Home Assistant config directory.

---

## Troubleshooting

- **Sensor shows 0**: The feed may be temporarily unavailable. Check **Settings > System > Logs** for errors from `free_games`.
- **Missing platforms**: Open the integration options and make sure the desired platforms are enabled.
- **Stale data**: The integration polls hourly by default. You can lower the interval in the integration's options, or force an immediate refresh by reloading the integration from **Settings > Devices & Services**.

---

## License

[AGPL-3.0](LICENSE)
