import pandas as pd
import numpy as np
import xgboost as xgb #is the library name.
from sklearn.metrics import mean_squared_error, mean_absolute_error
import mlflow
import mlflow.xgboost
# ============================================================
# MLflow LOCAL TRACKING SETUP
# ============================================================

import os

# "os" is Python's built-in Operating System library.
# It helps Python work with files, folders, and paths on Windows.
#
# Syntax:
# import library_name
#
# Here:
# import os
# means: load the "os" library so we can work with file paths.


# ------------------------------------------------------------
# STEP 1: Choose the folder where MLflow will store its data
# ------------------------------------------------------------

tracking_path = os.path.abspath("mlruns").replace("\\", "/")

# Let's break this line into small parts:
#
# tracking_path =
#     A variable that will store the final MLflow folder path.
#
# "mlruns"
#     This is the folder name we want MLflow to use.
#     It will be created/used inside the current project folder.
#
# os.path
#     "path" is the part of the os library used for working with
#     file and folder paths.
#
# os.path.abspath("mlruns")
#     abspath = absolute path.
#     It converts the short/relative path "mlruns" into the
#     complete path of the folder.
#
#     Example:
#     "mlruns"
#         becomes something like:
#     C:\Users\Zafrullah Khan\Downloads\Interrship\
#     dynamic-pricing-platform\mlruns
#
# .replace("\\", "/")
#     Windows normally uses "\" in paths:
#     C:\Users\Zafrullah Khan\...
#
#     MLflow's file URI uses "/" instead:
#     C:/Users/Zafrullah Khan/...
#
#     replace("\\", "/") changes every "\" into "/".
#
#     IMPORTANT:
#     "\\"
#     is how we write one backslash inside a Python string.
#
# Final example:
# tracking_path =
# "C:/Users/Zafrullah Khan/Downloads/Interrship/
# dynamic-pricing-platform/mlruns"


# ------------------------------------------------------------
# STEP 2: Tell MLflow exactly where to store tracking data
# ------------------------------------------------------------

mlflow.set_tracking_uri("sqlite:///mlflow.db")

# Break the syntax:
#
# mlflow
#     This is the MLflow library.
#
# .set_tracking_uri()
#     This is an MLflow function.
#     It tells MLflow:
#     "Use this location to store/read experiment tracking data."
#
# f"file:///{tracking_path}"
#     This is an f-string.
#     f-string allows us to insert the value of tracking_path
#     inside another string.
#
#     Example:
#
#     tracking_path =
#     C:/Users/Zafrullah Khan/.../mlruns
#
#     Then:
#
#     f"file:///{tracking_path}"
#
#     becomes:
#
#     file:///C:/Users/Zafrullah Khan/.../mlruns
#
# "file:///"
#     tells MLflow that the tracking location is a LOCAL
#     folder on this computer, not a website/server.
#
# Final meaning:
# Tell MLflow to use the "mlruns" folder inside this project
# as its local tracking location.
#
# This also prevents MLflow from automatically creating the
# incorrect path that caused the "%20" error in:
# "Zafrullah%20Khan".

# ---- load your finished feature table ----
df = pd.read_csv("data/features/features_final.csv", parse_dates=["order_date"])

