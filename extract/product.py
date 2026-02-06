"""
Product-level extractors - title, price, about-this-item bullets.

Each function takes a BeautifulSoup object and returns the extracted value.
"""

import re


def get_product_title(soup):
    """Pull the product title from <span id="productTitle">."""
    tag = soup.find("span", id="productTitle")
    if tag:
        return tag.get_text(strip=True)
    return None


def get_price(soup):
    """Pull the price from <span class="a-price-whole">."""
    tag = soup.find("span", class_="a-price-whole")
    if tag:
        # remove trailing dot that amazon sometimes adds
        return tag.get_text(strip=True).rstrip(".")
    return None


def get_about_items(soup):
    """
    Extract the 'About this item' bullet points.

    Tries two approaches:
      1. Find the heading 'About this item' then grab its next <ul>
      2. Fallback: look for the feature-bullets container
    """
    bullets = []

    # approach 1: heading-based lookup
    heading = soup.find("h3", string=re.compile(r"About this item", re.IGNORECASE))
    if heading:
        ul = heading.find_next("ul", class_=re.compile(r"a-unordered-list"))
        if ul:
            bullets = _extract_list_items(ul)

    # approach 2: feature-bullets div
    if not bullets:
        container = soup.find("div", id="feature-bullets")
        if container:
            ul = container.find("ul")
            if ul:
                bullets = _extract_list_items(ul)

    # approach 3: direct class match on the <ul>
    if not bullets:
        ul = soup.find("ul", class_="a-unordered-list a-vertical a-spacing-small")
        if ul:
            bullets = _extract_list_items(ul)

    return bullets


def _extract_list_items(ul_tag):
    """Helper - pull text from each <li> inside a <ul>."""
    items = []
    for li in ul_tag.find_all("li"):
        span = li.find("span", class_="a-list-item")
        if span:
            text = span.get_text(strip=True)
            if text:
                items.append(text)
    return items
