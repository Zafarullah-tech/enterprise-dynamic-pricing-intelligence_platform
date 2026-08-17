import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import matplotlib.pyplot as plt

# ---- load the same trained model and features used throughout ----
model = xgb.XGBRegressor()
model.load_model("xgmlruns_model.json")

feature_cols = ["price", "competitor_price", "stock_on_hand", "is_promo", "is_holiday",
                "day_of_week", "month", "temperature_2m_mean", "precipitation_sum",
                "product_popularity", "inventory_turnover", "price_elasticity",
                "holiday_impact_ratio", "regional_avg_demand"]

df = pd.read_csv("data/features/features_final.csv", parse_dates=["order_date"])

# SHAP needs a full table of rows to compute explanations against — use a sample, not all 500k+ rows,
# since SHAP is computationally expensive; a few hundred rows is enough to be representative
sample_df = df.sample(n=300, random_state=42)[feature_cols]


# ============================================================
# STEP 1: Build the SHAP explainer
# ============================================================
# TreeExplainer is a version of SHAP built specifically for tree-based models
# (XGBoost, LightGBM, Random Forest) — much faster than generic SHAP for these model types
#Without this SHAP cannot understand XGBoost.
#Nothing is predicted yet.Only preparation.
#It only learns

#How many trees exist
#Every split
#Every node
#Every rule
#Every feature used
explainer = shap.TreeExplainer(model)

# calculate SHAP values: for every row and every feature, how much did that feature
# push the prediction UP or DOWN compared to the model's average prediction?
# Calculate SHAP values for every sampled product.
# SHAP measures how much each feature (price, promo, holiday, etc.)
# increases (+) or decreases (-) the model's prediction compared
# to the average prediction (base value). The sum of all SHAP values
# plus the base value equals the final prediction.
shap_values = explainer.shap_values(sample_df)


# ============================================================
# STEP 2: Explain ONE single prediction (a single product's demand forecast)
# ============================================================
def explain_single_prediction(row_index=0):
    # Select one product using its row number.
# [[ ]] keeps it as a DataFrame because XGBoost expects a DataFrame.
    row = sample_df.iloc[[row_index]]  # double brackets keep it as a DataFrame, not a Series
    # Predict demand for this single product.
# predict() returns [12.35], so [0] extracts the number 12.35.
    prediction = model.predict(row)[0]
# Get SHAP values for this product.
# One SHAP value for every feature.
    shap_row = shap_values[row_index]

    # pair each feature name with its SHAP value (impact), then sort by absolute impact
    # Sort by the size of the SHAP impact (ignore + or - while sorting).
# key=abs uses absolute values only to decide the order.
# ascending=False means show the biggest impacts first.
    impact = pd.DataFrame({
        "feature": feature_cols,
        "shap_value": shap_row }).sort_values("shap_value", key=abs, ascending=False)# key==>is NOT a dictionary key.It is a parameter of the sort_values() function.

    print(f"Predicted demand: {prediction:.2f}")
    # Print the model's average prediction (base value).
# SHAP starts explaining every prediction from this value.
# eg 10,8,6==>10+8+6/3=8
    print(f"Base value (average prediction across all data): {explainer.expected_value:.2f}")
    print("\nTop features driving this prediction:")
    # Display only the top 5 most important features.
   # index=False hides row numbers while printing.
   #.to_string() means Convert DataFrame into text.
    print(impact.head(5).to_string(index=False))

    return impact #Sends data back to the caller.


# ============================================================
# STEP 3: Summary chart — overall feature importance across many products
# ============================================================
def plot_summary():
    shap.summary_plot(shap_values, sample_df, show=False)
    ## Adjust spacing so labels and titles fit properly.
    plt.tight_layout()
    # Save the SHAP graph as an image.
# dpi=150 gives good image quality.
    plt.savefig("reports/shap_summary_plot.png", dpi=150)
    print("Saved SHAP summary plot to reports/shap_summary_plot.png")
    print(sample_df.iloc[0][["product_popularity", "price_elasticity", "price"]])

if __name__ == "__main__":
    explain_single_prediction(row_index=0)
    plot_summary()