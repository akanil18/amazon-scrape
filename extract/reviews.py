"""
Review extractor - pulls individual review data from the HTML.

Each review on Amazon sits inside <li data-hook="review">.
We grab: profile name, rating, review tag (title), date, and body text.
"""

import re


def get_reviews(soup):
    """
    Extract all reviews from a page's soup.

    Returns a list of dicts, one per review.
    """
    reviews = []
    review_blocks = soup.find_all("li", attrs={"data-hook": "review"})

    # also check for div-based review containers (some pages use these)
    if not review_blocks:
        review_blocks = soup.find_all("div", id=re.compile(r"^customer_review-"))

    for block in review_blocks:
        review = _parse_single_review(block)
        if review:
            reviews.append(review)

    return reviews


def _parse_single_review(block):
    """Parse one review block and return a dict."""

    # profile name
    profile_tag = block.find("span", class_="a-profile-name")
    profile_name = profile_tag.get_text(strip=True) if profile_tag else ""

    # star rating (e.g. "5.0 out of 5 stars")
    rating = _extract_rating(block)

    # review tag / title
    review_tag = _extract_review_tag(block)

    # review date
    date_tag = block.find("span", attrs={"data-hook": "review-date"})
    review_date = date_tag.get_text(strip=True) if date_tag else ""

    # review body text
    review_text = _extract_review_text(block)

    return {
        "profile_name": profile_name,
        "rating": rating,
        "review_tag": review_tag,
        "review_date": review_date,
        "review_text": review_text,
    }


def _extract_rating(block):
    """Pull the numeric rating from the star icon."""
    star_tag = block.find("i", attrs={"data-hook": "review-star-rating"})
    if star_tag:
        alt = star_tag.find("span", class_="a-icon-alt")
        if alt:
            text = alt.get_text(strip=True)
            match = re.search(r"([\d.]+)\s*out of", text)
            return match.group(1) if match else text
    return None


def _extract_review_tag(block):
    """Pull the review title/tag text (the bold headline)."""
    title_link = block.find("a", attrs={"data-hook": "review-title"})
    if title_link:
        # skip the star-rating span, grab the actual title span
        for span in title_link.find_all("span"):
            classes = span.get("class") or []
            if "a-icon-alt" not in classes:
                text = span.get_text(strip=True)
                if text:
                    return text
    return ""


def _extract_review_text(block):
    """Pull the main review body text."""
    body_tag = block.find("span", attrs={"data-hook": "review-body"})
    if body_tag:
        # prefer the inner content div
        inner = body_tag.find("div", class_=re.compile("review-text-content"))
        if inner:
            return inner.get_text(strip=True)
        return body_tag.get_text(strip=True)
    return ""
