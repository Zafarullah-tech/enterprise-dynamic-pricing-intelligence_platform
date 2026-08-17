import pandas as pd

# reload the raw files we need for this specific task
orders = pd.read_csv("data/raw/olist_orders_dataset.csv", parse_dates=["order_purchase_timestamp"])
items = pd.read_csv("data/raw/olist_order_items_dataset.csv")
customers = pd.read_csv("data/raw/olist_customers_dataset.csv")

# join orders to customers and order items so we know: which customer, bought what, for how much
df = items.merge(orders, on="order_id", how="left")
df = df.merge(customers, on="customer_id", how="left")

# group by unique customer, and calculate simple behavior metrics
#Means ===>Aggregate.
#It means
#Calculate summary statistics.
#Example
#Instead of100,200,50
#calculate
#Total
#Average
#Count
segments = df.groupby("customer_unique_id").agg(
    total_orders=("order_id", "nunique"),      # how many separate orders this customer made remove duplication like at a time customer purchase muliple product that have same order_ID like o1,o1,o1,o2,o3,o4 total 6 but but after unique 4
    total_spent=("price", "sum"),               # total amount spent across all orders Example 100,200,300,Output600
    avg_order_value=("price", "mean")            # average price per item bought average =600/3=300
).reset_index()

# simple rule-based segmentation
def assign_segment(row):
    if row["total_orders"] >= 3:
        return "loyal_repeat_buyer"
    elif row["avg_order_value"] >= 150:
        return "high_value_shopper"
    else:
        return "one_time_buyer"

segments["customer_segment"] = segments.apply(assign_segment, axis=1) #This line applies the function to every row.
#function → the function to run (assign_segment)
#axis=1 → work row by row (not column by column)

segments.to_csv("data/processed/customer_segments.csv", index=False)
print(segments["customer_segment"].value_counts())#Counts how many customers belong to each segment.Example output:
#one_time_buyer        78000
#loyal_repeat_buyer    15000
#high_value_shopper     7000
print(segments.head())