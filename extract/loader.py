"""
HTML loader - reads saved HTML files and splits them into pages.

The html_scraper.py saves multiple pages (product + reviews) into one file
separated by metadata headers. This module handles that splitting.
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup

# pattern that separates each page section in the combined HTML file
PAGE_HEADER = re.compile(
    r"={80}\nPAGE:\s*(.+?)\nURL:\s*(.+?)\nTIMESTAMP:\s*(.+?)\nSIZE:\s*(.+?)\n={80}"
)


def load_html(filepath):
    """Read the raw HTML file content."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"HTML file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_pages(raw_content):
    """
    Split a combined HTML file into individual page sections.

    Returns list of dicts: [{label, url, timestamp, soup}, ...]
    Each 'soup' is a ready-to-use BeautifulSoup object.
    """
    pages = []
    separators = list(PAGE_HEADER.finditer(raw_content))

    # no separators → treat the whole file as one page
    if not separators:
        soup = BeautifulSoup(raw_content, "lxml")
        pages.append({
            "label": "full_file",
            "url": "",
            "timestamp": "",
            "soup": soup,
        })
        return pages

    for i, match in enumerate(separators):
        label = match.group(1).strip()
        url = match.group(2).strip()
        timestamp = match.group(3).strip()

        # grab the html between this header and the next one
        start = match.end()
        end = separators[i + 1].start() if i + 1 < len(separators) else len(raw_content)
        html = raw_content[start:end].strip()

        soup = BeautifulSoup(html, "lxml")
        pages.append({
            "label": label,
            "url": url,
            "timestamp": timestamp,
            "soup": soup,
        })

    return pages
