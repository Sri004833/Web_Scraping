"""Base scraper module providing resilient HTTP sessions, retries, and rate limiting."""
import logging
import time
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 "
    "RealisierenScraper/1.0 (Assessment Bot)"
)


class BaseScraper:
    """Base class for scrapers handling networking, sessions, retries, and rate limiting."""

    def __init__(
        self,
        rate_limit_delay: float = 0.5,
        timeout: int = 15,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
    ):
        """Initialize the scraper with session configuration and rate limiting.

        Args:
            rate_limit_delay: Delay in seconds between successive requests (default: 0.5s).
            timeout: Network request timeout in seconds (default: 15s).
            max_retries: Maximum number of retry attempts for transient server errors.
            user_agent: Custom User-Agent string.
        """
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent or DEFAULT_USER_AGENT
        self.session = self._create_resilient_session()
        self._last_request_time: float = 0.0

    def _create_resilient_session(self) -> requests.Session:
        """Create a requests.Session configured with automatic retries and custom headers."""
        session = requests.Session()
        session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1.0,  # 1s, 2s, 4s backoff delays
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _apply_rate_limit(self) -> None:
        """Enforce rate limiting by sleeping if elapsed time is less than delay."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def fetch_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a webpage URL and parse it into a BeautifulSoup object.

        Args:
            url: The HTTP/HTTPS URL to request.

        Returns:
            BeautifulSoup instance if request succeeded, or None if failed.
        """
        self._apply_rate_limit()
        logger.debug("Requesting URL: %s", url)

        try:
            response = self.session.get(url, timeout=self.timeout)
            # Ensure correct character encoding for special symbols (e.g., currency symbols like £)
            response.encoding = "utf-8"

            if response.status_code != 200:
                logger.error(
                    "HTTP %s received for URL %s (final response after retries)",
                    response.status_code,
                    url,
                )
                return None

            try:
                soup = BeautifulSoup(response.text, "lxml")
            except Exception:
                soup = BeautifulSoup(response.text, "html.parser")

            return soup

        except requests.exceptions.Timeout as exc:
            logger.error("Timeout fetching URL %s: %s", url, exc)
            return None
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error fetching URL %s: %s", url, exc)
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("Request failed for URL %s: %s", url, exc)
            return None
        except Exception as exc:
            logger.error("Unexpected error fetching URL %s: %s", url, exc)
            return None

    def scrape(self, max_pages: Optional[int] = None) -> list[dict]:
        """Scrape all records from the target website.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement scrape()")
