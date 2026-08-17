import pandas as pd
import numpy as np

# load your final merged table from the data collection stage
df = pd.read_csv("data/features/merged_raw.csv", parse_dates=["order_date"])

# sort by product and date — required for any "over time" calculation (rolling averages, frequency, etc.)
# without sorting, pandas might calculate trends using rows in the wrong chronological order
#reset_index(drop=True) it delete the previoous index delete like 1,0,2 disorder and create the new order one 0,1,2,3,4...
df = df.sort_values(["product_id", "order_date"]).reset_index(drop=True)
#Feature 1: Time-Based Features
df["day_of_week"] = df["order_date"].dt.dayofweek     # 0=Monday ... 6=Sunday
df["day_name"] = df["order_date"].dt.day_name()         # human-readable version, for reports/dashboard
df["month"] = df["order_date"].dt.month                 # captures seasonal patterns across the year
#Feature 2: Purchase Frequency (per customer)
purchase_freq = df.groupby("customer_unique_id")["order_date"].apply(  #groupby("customer_unique_id")["order_date"] group by customer_unique_id and take only from table order_date
    lambda dates: dates.sort_values().diff().mean().days if len(dates) > 1 else np.nan #.diff==>Find the difference between consecutive rows.1,10,20==>10-1=9,20-10=10 first row 1 is NAn average 9+10/2=9.5 this all for one customer id similarly for other
    #.days remove timedelta Before 96 days 00:00:00 After 96
    #len(dates) means if customer purchase have more then one order then calculate the average otherwise nan
).reset_index(name="avg_days_between_purchases") # create new column and store result there

df = df.merge(purchase_freq, on="customer_unique_id", how="left") # Join this new feature back into the main table.

# customers with only 1 purchase have no "gap" to measure — fill with the overall average as a neutral default
df["avg_days_between_purchases"] = df["avg_days_between_purchases"].fillna(
    df["avg_days_between_purchases"].mean()
)
#Feature 3: Product Popularity
popularity = df.groupby("product_id").size().reset_index(name="product_popularity") #counting rows tells us how many times that product was sold.
df = df.merge(popularity, on="product_id", how="left")
#Feature 4: Inventory Turnover
#How fast is your inventory moving?
# turnover = demand ÷ stock on hand. Higher = moves fast, Lower = sits in the warehouse
df["inventory_turnover"] = df["avg_daily_demand"] / df["stock_on_hand"].replace(0, np.nan) #column.replace(old_value, new_value) replace the 0 in stock on hand by nan it avoid error and make it nan because we cannot divide anything by zero
df["inventory_turnover"] = df["inventory_turnover"].fillna(0) # fill nan by 0
#Instead of leaving the value empty (NaN), we replace it with 0.This tells the machine learning model:"There is no meaningful turnover value for this row."Many ML models also cannot handle NaN, so replacing it with 0 makes the dataset clean and usable.
#Feature 5: Price Elasticity
#If I change the price, how much does customer demand change?"
# ---------------- PRICE ELASTICITY ----------------
# Price Elasticity tells us how much customer demand changes
# when the product price changes.
#
# Formula:
# Price Elasticity = (% Change in Demand) / (% Change in Price)
#
# Example:
# Day 1: Price = $100, Sold = 100 units
# Day 2: Price = $110 (+10%), Sold = 80 units (-20%)
# Elasticity = -20% / 10% = -2
# Meaning: Every 1% increase in price causes about a 2% decrease in demand.
#
# Possible Cases:
#
# 1. Elasticity = -2 (|E| > 1)  -> Very Sensitive (Elastic)
#    Price: $100 → $110 (+10%)
#    Demand: 100 → 80 (-20%)
#    Customers stop buying quickly when price increases.
#
# 2. Elasticity = -0.2 (|E| < 1) -> Less Sensitive (Inelastic)
#    Price: $100 → $110 (+10%)
#    Demand: 100 → 98 (-2%)
#    Customers still buy even after the price increases.
#
# 3. Elasticity = 0
#    Price changes but demand stays the same.
#    Example:
#    Price: $100 → $110
#    Demand: 100 → 100
#
# 4. Positive Elasticity (Rare)
#    Price: $100 → $120
#    Demand: 100 → 120
#    Price and demand increase together (luxury/Veblen goods).
#
# Dynamic Pricing uses this feature to predict how changing
# the price may increase or decrease future demand.
# ---------------------------------------------------
daily = df.groupby(["product_id", "order_date"]).agg(
    units_sold=("order_id", "count"),
    price=("price", "mean")
).reset_index()

daily["price_pct_change"] = daily.groupby("product_id")["price"].pct_change()#Percentage Change = (New Value − Old Value) / Old Value it return nan for first entry because there is no previous record 110-100/100=0.10 10 per incease means change same for the units sold
daily["demand_pct_change"] = daily.groupby("product_id")["units_sold"].pct_change()

daily["price_elasticity"] = np.where( # numpy version condtion like if else
    daily["price_pct_change"] != 0,# condition
    daily["demand_pct_change"] / daily["price_pct_change"],# true
    np.nan # false 
)

df = df.merge(daily[["product_id", "order_date", "price_elasticity"]], on=["product_id", "order_date"], how="left")
df["price_elasticity"] = df["price_elasticity"].fillna(0)
df["price_elasticity"] = np.clip(df["price_elasticity"], -10, 10)

#Feature 6: Holiday Impact

# first make sure we have a rolling demand column to compare — reuse product-level daily demand
daily["rolling_7d_demand"] = daily.groupby("product_id")["units_sold"].transform(#Transform meansCalculate something and return the same number of rows.It replaces/adds values in the DataFrame
    lambda x: x.rolling(7, min_periods=1).mean()
)
df = df.merge(daily[["product_id", "order_date", "rolling_7d_demand"]], on=["product_id", "order_date"], how="left")

holiday_avg = df[df["is_holiday"] == True].groupby("product_id")["rolling_7d_demand"].mean()# it check the complete table and calculate only those value of rolling 7day where is holiday is true same for the other
normal_avg = df[df["is_holiday"] == False].groupby("product_id")["rolling_7d_demand"].mean()
#Interpretation:
# > 1.0  -> Product sells more during holidays.
# = 1.0  -> Holidays have no noticeable effect.
# < 1.0  -> Product sells less during holidays.
holiday_impact = (holiday_avg / normal_avg).reset_index(name="holiday_impact_ratio")
df = df.merge(holiday_impact, on="product_id", how="left")
df["holiday_impact_ratio"] = df["holiday_impact_ratio"].fillna(1.0)  # 1.0 = no measurable difference

#Feature 7: Customer Lifetime Value

clv = df.groupby("customer_unique_id").agg(
    total_spent=("price", "sum"),
    total_orders=("order_id", "nunique")# nunique remove the duplication of same order consider at one time o1,o1=o1,o2,o3
).reset_index()
clv["clv_score"] = clv["total_spent"] * clv["total_orders"]   # simple combined value score

df = df.merge(clv[["customer_unique_id", "clv_score"]], on="customer_unique_id", how="left")

#Feature 8: Regional Trends
regional_trend = df.groupby("region")["rolling_7d_demand"].mean().reset_index(name="regional_avg_demand")
df = df.merge(regional_trend, on="region", how="left")

print(df.shape)
print(df.isna().sum())

df.to_csv("data/features/features_final.csv", index=False)