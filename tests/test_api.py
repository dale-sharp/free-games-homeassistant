"""Tests for api.py parsing functions — all phase1 except fetch error (phase2)."""

from __future__ import annotations

import sys

import aiohttp
import pytest
from aioresponses import aioresponses as mock_aioresponses
from bs4 import BeautifulSoup

from custom_components.free_games.api import (
    GameOffer,
    _parse_content,
    _parse_entry,
    _parse_title,
    fetch_feed_data,
    parse_feed,
    resolve_platform_key,
)


@pytest.mark.phase1
def test_parse_title_valid() -> None:
    platform, offer_type = _parse_title("Steam (Game) - Tell Me Why")
    assert platform == "Steam"
    assert offer_type == "Game"


@pytest.mark.phase1
def test_parse_title_no_match() -> None:
    platform, offer_type = _parse_title("NoMatchHere")
    assert platform == ""
    assert offer_type == ""


@pytest.mark.phase1
def test_game_name_without_separator_returns_full_title() -> None:
    offer = GameOffer(
        id="1",
        title="No Separator Here",
        store="Steam",
        platform="PC",
        type="Game",
        claim_url="https://example.com",
        published="2026-06-20T00:00:00Z",
    )
    assert offer.game_name == "No Separator Here"


@pytest.mark.phase1
def test_parse_content_all_fields() -> None:
    html = """
    <content>
      <div>
        <img src="https://cdn.example.com/cover.jpg"/>
        <ul>
          <li>Offer valid from: 2026-06-20</li>
          <li>Offer valid to: 2026-06-30</li>
          <li>Description: A great game about things.</li>
          <li>Genres: Action, Adventure</li>
          <li>Recommended price (Steam): 9.99 EUR</li>
        </ul>
      </div>
    </content>
    """
    result = _parse_content(html)
    assert result["image_url"] == "https://cdn.example.com/cover.jpg"
    assert result["offer_from"] == "2026-06-20"
    assert result["offer_to"] == "2026-06-30"
    assert result["description"] == "A great game about things."
    assert result["genres"] == ["Action", "Adventure"]
    assert result["recommended_price"] == "9.99 EUR"


@pytest.mark.phase1
def test_parse_content_empty() -> None:
    result = _parse_content("")
    assert result == {
        "image_url": "",
        "offer_from": "",
        "offer_to": "",
        "description": "",
        "genres": [],
        "recommended_price": "",
    }


@pytest.mark.phase2
def test_parse_entry_genres_from_category_tags_when_content_has_none() -> None:
    soup = BeautifulSoup(
        "<feed xmlns='http://www.w3.org/2005/Atom'>"
        "<entry>"
        "<id>https://example.com/1</id>"
        "<title>Steam (Game) - Some Game</title>"
        '<link href="https://example.com/1"/>'
        "<published>2026-06-20T00:00:00Z</published>"
        '<content type="xhtml"><div/></content>'
        '<category term="Action" label="Action"/>'
        '<category term="Indie" label="Indie"/>'
        "</entry>"
        "</feed>",
        "xml",
    )
    entry = soup.find("entry")
    offer = _parse_entry(entry)
    assert offer is not None
    assert offer.genres == ["Action", "Indie"]


@pytest.mark.phase1
def test_parse_entry_valid(sample_game_feed_xml: str) -> None:
    soup = BeautifulSoup(sample_game_feed_xml, "xml")
    entry = soup.find("entry")
    offer = _parse_entry(entry)
    assert offer is not None
    assert offer.title == "Steam (Game, PC) - Test Game"
    assert offer.store == "Steam"
    assert offer.platform == "PC"
    assert offer.type == "Game"
    assert offer.game_name == "Test Game"
    assert offer.claim_url == "https://store.steampowered.com/app/1234/"


@pytest.mark.phase2
def test_parse_entry_falls_back_to_title_without_category_tags() -> None:
    soup = BeautifulSoup(
        "<feed xmlns='http://www.w3.org/2005/Atom'>"
        "<entry>"
        "<id>https://example.com/1</id>"
        "<title>Steam (Game) - Legacy Title Game</title>"
        '<link href="https://example.com/1"/>'
        "<published>2026-06-20T00:00:00Z</published>"
        '<content type="xhtml"><div/></content>'
        "</entry>"
        "</feed>",
        "xml",
    )
    entry = soup.find("entry")
    offer = _parse_entry(entry)
    assert offer is not None
    assert offer.store == "Steam"
    assert offer.type == "Game"
    assert offer.platform == ""


