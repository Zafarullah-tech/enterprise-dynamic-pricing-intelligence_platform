import pandas as pd 


# parse_dates tell it is the time date format plain text or string it convert into time date format
orders = pd.read_csv("data/raw/olist_orders_dataset.csv", parse_dates=["order_purchase_timestamp"])

items = pd.read_csv("data/raw/olist_order_items_dataset.csv")

customers = pd.read_csv("data/raw/olist_customers_dataset.csv")


products = pd.read_csv("data/raw/olist_products_dataset.csv")


translation = pd.read_csv("data/raw/product_category_name_translation.csv")

# MERGE (join) the tables together, like a SQL JOIN
# merge() combines two tables by matching rows that share a common column (like "order_id")
# how="left" means: keep every row from the left table, and attach matching info from the right table
df = items.merge(orders, on="order_id", how="left")


df = df.merge(customers, on="customer_id", how="left")


df = df.merge(products, on="product_id", how="left")


df = df.merge(translation, on="product_category_name", how="left")



# CLEAN & SHAPE the final table 

# extract just the date (no time) from the full timestamp — we don't need hour/minute for daily sales analysis
df["order_date"] = df["order_purchase_timestamp"].dt.date

# only keep orders that were actually completed — cancelled/returned orders would distort demand numbers
df = df[df["order_status"] == "delivered"]

# select only the columns we actually need going forward, and rename them to clearer names
newdf = df[["order_id", "product_id", "product_category_name_english",
           "customer_state", "customer_unique_id", "order_date", "price"]].rename(
           columns={"customer_state": "region", "product_category_name_english": "category"})

# save this cleaned table to disk as a CS
# index=False means: don't save pandas' internal row-numbering column into the file like 1 2 3
newdf.to_csv("data/processed/cleaned_dataset_sales.csv", index=False)
# print basic info so you can sanity-check the result before moving on
print(newdf.shape)     # (number_of_rows, number_of_columns)
print(newdf.head())    # first 5 rows