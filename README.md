# Multi-Source Web Scraping & Data Consolidation

A robust, production-grade Python ETL (Extract, Transform, Load) pipeline that extracts data from multiple public web sources, standardizes heterogeneous data structures into a unified schema, performs rigorous data cleaning, validates records against business constraints, detects and eliminates duplicates via cryptographic fingerprinting, and outputs a consolidated CSV dataset alongside an execution summary report and detailed audit log.

Built for the **Realisieren Technologies Technical Assessment**.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Project Structure](#architecture--project-structure)
3. [System Requirements & Installation](#system-requirements--installation)
4. [How to Run](#how-to-run)
5. [Data Sources & Inspection Observations](#data-sources--inspection-observations)
6. [Common Data Model (Standardized Schema)](#common-data-model-standardized-schema)
7. [Dynamic Pagination Architecture](#dynamic-pagination-architecture)
8. [Data Cleaning & Normalization Approach](#data-cleaning--normalization-approach)
9. [Validation Strategy & Error Accounting](#validation-strategy--error-accounting)
10. [Duplicate Detection & Fingerprinting](#duplicate-detection--fingerprinting)
11. [Error Handling & Network Resilience](#error-handling--network-resilience)
12. [Output Files & Reconciliation Report](#output-files--reconciliation-report)
13. [Assumptions & Known Limitations](#assumptions--known-limitations)
14. [Testing & Quality Verification](#testing--quality-verification)
15. [AI Usage Summary](#ai-usage-summary)
16. [Interview Follow-Up Questions & Answers](#interview-follow-up-questions--answers)

---

## 1. Project Overview

Real-world web data is noisy, inconsistently structured, and prone to transient network anomalies. This project demonstrates an automated ETL pipeline that addresses these challenges across two distinct public sites:
- **Source 1: Books to Scrape** (`https://books.toscrape.com/`) &mdash; 1,000 books cataloged across 50 pages with prices, ratings, and product links.
- **Source 2: Quotes to Scrape** (`https://quotes.toscrape.com/`) &mdash; 100 quotes distributed across 10 pages with authors, tags, and biographies.

### Key Capabilities:
- **Dynamic Pagination**: Discovers the next page link (`li.next > a`) dynamically; zero hardcoding of page ranges.
- **Unified Data Model**: Merges two vastly different entity shapes (e-commerce books vs. literary quotes) into a single standard schema.
- **Pure Functional Cleaning**: Separates network I/O from string parsing, ensuring pure functions testable without internet connectivity.
- **Strict Validation Rules**: Verifies data integrity with granular error reasons recorded in the summary report.
- **Cryptographic Fingerprinting**: Collapses punctuation, whitespace, and case differences into SHA-256 fingerprints to identify duplicates.
- **Mathematical Reconciliation**: Enforces that:
  $$\text{Raw Records} - \text{Rejected Records} - \text{Duplicates} = \text{Final Records}$$

---

## 2. Architecture & Project Structure

The project follows a decoupled 3-tier architecture:

```
Inter/
├── scrapers/                     # Layer 1: Extraction & Network I/O
│   ├── __init__.py
│   ├── base_scraper.py           # Shared HTTP session, retries, rate limiting
│   ├── books_scraper.py          # Books to Scrape spider with pagination
│   └── quotes_scraper.py         # Quotes to Scrape spider with pagination
├── processing/                   # Layer 2: Pure Data Transformation
│   ├── __init__.py
│   ├── cleaning.py               # Pure functions for whitespace, price, rating, tags
│   ├── validation.py             # Validation rules and failure accounting
│   └── deduplication.py          # Hash-based duplicate detection logic
├── tests/                        # Automated Unit Test Suite (no internet needed)
│   ├── __init__.py
│   ├── test_cleaning.py          # Unit tests for all cleaners
│   ├── test_validation.py        # Unit tests for validation edge cases
│   └── test_deduplication.py     # Unit tests for duplicate detection
├── output/                       # Generated Artifacts
│   ├── final_dataset.csv         # Consolidated CSV dataset (1099 rows)
│   └── summary_report.json       # Mathematical reconciliation report
├── logs/
│   └── scraper.log               # Timestamped audit log of all operations
├── main.py                       # Layer 3: Pipeline orchestrator & CLI
├── requirements.txt              # Pinned library dependencies
├── README.md                     # Comprehensive technical documentation
└── AI_USAGE.md                   # AI usage, prompt log, and verification record
```

---

## 3. System Requirements & Installation

- **Operating System**: Windows, macOS, or Linux
- **Python Version**: Python 3.10, 3.11, or 3.12 (Tested on Python 3.10.11)

### Setup Instructions:

1. Clone or extract the repository and enter the directory:
   ```bash
   cd Inter
   ```

2. Create a clean Python virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD)**:
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - **macOS / Linux**:
     ```bash
     source venv/bin/activate
     ```

4. Install the pinned dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 4. How to Run

### Run the Complete Pipeline (Default):
Run the entire job with a single command:
```bash
python main.py
```
This scrapes all 50 pages of Books to Scrape and all 10 pages of Quotes to Scrape with polite 0.5s rate-limiting, performs cleaning, validation, deduplication, and generates:
- `output/final_dataset.csv`
- `output/summary_report.json`
- `logs/scraper.log`

### Optional CLI Arguments:
`main.py` provides command-line flags for development, testing, and debugging:

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--max-pages` | `int` | `None` | Limit page count per source (e.g. `--max-pages 2` for rapid testing) |
| `--sources` | `str` | `both` | Select sources to scrape: `both`, `books`, or `quotes` |
| `--rate-limit`| `float`| `0.5` | Delay in seconds between requests (prevents server overload) |
| `--timeout` | `int` | `15` | Request timeout in seconds |
| `--output-dir`| `Path` | `output`| Target directory for output files |
| `--log-file` | `Path` | `logs/scraper.log` | Path for execution log |

#### Example CLI Commands:
```bash
# Rapid test run: scrape only first 2 pages of each site
python main.py --max-pages 2

# Scrape only Quotes to Scrape
python main.py --sources quotes

# Custom rate limit and output directory
python main.py --rate-limit 0.2 --output-dir custom_output
```

---

## 5. Data Sources & Inspection Observations

As required by Stage 1 of the specification, both websites were inspected via browser developer tools to isolate element selectors and identify edge cases:

| Observation Area | Books to Scrape (`books.toscrape.com`) | Quotes to Scrape (`quotes.toscrape.com`) |
| :--- | :--- | :--- |
| **Record Container** | `article.product_pod` | `div.quote` |
| **Main Text / Title** | `h3 > a`: **Crucial**: The visible anchor text is truncated with `...` (e.g., *"The Coming Woman: A Novel..."*). The full title resides inside the `title` attribute. | `span.text`: Enclosed in decorative Unicode curly quotation marks (`“...”`). |
| **Price** | `p.price_color`: Prepended with currency symbol (e.g. `£51.77`). Requires UTF-8 decoding to avoid `Â£51.77`. | None (Not present). |
| **Rating** | `p.star-rating`: Encoded in class list (e.g. `['star-rating', 'Three']`). Needs mapping to integers 1–5. | None (Not present). |
| **Author** | None (Not present on listing pod). | `small.author`: Plain text author name. |
| **Tags** | None (Not present on listing pod). | `a.tag`: Zero or more tags per quote container. |
| **Detail Link** | `h3 > a[href]`: Relative link to product page (e.g. `catalogue/...`). Resolved via `urljoin`. | `a[href*="/author/"]`: Link to author biography page. Resolved via `urljoin`. |
| **Pagination Link** | `li.next > a`: Relative URL pointing to next page. | `li.next > a`: Relative URL pointing to next page. |

---

## 6. Common Data Model (Standardized Schema)

A CSV dataset requires consistent column headers across all records. To avoid data corruption, inapplicable fields are left empty rather than filled with misleading dummy data (such as assigning price `0` to a quote).

| Column Name | Books to Scrape | Quotes to Scrape | Data Type / Representation |
| :--- | :--- | :--- | :--- |
| `source` | `"Books to Scrape"` | `"Quotes to Scrape"` | String |
| `name_or_title` | Full Book Title | Cleaned Quote Text | String (cleaned, stripped of curly quotes) |
| `category` | Empty string `""` (see notes) | `"Quotes"` | String |
| `price` | Numeric decimal (e.g. `51.77`) | Empty string `""` | Float / Empty |
| `rating` | Integer `1` to `5` | Empty string `""` | Integer / Empty |
| `author` | Empty string `""` | Author Name | String |
| `tags` | Empty string `""` | Semicolon-delimited tags | String (`tag1;tag2`, lowercase, sorted) |
| `description` | Empty string `""` (see notes) | Empty string `""` | String |
| `source_url` | Full absolute book URL | Full author biography URL | String (`https://...`) |
| `scraped_at` | ISO 8601 UTC Timestamp | ISO 8601 UTC Timestamp | String (`YYYY-MM-DDTHH:MM:SSZ`) |

---

## 7. Dynamic Pagination Architecture

Both scrapers implement dynamic pagination:
1. Start at the site root/index URL.
2. Download and parse the HTML DOM.
3. Extract all available records on the current page.
4. Locate the next page anchor element: `li.next > a`.
5. If found:
   - Extract the relative link from `href`.
   - Convert to an absolute URL via `urllib.parse.urljoin(current_url, next_href)`.
   - Iterate to the next page.
6. If `li.next > a` is not found, pagination terminates gracefully.

**Why avoid hardcoded ranges like `range(1, 51)`?**
Hardcoding page counts is brittle: if books are added or removed, a fixed loop either crashes on a 404 error or silently skips newly added pages. Dynamic pagination guarantees adaptability to catalogue changes.

---

## 8. Data Cleaning & Normalization Approach

All cleaning logic is isolated in `processing/cleaning.py` as pure functions with no network or disk side-effects:

1. **`clean_text(text)`**:
   - Replaces non-breaking spaces (`\xa0`) with standard spaces.
   - Replaces tabs, newlines, and multi-space sequences with a single space.
   - Strips leading and trailing whitespace.
   - Handles `None` safely.

2. **`strip_quotes(text)`**:
   - Removes standard double/single quotes (`"`, `'`) and typographical curly quotation marks (`“`, `”`, `‘`, `’`) from both ends of the text.

3. **`clean_price(price_val)`**:
   - Extracts numeric values using regex `r"[-+]?\d+(?:\.\d+)?"`.
   - Converts currency strings like `£51.77` or `Â£51.77` into a float `51.77` rounded to 2 decimal places.

4. **`clean_rating(rating_val)`**:
   - Maps English word numerals (`"One"`, `"Two"`, `"Three"`, `"Four"`, `"Five"`) and class combinations (e.g. `"star-rating Three"`) to integers `1` through `5`.

5. **`clean_tags(tags)`**:
   - Accepts list or delimited string of tags.
   - Converts all tags to lowercase.
   - Deduplicates and sorts alphabetically.
   - Joins with semicolons: `"change;deep-thoughts;thinking;world"`.

6. **`normalize_url(url)`**:
   - Ensures the URL starts with `http://` or `https://` and strips whitespace.

---

## 9. Validation Strategy & Error Accounting

Validation in `processing/validation.py` acts as a quality gate before records reach the final dataset:

### Validation Rules:
1. **Known Source**: `source` must strictly match `"Books to Scrape"` or `"Quotes to Scrape"`.
2. **Has Name/Title**: `name_or_title` must not be null or blank.
3. **Valid URL**: `source_url` must be present and start with `http://` or `https://`.
4. **Valid Price**: If a price exists, it must be numeric and $\ge 0$.
5. **Valid Rating**: If a rating exists, it must be an integer between 1 and 5 ($1 \le \text{rating} \le 5$).

### Failure Accounting:
When a record violates one or more rules:
- It is excluded from the final CSV.
- A descriptive warning is logged in `logs/scraper.log`.
- Rejection counters are incremented by specific reason in `output/summary_report.json`.

---

## 10. Duplicate Detection & Fingerprinting

### Fingerprint Algorithm:
Duplicate detection operates via deterministic SHA-256 fingerprinting:
1. Identify distinguishing fields:
   - **Books**: `source` + `name_or_title`
   - **Quotes**: `source` + `author` + first 50 characters of `name_or_title`
2. Apply deep normalization:
   - Lowercase the strings.
   - Remove all punctuation and symbols (`re.sub(r"[^\w\s]", "", text)`).
   - Collapse whitespace sequences (`re.sub(r"\s+", " ", text).strip()`).
3. Construct composite key and hash with SHA-256:
   $$\text{Fingerprint} = \text{SHA256}(\text{normalized\_composite})$$
4. Maintain a `seen_fingerprints` set. If a hash already exists, the record is flagged as a duplicate.

### Why Remove Duplicates Instead of Flagging?
The specification requires a tidy, final analytical dataset where:
$$\text{Raw Collected} - \text{Rejected} - \text{Duplicates} = \text{Final Records}$$
Dropping duplicates prevents skewing downstream aggregations, price averages, and word counts. All duplicate occurrences are logged and counted in the audit report.

*Discovery during full run*: The site `books.toscrape.com` actually contains 1 legitimate duplicate book (*"The Star-Touched Queen"*). Our fingerprinting algorithm accurately caught and removed it!

---

## 11. Error Handling & Network Resilience

1. **Exponential Backoff Retries**:
   - Configured via `urllib3.util.Retry` on `requests.Session`.
   - Retries up to 3 times on transient errors (`429 Too Many Requests`, `500 Internal Server Error`, `502 Bad Gateway`, `503 Service Unavailable`, `504 Gateway Timeout`) with backoff delays (1s, 2s, 4s).

2. **Polite Rate Limiting**:
   - `BaseScraper` tracks request timestamps and enforces a configurable delay (default `0.5s`) between requests to avoid overwhelming public servers.

3. **Character Encoding Safety**:
   - Forces `response.encoding = "utf-8"` before reading `response.text`, avoiding garbled symbols like `Â£`.

4. **Fault Isolation**:
   - Each source is wrapped in separate `try/except` blocks in `main.py`. A failure on Quotes to Scrape will never crash or invalidate the Books to Scrape pipeline.
   - Each individual record parsing is wrapped in a `try/except` block, ensuring a single malformed HTML element skips only that item without halting the scrape.

---

## 12. Output Files & Reconciliation Report

After executing `python main.py`, the following output files are produced:

### 1. `output/final_dataset.csv`
- Header: `source,name_or_title,category,price,rating,author,tags,description,source_url,scraped_at`
- Contains exactly **1,099 rows** of clean, validated, non-duplicate data.

### 2. `output/summary_report.json`
```json
{
  "execution": {
    "start_time_utc": "2026-10-07T01:34:29.659376+00:00",
    "end_time_utc": "2026-10-07T01:35:07.583807+00:00",
    "duration_seconds": 37.92
  },
  "sources": {
    "Books to Scrape": {
      "raw_records": 1000,
      "cleaned_records": 1000,
      "valid_records": 1000,
      "rejected_records": 0,
      "rejection_reasons": {},
      "duplicates_removed": 1,
      "final_records": 999
    },
    "Quotes to Scrape": {
      "raw_records": 100,
      "cleaned_records": 100,
      "valid_records": 100,
      "rejected_records": 0,
      "rejection_reasons": {},
      "duplicates_removed": 0,
      "final_records": 100
    }
  },
  "overall": {
    "total_raw_collected": 1100,
    "total_cleaned": 1100,
    "total_rejected": 0,
    "rejection_reasons": {},
    "total_duplicates_removed": 1,
    "total_final_records": 1099,
    "reconciliation": {
      "formula": "raw - rejected - duplicates == final",
      "calculated": "1100 - 0 - 1 = 1099",
      "expected": 1099,
      "reconciled": true
    }
  }
}
```

### 3. `logs/scraper.log`
Full audit trail tracking start times, page URLs, duplicate alerts, and termination summaries.

---

## 13. Assumptions & Known Limitations

1. **Book Category & Description**:
   - *Limitation*: The category and full synopsis of books are only present on their individual detail pages, not on the 50 catalogue listing pages.
   - *Design Choice*: Visiting 1,000 individual detail pages with polite rate limits would require 1,000 additional HTTP requests (~8-10 minutes of execution time and unneeded traffic on a practice server). Following the assignment's explicit beginner guidance, these fields are represented as empty strings in the listing scraper rather than making unpolite requests or guessing values.
2. **Quote Source URL**:
   - Chosen as the author biography URL (`https://quotes.toscrape.com/author/...`), providing meaningful provenance for each quote.
3. **Fixed Category for Quotes**:
   - Quotes assign the documented label `"Quotes"` in the `category` column to differentiate entity types in tabular BI tools.

---

## 14. Testing & Quality Verification

Automated unit tests run entirely offline without network access:
```bash
pytest -v
```
All **19 tests** pass:
- `tests/test_cleaning.py`: Validates text collapsing, non-breaking space replacement, quote stripping, currency parsing, rating conversion, and tag sorting.
- `tests/test_validation.py`: Tests valid/invalid source names, negative prices, out-of-range ratings, and malformed URLs.
- `tests/test_deduplication.py`: Uses deliberately duplicated synthetic records with irregular punctuation and whitespace to prove duplicate identification and removal.

---

## 15. AI Usage Summary

AI assistance was utilized for initial selector drafting, retry strategy structuring, test edge case generation, and documentation. All AI proposals were reviewed, refined, and verified against unit tests and real web crawls. Complete prompt logs, bug corrections, and verification steps are detailed in [`AI_USAGE.md`](AI_USAGE.md).

---

## 16. Interview Follow-Up Questions & Answers

### 1. Why did you choose Requests + BeautifulSoup?
Both target sites are static, server-rendered HTML. They do not employ client-side JavaScript rendering (such as React or Angular) or heavy anti-bot mechanisms. Using browser automation tools like Playwright or Selenium would introduce significant memory and CPU overhead, slow down execution by 5-10x, and add unnecessary external browser dependencies. `Requests` + `BeautifulSoup` (with `lxml` parser) provides maximum speed, low resource usage, and supreme maintainability.

### 2. How does pagination work?
Rather than hardcoding page counts (e.g. `range(1, 51)`), the scrapers follow the `li.next > a` element on each page. The relative link is resolved against the current page URL using `urllib.parse.urljoin()`. When the last page is reached and no next link exists, the pagination loop gracefully terminates.

### 3. How did you handle missing fields?
We designed a unified 10-column schema where missing or source-specific attributes (e.g. `author` for books, `price` for quotes) are represented as empty strings (`""`) or `None`. We strictly avoid inventing fake default data (such as price `0` for quotes), preserving analytical integrity.

### 4. How did you handle failed requests?
We mounted a resilient `HTTPAdapter` configured with `urllib3.util.Retry(total=3, backoff_factor=1.0)` targeting status codes `429, 500, 502, 503, 504`. If an unrecoverable failure occurs, it is logged as an ERROR, and the pipeline continues to process remaining pages or the other source.

### 5. How does your duplicate-detection logic work?
We generate a deterministic SHA-256 hash fingerprint from normalized core fields:
- Books: `source + title`
- Quotes: `source + author + first 50 characters of quote text`
Before hashing, strings are lowercased, punctuation is stripped, and whitespace sequences are collapsed. A set of seen fingerprints ensures identical entities with subtle spacing or capitalization differences are filtered out.

### 6. Why did you choose your standardized schema?
To facilitate direct tabular analysis (e.g. Pandas, SQL, or Excel), records from disparate sources must share identical columns. We chose a schema containing universal provenance fields (`source`, `source_url`, `scraped_at`), primary entity names (`name_or_title`, `category`), and source-specific metrics (`price`, `rating`, `author`, `tags`, `description`).

### 7. What assumptions did you make?
1. That pagination is linear and forward-navigating via `li.next > a`.
2. That 0.5s polite delay is an appropriate polite rate-limit for the practice sites.
3. That book listing pages are sufficient for cataloging books without launching 1,000 detail requests.

### 8. Which parts were AI-assisted?
Initial boilerplates for `BaseScraper` and cleaning regex patterns. Comprehensive prompt history and review cycles are recorded in `AI_USAGE.md`.

### 9. Did AI-generated code create any problems?
Yes:
- The AI initially extracted book titles using `a.get_text()` instead of `a.get('title')`, which caused truncated titles containing `...`.
- The AI sliced the first 50 characters of quotes before whitespace normalization, which caused duplicate detection failures when leading spaces were present.
Both defects were caught, corrected, and verified with unit tests.

### 10. How did you verify that the final result was correct?
1. Executed 19 pytest unit tests verifying all cleaning, validation, and deduplication logic.
2. Inspected generated CSV and confirmed 1099 data rows matching the mathematical reconciliation:
   $$\text{Raw } (1100) - \text{Rejected } (0) - \text{Duplicates } (1) = 1099$$
3. Verified the log file recorded all 60 pages and the single duplicate book.

### 11. What would you change if this scraper had to run regularly in production?
- **Asynchronous I/O**: Migrate to `aiohttp` / `asyncio` or `Scrapy` with a polite concurrency pool to scrape thousands of pages in seconds.
- **Database Storage**: Replace CSV output with PostgreSQL / MongoDB using upserts (`ON CONFLICT DO UPDATE`) to support incremental scrapes.
- **Proxy Rotation**: Implement rotating residential/datacenter proxies and randomized user-agents.
- **Monitoring & Alerts**: Integrate OpenTelemetry or Prometheus metrics and alert on failure rate anomalies via Slack / PagerDuty.
