"""
Chrome WebDriver factory.

Creates a headless Chrome instance with anti-detection tweaks and a
persistent user profile so Amazon sees a "returning visitor".
"""

import logging
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

from scraper.settings import PROFILE_DIR, CHROME_BINARY

logger = logging.getLogger(__name__)


def create_driver() -> webdriver.Chrome:
    """Create and return a configured Chrome WebDriver."""

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    options = ChromeOptions()

    # Chrome binary ---------------------------------------------------------
    if os.path.exists(CHROME_BINARY):
        options.binary_location = CHROME_BINARY

    # Persistent profile (looks like a returning user) ----------------------
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")

    # Anti-automation flags -------------------------------------------------
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Headless mode ---------------------------------------------------------
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")

    # Stability -------------------------------------------------------------
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    logger.info("Creating Chrome driver …")
    driver = webdriver.Chrome(options=options)

    # Remove the webdriver navigator flag -----------------------------------
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        },
    )

    driver.set_page_load_timeout(60)
    driver.implicitly_wait(10)

    logger.info("Driver created successfully.")
    return driver
