"""Unit tests for processing/deduplication.py."""
import pytest
from processing.deduplication import generate_fingerprint, deduplicate_records


def test_fingerprint_case_and_whitespace_insensitivity():
    rec1 = {"source": "Books to Scrape", "name_or_title": "Example Book Title"}
    rec2 = {"source": "Books to Scrape", "name_or_title": "  Example Book Title  "}
    rec3 = {"source": "Books to Scrape", "name_or_title": "EXAMPLE BOOK TITLE"}
    rec4 = {"source": "Books to Scrape", "name_or_title": "Example, Book: Title!"}

    fp1 = generate_fingerprint(rec1)
    fp2 = generate_fingerprint(rec2)
    fp3 = generate_fingerprint(rec3)
    fp4 = generate_fingerprint(rec4)

    assert fp1 == fp2
    assert fp2 == fp3
    assert fp3 == fp4


def test_fingerprint_quote_fields():
    quote_text_1 = "The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking."
    quote_text_2 = "  THE WORLD AS WE HAVE CREATED IT IS A PROCESS OF OUR THINKING! It has extra different endings here..."
    
    # Both share the same first 50 chars when normalized
    rec1 = {
        "source": "Quotes to Scrape",
        "author": "Albert Einstein",
        "name_or_title": quote_text_1,
    }
    rec2 = {
        "source": "Quotes to Scrape",
        "author": "  albert einstein  ",
        "name_or_title": quote_text_2,
    }

    assert generate_fingerprint(rec1) == generate_fingerprint(rec2)


def test_deduplicate_records_with_deliberate_duplicates():
    sample_records = [
        {
            "source": "Books to Scrape",
            "name_or_title": "A Light in the Attic",
            "price": 51.77,
            "rating": 3,
            "source_url": "https://books.toscrape.com/catalogue/1.html",
        },
        {
            "source": "Books to Scrape",
            "name_or_title": "  a light in the attic  ",
            "price": 51.77,
            "rating": 3,
            "source_url": "https://books.toscrape.com/catalogue/1.html",
        },
        {
            "source": "Books to Scrape",
            "name_or_title": "A LIGHT IN THE ATTIC",
            "price": 51.77,
            "rating": 3,
            "source_url": "https://books.toscrape.com/catalogue/1.html",
        },
        {
            "source": "Books to Scrape",
            "name_or_title": "Tipping the Velvet",
            "price": 53.74,
            "rating": 1,
            "source_url": "https://books.toscrape.com/catalogue/2.html",
        },
        {
            "source": "Quotes to Scrape",
            "author": "Albert Einstein",
            "name_or_title": "The world as we have created it is a process of our thinking.",
            "source_url": "https://quotes.toscrape.com/author/Albert-Einstein/",
        },
        {
            "source": "Quotes to Scrape",
            "author": "albert einstein",
            "name_or_title": "  THE WORLD AS WE HAVE CREATED IT IS A PROCESS OF OUR THINKING!  ",
            "source_url": "https://quotes.toscrape.com/author/Albert-Einstein/",
        },
    ]

    unique_recs, dup_recs = deduplicate_records(sample_records)

    # 4 unique records expected: 2 books ("A Light in the Attic" & "Tipping the Velvet") and 1 quote ("Albert Einstein...")
    # Wait: 2 books + 1 quote = 3 unique records!
    # And 3 duplicates: 2 book duplicates + 1 quote duplicate = 3 duplicate records!
    assert len(unique_recs) == 3
    assert len(dup_recs) == 3
    assert len(unique_recs) + len(dup_recs) == len(sample_records)
