import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np
import mlflow
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np
import mlflow
import os


# ------------------------------------------------------------
# MLflow local tracking setup
# ------------------------------------------------------------

# "mlruns" = folder where MLflow will store experiment information
# such as runs, parameters, metrics, and other tracking files.
#
# os.path.abspath("mlruns")
#     converts the relative path "mlruns" into the full path.
#
# .replace("\\", "/")
#     changes Windows "\" into "/" for a file URI.
tracking_path = os.path.abspath("mlruns").replace("\\", "/")

# Use a local SQLite database for MLflow tracking.
# The database file will be created in the project folder.
mlflow.set_tracking_uri("sqlite:///mlflow.db")
# Load the final dataset.
df = pd.read_csv(
    "data/features/features_final.csv",
    parse_dates=["order_date"]
)

# Find the product with the most sales/rows.
# groupby("product_id") -> separate products.
# size() -> count rows for each product.
# idxmax() -> return the product with the largest count.
top_product = df.groupby("product_id").size().idxmax()

# Keep only the selected product.
product_daily = df[df["product_id"] == top_product]

# Convert individual sales rows into ONE daily demand value.
# groupby("order_date") -> separate the product by date.
# size() -> count how many sales happened on each date.
# reset_index(name="y") -> make a normal table and call demand "y".
product_daily = (
    product_daily
    .groupby("order_date")
    .size()
    .reset_index(name="y")
)

# Prophet requires the date column to be called "ds".
product_daily = product_daily.rename(
    columns={"order_date": "ds"}
)

# Find the date at approximately 80% of the timeline.
# First 80% = training data.
# Last 20% = testing data.
cutoff = product_daily["ds"].quantile(0.8)

# Use past data for training.
train = product_daily[product_daily["ds"] <= cutoff]

# Use future/unseen data for testing.
test = product_daily[product_daily["ds"] > cutoff]

# Start an MLflow experiment run.
with mlflow.start_run(run_name="prophet_baseline"):

    # Create a new Prophet forecasting model.
    model = Prophet()

    # Train Prophet using historical dates and demand.
    model.fit(train)

    # Give Prophet the future dates for which we want predictions.
    future = test[["ds"]]

    # Predict demand for those future dates.
    forecast = model.predict(future)

    # Compare actual demand with predicted demand using RMSE.
    rmse = np.sqrt(
        mean_squared_error(
            test["y"],
            forecast["yhat"]
        )
    )

    # Compare actual demand with predicted demand using MAE.
    mae = mean_absolute_error(
        test["y"],
        forecast["yhat"]
    )

    # Save the evaluation results in MLflow.
    mlflow.log_metric("rmse", rmse)
    mlflow.log_metric("mae", mae)

    # Display the results.
    print(
        f"Prophet — RMSE: {rmse:.3f} | MAE: {mae:.3f}"
    )