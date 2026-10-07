"""Scraper implementation for Quotes to Scrape (https://quotes.toscrape.com/)."""
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

QUOTES_START_URL = "https://quotes.toscrape.com/"
SOURCE_NAME = "Quotes to Scrape"


class QuotesScraper(BaseScraper):
    """Scraper for quotes.toscrape.com with dynamic pagination."""

    def __init__(
        self,
        start_url: str = QUOTES_START_URL,
        rate_limit_delay: float = 0.5,
        timeout: int = 15,
        max_retries: int = 3,
    ):
        super().__init__(
            rate_limit_delay=rate_limit_delay,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.start_url = start_url

    def scrape(self, max_pages: Optional[int] = None) -> list[dict]:
        """Scrape all quotes across paginated pages following 'next' link.

        Args:
            max_pages: Optional maximum number of pages to scrape (useful for testing).

        Returns:
            List of raw quote record dictionaries.
        """
        records: list[dict] = []
        current_url: Optional[str] = self.start_url
        page_num = 1

        logger.info("Starting scrape for source: %s", SOURCE_NAME)

        while current_url:
            if max_pages is not None and page_num > max_pages:
                logger.info("Reached maximum page limit of %d. Stopping Quotes scraper.", max_pages)
                break

            logger.info("Scraping Quotes page %d: %s", page_num, current_url)
            soup = self.fetch_soup(current_url)

            if soup is None:
                logger.error(
                    "Failed to retrieve Quotes page %d (%s) after retries. Stopping Quotes scrape.",
                    page_num,
                    current_url,
                )
                break

            quote_elements = soup.select("div.quote")
            if not quote_elements:
                logger.warning("No quote items found on page %d (%s).", page_num, current_url)

            page_records_count = 0
            for quote_div in quote_elements:
                try:
                    record = self._extract_quote_record(quote_div, current_url)
                    if record:
                        records.append(record)
                        page_records_count += 1
                except Exception as exc:
                    logger.warning("Failed to parse a quote record on page %d: %s", page_num, exc)

            logger.debug(
                "Extracted %d quote records from page %d (Cumulative: %d)",
                page_records_count,
                page_num,
                len(records),
            )

            # Dynamic pagination: follow 'next' link
            next_link_elem = soup.select_one("li.next > a")
            if next_link_elem and next_link_elem.get("href"):
                next_rel_href = next_link_elem["href"].strip()
                current_url = urljoin(current_url, next_rel_href)
                page_num += 1
            else:
                logger.info(
                    "No 'next' link found on page %d. Finished Quotes scraping (Total pages: %d).",
                    page_num,
                    page_num,
                )
                current_url = None

        logger.info(
            "Completed Quotes scrape. Total raw records collected: %d across %d page(s).",
            len(records),
            page_num if current_url is None else page_num - 1,
        )
        return records

    def _extract_quote_record(self, quote_div, page_url: str) -> Optional[dict]:
        """Safely extract raw quote data from a div.quote element.

        Args:
            quote_div: BeautifulSoup Tag representing one quote container.
            page_url: The URL of the page containing this quote.

        Returns:
            Dictionary containing raw record fields, or None if essential tags are missing.
        """
        # Quote text
        text_elem = quote_div.select_one("span.text")
        if text_elem is None:
            logger.warning("Missing span.text in quote container on %s", page_url)
            return None
        raw_text = text_elem.get_text()

        # Author name
        author_elem = quote_div.select_one("small.author")
        raw_author = author_elem.get_text() if author_elem else ""

        # Author bio URL / link
        author_link = quote_div.select_one('a[href*="/author/"]')
        if author_link and author_link.get("href"):
            source_url = urljoin(page_url, author_link["href"].strip())
        else:
            source_url = page_url

        # Tags
        tag_elems = quote_div.select("a.tag")
        raw_tags = [t.get_text() for t in tag_elems]

        # Timestamp in UTC
        scraped_at = datetime.now(timezone.utc).isoformat()

        return {
            "source": SOURCE_NAME,
            "source_url": source_url,
            "name_or_title": raw_text,
            "category": "Quotes",  # Fixed documented label
            "price": "",
            "rating": "",
            "author": raw_author,
            "tags": raw_tags,
            "description": "",
            "scraped_at": scraped_at,
        }
