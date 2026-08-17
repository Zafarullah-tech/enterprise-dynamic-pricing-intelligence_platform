from fastapi import APIRouter, HTTPException
import pandas as pd
import xgboost as xgb

router = APIRouter()

model = xgb.XGBRegressor()
model.load_model("xgmlruns_model.json")

feature_cols = ["price", "competitor_price", "stock_on_hand", "is_promo", "is_holiday",
                "day_of_week", "month", "temperature_2m_mean", "precipitation_sum",
                "product_popularity", "inventory_turnover", "price_elasticity",
                "holiday_impact_ratio", "regional_avg_demand"]

df = pd.read_csv("data/features/features_final.csv", parse_dates=["order_date"])

@router.get("/{product_id}")
def forecast_demand(product_id: str):
    product_rows = df[df["product_id"] == product_id]
    if product_rows.empty:
        raise HTTPException(status_code=404, detail="Product not found")

    row = product_rows.iloc[-1]  # most recent row for this product
    predicted = model.predict(pd.DataFrame([row[feature_cols]]))[0]
    predicted = max(float(predicted), 0)  # demand can't be negative — same safeguard as pricing

    return {
        "product_id": product_id,
        "predicted_next_day_demand": round(float(predicted), 2)
    }