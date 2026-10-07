"""Scraper implementation for Books to Scrape (https://books.toscrape.com/)."""
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BOOKS_START_URL = "https://books.toscrape.com/index.html"
SOURCE_NAME = "Books to Scrape"


class BooksScraper(BaseScraper):
    """Scraper for books.toscrape.com with dynamic pagination."""

    def __init__(
        self,
        start_url: str = BOOKS_START_URL,
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
        """Scrape all books across paginated pages following 'next' link.

        Args:
            max_pages: Optional maximum number of pages to scrape (useful for testing).

        Returns:
            List of raw book record dictionaries.
        """
        records: list[dict] = []
        current_url: Optional[str] = self.start_url
        page_num = 1

        logger.info("Starting scrape for source: %s", SOURCE_NAME)

        while current_url:
            if max_pages is not None and page_num > max_pages:
                logger.info("Reached maximum page limit of %d. Stopping Books scraper.", max_pages)
                break

            logger.info("Scraping Books page %d: %s", page_num, current_url)
            soup = self.fetch_soup(current_url)

            if soup is None:
                logger.error(
                    "Failed to retrieve Books page %d (%s) after retries. Stopping Books scrape.",
                    page_num,
                    current_url,
                )
                break

            product_pods = soup.select("article.product_pod")
            if not product_pods:
                logger.warning("No book items found on page %d (%s).", page_num, current_url)

            page_records_count = 0
            for pod in product_pods:
                try:
                    record = self._extract_book_record(pod, current_url)
                    if record:
                        records.append(record)
                        page_records_count += 1
                except Exception as exc:
                    logger.warning("Failed to parse a book record on page %d: %s", page_num, exc)

            logger.debug(
                "Extracted %d book records from page %d (Cumulative: %d)",
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
                    "No 'next' link found on page %d. Finished Books scraping (Total pages: %d).",
                    page_num,
                    page_num,
                )
                current_url = None

        logger.info(
            "Completed Books scrape. Total raw records collected: %d across %d page(s).",
            len(records),
            page_num if current_url is None else page_num - 1,
        )
        return records

    def _extract_book_record(self, pod, page_url: str) -> Optional[dict]:
        """Safely extract raw book data from an article.product_pod element.

        Args:
            pod: BeautifulSoup Tag representing one product pod.
            page_url: The URL of the page containing this pod.

        Returns:
            Dictionary containing raw record fields, or None if essential tags are missing.
        """
        # Title and URL are located within h3 > a
        title_anchor = pod.select_one("h3 > a")
        if title_anchor is None:
            logger.warning("Missing h3 > a in product pod on %s", page_url)
            return None

        # Full title is in the 'title' attribute; visible text might be truncated with "..."
        raw_title = title_anchor.get("title") or title_anchor.get_text()

        # Product URL (convert relative link to absolute URL)
        raw_href = title_anchor.get("href", "")
        detail_url = urljoin(page_url, raw_href) if raw_href else ""

        # Price element
        price_elem = pod.select_one("p.price_color")
        raw_price = price_elem.get_text() if price_elem else ""

        # Star rating element (stored in classes, e.g. class="star-rating Three")
        rating_elem = pod.select_one("p.star-rating")
        if rating_elem:
            classes = rating_elem.get("class", [])
            # Convert list of classes to a single string for cleaning function
            raw_rating = " ".join(classes) if isinstance(classes, list) else str(classes)
        else:
            raw_rating = ""

        # Timestamp in UTC
        scraped_at = datetime.now(timezone.utc).isoformat()

        # Common schema raw record
        return {
            "source": SOURCE_NAME,
            "source_url": detail_url,
            "name_or_title": raw_title,
            "category": "",  # Empty on listing page as per design/limitations
            "price": raw_price,
            "rating": raw_rating,
            "author": "",
            "tags": "",
            "description": "",  # Empty on listing page
            "scraped_at": scraped_at,
        }
