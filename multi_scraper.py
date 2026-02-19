"""
Dockers Multi-Product Scraper
Scrapes multiple Dockers product URLs and stores results
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

RATE_LIMIT_DELAY = 2  # seconds between requests


def extract_price(price_text: str) -> Optional[float]:
    """
    Extract numeric price from text.
    
    Args:
        price_text: Price text (e.g., "$49.99")
        
    Returns:
        Float price or None if extraction fails
    """
    try:
        cleaned = price_text.strip().replace('$', '').replace(',', '')
        return float(cleaned)
    except (ValueError, AttributeError) as e:
        logger.warning(f"Could not parse price: {price_text}")
        return None


def scrape_product(product_url: str) -> Optional[Dict]:
    """
    Scrape a single Dockers product.
    
    Args:
        product_url: URL of the product
        
    Returns:
        Dictionary with product data or None if scraping fails
    """
    try:
        logger.info(f"Scraping: {product_url}")
        response = requests.get(product_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract product name
        name_elem = soup.select_one('h1.product-form_title')
        name = name_elem.text.strip() if name_elem else None
        
        if not name:
            logger.warning(f"Could not extract name from {product_url}")
            return None
        
        logger.info(f"Product: {name}")
        
        # Extract subtitle/description
        subtitle_elem = soup.select_one('p.product-form_subtitle')
        subtitle = subtitle_elem.text.strip() if subtitle_elem else None
        
        # Extract current price and original price
        current_price = None
        original_price = None
        
        price_container = soup.select_one('div[js-product-form="priceElements"]')
        if price_container:
            price_spans = price_container.find_all('span')
            for span in price_spans:
                price_text = span.text.strip()
                if price_text.startswith('$'):
                    if not current_price:
                        current_price = extract_price(price_text)
                    elif not original_price and original_price != current_price:
                        original_price = extract_price(price_text)
        
        # Fallback to meta tags
        if not current_price:
            price_meta = soup.select_one('meta[itemprop="price"]')
            if price_meta:
                current_price = extract_price(price_meta.get('content', ''))
        
        # Extract availability
        availability = "In Stock"
        
        oos_button = soup.select_one('button:contains("Out of Stock"), [class*="out-of-stock"]')
        if oos_button:
            availability = "Out of Stock"
        
        availability_meta = soup.select_one('meta[itemprop="availability"]')
        if availability_meta:
            availability_url = availability_meta.get('content', '')
            if 'OutOfStock' in availability_url:
                availability = "Out of Stock"
            elif 'InStock' in availability_url:
                availability = "In Stock"
        
        # Build product dictionary
        product_data = {
            'name': name,
            'subtitle': subtitle,
            'current_price': current_price,
            'original_price': original_price,
            'discount_percentage': None,
            'url': product_url,
            'availability': availability,
            'is_on_sale': original_price is not None and current_price is not None and current_price < original_price
        }
        
        # Calculate discount percentage if on sale
        if product_data['is_on_sale']:
            discount = ((original_price - current_price) / original_price) * 100
            product_data['discount_percentage'] = round(discount, 2)
        
        logger.info(f"✓ Successfully scraped: {name}")
        return product_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {product_url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error scraping {product_url}: {e}")
        return None


def scrape_multiple_products(product_urls: List[str]) -> List[Dict]:
    """
    Scrape multiple Dockers products with rate limiting.
    
    Args:
        product_urls: List of product URLs
        
    Returns:
        List of product dictionaries
    """
    products = []
    
    for i, url in enumerate(product_urls):
        # Rate limiting (skip on first request)
        if i > 0:
            logger.info(f"Waiting {RATE_LIMIT_DELAY} seconds...")
            time.sleep(RATE_LIMIT_DELAY)
        
        product = scrape_product(url)
        if product:
            products.append(product)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Scraping Complete! Total products: {len(products)}/{len(product_urls)}")
    logger.info(f"{'='*60}\n")
    
    return products


def save_results(products: List[Dict], filename: str = "dockers_products.json") -> None:
    """
    Save scraped products to JSON file.
    
    Args:
        products: List of product dictionaries
        filename: Output filename
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {filename}")
    except IOError as e:
        logger.error(f"Error saving results: {e}")


def print_products(products: List[Dict]) -> None:
    """
    Print all products in formatted way.
    
    Args:
        products: List of product dictionaries
    """
    if not products:
        print("No products to display")
        return
    
    print(f"\n{'='*80}")
    print(f"DOCKERS PRODUCTS ({len(products)})")
    print(f"{'='*80}\n")
    
    for i, product in enumerate(products, 1):
        print(f"{i}. {product['name']}")
        if product['subtitle']:
            print(f"   Details: {product['subtitle']}")
        print(f"   Current Price: ${product['current_price']}" if product['current_price'] else "   Current Price: N/A")
        print(f"   Original Price: ${product['original_price']}" if product['original_price'] else "   Original Price: N/A")
        if product['discount_percentage']:
            print(f"   Discount: {product['discount_percentage']}% OFF")
        print(f"   Availability: {product['availability']}")
        print(f"   URL: {product['url']}")
        print()


if __name__ == "__main__":
    # List of Dockers product URLs to scrape
    PRODUCT_URLS = [
        "https://us.dockers.com/products/signature-iron-free-khakis-classic-fit-with-stain-defender-a31590022",
        # Add more URLs here:
        # "https://us.dockers.com/products/...",
        # "https://us.dockers.com/products/...",
    ]
    
    logger.info("Starting multi-product scraper...")
    products = scrape_multiple_products(PRODUCT_URLS)
    
    if products:
        print_products(products)
        save_results(products)
    else:
        logger.error("Failed to scrape any products")
