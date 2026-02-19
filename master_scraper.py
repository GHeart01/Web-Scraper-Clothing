"""
Master Scraper - Runs all retailer scrapers in parallel
Combines results from Dockers, Amazon, JCPenney, and Macy's
"""

import threading
import json
import logging
from datetime import datetime
from typing import Dict, List

# Import individual scrapers
from Dockers_scraper import scrape_product
from amazon_scraper import search_amazon_dockers
from jcpenney_scraper import search_jcpenney_dockers
from macys_scraper import search_macys_dockers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MasterScraper:
    """Runs multiple scraper threads and aggregates results."""
    
    def __init__(self):
        self.results = {
            'dockers': [],
            'amazon': [],
            'jcpenney': [],
            'macys': [],
            'timestamp': None,
            'search_term': None
        }
        self.threads = []
        self.errors = []
    
    def scrape_dockers(self, url: str) -> None:
        """Scrape Dockers in a thread."""
        try:
            logger.info("Starting Dockers scraper thread...")
            product = scrape_product(url)
            self.results['dockers'].append(product)
        except Exception as e:
            logger.error(f"Dockers scraper error: {e}")
            self.errors.append(('Dockers', str(e)))
    
    def scrape_amazon(self, search_term: str) -> None:
        """Scrape Amazon in a thread."""
        try:
            logger.info("Starting Amazon scraper thread...")
            products = search_amazon_dockers(search_term)
            self.results['amazon'].extend(products)
        except Exception as e:
            logger.error(f"Amazon scraper error: {e}")
            self.errors.append(('Amazon', str(e)))
    
    def scrape_jcpenney(self, search_term: str) -> None:
        """Scrape JCPenney in a thread."""
        try:
            logger.info("Starting JCPenney scraper thread...")
            products = search_jcpenney_dockers(search_term)
            self.results['jcpenney'].extend(products)
        except Exception as e:
            logger.error(f"JCPenney scraper error: {e}")
            self.errors.append(('JCPenney', str(e)))
    
    def scrape_macys(self, search_term: str) -> None:
        """Scrape Macy's in a thread."""
        try:
            logger.info("Starting Macy's scraper thread...")
            products = search_macys_dockers(search_term)
            self.results['macys'].extend(products)
        except Exception as e:
            logger.error(f"Macy's scraper error: {e}")
            self.errors.append(("Macy's", str(e)))
    
    def run_all_scrapers(self, dockers_url: str, search_term: str = "Dockers Khakis") -> None:
        """
        Run all scrapers in parallel using threads.
        
        Args:
            dockers_url: URL to scrape from Dockers.com
            search_term: Search term for retailer searches
        """
        self.results['search_term'] = search_term
        self.results['timestamp'] = datetime.now().isoformat()
        
        logger.info(f"\n{'='*100}")
        logger.info(f"MASTER SCRAPER - Running all retailers in parallel")
        logger.info(f"Search Term: {search_term}")
        logger.info(f"Dockers URL: {dockers_url}")
        logger.info(f"{'='*100}\n")
        
        # Create threads for each scraper
        threads = [
            threading.Thread(target=self.scrape_dockers, args=(dockers_url,), name="DockersScraper"),
            threading.Thread(target=self.scrape_amazon, args=(search_term,), name="AmazonScraper"),
            threading.Thread(target=self.scrape_jcpenney, args=(search_term,), name="JCPenneyScraper"),
            threading.Thread(target=self.scrape_macys, args=(search_term,), name="MacysScraper"),
        ]
        
        # Start all threads
        logger.info("Starting all threads...\n")
        for thread in threads:
            thread.start()
            logger.info(f"✓ {thread.name} started")
        
        # Wait for all threads to complete
        logger.info("\nWaiting for all threads to complete...")
        for thread in threads:
            thread.join()
        
        logger.info("✓ All threads completed\n")
    
    def print_summary(self) -> None:
        """Print summary of all results."""
        total_products = sum(len(v) for k, v in self.results.items() if k != 'timestamp' and k != 'search_term')
        
        print(f"\n{'='*100}")
        print(f"PRICE COMPARISON RESULTS")
        print(f"{'='*100}")
        print(f"Search Term: {self.results['search_term']}")
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Total Products Found: {total_products}\n")
        
        # Print by retailer
        for retailer in ['dockers', 'amazon', 'jcpenney', 'macys']:
            products = self.results[retailer]
            print(f"\n{retailer.upper()} - {len(products)} products")
            print(f"{'-'*100}")
            
            if not products:
                print(f"  No products found")
            else:
                for i, product in enumerate(products, 1):
                    print(f"\n  {i}. {product.get('name', 'Unknown')}")
                    if product.get('price'):
                        print(f"     Price: ${product['price']:.2f}", end="")
                        if product.get('original_price') and product['original_price'] > product['price']:
                            discount = ((product['original_price'] - product['price']) / product['original_price']) * 100
                            print(f" (was ${product['original_price']:.2f}, save {discount:.0f}%)")
                        else:
                            print()
                    print(f"     Availability: {product.get('availability', 'Unknown')}")
                    if product.get('error'):
                        print(f"     Error: {product['error']}")
                    print(f"     URL: {product.get('url', 'N/A')}")
        
        # Print errors
        if self.errors:
            print(f"\n{'='*100}")
            print(f"ERRORS ({len(self.errors)})")
            print(f"{'='*100}")
            for retailer, error in self.errors:
                print(f"  {retailer}: {error}")
        
        print(f"\n{'='*100}\n")
    
    def save_results(self, filename: str = None) -> str:
        """
        Save results to JSON file.
        
        Args:
            filename: Output filename (default: prices_TIMESTAMP.json)
        
        Returns:
            Filename where results were saved
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"prices_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Results saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return None
    
    def get_lowest_price(self) -> Dict:
        """Find the lowest price across all retailers."""
        all_products = []
        
        for retailer in ['dockers', 'amazon', 'jcpenney', 'macys']:
            for product in self.results[retailer]:
                if product.get('price'):
                    all_products.append({
                        **product,
                        'retailer_key': retailer
                    })
        
        if all_products:
            lowest = min(all_products, key=lambda x: x.get('price', float('inf')))
            return lowest
        
        return None
    
    def get_price_comparison(self) -> List[Dict]:
        """Get all products sorted by price."""
        all_products = []
        
        for retailer in ['dockers', 'amazon', 'jcpenney', 'macys']:
            for product in self.results[retailer]:
                if product.get('price'):
                    all_products.append(product)
        
        return sorted(all_products, key=lambda x: x.get('price', float('inf')))


def main():
    """Main execution."""
    # Configuration
    DOCKERS_URL = "https://us.dockers.com/products/mens-signature-iron-free-khaki-stretch-flat-front-pants?color=Black"
    SEARCH_TERM = "Dockers Khakis"
    
    # Run scrapers
    scraper = MasterScraper()
    scraper.run_all_scrapers(DOCKERS_URL, SEARCH_TERM)
    
    # Print results
    scraper.print_summary()
    
    # Get best price
    best_price = scraper.get_lowest_price()
    if best_price:
        print(f"BEST PRICE: {best_price['retailer'].upper()} - ${best_price['price']:.2f}")
        print(f"URL: {best_price['url']}\n")
    
    # Save results
    scraper.save_results()


if __name__ == "__main__":
    main()
