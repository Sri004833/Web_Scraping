"""Data validation module ensuring records meet quality standards before persisting."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ALLOWED_SOURCES = {"Books to Scrape", "Quotes to Scrape"}


def validate_record(record: dict) -> list[str]:
    """Check a single cleaned record and return a list of failure reasons.

    An empty list indicates the record is valid.

    Rules:
    1. Known source: source is one of the allowed names ('Books to Scrape', 'Quotes to Scrape')
    2. Has a name: name_or_title is not empty
    3. Valid URL: source_url starts with http:// or https://
    4. Valid price: if present, must be numeric and >= 0
    5. Valid rating: if present, must be integer between 1 and 5

    Args:
        record: Cleaned record dictionary.

    Returns:
        List of validation error strings.
    """
    errors: list[str] = []

    # Rule 1: Known source
    source = record.get("source")
    if not source or source not in ALLOWED_SOURCES:
        errors.append(f"Unknown or missing source: '{source}'")

    # Rule 2: Has a name or title
    name_or_title = record.get("name_or_title")
    if not name_or_title or not str(name_or_title).strip():
        errors.append("Missing name_or_title")

    # Rule 3: Valid URL
    source_url = record.get("source_url")
    if not source_url or not str(source_url).startswith(("http://", "https://")):
        errors.append(f"Invalid or missing source_url: '{source_url}'")

    # Rule 4: Valid price (if present)
    price = record.get("price")
    if price is not None and price != "":
        try:
            val = float(price)
            if val < 0:
                errors.append(f"Price cannot be negative: {val}")
        except (ValueError, TypeError):
            errors.append(f"Price is not a valid number: {price}")

    # Rule 5: Valid rating (if present)
    rating = record.get("rating")
    if rating is not None and rating != "":
        try:
            val = int(rating)
            if not (1 <= val <= 5):
                errors.append(f"Rating must be between 1 and 5: {val}")
        except (ValueError, TypeError):
            errors.append(f"Rating is not a valid integer: {rating}")

    return errors


def validate_records(
    records: list[dict],
) -> tuple[list[dict], dict[str, int], list[tuple[dict, list[str]]]]:
    """Validate a collection of cleaned records.

    Args:
        records: List of cleaned records.

    Returns:
        A tuple of:
        - valid_records: List of records passing all validation checks.
        - rejection_counts: Dictionary mapping error reasons to occurrence counts.
        - rejected_records: List of tuples containing (rejected_record, error_reasons).
    """
    valid_records: list[dict] = []
    rejection_counts: dict[str, int] = {}
    rejected_records: list[tuple[dict, list[str]]] = []

    for rec in records:
        errors = validate_record(rec)
        if not errors:
            valid_records.append(rec)
        else:
            rejected_records.append((rec, errors))
            for err in errors:
                # Normalize key for concise reporting
                key = err.split(":")[0].strip()
                rejection_counts[key] = rejection_counts.get(key, 0) + 1
            logger.warning(
                "Record rejected from '%s' (%s): %s",
                rec.get("source", "Unknown"),
                rec.get("name_or_title", "Unknown"),
                ", ".join(errors),
            )

    return valid_records, rejection_counts, rejected_records
