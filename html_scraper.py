"""
Entry point — Amazon HTML Scraper.

Usage:
    python html_scraper.py
"""

import logging
import sys

from scraper.settings import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL
from scraper import AmazonHTMLScraper

# Configure root logger
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
)

logger = logging.getLogger(__name__)

# Product URL to scrape
PRODUCT_URL = (
    "https://www.amazon.in/XYXX-Regular-T-Shirt-XY_CR14_Polo-Tshirt_1_Rose/"
    "dp/B0CZL992QG/ref=sr_1_3_sspa?sr=8-3-spons&aref=UFwc6Y2wRZ"
    "&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&psc=1"
)


def main() -> None:
    """Run the scraper."""
    scraper = AmazonHTMLScraper()

    try:
        if not scraper.start():
            sys.exit(1)

        success = scraper.scrape_product_to_reviews(PRODUCT_URL)
        scraper.stop("Completed successfully" if success else "Failed or blocked")
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        scraper.stop("User interrupt")
        sys.exit(130)

    except Exception as exc:
        logger.exception("Fatal error: %s", exc)
        scraper.stop(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
