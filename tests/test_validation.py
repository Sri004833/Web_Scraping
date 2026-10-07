"""Unit tests for processing/validation.py."""
import pytest
from processing.validation import validate_record, validate_records


def test_validate_record_valid_book():
    record = {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/catalogue/book_1/index.html",
        "name_or_title": "A Light in the Attic",
        "category": "",
        "price": 51.77,
        "rating": 3,
        "author": "",
        "tags": "",
        "description": "",
        "scraped_at": "2026-10-07T00:00:00Z",
    }
    errors = validate_record(record)
    assert errors == []


def test_validate_record_valid_quote():
    record = {
        "source": "Quotes to Scrape",
        "source_url": "https://quotes.toscrape.com/author/Albert-Einstein/",
        "name_or_title": "The world as we have created it...",
        "category": "Quotes",
        "price": "",
        "rating": "",
        "author": "Albert Einstein",
        "tags": "change;thinking;world",
        "description": "",
        "scraped_at": "2026-10-07T00:00:00Z",
    }
    errors = validate_record(record)
    assert errors == []


def test_validate_record_invalid_source():
    record = {
        "source": "Unknown Scraper Source",
        "source_url": "https://example.com",
        "name_or_title": "Some Title",
        "price": "",
        "rating": "",
    }
    errors = validate_record(record)
    assert any("Unknown or missing source" in err for err in errors)


def test_validate_record_missing_title():
    record = {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/catalogue/test.html",
        "name_or_title": "   ",
        "price": 10.0,
        "rating": 2,
    }
    errors = validate_record(record)
    assert "Missing name_or_title" in errors


def test_validate_record_invalid_url():
    record = {
        "source": "Books to Scrape",
        "source_url": "ftp://books.toscrape.com",
        "name_or_title": "Test Book",
        "price": 10.0,
        "rating": 2,
    }
    errors = validate_record(record)
    assert any("Invalid or missing source_url" in err for err in errors)


def test_validate_record_invalid_price():
    record = {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/catalogue/test.html",
        "name_or_title": "Test Book",
        "price": -5.99,
        "rating": 2,
    }
    errors = validate_record(record)
    assert any("Price cannot be negative" in err for err in errors)


def test_validate_record_invalid_rating():
    record = {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/catalogue/test.html",
        "name_or_title": "Test Book",
        "price": 20.0,
        "rating": 6,
    }
    errors = validate_record(record)
    assert any("Rating must be between 1 and 5" in err for err in errors)


def test_validate_records_batch():
    records = [
        {
            "source": "Books to Scrape",
            "source_url": "https://books.toscrape.com/catalogue/test1.html",
            "name_or_title": "Valid Book 1",
            "price": 10.0,
            "rating": 4,
        },
        {
            "source": "Invalid Source",
            "source_url": "https://example.com",
            "name_or_title": "Invalid 1",
        },
        {
            "source": "Books to Scrape",
            "source_url": "not-a-url",
            "name_or_title": "",
        },
    ]
    valid_recs, counts, rejected = validate_records(records)
    assert len(valid_recs) == 1
    assert len(rejected) == 2
    assert counts.get("Unknown or missing source") == 1
    assert counts.get("Missing name_or_title") == 1
    assert counts.get("Invalid or missing source_url") == 1
