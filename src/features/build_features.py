import pandas as pd

#LOAD all processed files

sales = pd.read_csv("data/processed/cleaned_dataset_sales.csv", parse_dates=["order_date"])

inventory = pd.read_csv("data/processed/inventory.csv")


competitor = pd.read_csv("data/processed/competitor_prices.csv", parse_dates=["order_date"])


promotions = pd.read_csv("data/processed/promotions.csv", parse_dates=["order_date"])


seasonal = pd.read_csv("data/processed/seasonal_flags.csv", parse_dates=["order_date"])


weather = pd.read_csv("data/external/weather.csv")


Customer_segments = pd.read_csv("data/processed/customer_segments.csv")


# ---- MERGE step by step ----
# the golden rule: you join ON whatever columns make each row UNIQUE in the file you're bringing in.
# if a file only varies by one thing (e.g. just product, or just date, or just customer),
# you only need that one column as the key. If it varies by TWO things together
# (e.g. a specific product on a specific date), you need BOTH columns, or you'd
# accidentally match the wrong rows together.


df = sales.merge(inventory, on="product_id", how="left")

# competitor prices and promotions vary by BOTH product and date
# (product A's competitor price on July 1st ≠ product A's competitor price on July 5th)
# so we must match on both columns together, otherwise pandas could pair a product
# with the wrong date's competitor price
df = df.merge(competitor, on=["product_id", "order_date"], how="left")
df = df.merge(promotions, on=["product_id", "order_date"], how="left")

# seasonal flags only vary by DATE (a holiday is a holiday for every product, everywhere)
# there's no product_id column in this file at all, so we join on order_date alone
df = df.merge(seasonal, on="order_date", how="left")

# weather varies by BOTH region and date (Sao Paulo's weather on July 1st ≠ Bahia's weather on July 1st)
# so we need both columns together as the key — using only "order_date" would wrongly
# average/duplicate weather across all regions for that day
weather = weather.rename(columns={"time": "order_date"})   # rename to match our column name
weather["order_date"] = pd.to_datetime(weather["order_date"])  # ensure both sides are the same date type
df = df.merge(weather, on=["region", "order_date"], how="left")

# customer segments vary ONLY by customer — a person's segment doesn't change per product or date,
# so we join on customer_unique_id alone, not product_id or order_date
df = df.merge(Customer_segments, on="customer_unique_id", how="left")


# ---- CLEANUP: fix issues the merges created ----

# several of the source files each had their own "order_id" column.
# when pandas merges two tables that both have a column with the same name,
# it can't just combine them — it renames both with _x (left table) and _y (right table)
# so nothing is silently lost. We now have 3 near-duplicate columns holding the same value.
df["order_id"] = df["order_id_x"]          # keep one clean copy (doesn't matter which _x/_y, they match)
df = df.drop(columns=["order_id_x", "order_id_y"])   # delete the other two duplicates

# a small number of products have no English category translation available in the raw data,
# which left "category" blank (NaN) for ~6,881 rows after the merge.
# fillna() finds every blank value in that column and replaces it with a placeholder,
# so later grouping/feature steps don't error out or silently drop these real sales rows
df["category"] = df["category"].fillna("unknown_category")


# ---- SANITY CHECK + SAVE ----

print(df.shape)          # (rows, columns) — confirm no rows were unexpectedly duplicated/lost
print(df.isna().sum())   # check remaining missing values per column

df.to_csv("data/features/merged_raw.csv", index=False)