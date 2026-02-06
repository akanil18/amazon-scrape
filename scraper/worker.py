"""
Core scraper logic — the AmazonHTMLScraper orchestrator.

Coordinates the driver, human-like actions, block detection, and HTML
extraction into a single high-level workflow.
"""

import logging
import re
import time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from scraper.settings import (
    OUTPUT_DIR,
    PAGE_LOAD_WAIT,
    ACTION_WAIT,
    AFTER_CLICK_WAIT,
    MAX_REVIEW_PAGES,
    SEE_MORE_REVIEWS_XPATH,
    SEE_MORE_REVIEWS_CSS,
    NEXT_PAGE_XPATH,
    NEXT_PAGE_FALLBACKS,
)
from scraper.driver import create_driver
from scraper.actions import random_wait, human_scroll
from scraper.detection import check_for_blocks
from scraper.extractor import save_html_to_single_file

logger = logging.getLogger(__name__)


class AmazonHTMLScraper:
    """Scrape an Amazon product page and all its review pages into one HTML file."""

    def __init__(self) -> None:
        self.driver = None
        self.output_file = None
        self.total_pages: int = 0
        self.total_bytes: int = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """Launch the browser and prepare the output file."""
        logger.info("=" * 60)
        logger.info("AMAZON HTML SCRAPER")
        logger.info("=" * 60)

        self.driver = create_driver()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = OUTPUT_DIR / f"amazon_scrape_{timestamp}.html"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, "w", encoding="utf-8") as fh:
            fh.write(f"<!-- Amazon HTML Scrape Started: {datetime.now()} -->\n")

        logger.info("Output file: %s", self.output_file)
        return True

    def stop(self, reason: str = "Complete") -> None:
        """Shut down the browser and log a summary."""
        logger.info("=" * 60)
        logger.info("STOPPING: %s", reason)
        logger.info("=" * 60)
        logger.info("Output file : %s", self.output_file)
        logger.info("Total pages : %d", self.total_pages)
        logger.info("Total size  : %s bytes", f"{self.total_bytes:,}")

        if self.driver:
            self.driver.quit()
            self.driver = None

        logger.info("Browser closed.")

    # ------------------------------------------------------------------
    # Main workflow
    # ------------------------------------------------------------------

    def scrape_product_to_reviews(self, product_url: str) -> bool:
        """
        End-to-end workflow:

        1. Load product page and save its HTML.
        2. Scroll to "See more reviews" and navigate there.
        3. Loop through review pages (scroll → save → next) until done.

        Returns *True* on success.
        """

        # --- Step 1: Product page -----------------------------------------
        logger.info("STEP 1: LOAD PRODUCT PAGE")
        logger.info("URL: %s", product_url[:80])

        try:
            self.driver.get(product_url)
        except TimeoutException:
            logger.error("Page load timeout.")
            return False

        random_wait(PAGE_LOAD_WAIT[0], PAGE_LOAD_WAIT[1], "page load")

        is_blocked, reason = check_for_blocks(self.driver)
        if is_blocked:
            logger.warning("BLOCKED: %s", reason)
            return False

        logger.info("Saving product page HTML …")
        size = save_html_to_single_file(self.driver, self.output_file, "product_page")
        self.total_pages += 1
        self.total_bytes += size

        # --- Step 2: Find "See more reviews" ------------------------------
        logger.info("STEP 2: SCROLL TO FIND 'SEE MORE REVIEWS'")

        see_more = human_scroll(
            self.driver,
            target_xpath=SEE_MORE_REVIEWS_XPATH,
            stop_on_find=True,
        )

        if not see_more:
            try:
                see_more = self.driver.find_element(By.CSS_SELECTOR, SEE_MORE_REVIEWS_CSS)
            except NoSuchElementException:
                logger.error("'See more reviews' link not found.")
                return False

        href = see_more.get_attribute("href")
        logger.info("Found link href: %s", href[:70] if href else href)

        random_wait(ACTION_WAIT[0], ACTION_WAIT[1], "before navigation")

        # --- Step 3: Navigate to reviews page 1 ---------------------------
        logger.info("STEP 3: NAVIGATE TO REVIEWS PAGE 1")

        if href.startswith("/"):
            href = "https://www.amazon.in" + href

        self.driver.get(href)
        random_wait(AFTER_CLICK_WAIT[0], AFTER_CLICK_WAIT[1], "reviews page load")

        is_blocked, reason = check_for_blocks(self.driver)
        if is_blocked:
            logger.warning("BLOCKED: %s", reason)
            return False

        asin_match = re.search(r"/product-reviews/([A-Z0-9]{10})", self.driver.current_url)
        asin = asin_match.group(1) if asin_match else "UNKNOWN"
        logger.info("Detected ASIN: %s", asin)

        # --- Step 4: Scroll reviews page 1 --------------------------------
        logger.info("STEP 4: SCROLL REVIEWS PAGE 1")
        human_scroll(self.driver, target_xpath=None, stop_on_find=False)

        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        logger.info("Saving reviews page 1 HTML …")
        size = save_html_to_single_file(self.driver, self.output_file, "reviews_page_1")
        self.total_pages += 1
        self.total_bytes += size

        # --- Pagination loop ----------------------------------------------
        page_number = 1

        while page_number < MAX_REVIEW_PAGES:
            logger.info("PROCESSING REVIEWS PAGE %d", page_number)

            # A – scroll down
            next_el = human_scroll(
                self.driver,
                target_xpath=NEXT_PAGE_XPATH,
                stop_on_find=True,
            )

            # B – fallback selectors
            if not next_el:
                next_el = self._find_next_page_button()

            # C – reached last page?
            if not next_el:
                logger.info("No 'Next page' button — reached last page.")
                break

            if self._is_blocked_or_redirected():
                break

            self._log_review_count(page_number)

            # D – scroll to button & click
            next_href = self._click_next_page(next_el)
            if next_href is None:
                break

            # E – wait for next page
            random_wait(AFTER_CLICK_WAIT[0], AFTER_CLICK_WAIT[1], "page load")

            current_url = self.driver.current_url
            if current_url == next_href:
                logger.warning("URL unchanged after click.")
                time.sleep(3)
                if self.driver.current_url == next_href:
                    logger.warning("Page did not change — stopping.")
                    break

            page_number += 1
            logger.info("Current URL: %s", self.driver.current_url[:80])

            if self._looks_like_last_page():
                break

            # F – save HTML
            size = save_html_to_single_file(
                self.driver, self.output_file, f"reviews_page_{page_number}"
            )
            self.total_pages += 1
            self.total_bytes += size
            logger.info("Page %d complete.", page_number)

        # --- Done ---------------------------------------------------------
        logger.info("SCRAPING COMPLETE — %d pages, %s bytes",
                     self.total_pages, f"{self.total_bytes:,}")
        return True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_next_page_button(self):
        """Try every fallback selector for the 'Next page' link."""
        logger.debug("Looking for 'Next page' button (fallbacks) …")
        for kind, selector in NEXT_PAGE_FALLBACKS:
            try:
                if kind == "xpath":
                    el = self.driver.find_element(By.XPATH, selector)
                else:
                    el = self.driver.find_element(By.CSS_SELECTOR, selector)
                if el and el.is_displayed():
                    logger.debug("Found via %s: %s", kind, selector)
                    return el
            except NoSuchElementException:
                continue
        return None

    def _is_blocked_or_redirected(self) -> bool:
        url = self.driver.current_url
        if "/errors/validateCaptcha" in url or "captcha" in url.lower():
            logger.warning("CAPTCHA detected — stopping.")
            return True
        if "/ap/signin" in url:
            logger.warning("Login redirect — stopping.")
            return True
        return False

    def _log_review_count(self, page_number: int) -> None:
        try:
            reviews = self.driver.find_elements(By.CSS_SELECTOR, "div[data-hook='review']")
            if not reviews:
                reviews = self.driver.find_elements(By.CSS_SELECTOR, "[data-hook='review-body']")
            if reviews:
                logger.info("Found %d reviews on page %d.", len(reviews), page_number)
        except Exception as exc:
            logger.debug("Could not count reviews: %s", exc)

    def _click_next_page(self, element) -> str | None:
        """Scroll to *element*, click it, and return the pre-click URL (or *None* on failure)."""
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior:'smooth', block:'center'});",
                element,
            )
            time.sleep(1)
        except Exception as exc:
            logger.debug("Could not scroll to button: %s", exc)

        random_wait(ACTION_WAIT[0], ACTION_WAIT[1], "before clicking Next")

        pre_click_url = self.driver.current_url
        next_href = element.get_attribute("href")
        logger.info("Next page href: %s", (next_href or "")[:70])

        try:
            self.driver.execute_script("arguments[0].click();", element)
        except Exception:
            try:
                element.click()
            except Exception:
                if next_href:
                    logger.info("Click failed — navigating to href directly.")
                    self.driver.get(next_href)
                else:
                    logger.error("Cannot click 'Next page' — stopping.")
                    return None

        return pre_click_url

    def _looks_like_last_page(self) -> bool:
        source = self.driver.page_source.lower()
        if "there are no customer reviews" in source or "no reviews" in source[:5000]:
            logger.info("'No reviews' message — last page reached.")
            return True
        try:
            title = self.driver.title.lower()
            if "page not found" in title or "404" in title:
                logger.info("404 detected — last page reached.")
                return True
        except Exception:
            pass
        return False
