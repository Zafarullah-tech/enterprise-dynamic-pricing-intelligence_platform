import pandas as pd
import numpy as np
import xgboost as xgb
#Revenue Simulation means predicting or estimating how the company's revenue will change before actually changing the product price.
# ---- reuse the same trained model and feature list from Phase 4/5 ----
model = xgb.XGBRegressor()
model.load_model("xgmlruns_model.json")

feature_cols = ["price", "competitor_price", "stock_on_hand", "is_promo", "is_holiday",
                "day_of_week", "month", "temperature_2m_mean", "precipitation_sum",
                "product_popularity", "inventory_turnover", "price_elasticity",
                "holiday_impact_ratio", "regional_avg_demand"]

ASSUMED_MARGIN = 0.30  # same assumption as Phase 5 — no real cost data available


def predict_demand_at_price(product_row, price):
    """Helper: ask the model 'how much would sell at this specific price?'"""
        # Make a copy so the original product data is not changed.
    row_copy = product_row.copy()
    # Temporarily replace the current price with the new test price.
    row_copy["price"] = price # give the new update price on which we find the demand
     # Predict demand using the trained XGBoost model.
    predicted = model.predict(pd.DataFrame([row_copy[feature_cols]]))[0] #from row_copy, give me ONLY these columns. features wala"


    return max(predicted, 0)  # demand can't be negative


def simulate_revenue(product_row, recommended_price):
    """
    Compares CURRENT price vs RECOMMENDED price across:
    Revenue Impact, Profit Margin, Customer Conversion, Inventory Movement
    """
    # Read the current selling price of the product.
    current_price = product_row["price"]
    # Read the current stock available.
    stock = product_row["stock_on_hand"]

    # ---- predict demand under both scenarios ----
    # Predict demand at the current price.
    demand_current = predict_demand_at_price(product_row, current_price)
    # Predict demand at the recommended price.
    demand_recommended = predict_demand_at_price(product_row, recommended_price)

    # ---- 1. Revenue Impact ----
    # Revenue at the current price.
    revenue_current = current_price * demand_current
    # Revenue at the recommended price.
    revenue_recommended = recommended_price * demand_recommended
    # Compare both revenues.
    # Positive = revenue increased.
    # Negative = revenue decreased.
    revenue_impact = revenue_recommended - revenue_current

    # ---- 2. Profit Margin ----
    # Calculate profit at the current price.
    profit_current = revenue_current * ASSUMED_MARGIN
    # Calculate profit at the recommended price.
    profit_recommended = revenue_recommended * ASSUMED_MARGIN

    # ---- 3. Customer Conversion (approximated) ----
    #How many people who visited the product actually bought it?
   # Customer Conversion (%) =
    #(Number of Customers Who Bought / Number of Visitors) × 100
    # we don't have real "site visits" or "conversion rate" data, so we approximate:
    # Estimate customer conversion using predicted demand.
    # Since we don't have website visitor data,
    # demand change is used as a conversion proxy.
    #Logic:

#If predicted demand increases → probably more customers are buying.
#If predicted demand decreases → probably fewer customers are buying.
 #Example:
# Current Demand = 20 units
# Recommended Demand = 18 units
#
# Conversion Change
# = ((18 - 20) / 20) × 100
# = -10%
#
# Meaning:
# Estimated customer conversion decreased by 10%.
    if demand_current > 0:
        conversion_change_pct = ((demand_recommended - demand_current) / demand_current) * 100
    else:
         # Avoid division by zero.
        conversion_change_pct = 0.0

    # ---- 4. Inventory Movement ----
    # how many days would current stock last, at each demand rate?
    days_of_stock_current = stock / demand_current if demand_current > 0 else np.inf #np.inf means infinity which means Nobody is buying. Stock will never finish.
    days_of_stock_recommended = stock / demand_recommended if demand_recommended > 0 else np.inf

    return {
        "current_price": round(current_price, 2),
        "recommended_price": round(recommended_price, 2),
        "revenue_current": round(revenue_current, 2),
        "revenue_recommended": round(revenue_recommended, 2),
        "revenue_impact": round(revenue_impact, 2),
        "profit_current": round(profit_current, 2),
        "profit_recommended": round(profit_recommended, 2),
        "conversion_change_pct": round(conversion_change_pct, 1),
        "days_of_stock_current": round(days_of_stock_current, 1),
        "days_of_stock_recommended": round(days_of_stock_recommended, 1),
    }


# ============================================================
# QUICK TEST
# ============================================================
if __name__ == "__main__":
    from src.models.pricing.optimize_price import recommend_base_price

    df = pd.read_csv("data/features/features_final.csv", parse_dates=["order_date"])
    sample_product = df.iloc[0]

    price_result = recommend_base_price(sample_product)
    simulation_result = simulate_revenue(sample_product, price_result["base_price"])

    print(simulation_result)