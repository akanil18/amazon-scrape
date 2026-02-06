"""
Block / CAPTCHA detection helpers.
"""

import logging

from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)

# Strings that indicate Amazon is showing a CAPTCHA challenge
_CAPTCHA_INDICATORS = [
    "enter the characters you see below",
    "type the characters you see",
    "sorry, we just need to make sure you're not a robot",
]


def check_for_blocks(driver: WebDriver) -> tuple[bool, str | None]:
    """
    Inspect the current page for signs of blocking.

    Returns
    -------
    (is_blocked, reason) : tuple[bool, str | None]
        *is_blocked* is ``True`` when the page looks like a login redirect,
        CAPTCHA challenge, or suspiciously small stub.
    """
    url = driver.current_url.lower()

    # Login / register redirect
    if "/ap/signin" in url or "/ap/register" in url:
        return True, "Login redirect detected"

    # CAPTCHA URL
    if "captcha" in url:
        return True, "CAPTCHA URL detected"

    try:
        source = driver.page_source.lower()

        for indicator in _CAPTCHA_INDICATORS:
            if indicator in source:
                return True, f"CAPTCHA detected: {indicator}"

        if len(source) < 5_000:
            return True, f"Page suspiciously small: {len(source)} bytes"

    except Exception as exc:
        return True, f"Error reading page: {exc}"

    return False, None
