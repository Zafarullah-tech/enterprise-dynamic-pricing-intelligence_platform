import pandas as pd
import numpy as np
import xgboost as xgb

# LOAD THE TRAINED DEMAND FORECASTING MODEL
# Create an XGBoost regression model object.
# This object will be used to load the already-trained model.
model = xgb.XGBRegressor()

# Load the trained model saved during the training phase.
# We do NOT need to train the model again with .fit().
model.load_model("xgmlruns_model.json")

# FEATURES USED BY THE TRAINED MODEL
# These must be the same feature columns that were used
# when the XGBoost model was trained.
feature_cols = [
    "price",
    "competitor_price",
    "stock_on_hand",
    "is_promo",
    "is_holiday",
    "day_of_week",
    "month",
    "temperature_2m_mean",
    "precipitation_sum",
    "product_popularity",
    "inventory_turnover",
    "price_elasticity",
    "holiday_impact_ratio",
    "regional_avg_demand"
]
# PROFIT MARGIN ASSUMPTION
# The Olist dataset does not contain actual product cost
# Therefore, we assume that 30% of revenue becomes profit.
# Example:
# Price = 100
# Margin = 30%
# Assumed profit per sale = 100 × 0.30 = 30
ASSUMED_MARGIN = 0.30

# 1. BASE PRICE — FIND THE MOST PROFITABLE PRICE

#product_row it take the first row of dataset at 0 index 
#price_range_pct=0.20 it start from -20 to 20 perc at inceae by 2 step
def recommend_base_price(product_row,price_range_pct=0.20,step_pct=0.02):
    """
    Try prices from -20% to +20% of the current price.
    For each product price:
    1. Change the product price temporarily.
    2. Ask the trained XGBoost model to predict demand.
    3. Calculate expected profit.
    4. Keep the price with the highest expected profit.
    """

    # Get the product's current price.
    current_price = product_row["price"]

    # Store the best result found so far.
    # -np.inf means negative infinity, so the first real
    # profit score will automatically become the best score.
    best_price = current_price 
    best_score = -np.inf # we do not give zero because it not safe for negative value infinity is the safe point
    best_demand = 0 # because we donot now the demand in advance

    # Generate percentage changes:
    # -20%, -18%, -16%, ..., 0%, ..., +18%, +20%
    #
    # np.arange(start, stop, step)
    # generates numbers using the selected step size.
                          #-0.20              0.22 because it exclude   0.02
    for pct in np.arange( -price_range_pct, price_range_pct + step_pct, step_pct):
        # Convert the percentage change into an actual price.
        #
        # Example:
        # Current price = 100
        # pct = 0.10
        # test_price = 100 × 1.10 = 110
        # if we remove 1 then it only give 10 answer which is not the final price answer
        test_price = current_price * (1 + pct)

        # Make a temporary copy of the product row.
        # We don't want to modify the original data.
        row_copy = product_row.copy()

        # Change only the price for this test.
        # All other product features remain the same.
        row_copy["price"] = test_price

        # Convert the one product row into a one-row DataFrame
        # containing exactly the features the model expects.
        #
        # The trained model then predicts demand at this
        # candidate price.
        # Convert one product row into a DataFrame and predict demand.
        # model.predict() returns an array (e.g., [25.7]).
        # [0] extracts the first and only prediction because we predict for one row.
        # foe one it not make issue but for more values in row it make issue,if we not write zero
        predicted_demand = model.predict(
            pd.DataFrame([row_copy[feature_cols]])
        )[0]

        # Demand cannot be negative.
        # If the model predicts a negative number, replace it with 0.
        predicted_demand = max(predicted_demand, 0)

        # Calculate expected profit.
        #
        # Expected Profit =
        # Price × Predicted Demand × Assumed Profit Margin
        score = ( test_price * predicted_demand * ASSUMED_MARGIN)

        # If this product gives more profit than any
        # previous product, save it as the new best option.
        if score > best_score:

            best_score = score
            best_price = test_price
            best_demand = predicted_demand

    # Return the best price and its expected results.
    return {
        "base_price": round(best_price, 2),
        "expected_demand": round(best_demand, 1),
        "expected_profit": round(best_score, 2)
    }


# ============================================================
# 2. DISCOUNT PRICE
# ============================================================

def discount_price(base_price, discount_pct=0.10):
    # Apply a normal 10% discount by default.
    #
    # Example:
    # 100 × (1 - 0.10) = 90
    return round(
        base_price * (1 - discount_pct),
        2
    )


# ============================================================
# 3. PROMOTIONAL PRICE
# ============================================================

def promotional_price(base_price,promo_discount_pct=0.15):
    # Apply a deeper 15% discount by default.
    #
    # Example:
    # 100 × (1 - 0.15) = 85
    return round(
        base_price * (1 - promo_discount_pct),
        2
    )


# ============================================================
# 4. REGIONAL PRICE
# ============================================================

def regional_price( base_price,region_avg_demand, overall_avg_demand):

    # Compare regional demand with the overall average demand.
    #
    # Example:
    # Region demand = 120
    # Overall demand = 100
    # Adjustment = 120 / 100 = 1.20
    adjustment_factor = ( region_avg_demand / overall_avg_demand )

    # Limit the adjustment between 0.85 and 1.15.
    # This prevents extreme regional price changes.

# Limit the adjustment factor between 0.85 and 1.15.
#
# Why?
# We don't want extremely high or extremely low prices.
#
# Rules:
# If adjustment_factor > 1.15
#     Use 1.15 (maximum 15% price increase)
#
# If adjustment_factor < 0.85
#     Use 0.85 (maximum 15% price decrease)
#
# Otherwise
#     Keep the original value.
#
# Examples:
# np.clip(1.30, 0.85, 1.15) -> 1.15
# np.clip(0.60, 0.85, 1.15) -> 0.85
# np.clip(1.05, 0.85, 1.15) -> 1.05
    adjustment_factor = np.clip( adjustment_factor, 0.85, 1.15)
    # Apply the regional adjustment to the optimized base price.
