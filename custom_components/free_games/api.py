"""API client for fetching and parsing LootScraper Atom XML feeds."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from .const import PLATFORM_KEY_CATEGORIES

_LOGGER = logging.getLogger(__package__)

# Atom feed namespace
_ATOM_NS = "http://www.w3.org/2005/Atom"


@dataclass
class GameOffer:
    """Represents a single game or loot offer from the feed."""

    id: str
    title: str
    store: str
    platform: str
    type: str
    # claim_url and image_url are external URLs from the LootScraper feed,
    # passed through without validation by design — this is standard RSS reader behaviour.
    claim_url: str
    published: str
    updated: str = ""
    image_url: str = ""
    description: str = ""
    genres: list[str] = field(default_factory=list)
    recommended_price: str = ""
    offer_from: str = ""
    offer_to: str = ""
    platform_key: str = ""

    @property
    def game_name(self) -> str:
        """Return just the game name portion of the title.

        Title format: 'Store (Type, Platform) - Game Name'
        """
        if " - " in self.title:
            return self.title.split(" - ", 1)[1].strip()
        return self.title

    def as_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary for HA state/attributes."""
        return {
            "id": self.id,
            "title": self.title,
            "game_name": self.game_name,
            "store": self.store,
            "platform": self.platform,
            "type": self.type,
            "claim_url": self.claim_url,
            "published": self.published,
            "updated": self.updated,
            "image_url": self.image_url,
            "description": self.description[:500] if self.description else "",
            "genres": self.genres,
            "recommended_price": self.recommended_price,
            "offer_from": self.offer_from,
            "offer_to": self.offer_to,
            "platform_key": self.platform_key,
        }


def _build_platform_key_lookup() -> dict[tuple[str, str, str | None], str]:
    return {
        (source, offer_type, platform): key
        for key, (source, offer_type, platform) in PLATFORM_KEY_CATEGORIES.items()
    }


_PLATFORM_KEY_LOOKUP: dict[tuple[str, str, str | None], str] = (
    _build_platform_key_lookup()
)


def resolve_platform_key(source: str, offer_type: str, platform: str) -> str | None:
    """Resolve category term values to a PLATFORM_FEEDS key.

    Tries an exact (source, type, platform) match first — needed to
    disambiguate Epic PC/Android/iOS — then falls back to a (source, type)
    wildcard match. Returns None if no known platform_key matches either.
    """
    exact = _PLATFORM_KEY_LOOKUP.get((source, offer_type, platform))
    if exact is not None:
        return exact
    return _PLATFORM_KEY_LOOKUP.get((source, offer_type, None))


def _parse_title(title: str) -> tuple[str, str]:
    """Split 'Platform (Type) - Name' into (platform, offer_type).

    Returns ("", "") if the title does not match the expected format.
    """
    match = re.match(r"^(.+?)\s*\((.+?)\)\s*-\s*.+$", title)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return "", ""


def _parse_content(content_html: str) -> dict[str, Any]:
    """Parse the xhtml content block of an Atom entry.

    Extracts: image_url, offer_from, offer_to, description, genres,
    recommended_price.
    """
    result: dict[str, Any] = {
        "image_url": "",
        "offer_from": "",
        "offer_to": "",
        "description": "",
        "genres": [],
        "recommended_price": "",
    }

    if not content_html:
        return result

    soup = BeautifulSoup(content_html, "html.parser")

    # Image
    img = soup.find("img")
    if img and img.get("src"):
        result["image_url"] = img["src"]

    # Pull all <li> text nodes for structured fields
    for li in soup.find_all("li"):
        text = li.get_text(separator=" ", strip=True)

        if text.startswith("Offer valid from:"):
            result["offer_from"] = text.replace("Offer valid from:", "").strip()
        elif text.startswith("Offer valid to:"):
            result["offer_to"] = text.replace("Offer valid to:", "").strip()
        elif text.startswith("Description:"):
            result["description"] = text.replace("Description:", "").strip()
        elif text.startswith("Genres:"):
            genres_raw = text.replace("Genres:", "").strip()
            result["genres"] = [g.strip() for g in genres_raw.split(",") if g.strip()]
        elif "Recommended price" in text:
            # Format: "Recommended price (Steam): 9.99 EUR"
            price_match = re.search(r":\s*(.+)$", text)
            if price_match:
                result["recommended_price"] = price_match.group(1).strip()

    return result


def _parse_categories(entry: Any) -> dict[str, tuple[str, str]]:
    """Extract source/platform/type metadata from an entry's <category> tags.

    Returns a dict keyed by "source", "platform", "type" — only keys actually
    present on the entry are included. Each value is (term_value, label),
    e.g. {"source": ("EPIC", "Epic Games"), "platform": ("ANDROID", "Android")}.
    """
    result: dict[str, tuple[str, str]] = {}
    for cat in entry.find_all("category"):
        term = cat.get("term", "")
        label = cat.get("label", "")
        prefix, sep, value = term.partition(":")
        if sep and prefix in ("source", "platform", "type"):
            result[prefix] = (value, label)
    return result


