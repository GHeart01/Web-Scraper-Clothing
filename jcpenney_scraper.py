"""
JCPenney Dockers Product Scraper
Scrapes product names, prices, and availability from JCPenney
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import Dict, Optional
import time
from urllib.parse import urlencode  # FIX 4: proper query string encoding

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
    'Cache-Control': 'max-age=0',
}


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


def scrape_jcpenney_product(url: str) -> Dict:
    """
    Scrape a single JCPenney product page.

    Args:
        url: JCPenney product URL

    Returns:
        Dictionary with product info
    """
    logger.info(f"Scraping JCPenney: {url}")

    result = {
        'retailer': 'JCPenney',
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
        for selector in ['h1', 'h1.productTitle', '[data-testid="product-title"]', '.product-name']:
            tag = soup.select_one(selector)
            if tag:
                name = tag.get_text(strip=True)
                if name and len(name) > 5:
                    break

        result['name'] = name or 'Unknown'

        # Try multiple selectors for price
        price = None
        for selector in ['.selling-price', '[data-testid="selling-price"]', '.price', '.productPrice']:
            tag = soup.select_one(selector)
            if tag:
                price_text = tag.get_text(strip=True)
                price = extract_price(price_text)
                if price:
                    break

        result['price'] = price

        # Try to find original price
        original_price = None
        for selector in ['.original-price', '.was-price', '[data-testid="original-price"]']:
            tag = soup.select_one(selector)
            if tag:
                price_text = tag.get_text(strip=True)
                original_price = extract_price(price_text)
                if original_price:
                    break

        result['original_price'] = original_price

        # FIX 1: Scope availability check to a targeted element instead of
        # searching the entire page text, which caused false positives.
        availability = 'Check Site'
        for selector in ['[data-testid="availability"]', '.availability', '#availability']:
            avail_tag = soup.select_one(selector)
            if avail_tag:
                avail_text = avail_tag.get_text(strip=True).lower()
                if 'in stock' in avail_text:
                    availability = 'In Stock'
                elif 'out of stock' in avail_text or 'unavailable' in avail_text:
                    availability = 'Out of Stock'
                break

        result['availability'] = availability

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


def search_jcpenney_dockers(search_term: str = "Dockers Khakis") -> list:
    """
    Search JCPenney for Dockers products.

    Args:
        search_term: Search query

    Returns:
        List of product dictionaries
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Searching JCPenney for: {search_term}")
    logger.info(f"{'='*80}\n")

    products = []

    try:
        # FIX 4: Use urlencode for safe query string construction instead of
        # manual .replace(' ', '+'), which fails on special characters.
        search_url = f"https://www.jcpenney.com/search?{urlencode({'q': search_term})}"
        logger.info(f"Search URL: {search_url}\n")

        response = requests.get(search_url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # FIX 2: Collect links into a set to prevent duplicates when both
        # selectors match, then convert back to a list for iteration.
        product_links = set()

        for link in soup.find_all('a', {'data-testid': 'productCardLink'}):
            if link.get('href'):
                href = link['href']
                if not href.startswith('http'):
                    href = 'https://www.jcpenney.com' + href
                product_links.add(href)

        # Fallback selector if data-testid approach yields nothing
        if not product_links:
            for link in soup.find_all('a', class_='productCardLink'):
                if link.get('href'):
                    href = link['href']
                    if not href.startswith('http'):
                        href = 'https://www.jcpenney.com' + href
                    product_links.add(href)

        product_links = list(product_links)
        logger.info(f"Found {len(product_links)} products")

        # Scrape each product (limit to first 3)
        for i, link in enumerate(product_links[:3], 1):
            logger.info(f"\nProduct {i}/{min(3, len(product_links))}")
            product = scrape_jcpenney_product(link)
            products.append(product)
            time.sleep(2)  # 2-second delay between requests

    except Exception as e:
        logger.error(f"Search error: {e}")

    return products


if __name__ == "__main__":
    results = search_jcpenney_dockers("Dockers Khakis")

    print(f"\n{'='*80}")
    print(f"JCPENNEY RESULTS - {len(results)} Products Found")
    print(f"{'='*80}\n")

    for i, product in enumerate(results, 1):
        print(f"{i}. {product['name']}")
        print(f"   Price:        ${product['price']}")
        print(f"   Orig. Price:  ${product['original_price']}")  # FIX 3: was missing
        print(f"   Availability: {product['availability']}")
        print(f"   URL:          {product['url']}")
        if product['error']:
            print(f"   Error:        {product['error']}")
        print()