"""Duplicate detection module utilizing normalized hash fingerprinting."""
import hashlib
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def _normalize_string_for_fingerprint(text: Optional[str]) -> str:
    """Lowercase, strip punctuation, and collapse consecutive whitespace."""
    if not text:
        return ""
    lowered = text.lower()
    # Remove all punctuation and symbols (keeping alphanumeric and whitespace)
    no_punct = re.sub(r"[^\w\s]", "", lowered)
    # Collapse consecutive spaces
    return re.sub(r"\s+", " ", no_punct).strip()


def generate_fingerprint(record: dict) -> str:
    """Generate a deterministic SHA-256 fingerprint for a record.

    Identifying fields:
    - Books: source + title
    - Quotes: source + author + first 50 characters of quote text

    Args:
        record: Cleaned record dictionary.

    Returns:
        Hexadecimal SHA-256 hash string.
    """
    source = record.get("source", "")
    norm_source = _normalize_string_for_fingerprint(source)

    if source == "Quotes to Scrape":
        author = record.get("author", "")
        raw_text = record.get("name_or_title", "")

        norm_author = _normalize_string_for_fingerprint(author)
        # Normalize text first (strip spaces/punctuation/lowercase), then slice first 50 chars
        norm_quote = _normalize_string_for_fingerprint(raw_text)[:50]
        composite = f"{norm_source}|{norm_author}|{norm_quote}"
    else:
        # Books to Scrape or generic
        title = record.get("name_or_title", "")
        norm_title = _normalize_string_for_fingerprint(title)
        composite = f"{norm_source}|{norm_title}"

    return hashlib.sha256(composite.encode("utf-8")).hexdigest()


def deduplicate_records(
    records: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Separate unique records from duplicates based on fingerprinting.

    Args:
        records: List of validated records.

    Returns:
        A tuple of (unique_records, duplicate_records).
    """
    seen_fingerprints: set[str] = set()
    unique_records: list[dict] = []
    duplicate_records: list[dict] = []

    for rec in records:
        fp = generate_fingerprint(rec)
        if fp in seen_fingerprints:
            logger.info(
                "Duplicate detected for '%s' ('%s'). Skipping record.",
                rec.get("source"),
                rec.get("name_or_title"),
            )
            duplicate_records.append(rec)
        else:
            seen_fingerprints.add(fp)
            unique_records.append(rec)

    return unique_records, duplicate_records
