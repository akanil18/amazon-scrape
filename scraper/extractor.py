"""
HTML extraction — append each page's source to a single output file.
"""

import logging
from datetime import datetime
from pathlib import Path

from selenium.webdriver.remote.webdriver import WebDriver

from scraper.settings import OUTPUT_DIR

logger = logging.getLogger(__name__)


def save_html_to_single_file(
    driver: WebDriver,
    output_file: Path,
    page_label: str,
) -> int:
    """
    Append the current page's HTML to *output_file* with a metadata separator.

    Returns the number of bytes written.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    html = driver.page_source
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_url = driver.current_url

    separator = (
        f"\n\n{'=' * 80}\n"
        f"PAGE: {page_label}\n"
        f"URL: {current_url}\n"
        f"TIMESTAMP: {timestamp}\n"
        f"SIZE: {len(html):,} bytes\n"
        f"{'=' * 80}\n\n"
    )

    with open(output_file, "a", encoding="utf-8") as fh:
        fh.write(separator)
        fh.write(html)

    logger.info("HTML appended  %-25s  %s bytes", page_label, f"{len(html):,}")
    return len(html)