def _parse_entry(entry: Any) -> GameOffer | None:
    """Parse a single BeautifulSoup <entry> tag into a GameOffer.

    Returns None if the entry is missing required fields or unparseable.
    """
    try:
        # Required fields
        id_tag = entry.find("id")
        title_tag = entry.find("title")
        published_tag = entry.find("published")
        link_tag = entry.find("link")
        content_tag = entry.find("content")

        if not id_tag or not title_tag:
            return None

        entry_id = id_tag.get_text(strip=True)
        title = title_tag.get_text(strip=True)
        published = published_tag.get_text(strip=True) if published_tag else ""
        updated_tag = entry.find("updated")
        updated = updated_tag.get_text(strip=True) if updated_tag else ""

        # Claim URL from <link href="..."/>
        claim_url = ""
        if link_tag:
            claim_url = link_tag.get("href", "") or ""

        # source/platform/type come from <category> tags when present (the
        # authoritative, machine-readable source); title parsing is a
        # fallback only for feeds without them.
        categories = _parse_categories(entry)
        if "source" in categories and "type" in categories:
            source_term, store = categories["source"]
            type_term, offer_type = categories["type"]
            if "platform" in categories:
                platform_term, platform = categories["platform"]
            else:
                platform_term, platform = "", ""
            platform_key = (
                resolve_platform_key(source_term, type_term, platform_term) or ""
            )
        else:
            store, offer_type = _parse_title(title)
            if not store:
                store = title
                offer_type = "Game"
            platform = ""
            platform_key = ""

        # Parse xhtml content block
        content_data: dict[str, Any] = {}
        if content_tag:
            content_data = _parse_content(str(content_tag))

        # Genres can also come from <category> tags (Steam genre categories),
        # but never from the source/platform/type metadata categories above.
        genres: list[str] = content_data.get("genres", [])
        if not genres:
            for cat in entry.find_all("category"):
                term = cat.get("term", "")
                label = cat.get("label", "")
                if label and not term.startswith(("source:", "platform:", "type:")):
                    genres.append(label)

        return GameOffer(
            id=entry_id,
            title=title,
            store=store,
            platform=platform,
            type=offer_type,
            platform_key=platform_key,
            claim_url=claim_url,
            published=published,
            updated=updated,
            image_url=content_data.get("image_url", ""),
            description=content_data.get("description", ""),
            genres=genres,
            recommended_price=content_data.get("recommended_price", ""),
            offer_from=content_data.get("offer_from", ""),
            offer_to=content_data.get("offer_to", ""),
        )

    except Exception:  # noqa: BLE001
        _LOGGER.debug("Failed to parse feed entry: %s", entry, exc_info=True)
        return None


def parse_feed(xml_data: str | bytes) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse an Atom XML feed string into structured game offer data.

    Args:
        xml_data: Raw Atom XML content as str or bytes.

    Returns:
        Tuple of (list of offer dicts, feed metadata dict).
        Each offer dict matches GameOffer.as_dict() output.
    """
    if isinstance(xml_data, bytes):
        xml_data = xml_data.decode("utf-8", errors="replace")

    if not xml_data or not xml_data.strip():
        return [], {}

    try:
        soup = BeautifulSoup(xml_data, "xml")
    except Exception:  # noqa: BLE001
        _LOGGER.warning("Failed to parse XML feed", exc_info=True)
        return [], {}

    if soup.find("feed") is None:
        _LOGGER.warning("XML parsed but no <feed> root found — not a valid Atom feed")
        return [], {}

    # Feed-level metadata
    feed_title = ""
    feed_updated = ""
    title_tag = soup.find("title")
    if title_tag:
        feed_title = title_tag.get_text(strip=True)
    updated_tag = soup.find("updated")
    if updated_tag:
        feed_updated = updated_tag.get_text(strip=True)

    metadata: dict[str, Any] = {
        "feed_title": feed_title,
        "feed_updated": feed_updated,
    }

    offers: list[dict[str, Any]] = []
    for entry_tag in soup.find_all("entry"):
        offer = _parse_entry(entry_tag)
        if offer is not None:
            offers.append(offer.as_dict())

    _LOGGER.debug("Parsed %d offers from feed '%s'", len(offers), feed_title)
    return offers, metadata


async def fetch_feed_data(
    session: aiohttp.ClientSession,
    feed_url: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch and parse a single Atom XML feed URL.

    Args:
        session: An active aiohttp.ClientSession.
        feed_url: Full URL to the Atom XML feed.

    Returns:
        Tuple of (list of offer dicts, feed metadata dict).

    Raises:
        aiohttp.ClientError: On network errors.
        ValueError: If the server returns a non-200 response.
    """
    _LOGGER.debug("Fetching feed: %s", feed_url)
    try:
        async with session.get(
            feed_url,
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "HomeAssistant-FreeGames/1.0"},
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"Feed returned HTTP {response.status} for {feed_url!r}"
                )
            raw_xml = await response.text(encoding="utf-8", errors="replace")

    except aiohttp.ClientError as err:
        raise aiohttp.ClientError(
            f"Network error fetching feed {feed_url!r}: {err}"
        ) from err

    if not raw_xml or not raw_xml.strip():
        _LOGGER.warning("Empty response from feed: %s", feed_url)
        return [], {}

    return parse_feed(raw_xml)
