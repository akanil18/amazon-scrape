"""
Main entry point - ties everything together.

Usage:
    python -m extract.run
    python -m extract.run path/to/file.html

Reads the latest HTML file, extracts product info + reviews,
and saves the result as JSON in data/output/.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

from extract.loader import load_html, split_pages
from extract.product import get_product_title, get_price, get_about_items
from extract.reviews import get_reviews


# paths
BASE_DIR = Path(__file__).resolve().parent.parent
HTML_DIR = BASE_DIR / "data" / "html"
OUTPUT_DIR = BASE_DIR / "data" / "output"


def extract_all(html_filepath):
    """
    Full extraction pipeline.

    1. Load & split the HTML into pages
    2. Extract product info from product page
    3. Collect reviews from all pages
    4. Return the combined result dict
    """
    raw = load_html(html_filepath)
    pages = split_pages(raw)

    print(f"[+] Loaded {len(pages)} page(s) from {Path(html_filepath).name}")

    # -- product info (from the product page) --
    product_title = None
    price = None
    about_items = []

    for page in pages:
        if page["label"] == "product_page" or page["label"] == "full_file":
            soup = page["soup"]
            product_title = get_product_title(soup)
            price = get_price(soup)
            about_items = get_about_items(soup)
            print(f"[+] Product: {product_title}")
            print(f"[+] Price: {price}")
            print(f"[+] About items: {len(about_items)} bullet(s)")
            break

    # -- reviews (from all pages that contain them) --
    all_reviews = []
    seen_ids = set()

    for page in pages:
        page_reviews = get_reviews(page["soup"])
        for r in page_reviews:
            # deduplicate by profile_name + review_tag combo
            key = (r["profile_name"], r["review_tag"])
            if key not in seen_ids:
                seen_ids.add(key)
                all_reviews.append(r)

    print(f"[+] Reviews found: {len(all_reviews)}")

    # -- build final output --
    result = {
        "product_title": product_title,
        "price": price,
        "about_this_item": about_items,
        "reviews": all_reviews,
    }

    return result


def save_json(data, output_path):
    """Write the result dict to a JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[+] Saved: {output_path}")


def main():
    """Pick the HTML file and run extraction."""

    # accept a file path as argument, or use the latest one
    if len(sys.argv) > 1:
        html_file = Path(sys.argv[1])
    else:
        files = sorted(HTML_DIR.glob("amazon_scrape_*.html"), reverse=True)
        if not files:
            print("[!] No HTML files found in data/html/. Run the scraper first.")
            return
        html_file = files[0]
        print(f"[*] Using latest file: {html_file.name}")

    # run extraction
    data = extract_all(html_file)

    # save output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"product_{timestamp}.json"
    save_json(data, output_file)

    # quick preview
    print(f"\n{'=' * 50}")
    print("EXTRACTION COMPLETE")
    print(f"{'=' * 50}")
    print(f"  Title : {data['product_title']}")
    print(f"  Price : Rs.{data['price']}")
    print(f"  Bullets: {len(data['about_this_item'])}")
    print(f"  Reviews: {len(data['reviews'])}")
    print(f"  Output : {output_file}")


if __name__ == "__main__":
    main()
