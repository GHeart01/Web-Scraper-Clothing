"""
Dockers Price Comparison Web Scraper
Extracts product data from Dockers.com with pagination and error handling
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://www.dockers.com"
PRODUCTS_ENDPOINT = "/en/shop/mens/pants"
RATE_LIMIT_DELAY = 2  # seconds between requests
REQUEST_TIMEOUT = 10  # seconds

# Headers to mimic browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def fetch_page(url: str) -> Optional[BeautifulSoup]:
    """
    Fetch a page and return BeautifulSoup object.
    
    Args:
        url: URL to fetch
        
    Returns:
        BeautifulSoup object or None if request fails
    """
    try:
        logger.info(f"Fetching: {url}")
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def extract_price(price_text: str) -> Optional[float]:
    """
    Extract numeric price from text.
    
    Args:
        price_text: Price text (e.g., "$49.99" or "49.99")
        
    Returns:
        Float price or None if extraction fails
    """
    try:
        # Remove common currency symbols and whitespace
        cleaned = price_text.strip().replace('$', '').replace(',', '')
        return float(cleaned)
    except (ValueError, AttributeError) as e:
        logger.warning(f"Could not parse price: {price_text} - {e}")
        return None


def extract_product_data(product_element) -> Optional[Dict]:
    """
    Extract product data from a product element.
    
    Args:
        product_element: BeautifulSoup element representing a product
        
    Returns:
        Dictionary with product data or None if required fields are missing
    """
    try:
        # Extract product name and URL from link
        link_elem = product_element.select_one('a[href*="/products/"]')
        name = None
        product_url = None
        
        if link_elem:
            name = link_elem.get('title') or link_elem.get_text(strip=True)
            if 'href' in link_elem.attrs:
                product_url = urljoin(BASE_URL, link_elem['href'])
        
        if not name:
            logger.debug("Skipping product - no name found")
            return None
        
        # Extract current price
        price_elem = product_element.select_one('[data-testid*="price"], .product-card_price, .price, span[class*="price"]')
        current_price = None
        if price_elem:
            current_price = extract_price(price_elem.text)
        
        # Extract original price (if on sale) - look for strikethrough or "was" price
        original_price = None
        original_elem = product_element.select_one('[class*="original"], [class*="regular"], [class*="was"], s')
        if original_elem:
            original_price = extract_price(original_elem.text)
        
        # Extract availability status
        availability = "In Stock"  # Default to in stock
        availability_elem = product_element.select_one('[class*="availability"], [class*="stock"], [data-testid*="availability"]')
        if availability_elem:
            availability_text = availability_elem.text.strip().lower()
            if 'out of stock' in availability_text or 'unavailable' in availability_text:
                availability = "Out of Stock"
            elif 'in stock' in availability_text or 'available' in availability_text:
                availability = "In Stock"
        else:
            # Check for out of stock indicators
            if product_element.select_one('[class*="out-of-stock"], [class*="unavailable"], button:contains("Out")'):
                availability = "Out of Stock"
        
        # Build product dictionary
        product_data = {
            'name': name,
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
        
        logger.debug(f"Extracted product: {name}")
        return product_data
        
    except Exception as e:
        logger.warning(f"Error extracting product data: {e}")
        return None


def get_next_page_url(soup: BeautifulSoup, current_page: int) -> Optional[str]:
    """
    Get the next page URL from pagination controls.
    
    Args:
        soup: BeautifulSoup object of current page
        current_page: Current page number
        
    Returns:
        URL of next page or None if not found
    """
    try:
        # Try to find next page button
        next_button = soup.select_one('a[rel="next"], .pagination a.next, [aria-label*="next"], a:contains("Next")')
        if next_button and 'href' in next_button.attrs:
            return urljoin(BASE_URL, next_button['href'])
        
        # Alternative: construct next page URL based on pagination pattern
        # Many sites use ?page=N or ?offset=N patterns
        next_page_num = current_page + 1
        # This would need to be adjusted based on actual Dockers.com pagination
        return None
        
    except Exception as e:
        logger.warning(f"Error finding next page: {e}")
        return None


def scrape_dockers(max_pages: int = 5) -> List[Dict]:
    """
    Scrape Dockers products across multiple pages.
    
    Args:
        max_pages: Maximum number of pages to scrape
        
    Returns:
        List of product dictionaries
    """
    products = []
    current_url = urljoin(BASE_URL, PRODUCTS_ENDPOINT)
    page_count = 0
    
    while current_url and page_count < max_pages:
        logger.info(f"Scraping page {page_count + 1}...")
        
        # Rate limiting
        if page_count > 0:
            logger.info(f"Waiting {RATE_LIMIT_DELAY} seconds before next request...")
            time.sleep(RATE_LIMIT_DELAY)
        
        # Fetch page
        soup = fetch_page(current_url)
        if not soup:
            logger.error(f"Failed to fetch page {page_count + 1}, stopping")
            break
        
        # Extract products from page
        product_elements = soup.select('li.product-card_thumbnail-container')
        
        if not product_elements:
            logger.warning(f"No products found on page {page_count + 1}")
            break
        
        logger.info(f"Found {len(product_elements)} products on page {page_count + 1}")
        
        # Process each product
        for product_elem in product_elements:
            product_data = extract_product_data(product_elem)
            if product_data:
                products.append(product_data)
        
        logger.info(f"Total products extracted so far: {len(products)}")
        
        # Find next page
        current_url = get_next_page_url(soup, page_count)
        page_count += 1
    
    logger.info(f"Scraping complete! Total products: {len(products)}")
    return products


def save_results_to_file(products: List[Dict], filename: str = "dockers_products.json") -> None:
    """
    Save scraped products to JSON file.
    
    Args:
        products: List of product dictionaries
        filename: Output filename
    """
    import json
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {filename}")
    except IOError as e:
        logger.error(f"Error saving results: {e}")


def print_sample_results(products: List[Dict], sample_size: int = 5) -> None:
    """
    Print sample of scraped products.
    
    Args:
        products: List of product dictionaries
        sample_size: Number of products to display
    """
    if not products:
        print("No products to display")
        return
    
    print(f"\n{'='*80}")
    print(f"Sample Results (showing {min(sample_size, len(products))} of {len(products)} products)")
    print(f"{'='*80}\n")
    
    for i, product in enumerate(products[:sample_size], 1):
        print(f"Product {i}: {product['name']}")
        print(f"  Current Price: ${product['current_price']}" if product['current_price'] else "  Current Price: N/A")
        print(f"  Original Price: ${product['original_price']}" if product['original_price'] else "  Original Price: N/A")
        if product['discount_percentage']:
            print(f"  Discount: {product['discount_percentage']}%")
        print(f"  Availability: {product['availability']}")
        print(f"  URL: {product['url']}")
        print()


if __name__ == "__main__":
    # Run scraper
    print("Starting Dockers.com price scraper...")
    products = scrape_dockers(max_pages=3)
    
    # Display sample results
    print_sample_results(products, sample_size=5)
    
    # Save results
    save_results_to_file(products)
