import pandas as pd
import numpy as np

newdf = pd.read_csv("data/processed/cleaned_dataset_sales.csv", parse_dates=["order_date"])

np.random.seed(3)

# for each row, generate a random number between 0 and 1 by uring rand();
# if it's less than 0.05 (5%), mark that row as a promo day
# this simulates: "about 5% of all sales happened during some kind of promotion"
#Promotion = "This product is part of a promotional campaign."
# if less then 0.05 true and greater then false
newdf["is_promo"] = np.random.rand(len(newdf)) < 0.05

# where is_promo is True, discount the price by 10-20%; otherwise keep the original price
#Discount = "The price is reduced by 10–20%."
#Promo Price = "The final price after applying the discount."
# np.where(condition, value_if_true, value_if_false) — like an if/else applied to the whole column at once
#(0.8, 0.9, len( ===>These numbers represent 80% to 90% of the original price.
newdf["promo_price"] = np.where(
    newdf["is_promo"],# condition
    newdf["price"] * np.random.uniform(0.8, 0.9, len(newdf)),# true run
    newdf["price"] # false run
)

newdf[["order_id", "product_id", "order_date", "is_promo", "promo_price"]].to_csv(
    "data/processed/promotions.csv", index=False)

# value_counts() shows how many rows are True vs False — a quick sanity check that ~5% got flagged
print(newdf["is_promo"].value_counts())