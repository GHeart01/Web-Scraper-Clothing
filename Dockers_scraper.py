"""
Dockers Signature Iron Free Khakis Scraper
Extracts product data from a specific Dockers product page
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
from typing import Dict, Optional
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Product URL
PRODUCT_URL = "https://us.dockers.com/products/signature-iron-free-khakis-classic-fit-with-stain-defender-a31590022"

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


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
        logger.warning(f"Could not parse price: {price_text} - {e}")
        return None


def scrape_product() -> Optional[Dict]:
    """
    Scrape Dockers Signature Iron Free Khakis product data.
    
    Returns:
        Dictionary with product data or None if scraping fails
    """
    try:
        logger.info(f"Fetching: {PRODUCT_URL}")
        response = requests.get(PRODUCT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract product name
        name_elem = soup.select_one('h1.product-form_title')
        name = name_elem.text.strip() if name_elem else "Signature Iron Free Khakis"
        logger.info(f"Product: {name}")
        
        # Extract subtitle/description
        subtitle_elem = soup.select_one('p.product-form_subtitle')
        subtitle = subtitle_elem.text.strip() if subtitle_elem else None
        
        # Extract current price - look for price within the price elements container
        current_price = None
        original_price = None
        
        # Find the price container
        price_container = soup.select_one('div[js-product-form="priceElements"]')
        if price_container:
            # Look for current/sale price
            price_spans = price_container.find_all('span')
            for span in price_spans:
                price_text = span.text.strip()
                if price_text.startswith('$'):
                    # First price found is usually the current price
                    if not current_price:
                        current_price = extract_price(price_text)
                    # Second price might be original
                    elif not original_price and original_price != current_price:
                        original_price = extract_price(price_text)
        
        # Alternative: look for meta tags with price info
        if not current_price:
            price_meta = soup.select_one('meta[itemprop="price"]')
            if price_meta:
                current_price = extract_price(price_meta.get('content', ''))
        
        # Extract availability
        availability = "In Stock"
        
        # Check for out of stock button or text
        oos_button = soup.select_one('button:contains("Out of Stock"), [class*="out-of-stock"]')
        if oos_button:
            availability = "Out of Stock"
        
        # Try to find availability meta tag
        availability_meta = soup.select_one('meta[itemprop="availability"]')
        if availability_meta:
            availability_url = availability_meta.get('content', '')
            if 'OutOfStock' in availability_url:
                availability = "Out of Stock"
            elif 'InStock' in availability_url:
                availability = "In Stock"
        
        logger.info(f"Current Price: ${current_price}")
        if original_price:
            logger.info(f"Original Price: ${original_price}")
        logger.info(f"Availability: {availability}")
        
        # Build product dictionary
        product_data = {
            'name': name,
            'subtitle': subtitle,
            'current_price': current_price,
            'original_price': original_price,
            'discount_percentage': None,
            'url': PRODUCT_URL,
            'availability': availability,
            'is_on_sale': original_price is not None and current_price is not None and current_price < original_price
        }
        
        # Calculate discount percentage if on sale
        if product_data['is_on_sale']:
            discount = ((original_price - current_price) / original_price) * 100
            product_data['discount_percentage'] = round(discount, 2)
            logger.info(f"Discount: {product_data['discount_percentage']}%")
        
        return product_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching product: {e}")
        return None
    except Exception as e:
        logger.error(f"Error scraping product: {e}")
        return None


def save_results(product_data: Dict, filename: str = "dockers_product.json") -> None:
    """
    Save scraped product to JSON file.
    
    Args:
        product_data: Product dictionary
        filename: Output filename
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(product_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {filename}")
    except IOError as e:
        logger.error(f"Error saving results: {e}")


def print_product(product: Dict) -> None:
    """
    Print product data in formatted way.
    
    Args:
        product: Product dictionary
    """
    if not product:
        print("No product data to display")
        return
    
    print(f"\n{'='*60}")
    print(f"DOCKERS SIGNATURE IRON FREE KHAKIS")
    print(f"{'='*60}\n")
    
    print(f"Product: {product['name']}")
    if product['subtitle']:
        print(f"Details: {product['subtitle']}")
    print(f"\nPrice Information:")
    print(f"  Current Price: ${product['current_price']}" if product['current_price'] else "  Current Price: N/A")
    print(f"  Original Price: ${product['original_price']}" if product['original_price'] else "  Original Price: N/A")
    if product['discount_percentage']:
        print(f"  Discount: {product['discount_percentage']}% OFF")
    print(f"\nAvailability: {product['availability']}")
    print(f"URL: {product['url']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    logger.info("Starting Dockers product scraper...")
    product = scrape_product()
    
    if product:
        print_product(product)
        save_results(product)
    else:
        logger.error("Failed to scrape product")