#
# Examples:
# Base Price = 100
#
# adjustment_factor = 1.15
# New Price = 100 × 1.15 = 115
#
# adjustment_factor = 0.85
# New Price = 100 × 0.85 = 85
#
# round(..., 2) keeps only two decimal places.
    # Apply the regional adjustment to the base price.
    return round( base_price * adjustment_factor, 2)


# ============================================================
# 5. PEAK / HOLIDAY PRICE
# ============================================================

def peak_price( base_price, is_peak_day, peak_markup_pct=0.08):

    # If this is a peak day, increase the price by 8%.
    # Otherwise, keep the original base price.
    #
    # Example:
    # Peak day = True
    # 100 × 1.08 = 108
    #value_if_true if condition else value_if_false
    return round(base_price * (1 + peak_markup_pct), 2) if is_peak_day else base_price


# ============================================================
# 6. BUNDLE PRICE
# ============================================================

def bundle_price(price_list,bundle_discount_pct=0.15):
    # Add the prices of all products in the bundle.
    
    # Example:
    # [100, 80]
    # total = 180
    total = sum(price_list)
    # Apply the bundle discount.
    #
    # 180 × (1 - 0.15) = 153
    # Apply the bundle discount.
#
# Example:
# Total = 180
# Discount = 15%
# Final Price = 180 × (1 - 0.15) = 153
#
# round(..., 2) keeps only 2 decimal places.
    return round(total * (1 - bundle_discount_pct),2)
# ============================================================
# 7. PRICING CONFIDENCE SCORE
# ============================================================

def pricing_confidence_score(product_row, all_popularity_values):
    """
    Calculate a 0–100 confidence score for a product's
    pricing recommendation.

    The score has two parts:

    1. Product history/popularity → maximum 60 points
       More popular products have more historical information.

    2. Price elasticity stability → maximum 40 points
       Less extreme elasticity gives more confidence.
    """

    # ---------------------------------------------------------
    # 1. HISTORY SCORE — maximum 60 points
    # ---------------------------------------------------------

    # Find the highest product popularity in the whole dataset.
    # We use it as the reference point instead of an arbitrary 50.
    max_popularity = all_popularity_values.max()

    # Compare this product's popularity with the maximum popularity.
    #
    # Example:
    # product popularity = 0.8
    # maximum popularity = 1.0
    #
    # 0.8 / 1.0 = 0.8
    #
    # Then convert that 0.8 into a maximum of 60 points.
    history_score = min(
        product_row["product_popularity"] / max_popularity,
        1
    ) * 60


    # ---------------------------------------------------------
    # 2. ELASTICITY STABILITY — maximum 40 points
    # ---------------------------------------------------------

    # abs() removes the negative sign.
    #
    # Example:
    # abs(-2) = 2
    #
    # We care about how extreme elasticity is.
    elasticity = abs(product_row["price_elasticity"])

    # Convert elasticity into a stability value.
    #
    # /10 means 10 is our chosen maximum/extreme reference.
    #
    # 1 - (...) reverses the relationship:
    # smaller elasticity → higher stability
    # larger elasticity  → lower stability
    #
    # max(0, ...) prevents the stability score
    # from becoming negative.
    # price_elasticity is already capped to [-10, 10], so this part is correct as-is
    elasticity_stability = max(
        0,
        1 - elasticity / 10
    ) * 40


    # ---------------------------------------------------------
    # 3. FINAL CONFIDENCE SCORE
    # ---------------------------------------------------------

    # Add:
    # history score       → maximum 60
    # elasticity score    → maximum 40
    #
    # Maximum possible total = 100.
    final_score = history_score + elasticity_stability

    # Convert to normal Python float
    # and keep one decimal place.
    return round(float(final_score), 1)


# ============================================================
# QUICK TEST
# ============================================================

# This block runs only when this Python file is executed directly.
# It does not automatically run when the file is imported elsewhere.
# This block runs ONLY when this file is executed directly.
# It is used to test the functions in this file.
# If another file imports this file, this block will NOT run.
# Only the functions (tools) will be imported and can be used with new data.
if __name__ == "__main__":

    # Load the final feature dataset.
    df = pd.read_csv( "data/features/features_final.csv", parse_dates=["order_date"] )

    # Select the first row as a sample product for testing.
    sample_product = df.iloc[0]

    # Find the base price that gives the highest expected profit.
    result = recommend_base_price(sample_product)

    # Display the base price recommendation.
    print( "Base price recommendation:", result )

    # Calculate and display a normal discount price.
    print("Discount price:",discount_price(result["base_price"]))

    # Calculate and display a promotional price.
    print("Promotional price:",promotional_price(result["base_price"]) )

    # Calculate and display a regional price.
    #
    # sample_product["regional_avg_demand"]
    #     = demand strength of this product's region means one row
    #
    # df["regional_avg_demand"].mean() = overall average regional demand

    print( "Regional price:",regional_price( result["base_price"],sample_product["regional_avg_demand"],df["regional_avg_demand"].mean()) )

    # Calculate peak-day price.
    # If is_holiday is True, apply the peak markup.
    print("Peak day price:",peak_price(result["base_price"],sample_product["is_holiday"]))

    # Example bundle containing two products:
    # Product 1 = recommended base price
    # Product 2 = 80% of the recommended base price
    print("Bundle price (2 products):",bundle_price([result["base_price"],result["base_price"] * 0.8]))
    print("Pricing confidence score:", pricing_confidence_score(sample_product, df["product_popularity"]))