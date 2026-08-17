import pandas as pd
import numpy as np  

# load the cleaned sales table 
newdf = pd.read_csv("data/processed/cleaned_dataset_sales.csv", parse_dates=["order_date"])

# STEP 1: figure out how many units of each product sold on each day
# groupby(...).size() counts how many rows exist for each (product_id, order_date) pair
# = how many units of that product were sold on that specific day
daily_demand = newdf.groupby(["product_id", "order_date"]).size().reset_index(name="units_sold")

# STEP 2: Average daily sales of every product.
avg_demand = daily_demand.groupby("product_id")["units_sold"].mean().reset_index(name="avg_daily_demand")

# STEP 3: simulate inventory since Olist has no real stock data
# seed(42) makes the random numbers reproducible — same result every time you run the script
np.random.seed(42)

# logic: stock_on_hand = avg_daily_demand × a random number of "buffer days" between 15 and 45
# this mimics real retail practice: warehouses keep enough stock to cover ~2-6 weeks of expected sales
avg_demand["stock_on_hand"] = (
    avg_demand["avg_daily_demand"] * np.random.randint(15, 46, size=len(avg_demand))
).round()

# save the result
avg_demand.to_csv("data/processed/inventory.csv", index=False)
print(avg_demand.head())