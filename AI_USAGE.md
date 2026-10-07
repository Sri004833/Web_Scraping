# AI Usage & Verification Log

In compliance with the assignment instructions (Sections 10 and 11), this document records how Artificial Intelligence (AI) was utilized throughout the design, development, debugging, and verification of the web scraping and data consolidation pipeline.

---

## 1. AI Tools Used

- **Antigravity AI (powered by Gemini 3.8 Flash / Pro models)**: Used as the primary interactive pair-programming assistant for code architecture, refactoring, test case generation, and documentation.
- **Python AST & Pytest Test Runners**: Used in tandem with AI suggestions to immediately verify all unit tests and ETL contracts.

---

## 2. What Each Tool Was Used For

| Area | Purpose |
| :--- | :--- |
| **Architecture & Structure** | Designing the 3-tier decoupled ETL structure (`scrapers/`, `processing/`, `main.py`). |
| **HTML Selector Verification** | Crafting precise CSS selectors for dynamic elements (e.g. `article.product_pod`, `li.next > a`, `p.star-rating`). |
| **Resilient Networking Design** | Generating the `urllib3.util.Retry` strategy with exponential backoff on HTTP status codes 429, 500, 502, 503, 504. |
| **Data Cleaning & Regex** | Formulating clean text, curly-quote stripping, price regex extraction, and rating word-to-integer mappings. |
| **Deduplication Logic** | Creating SHA-256 deterministic fingerprinting based on normalized string composites. |
| **Unit Test Suite** | Generating test cases for edge cases (zero values, negative numbers, malformed URLs, non-breaking spaces). |

---

## 3. Representative Prompts Used

### Prompt 1: Resilient Networking Session
> *"Design a reusable BaseScraper class in Python using requests.Session and urllib3 Retry that handles transient HTTP failures (429, 500, 502, 503, 504) with backoff factors, sets UTF-8 response encoding to avoid currency encoding corruptions (e.g. Â£), and enforces rate-limiting delays."*

### Prompt 2: Dynamic Pagination Loop
> *"Write BooksScraper and QuotesScraper classes with dynamic pagination that follow the 'next' button (li.next > a) using urllib.parse.urljoin until no next link is present, avoiding hardcoded range loops."*

### Prompt 3: Duplicate Fingerprinting & Edge Cases
> *"Write a duplicate detection module in processing/deduplication.py. Books are identified by source + title; Quotes are identified by source + author + first 50 characters of quote text. Ensure that whitespace variations, punctuation, and capitalization differences collapse into identical SHA-256 fingerprints."*

### Prompt 4: Comprehensive Test Generation
> *"Write exhaustive unit tests in pytest for data cleaning, validation rules, and deliberately duplicated sample records without relying on network access."*

---

## 4. Which Parts of the Code Were AI-Assisted

1. **`scrapers/base_scraper.py`**: Initial boilerplate for `requests.Session` with `HTTPAdapter` and `Retry`.
2. **`scrapers/books_scraper.py` & `quotes_scraper.py`**: CSS selector parsing and dynamic pagination loops.
3. **`processing/cleaning.py`**: Regex pattern for price extraction and whitespace normalization.
4. **`processing/validation.py`**: Verification checks and structured error message breakdown.
5. **`processing/deduplication.py`**: Normalization helper and SHA-256 composite hashing.
6. **`tests/`**: Test cases for pytest.

---

## 5. Important Changes Made After Reviewing AI Output

1. **Character Encoding Fix**:
   - *AI Proposal*: Default `requests.get()` without setting encoding.
   - *Issue Identified*: On certain platforms or Windows environments, the pound currency symbol `£` could be misread as `Â£`.
   - *Fix Applied*: Explicitly specified `response.encoding = "utf-8"` immediately upon receiving the response in `BaseScraper`.

2. **Full Title Preservation in Books**:
   - *AI Proposal*: Initially extracted book titles using `h3 > a.get_text()`.
   - *Issue Identified*: On Books to Scrape, visible title text inside the anchor is truncated with an ellipsis (`...`) for longer titles.
   - *Fix Applied*: Inspected the element and prioritized extracting `a.get("title")` (which holds the complete untruncated title), falling back to `a.get_text()` only if absent.

3. **Quote Fingerprint Prefix Timing Bug**:
   - *AI Proposal*: Sliced `raw_text[:50]` before cleaning or normalizing whitespace.
   - *Issue Identified*: If a quote had leading whitespace or quotes, slicing the raw string first yielded a different 50-character prefix than an already-cleaned quote, causing false negatives in deduplication.
   - *Fix Applied*: Updated `generate_fingerprint` to normalize, lowercase, remove punctuation, and collapse whitespace **first**, and only then take the first 50 characters (`_normalize_string_for_fingerprint(raw_text)[:50]`).

4. **Empty Field Representation vs. Fake Data**:
   - *AI Proposal*: Set default price to `0.0` or category to `"General"` when missing.
   - *Issue Identified*: Per specification guidelines, inventing fake values (e.g. giving quotes a price of 0) corrupts data integrity.
   - *Fix Applied*: Preserved missing fields as empty strings / `None`, keeping schema uniform across both sources.

---

## 6. How the Final Solution Was Tested and Verified

1. **Unit Testing without Network**:
   - Created 19 unit tests across `tests/test_cleaning.py`, `tests/test_validation.py`, and `tests/test_deduplication.py`.
   - Executed via `pytest -v`, ensuring 100% pass rate.
   - Included deliberately duplicated records in tests to prove deduplication works even though the target sites host unique records.

2. **Integration / Dry Run**:
   - Tested pipeline execution using `python main.py --max-pages 2`.
   - Verified that both sources were scraped, reconciled, and output files were generated with proper schema.

3. **Full End-to-End Production Run**:
   - Executed `python main.py` across all 50 pages of Books to Scrape and 10 pages of Quotes to Scrape.
   - Verified mathematical reconciliation in `output/summary_report.json`:
     $$\text{raw\_records} - \text{rejected\_records} - \text{duplicates} = \text{final\_records}$$
   - Confirmed row count and verified schema across `output/final_dataset.csv`.
