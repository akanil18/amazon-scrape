"""
Centralised configuration for the Amazon HTML scraper.

All tuneable knobs — paths, timing, selectors, logging — live here so that
every other module can just ``from scraper.settings import …``.
"""

import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent   # project root
PROFILE_DIR = BASE_DIR / "profiles" / "amazon_home"
OUTPUT_DIR = BASE_DIR / "data" / "html"
CHROME_BINARY = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

# ---------------------------------------------------------------------------
# Timing (seconds) — kept fast but human-looking
# ---------------------------------------------------------------------------
PAGE_LOAD_WAIT = (5, 10)       # after a page load
SCROLL_STEP = (300, 500)       # pixels per scroll tick
SCROLL_PAUSE = (0.3, 0.8)     # pause between scroll ticks
ACTION_WAIT = (2, 4)           # before clicking a link
AFTER_CLICK_WAIT = (5, 10)    # after clicking a link

# ---------------------------------------------------------------------------
# Selectors
# ---------------------------------------------------------------------------
SEE_MORE_REVIEWS_XPATH = "//a[@data-hook='see-all-reviews-link-foot']"
SEE_MORE_REVIEWS_CSS = "a[data-hook='see-all-reviews-link-foot']"

NEXT_PAGE_XPATH = "//a[contains(text(), 'Next page')]"
NEXT_PAGE_CSS = "li.a-last a"

# Fallback selectors tried when the primary ones miss
NEXT_PAGE_FALLBACKS: list[tuple[str, str]] = [
    ("xpath", "//li[@class='a-last']/a"),
    ("xpath", "//a[contains(text(), 'Next page')]"),
    ("xpath", "//a[contains(@href, 'pageNumber')]//span[contains(text(), 'Next')]"),
    ("xpath", "//a[contains(text(), 'Next')]"),
    ("css", "li.a-last a"),
    ("css", ".a-pagination .a-last a"),
    ("css", "a[href*='pageNumber'][class*='a-last']"),
]

# ---------------------------------------------------------------------------
# Limits
# ---------------------------------------------------------------------------
MAX_REVIEW_PAGES = 500