@pytest.mark.phase2
def test_parse_entry_falls_back_to_full_title_when_title_unparseable() -> None:
    soup = BeautifulSoup(
        "<feed xmlns='http://www.w3.org/2005/Atom'>"
        "<entry>"
        "<id>https://example.com/1</id>"
        "<title>Completely Unstructured Title</title>"
        '<link href="https://example.com/1"/>'
        "<published>2026-06-20T00:00:00Z</published>"
        "</entry>"
        "</feed>",
        "xml",
    )
    entry = soup.find("entry")
    offer = _parse_entry(entry)
    assert offer is not None
    assert offer.store == "Completely Unstructured Title"
    assert offer.type == "Game"


@pytest.mark.phase2
def test_parse_entry_loot_type_from_category_tags(sample_loot_feed_xml: str) -> None:
    soup = BeautifulSoup(sample_loot_feed_xml, "xml")
    entry = soup.find("entry")
    offer = _parse_entry(entry)
    assert offer is not None
    assert offer.store == "Steam"
    assert offer.platform == "PC"
    assert offer.type == "Loot"


@pytest.mark.phase2
def test_parse_entry_genres_not_polluted_by_metadata_categories(
    sample_game_feed_xml: str,
) -> None:
    soup = BeautifulSoup(sample_game_feed_xml, "xml")
    entry = soup.find_all("entry")[0]
    offer = _parse_entry(entry)
    assert offer is not None
    assert offer.genres == ["Action", "Adventure"]
    assert "Steam" not in offer.genres
    assert "PC" not in offer.genres
    assert "Game" not in offer.genres


@pytest.mark.phase1
def test_parse_entry_missing_required_fields() -> None:
    soup = BeautifulSoup(
        "<feed xmlns='http://www.w3.org/2005/Atom'><entry><link href='https://example.com'/></entry></feed>",
        "xml",
    )
    entry = soup.find("entry")
    assert _parse_entry(entry) is None


@pytest.mark.phase1
def test_parse_entry_swallows_unexpected_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """_parse_entry's except is defensive-only -- no real malformed entry reaches it
    (confirmed by fuzzing malformed/nested/weird entries during #17's investigation),
    so it's exercised here via a forced failure instead. This isolates one bad entry
    from crashing the whole feed's parse loop in parse_feed.
    """
    from custom_components.free_games import api

    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated parser failure")

    monkeypatch.setattr(api, "_parse_categories", _boom)

    soup = BeautifulSoup(
        "<feed xmlns='http://www.w3.org/2005/Atom'>"
        "<entry><id>1</id><title>T</title></entry>"
        "</feed>",
        "xml",
    )
    entry = soup.find("entry")
    assert _parse_entry(entry) is None


@pytest.mark.phase1
def test_parse_feed_swallows_beautifulsoup_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """parse_feed's except around BeautifulSoup is defensive-only -- lxml's 'xml'
    parser never actually raises on malformed/nested/entity-expansion input
    (confirmed during #17's investigation), so it's exercised here via a forced
    failure instead. Guards against a broken/incompatible parser backend.
    """
    from custom_components.free_games import api

    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated parser failure")

    monkeypatch.setattr(api, "BeautifulSoup", _boom)

    offers, metadata = parse_feed("<feed xmlns='http://www.w3.org/2005/Atom'/>")
    assert offers == []
    assert metadata == {}


@pytest.mark.phase1
def test_parse_feed_valid_atom(sample_game_feed_xml: str) -> None:
    offers, metadata = parse_feed(sample_game_feed_xml)
    assert len(offers) == 2
    assert metadata["feed_title"] == "LootScraper Free Offers"
    assert metadata["feed_updated"] == "2026-06-27T12:00:00Z"


@pytest.mark.phase1
def test_parse_feed_accepts_bytes_input(sample_game_feed_xml: str) -> None:
    offers_from_str, metadata_from_str = parse_feed(sample_game_feed_xml)
    offers_from_bytes, metadata_from_bytes = parse_feed(
        sample_game_feed_xml.encode("utf-8")
    )
    assert offers_from_bytes == offers_from_str
    assert metadata_from_bytes == metadata_from_str


@pytest.mark.phase1
def test_parse_feed_empty_string() -> None:
    offers, metadata = parse_feed("")
    assert offers == []
    assert metadata == {}


@pytest.mark.phase1
def test_parse_feed_malformed_xml(malformed_xml: str) -> None:
    offers, metadata = parse_feed(malformed_xml)
    assert offers == []
    assert metadata == {}


@pytest.mark.phase2
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="aioresponses incompatible with Windows ProactorEventLoop",
)
async def test_fetch_feed_data_http_error() -> None:
    with mock_aioresponses() as m:
        m.get("https://example.com/feed.xml", status=404)
        async with aiohttp.ClientSession() as session:
            with pytest.raises(ValueError, match="HTTP 404"):
                await fetch_feed_data(session, "https://example.com/feed.xml")


