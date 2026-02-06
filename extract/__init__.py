"""
Amazon product data extractor package.

Parses saved HTML files and pulls out product info + reviews.
"""

from extract.product import get_product_title, get_price, get_about_items
from extract.reviews import get_reviews
from extract.loader import load_html, split_pages
