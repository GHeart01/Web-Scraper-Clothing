-- Dockers Price Comparison App - PostgreSQL Database Schema
-- Created: February 18, 2026

-- Products Table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    image_url TEXT,
    dockers_sku VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on dockers_sku for quick lookups
CREATE INDEX idx_products_sku ON products(dockers_sku);
CREATE INDEX idx_products_category ON products(category);

-- Prices Table
CREATE TABLE prices (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    retailer VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2),
    url TEXT NOT NULL,
    in_stock BOOLEAN DEFAULT true,
    scraped_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX idx_prices_product_id ON prices(product_id);
CREATE INDEX idx_prices_retailer ON prices(retailer);
CREATE INDEX idx_prices_scraped_at ON prices(scraped_at);
-- Composite index for finding prices by product and retailer
CREATE INDEX idx_prices_product_retailer ON prices(product_id, retailer);
-- Index for finding latest prices per product
CREATE INDEX idx_prices_product_created ON prices(product_id, created_at DESC);

-- Price Alerts Table
CREATE TABLE price_alerts (
    id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    target_price DECIMAL(10, 2) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for alert queries
CREATE INDEX idx_alerts_product_id ON price_alerts(product_id);
CREATE INDEX idx_alerts_user_email ON price_alerts(user_email);
CREATE INDEX idx_alerts_active ON price_alerts(is_active);
-- Composite index for finding active alerts by user
CREATE INDEX idx_alerts_user_active ON price_alerts(user_email, is_active);
