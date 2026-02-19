"""
Amazon Dockers Product Scraper
Scrapes product names, prices, and availability from Amazon
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import Dict, Optional
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Headers to mimic real browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# FIX 1: Removed unused module-level `url` variable.
# It is now passed as an argument to scrape_amazon_product() directly.
DEFAULT_PRODUCT_URL = "https://www.amazon.com/Dockers-Relaxed-Signature-Khaki-Defender/dp/B0GKHR82HN?th=1&psc=1"


def extract_price(price_text: str) -> Optional[float]:
    """Extract price from text."""
    if not price_text:
        return None
    match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
    if match:
        try:
            return float(match.group(1).replace(',', ''))
        except ValueError:
            return None
    return None


def scrape_amazon_product(url: str) -> Dict:
    """
    Scrape a single Amazon product page.

    Args:
        url: Amazon product URL (e.g., https://www.amazon.com/dp/B0XXXXX)

    Returns:
        Dictionary with product info: name, price, original_price, availability, url
    """
    logger.info(f"Scraping Amazon: {url}")

    result = {
        'retailer': 'Amazon',
        'name': None,
        'price': None,
        'original_price': None,
        'availability': 'Unknown',
        'url': url,
        'error': None
    }

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Try multiple selectors for product name
        name = None
        for selector in ['h1 span', 'span[id*="title"]', '.product-title', 'h1']:
            tag = soup.select_one(selector)
            if tag:
                name = tag.get_text(strip=True)
                if name and len(name) > 5:
                    break

        result['name'] = name or 'Unknown'

        # FIX 2: Use `span.a-offscreen` to capture the full price string (e.g. "$49.99")
        # instead of `.a-price-whole` which only returns the dollar portion (e.g. "49").
        price = None
        for selector in ['span.a-offscreen', '.a-color-price', '[data-a-color="price"]']:
            tag = soup.select_one(selector)
            if tag:
                price_text = tag.get_text(strip=True)
                price = extract_price(price_text)
                if price:
                    break

        result['price'] = price

        # Try to find original/struck-through price
        original_price = None
        for selector in ['.a-price.a-text-price span.a-offscreen', '.a-price-old']:
            tag = soup.select_one(selector)
            if tag:
                price_text = tag.get_text(strip=True)
                original_price = extract_price(price_text)
                if original_price:
                    break

        result['original_price'] = original_price

        # FIX 3: Scope the availability check to the dedicated availability element
        # instead of searching the entire page text, which caused false positives.
        avail_div = soup.select_one('#availability span')
        if avail_div:
            availability_text = avail_div.get_text(strip=True).lower()
            if 'in stock' in availability_text:
                result['availability'] = 'In Stock'
            elif 'out of stock' in availability_text or 'unavailable' in availability_text:
                result['availability'] = 'Out of Stock'
            else:
                result['availability'] = 'Check Site'
        else:
            result['availability'] = 'Check Site'

        logger.info(f"  ✓ {result['name'][:50]} - ${result['price']}")
        return result

    except requests.exceptions.HTTPError as e:
        result['error'] = f"HTTP {e.response.status_code}: {e}"
        logger.error(f"  ✗ HTTP Error: {e}")
    except requests.exceptions.Timeout:
        result['error'] = "Request Timeout"
        logger.error(f"  ✗ Request Timeout")
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"  ✗ Error: {e}")

    return result


def search_amazon_dockers(search_term: str = "Dockers Khakis") -> list:
    """
    Search Amazon for Dockers products and return top results.

    Args:
        search_term: Search query (default: "Dockers Khakis")

    Returns:
        List of product dictionaries
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Searching Amazon for: {search_term}")
    logger.info(f"{'='*80}\n")

    products = []

    try:
        search_url = f"https://www.amazon.com/s?k={search_term.replace(' ', '+')}"
        logger.info(f"Search URL: {search_url}\n")

        response = requests.get(search_url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        product_links = []

        for container in soup.find_all('div', {'data-component-type': 's-search-result'}):
            # FIX 4: Guard against None before chaining .find('a'),
            # which previously caused an AttributeError crash.
            h2 = container.find('h2', class_='s-size-mini')
            if not h2:
                continue
            link = h2.find('a')
            if link and link.get('href'):
                href = link['href']
                # Ensure we don't double-prefix already absolute URLs
                if href.startswith('http'):
                    product_links.append(href)
                else:
                    product_links.append('https://www.amazon.com' + href)

        logger.info(f"Found {len(product_links)} products")

        # Scrape each product (limit to first 3 to avoid rate limiting)
        for i, link in enumerate(product_links[:3], 1):
            logger.info(f"\nProduct {i}/{min(3, len(product_links))}")
            product = scrape_amazon_product(link)
            products.append(product)
            time.sleep(2)  # 2-second delay between requests

    except Exception as e:
        logger.error(f"Search error: {e}")

    return products


if __name__ == "__main__":
    # Scrape the default product URL directly
    print(f"\n{'='*80}")
    print("Scraping default product URL...")
    print(f"{'='*80}\n")
    single = scrape_amazon_product(DEFAULT_PRODUCT_URL)
    print(f"Name:         {single['name']}")
    print(f"Price:        ${single['price']}")
    print(f"Orig. Price:  ${single['original_price']}")
    print(f"Availability: {single['availability']}")
    if single['error']:
        print(f"Error:        {single['error']}")

    # Search for multiple Dockers products
    results = search_amazon_dockers("Dockers Khakis men")

    print(f"\n{'='*80}")
    print(f"AMAZON SEARCH RESULTS - {len(results)} Products Found")
    print(f"{'='*80}\n")

    for i, product in enumerate(results, 1):
        print(f"{i}. {product['name']}")
        print(f"   Price:        ${product['price']}")
        print(f"   Orig. Price:  ${product['original_price']}")
        print(f"   Availability: {product['availability']}")
        print(f"   URL:          {product['url']}")
        if product['error']:
            print(f"   Error:        {product['error']}")
        print()