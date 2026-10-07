"""Unit tests for processing/cleaning.py."""
import pytest
from processing.cleaning import (
    clean_text,
    strip_quotes,
    clean_price,
    clean_rating,
    clean_tags,
    normalize_url,
    clean_record,
)


def test_clean_text():
    assert clean_text(" Hello \n World ") == "Hello World"
    assert clean_text("Item\xa0with\xa0non-breaking\xa0spaces\t\n") == "Item with non-breaking spaces"
    assert clean_text("   multiple     spaces   ") == "multiple spaces"
    assert clean_text("") == ""
    assert clean_text(None) == ""


def test_strip_quotes():
    assert strip_quotes("“The world as we have created it...”") == "The world as we have created it..."
    assert strip_quotes('"Double quotes"') == "Double quotes"
    assert strip_quotes("‘Single curly quotes’") == "Single curly quotes"
    assert strip_quotes("No quotes here") == "No quotes here"
    assert strip_quotes(None) == ""


def test_clean_price():
    assert clean_price("£51.77") == 51.77
    assert clean_price("Â£51.77") == 51.77
    assert clean_price("€19.99") == 19.99
    assert clean_price("$100.00") == 100.0
    assert clean_price(42.5) == 42.5
    assert clean_price("0.00") == 0.0
    assert clean_price("Free") is None
    assert clean_price("") is None
    assert clean_price(None) is None


def test_clean_rating():
    assert clean_rating("One") == 1
    assert clean_rating("two") == 2
    assert clean_rating("Three") == 3
    assert clean_rating("Four") == 4
    assert clean_rating("Five") == 5
    assert clean_rating("star-rating Three") == 3
    assert clean_rating("star-rating Five") == 5
    assert clean_rating(3) == 3
    assert clean_rating("4") == 4
    assert clean_rating("Zero") is None
    assert clean_rating("Six") is None
    assert clean_rating("") is None
    assert clean_rating(None) is None


def test_clean_tags():
    assert clean_tags(["world", "Life", "books"]) == "books;life;world"
    assert clean_tags("books, life; world") == "books;life;world"
    assert clean_tags(["duplicate", "duplicate", "tag"]) == "duplicate;tag"
    assert clean_tags([]) == ""
    assert clean_tags("") == ""
    assert clean_tags(None) == ""


def test_normalize_url():
    assert normalize_url("https://books.toscrape.com/catalogue/item.html") == "https://books.toscrape.com/catalogue/item.html"
    assert normalize_url("http://quotes.toscrape.com/author/Einstein") == "http://quotes.toscrape.com/author/Einstein"
    assert normalize_url("   https://example.com/page   ") == "https://example.com/page"
    assert normalize_url("ftp://example.com/file") == ""
    assert normalize_url("relative/path") == ""
    assert normalize_url("") == ""
    assert normalize_url(None) == ""


def test_clean_record_book():
    raw_book = {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/catalogue/book_1/index.html",
        "name_or_title": "  A Light in the Attic  ",
        "category": "",
        "price": "£51.77",
        "rating": "star-rating Three",
        "author": "",
        "tags": "",
        "description": "",
        "scraped_at": "2026-10-07T00:00:00Z",
    }
    cleaned = clean_record(raw_book)
    assert cleaned["source"] == "Books to Scrape"
    assert cleaned["name_or_title"] == "A Light in the Attic"
    assert cleaned["price"] == 51.77
    assert cleaned["rating"] == 3
    assert cleaned["author"] == ""
    assert cleaned["tags"] == ""


def test_clean_record_quote():
    raw_quote = {
        "source": "Quotes to Scrape",
        "source_url": "https://quotes.toscrape.com/author/Albert-Einstein/",
        "name_or_title": "“The world as we have created it is a process of our thinking.”",
        "category": "Quotes",
        "price": "",
        "rating": "",
        "author": "  Albert Einstein  ",
        "tags": ["thinking", "world", "change"],
        "description": "",
        "scraped_at": "2026-10-07T00:00:00Z",
    }
    cleaned = clean_record(raw_quote)
    assert cleaned["source"] == "Quotes to Scrape"
    assert cleaned["name_or_title"] == "The world as we have created it is a process of our thinking."
    assert cleaned["author"] == "Albert Einstein"
    assert cleaned["tags"] == "change;thinking;world"
    assert cleaned["price"] == ""
    assert cleaned["rating"] == ""
