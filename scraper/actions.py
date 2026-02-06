"""
Human-like browser actions — scrolling, random waits, viewport checks.
"""

import logging
import random
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException

from scraper.settings import SCROLL_STEP, SCROLL_PAUSE

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def random_wait(min_sec: float, max_sec: float, reason: str = "") -> None:
    """Sleep for a random duration between *min_sec* and *max_sec*."""
    wait_time = random.uniform(min_sec, max_sec)
    if reason:
        logger.debug("Waiting %.1fs (%s) …", wait_time, reason)
    time.sleep(wait_time)


def is_element_in_viewport(driver: WebDriver, element: WebElement) -> bool:
    """Return *True* when *element* is inside the current viewport."""
    try:
        return driver.execute_script(
            """
            var elem = arguments[0];
            var rect = elem.getBoundingClientRect();
            var wh   = window.innerHeight || document.documentElement.clientHeight;
            return (rect.top >= 0 && rect.top <= wh);
            """,
            element,
        )
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Scrolling
# ---------------------------------------------------------------------------

def human_scroll(
    driver: WebDriver,
    target_xpath: str | None = None,
    stop_on_find: bool = True,
) -> WebElement | None:
    """
    Scroll the page like a human would.

    Parameters
    ----------
    driver : WebDriver
        Active browser session.
    target_xpath : str, optional
        XPath of an element to search for while scrolling.
    stop_on_find : bool
        If *True*, stop scrolling as soon as *target_xpath* is found in the
        viewport.

    Returns
    -------
    WebElement or None
        The found element, or *None* if it was never encountered.
    """
    logger.info("Starting human-like scrolling …")

    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")
    current_pos = 0
    scroll_count = 0
    found_element: WebElement | None = None

    while current_pos < total_height - viewport_height:
        scroll_count += 1

        # Random scroll amount
        scroll_amount = random.randint(SCROLL_STEP[0], SCROLL_STEP[1])
        current_pos += scroll_amount

        # Smooth scroll
        driver.execute_script(
            f"window.scrollTo({{top: {current_pos}, behavior: 'smooth'}});"
        )

        # Reading pause
        time.sleep(random.uniform(SCROLL_PAUSE[0], SCROLL_PAUSE[1]))

        progress = min(100, int((current_pos / total_height) * 100))
        logger.debug(
            "Scroll %d: %dpx / %dpx (%d%%)",
            scroll_count, current_pos, total_height, progress,
        )

        # Check for target element
        if target_xpath and stop_on_find:
            try:
                element = driver.find_element(By.XPATH, target_xpath)
                if is_element_in_viewport(driver, element):
                    logger.info("Target element found in viewport.")
                    found_element = element
                    break
            except NoSuchElementException:
                pass

        # Occasional tiny scroll-back (human behaviour)
        if random.random() < 0.1:
            back = random.randint(30, 80)
            current_pos = max(0, current_pos - back)
            driver.execute_script(f"window.scrollTo(0, {current_pos});")
            time.sleep(0.3)

        # Page might lazy-load more content
        total_height = driver.execute_script("return document.body.scrollHeight")

    logger.info("Scrolling complete — %d scroll ticks.", scroll_count)
    return found_element
