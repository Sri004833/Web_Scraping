"""Processing package for data cleaning, validation, and deduplication."""
from processing.cleaning import (
    clean_text,
    strip_quotes,
    clean_price,
    clean_rating,
    clean_tags,
    normalize_url,
    clean_record,
)
from processing.validation import validate_record, validate_records
from processing.deduplication import generate_fingerprint, deduplicate_records

__all__ = [
    "clean_text",
    "strip_quotes",
    "clean_price",
    "clean_rating",
    "clean_tags",
    "normalize_url",
    "clean_record",
    "validate_record",
    "validate_records",
    "generate_fingerprint",
    "deduplicate_records",
]
