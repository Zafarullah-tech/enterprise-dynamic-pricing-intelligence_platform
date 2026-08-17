import pandas as pd
from sqlalchemy import create_engine

# ---- connect to your PostgreSQL database ----
# format: postgresql://username:password@host:port/database_name
# replace 'yourpassword' with your actual PostgreSQL password from the installer
#postgresql://postgres:zafar@123@localhost:5432/pricing_db
#             ↑       ↑            ↑        ↑       ↑
#          username password      host     port  database
#URL-encode the @ as %40:
engine = create_engine("postgresql://postgres:password@localhost:5432/pricing_db")

# ---- load your final feature table ----
df = pd.read_csv("data/features/features_final.csv", parse_dates=["order_date"])

# ============================================================
# 1. PRODUCTS — one row per unique product
# ============================================================
## Remove duplicate rows based on the "product_id" column.
# Keeps the first row for each unique product_id.
# Example: P001, P001, P002 → P001, P002

products = df[["product_id", "category", "product_popularity",
               "inventory_turnover", "price_elasticity", "holiday_impact_ratio"]].drop_duplicates(subset="product_id")
# Upload the products DataFrame into the PostgreSQL "products" table.
# "products"       → name of the PostgreSQL table.
# engine            → database connection created by SQLAlchemy.
# if_exists="append"→ add new rows without deleting existing data.
# index=False       → do not upload pandas' DataFrame index as a column.
products.to_sql("products", engine, if_exists="append", index=False)
print(f"Loaded {len(products)} products")

# ============================================================
# 2. CUSTOMERS — one row per unique customer
# ============================================================
customers = df[["customer_unique_id", "total_orders", "total_spent", "avg_order_value",
                "customer_segment", "avg_days_between_purchases", "clv_score"]].drop_duplicates(subset="customer_unique_id")
customers.to_sql("customers", engine, if_exists="append", index=False)
print(f"Loaded {len(customers)} customers")

# ============================================================
# 3. SALES HISTORY — one row per actual sale
# ============================================================
sales = df[["order_id", "product_id", "customer_unique_id", "order_date", "price",
            "region", "is_promo", "promo_price", "is_holiday", "day_of_week", "month"]]
sales.to_sql("sales_history", engine, if_exists="append", index=False)
print(f"Loaded {len(sales)} sales records")

# ============================================================
# 4. DAILY PRODUCT CONDITIONS — one row per product per date
# ============================================================
conditions = df[["product_id", "order_date", "stock_on_hand", "avg_daily_demand",
                  "competitor_price", "temperature_2m_mean", "precipitation_sum",
                  "regional_avg_demand"]].drop_duplicates(subset=["product_id", "order_date"])
conditions.to_sql("daily_product_conditions", engine, if_exists="append", index=False)
print(f"Loaded {len(conditions)} daily product condition records")

print("All tables loaded successfully.")