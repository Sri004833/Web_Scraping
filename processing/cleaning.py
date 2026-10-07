"""Data cleaning and normalization functions."""
import re
from typing import Any, Iterable, Optional

# Word to integer rating map
RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}

# Regex to extract float or integer numeric value
PRICE_REGEX = re.compile(r"[-+]?\d+(?:\.\d+)?")


def clean_text(text: Optional[str]) -> str:
    """Remove extra spaces, tabs, newlines, and non-breaking spaces (\xa0).

    Args:
        text: Input string or None.

    Returns:
        Cleaned string with normalized whitespace, or empty string if input is None.
    """
    if text is None:
        return ""
    # Replace non-breaking spaces and collapse whitespace sequences
    normalized = text.replace("\xa0", " ").strip()
    return re.sub(r"\s+", " ", normalized)


def strip_quotes(text: Optional[str]) -> str:
    """Remove standard and curly quotation marks around quote text.

    Args:
        text: Input quote text.

    Returns:
        Quote text with leading and trailing quote characters stripped.
    """
    cleaned = clean_text(text)
    # Strip double and single straight and curly quotation marks
    return cleaned.strip("“\"”'‘’")


def clean_price(price_val: Any) -> Optional[float]:
    """Turn currency price string (e.g. '£51.77', 'Â£51.77') into a float.

    Args:
        price_val: Price string, numeric value, or None.

    Returns:
        Float price value rounded to 2 decimal places, or None if invalid/missing.
    """
    if price_val is None:
        return None
    if isinstance(price_val, (int, float)):
        return round(float(price_val), 2)

    text = str(price_val).strip()
    match = PRICE_REGEX.search(text)
    if match:
        try:
            return round(float(match.group(0)), 2)
        except ValueError:
            return None
    return None


def clean_rating(rating_val: Any) -> Optional[int]:
    """Turn rating word (e.g. 'Three', 'star-rating Three') into integer 1 to 5.

    Args:
        rating_val: Rating string, integer, or None.

    Returns:
        Integer rating from 1 to 5, or None if unrecognized.
    """
    if rating_val is None:
        return None
    if isinstance(rating_val, int):
        return rating_val if 1 <= rating_val <= 5 else None

    text = str(rating_val).strip().lower()
    if not text:
        return None

    # Check direct word match
    if text in RATING_MAP:
        return RATING_MAP[text]

    # Check numeric digit string
    if text.isdigit():
        val = int(text)
        return val if 1 <= val <= 5 else None

    # Check space-separated tokens (e.g. from class attribute ['star-rating', 'Three'])
    tokens = text.split()
    for token in tokens:
        if token in RATING_MAP:
            return RATING_MAP[token]
        if token.isdigit() and 1 <= int(token) <= 5:
            return int(token)

    return None


def clean_tags(tags: Any) -> str:
    """Normalize tags by lowercasing, sorting alphabetically, and joining with ';'.

    Args:
        tags: List/iterable of tags or semicolon/comma-delimited string.

    Returns:
        Semicolon-joined string of unique sorted lowercase tags (e.g. 'change;deep-thoughts').
    """
    if not tags:
        return ""

    tag_list: list[str] = []
    if isinstance(tags, str):
        # Split by semicolon or comma
        raw_items = re.split(r"[;,]", tags)
        tag_list = [clean_text(item).lower() for item in raw_items if clean_text(item)]
    elif isinstance(tags, Iterable):
        for item in tags:
            cleaned = clean_text(str(item)).lower()
            if cleaned:
                tag_list.append(cleaned)
    else:
        cleaned = clean_text(str(tags)).lower()
        if cleaned:
            tag_list.append(cleaned)

    # Deduplicate and sort alphabetically
    unique_sorted = sorted(set(tag_list))
    return ";".join(unique_sorted)


def normalize_url(url: Optional[str]) -> str:
    """Ensure URL is complete, trimmed, and starts with http:// or https://.

    Args:
        url: Input URL string or None.

    Returns:
        Normalized URL string, or empty string if invalid.
    """
    if not url:
        return ""
    trimmed = str(url).strip()
    if trimmed.startswith(("http://", "https://")):
        return trimmed
    return ""


def clean_record(raw: dict) -> dict:
    """Transform a raw scraped record into a standardized cleaned record.

    Args:
        raw: Raw dictionary from either BooksScraper or QuotesScraper.

    Returns:
        Dictionary adhering to the standardized schema with cleaned values.
    """
    source = clean_text(raw.get("source"))
    source_url = normalize_url(raw.get("source_url"))

    if source == "Quotes to Scrape":
        name_or_title = strip_quotes(raw.get("name_or_title"))
        author = clean_text(raw.get("author"))
        tags = clean_tags(raw.get("tags"))
        price = None
        rating = None
        category = clean_text(raw.get("category")) or "Quotes"
    else:  # Books to Scrape or generic
        name_or_title = clean_text(raw.get("name_or_title"))
        author = clean_text(raw.get("author")) if raw.get("author") else ""
        tags = clean_tags(raw.get("tags")) if raw.get("tags") else ""
        price = clean_price(raw.get("price"))
        rating = clean_rating(raw.get("rating"))
        category = clean_text(raw.get("category"))

    description = clean_text(raw.get("description"))
    scraped_at = clean_text(raw.get("scraped_at"))

    return {
        "source": source,
        "name_or_title": name_or_title,
        "category": category,
        "price": price if price is not None else "",
        "rating": rating if rating is not None else "",
        "author": author,
        "tags": tags,
        "description": description,
        "source_url": source_url,
        "scraped_at": scraped_at,
    }