# ---- build the actual daily demand TARGET ----
# right now each row = one item sold. We need one row per (product, date) with a demand COUNT —
# that count is what the model will learn to predict.
daily = df.groupby(["product_id", "order_date"]).agg(

    # Count how many orders (rows) exist for this product on this date.
    # Example:
    # P1, 1 Jul -> O1, O2, O3
    # units_sold = 3
    units_sold=("order_id", "count"), # ← this becomes our prediction target

    # Take the average price for this product on this day.
    # Example:
    # Prices = 100, 110, 120
    # Average = (100+110+120)/3 = 110
    price=("price", "mean"),

    # Take the average competitor price for this product on this day.
    # Example:
    # Competitor prices = 95, 100, 105
    # Average = 100
    competitor_price=("competitor_price", "mean"),

    # Take the average stock available on this day.
    # Example:
    # Stock = 50, 49, 48
    # Average = 49
    stock_on_hand=("stock_on_hand", "mean"),

    # If ANY row has promotion=True, result=True.
    # Examples:
    # False, False, False -> False
    # False, True, False -> True
    # True, True, True -> True
    is_promo=("is_promo", "max"),

    # Same logic as promotion.
    # If ANY sale happened on a holiday -> True
    # Otherwise -> False
    is_holiday=("is_holiday", "max"),

    # Every row already has the same weekday.
    # Example:
    # Monday, Monday, Monday -> Monday
    # Just take the first value.
    day_of_week=("day_of_week", "first"),

    # Every row already belongs to the same month.
    # Example:
    # July, July, July -> July
    month=("month", "first"),

    # Average temperature for that product on that date.
    # Example:
    # 29°C, 30°C, 31°C -> 30°C
    temperature_2m_mean=("temperature_2m_mean", "mean"),

    # Average rainfall for that day.
    # Example:
    # 2mm, 1mm, 3mm -> 2mm
    precipitation_sum=("precipitation_sum", "mean"),

    # Product popularity is already the same for every row of that product.
    # Example:
    # 520, 520, 520 -> 520
    # Just take the first value.
    product_popularity=("product_popularity", "first"),

    # Average inventory turnover for this product on this day.
    # Example:
    # 0.40, 0.42, 0.38 -> 0.40
    inventory_turnover=("inventory_turnover", "mean"),

    # Average price elasticity for this product on this day.
    # Example:
    # -1.2, -1.0, -1.1 -> -1.1
    price_elasticity=("price_elasticity", "mean"),

    # Holiday impact ratio is already the same for this product.
    # Example:
    # 1.25, 1.25, 1.25 -> 1.25
    # Just take the first value.
    holiday_impact_ratio=("holiday_impact_ratio", "first"),

    # Average regional demand on this date.
    # Example:
    # 25, 26, 24 -> 25
    regional_avg_demand=("regional_avg_demand", "mean"),

).reset_index()

daily = daily.sort_values(["product_id", "order_date"])

# ---- the model predicts NEXT DAY's demand, so shift the target back by one row per product move the second row value to the first all value rearrange and the first one is remove and the last one become nan
daily["target_next_day_demand"] = daily.groupby("product_id")["units_sold"].shift(-1)

# drop the last day per product — it has no "next day" to predict, so target is NaN there
daily = daily.dropna(subset=["target_next_day_demand"]) #remove the last row subset=["target_next_day_demand"] this means remove the specifi column in dataframe that conatain nan other wise it remove all row in a table that contain nan

# ---- SPLIT BY DATE, not randomly ----
# why: in real deployment, you'll only ever have PAST data to train on and must predict the FUTURE.
# a random split would let the model "see" future rows during training, giving a falsely good score.
# Find the date that splits the dataset into approximately 80% past data and 20% future data.
cutoff_date = daily["order_date"].quantile(0.8)   # last 20% of the date range becomes the test set
train = daily[daily["order_date"] <= cutoff_date]
test = daily[daily["order_date"] > cutoff_date]

feature_cols = ["price", "competitor_price", "stock_on_hand", "is_promo", "is_holiday",
                "day_of_week", "month", "temperature_2m_mean", "precipitation_sum",
                "product_popularity", "inventory_turnover", "price_elasticity",
                "holiday_impact_ratio", "regional_avg_demand"]
# X_test = input features for testing.
# y_test = actual next day's demand used to evaluate the model.
X_train, y_train = train[feature_cols], train["target_next_day_demand"]
#Exactly the same, but for the test set.
#The model has never seen these rows before.
X_test, y_test = test[feature_cols], test["target_next_day_demand"]
# Display the number of training and testing rows to verify the data split.
print("Train rows:", len(X_train), "| Test rows:", len(X_test))

