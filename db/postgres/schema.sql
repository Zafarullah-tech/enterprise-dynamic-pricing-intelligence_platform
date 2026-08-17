-- Enterprise Dynamic Pricing Intelligence Platform — PostgreSQL Schema
-- Run against a database named 'pricing_db'
-- (Originally created directly via pgAdmin's Query Tool; saved here for reproducibility.)

CREATE TABLE products (
    product_id VARCHAR PRIMARY KEY,
    category VARCHAR,
    product_popularity INTEGER,
    inventory_turnover NUMERIC,
    price_elasticity NUMERIC,
    holiday_impact_ratio NUMERIC
);

CREATE TABLE customers (
    customer_unique_id VARCHAR PRIMARY KEY,
    total_orders INTEGER,
    total_spent NUMERIC,
    avg_order_value NUMERIC,
    customer_segment VARCHAR,
    avg_days_between_purchases NUMERIC,
    clv_score NUMERIC
);

CREATE TABLE sales_history (
    order_id VARCHAR,
    product_id VARCHAR REFERENCES products(product_id),
    customer_unique_id VARCHAR REFERENCES customers(customer_unique_id),
    order_date DATE,
    price NUMERIC,
    region VARCHAR,
    is_promo BOOLEAN,
    promo_price NUMERIC,
    is_holiday BOOLEAN,
    day_of_week INTEGER,
    month INTEGER
);

CREATE TABLE daily_product_conditions (
    product_id VARCHAR REFERENCES products(product_id),
    order_date DATE,
    stock_on_hand NUMERIC,
    avg_daily_demand NUMERIC,
    competitor_price NUMERIC,
    temperature_2m_mean NUMERIC,
    precipitation_sum NUMERIC,
    regional_avg_demand NUMERIC,
    PRIMARY KEY (product_id, order_date)
);

CREATE TABLE price_recommendations (
    product_id VARCHAR PRIMARY KEY REFERENCES products(product_id),
    current_price NUMERIC,
    recommended_price NUMERIC,
    expected_demand NUMERIC,
    expected_profit NUMERIC,
    updated_at TIMESTAMP DEFAULT NOW()
);