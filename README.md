# Web Scraper - Clothing Price Comparison

A Python web scraper for comparing Dockers clothing prices across retailers. Extract product data, track price changes, and set price alerts.

## Features

- **Web Scraping**: Extract product details (name, price, availability) from Dockers
- **Database Schema**: PostgreSQL schema for storing products, prices, and alerts
- **Price Tracking**: Monitor price changes over time
- **Price Alerts**: Set target prices and get notified when deals are available
- **Error Handling**: Robust error handling and logging
- **Rate Limiting**: Respectful scraping with configurable delays

## Project Structure

```
.
├── schema.sql              # PostgreSQL database schema
├── simple_scraper.py       # Single product scraper
├── scraper.py              # Multi-product scraper with pagination
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/GHeart01/Web-Scraper-Clothing.git
cd Web-Scraper-Clothing
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
psql -U your_username -d your_database -f schema.sql
```

## Usage

### Single Product Scraper
Scrape a specific Dockers product:
```bash
python simple_scraper.py
```

### Multi-Product Scraper
Scrape multiple products with pagination:
```bash
python scraper.py
```

## Database Schema

### Tables
- **products**: Product information (name, category, SKU, image)
- **prices**: Price history with retailer info
- **price_alerts**: User price alerts and target prices

### Key Features
- Foreign key relationships with cascade delete
- Indexes optimized for common queries
- Timestamps for audit trails

## Configuration

Edit the following in the scraper files:

```python
PRODUCT_URL = "https://us.dockers.com/products/..."  # Target URL
RATE_LIMIT_DELAY = 2  # Seconds between requests
REQUEST_TIMEOUT = 10  # Request timeout in seconds
```

## Output

Results are saved to JSON files:
- `dockers_product.json` - Single product results
- `dockers_products.json` - Multiple product results

## Technologies

- **BeautifulSoup4**: HTML parsing
- **Requests**: HTTP requests
- **PostgreSQL**: Data storage
- **Python 3.8+**: Core language

## Future Enhancements

- [ ] Support for multiple retailers
- [ ] Email notifications for price alerts
- [ ] Web dashboard for tracking
- [ ] Scheduled scraping with APScheduler
- [ ] API endpoints with FastAPI/Flask

## Legal Notice

This scraper is for educational purposes. Always check the website's `robots.txt` and Terms of Service before scraping.

## License

MIT License - Feel free to use this project for learning and personal use.

## Author

GHeart01