#Train XGBoost, log to MLflow
#Put every experiment inside a notebook called Demand Forecasting
# Create (or use) an MLflow experiment to store all demand forecasting runs.
mlflow.set_experiment("demand_forecasting")
# Start recording one experiment run in MLflow.
#with Automatically start something and automatically clean it up when you're finished.
with mlflow.start_run(run_name="xgboost_v1"):
    #A hyperparameter is:

#A setting that YOU choose before training the model. It controls how the model learns, not the data itself.
    params = {
        "n_estimators": 300, #n_estimators==>How many decision trees XGBoost should build.more oertarian and take more time and memory because model memoriaze everything usually 100 to 500
        "max_depth": 6,#max_depth means imagine tree ask question according to thee vlaue e.g Holiday?Promo? Price? Weather? Stock? Competitor? The tree can learn more complex patterns.Why not 1?=underfitting.Why not 50?=overfitting.Usually 3–8
        "learning_rate": 0.05, #learning_rate= How big a step the model takes while learning.large step fast but skipthe correct answer small step  take more time but more accurate # Why not 1?
# Too aggressive; may miss the optimum.

# Why not 0.0001?
# Too slow; needs many trees.

# Why 0.05?
# Good balance of speed and accuracy.
        "subsample": 0.8,
        # subsample = 0.8
# Each tree uses 80% of the training data.

# Why not 1?
# All trees use the same data, reducing diversity.

# Why 0.8?
# Creates diverse trees and helps reduce overfitting.
        "colsample_bytree": 0.8,
# Each tree uses 80% of the features.

# Why not 1?
# Trees become more similar.

# Why 0.8?
# Increases diversity and improves generalization.
        "random_state": 42
    }
    model = xgb.XGBRegressor(**params) #xgb is a library and xgbregression is a model and **params take the value of dictionary
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    mae = mean_absolute_error(y_test, preds)
    # ---- NAIVE BASELINE: predict tomorrow's demand = today's demand (no model at all) ----
    # Naive baseline: simply assumes tomorrow's demand will be the same as today's.
# It is used as a simple benchmark to compare whether the ML model performs better.
    test_with_baseline = test.copy()
    test_with_baseline["naive_prediction"] = test_with_baseline["units_sold"]

    naive_rmse = np.sqrt(mean_squared_error(y_test, test_with_baseline["naive_prediction"]))
    naive_mae = mean_absolute_error(y_test, test_with_baseline["naive_prediction"])

    print(f"Naive baseline — RMSE: {naive_rmse:.3f} | MAE: {naive_mae:.3f}")
    print(f"Your XGBoost   — RMSE: {rmse:.3f} | MAE: {mae:.3f}")
    # log everything to MLflow so every run is tracked and comparable later
    mlflow.log_params(params)
    mlflow.log_metric("rmse", rmse)
    mlflow.log_metric("mae", mae)
    #mlflow → Library xgboost → Submodule og_model() → Function
    mlflow.xgboost.log_model(model, "xgboost_model")# model ==# Save the trained XGBoost model to MLflow. xgboost_model is the name whic we save this model

    print(f"RMSE: {rmse:.3f} | MAE: {mae:.3f}") # f string 3f means show only 3 digit after decimal point
   # ---- ADD THIS LINE HERE ----
    model.save_model("xgmlruns_model.json")
    # -----------------------------

    #Step 3: Aggregate daily predictions into Weekly and Monthly demand

test = test.copy()# Create a separate copy so changes don't affect the original dataframe.
test["predicted_demand"] = preds # Add the model's predicted demand as a new column.
# Group predictions by week and product, then sum daily demand to get total weekly forecast.
#key and freq are fixed parameter names. freq=w means weakly
weekly_demand = test.groupby([pd.Grouper(key="order_date", freq="W"), "product_id"])["predicted_demand"].sum().reset_index()
# same like the above
monthly_demand = test.groupby([pd.Grouper(key="order_date", freq="ME"), "product_id"])["predicted_demand"].sum().reset_index()

weekly_demand.to_csv("data/features/weekly_demand_forecast.csv", index=False)
monthly_demand.to_csv("data/features/monthly_demand_forecast.csv", index=False)
