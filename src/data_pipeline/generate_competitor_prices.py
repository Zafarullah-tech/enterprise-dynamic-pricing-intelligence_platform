import pandas as pd
import numpy as np

newdf = pd.read_csv("data/processed/cleaned_dataset_sales.csv", parse_dates=["order_date"])

np.random.seed(7)

# simulate a competitor price: usually 15% lower to 15% higher than our own price, chosen randomly per row
# uniform(0.85, 1.15) picks a random multiplier in that range for EVERY row at once 
newdf["competitor_price"] = newdf["price"] * np.random.uniform(0.85, 1.15, size=len(newdf))

# sort so that each product's rows are in date order — required before doing a rolling calculation
newdf = newdf.sort_values(["product_id", "order_date"])

#Take the competitor_price values for each product separately. Then, for each product, calculate a rolling average using the current row and the previous two rows (starting immediately even if fewer than three rows exist). Finally, replace the original competitor_price column with these smoothed values.
#transform means replace the value in table and unchange them
# min_periods=1 means Start calculating even if only 1 or 2 rows are available if we not give then it take by default 3 and show the previous two result Nan Nan and show the third one
newdf["competitor_price"] = newdf.groupby("product_id")["competitor_price"].transform(
    lambda x: x.rolling(3, min_periods=1).mean()  # average of current + previous 2 rows
)

# keep only the relevant columns and save
newdf[["order_id", "product_id", "order_date", "competitor_price"]].to_csv(
    "data/processed/competitor_prices.csv", index=False)
print(newdf[["product_id", "order_date", "price", "competitor_price"]].head())