@pytest.mark.phase2
def test_consolidated_fixture_has_seven_entries(
    sample_consolidated_feed_xml: str,
) -> None:
    offers, _ = parse_feed(sample_consolidated_feed_xml)
    assert len(offers) == 7
    assert offers[0]["id"] == "https://feed.eikowagenknecht.com/lootscraper/1"
    assert offers[0]["title"] == "Steam (Game, PC) - Consolidated Steam Game"


@pytest.mark.phase2
def test_parse_entry_sets_platform_key_from_categories(
    sample_game_feed_xml: str,
) -> None:
    soup = BeautifulSoup(sample_game_feed_xml, "xml")
    entry = soup.find("entry")
    offer = _parse_entry(entry)
    assert offer is not None
    assert offer.platform_key == "steam_game"


@pytest.mark.phase2
def test_parse_entry_platform_key_empty_without_category_tags() -> None:
    soup = BeautifulSoup(
        "<feed xmlns='http://www.w3.org/2005/Atom'>"
        "<entry>"
        "<id>https://example.com/1</id>"
        "<title>Steam (Game) - Legacy Title Game</title>"
        '<link href="https://example.com/1"/>'
        "<published>2026-06-20T00:00:00Z</published>"
        '<content type="xhtml"><div/></content>'
        "</entry>"
        "</feed>",
        "xml",
    )
    entry = soup.find("entry")
    offer = _parse_entry(entry)
    assert offer is not None
    assert offer.platform_key == ""


@pytest.mark.phase2
def test_parse_entry_platform_empty_when_categories_lack_platform_tag() -> None:
    soup = BeautifulSoup(
        "<feed xmlns='http://www.w3.org/2005/Atom'>"
        "<entry>"
        "<id>https://example.com/1</id>"
        "<title>GOG (Game) - Some Game</title>"
        '<link href="https://example.com/1"/>'
        "<published>2026-06-20T00:00:00Z</published>"
        '<category term="source:GOG" label="GOG"/>'
        '<category term="type:GAME" label="Game"/>'
        "</entry>"
        "</feed>",
        "xml",
    )
    entry = soup.find("entry")
    offer = _parse_entry(entry)
    assert offer is not None
    assert offer.platform == ""
    assert offer.store == "GOG"


@pytest.mark.phase2
def test_parse_entry_loot_platform_key(sample_loot_feed_xml: str) -> None:
    soup = BeautifulSoup(sample_loot_feed_xml, "xml")
    entry = soup.find("entry")
    offer = _parse_entry(entry)
    assert offer is not None
    assert offer.platform_key == "steam_loot"


@pytest.mark.phase2
@pytest.mark.parametrize(
    ("source", "offer_type", "platform", "expected_key"),
    [
        ("STEAM", "GAME", "PC", "steam_game"),
        ("EPIC", "GAME", "PC", "epic_game"),
        ("EPIC", "GAME", "ANDROID", "epic_android"),
        ("EPIC", "GAME", "IOS", "epic_ios"),
        ("GOG", "GAME", "PC", "gog_game"),
        ("HUMBLE", "GAME", "PC", "humble_game"),
        ("ITCH", "GAME", "PC", "itch_game"),
        ("AMAZON", "GAME", "PC", "amazon_game"),
        ("AMAZON", "LOOT", "PC", "amazon_loot"),
        ("STEAM", "LOOT", "PC", "steam_loot"),
        ("APPLE", "GAME", "IOS", "apple_game"),
        ("GOOGLE", "GAME", "ANDROID", "google_game"),
        ("UBISOFT", "GAME", "PC", "ubisoft_game"),
        ("FAB", "ASSET", "PC", "fab_asset"),
        ("STEAM", "POINTS", "PC", "steam_points"),
    ],
)
def test_resolve_platform_key_known_combinations(
    source: str, offer_type: str, platform: str, expected_key: str
) -> None:
    assert resolve_platform_key(source, offer_type, platform) == expected_key


@pytest.mark.phase2
def test_resolve_platform_key_unmapped_combination_returns_none() -> None:
    assert resolve_platform_key("NINTENDO", "GAME", "PC") is None


@pytest.mark.phase2
def test_parse_feed_consolidated_fixture_resolves_all_platform_keys(
    sample_consolidated_feed_xml: str,
) -> None:
    offers, _ = parse_feed(sample_consolidated_feed_xml)
    keys = [o["platform_key"] for o in offers]
    assert keys.count("steam_game") == 1
    assert keys.count("epic_game") == 1
    assert keys.count("epic_android") == 1
    assert keys.count("epic_ios") == 1
    assert keys.count("gog_game") == 1
    assert keys.count("amazon_loot") == 1
    assert keys.count("") == 1  # the Nintendo entry has no known platform_key
