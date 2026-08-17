from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
from src.models.pricing.optimize_price import recommend_base_price

router = APIRouter()
df = pd.read_csv("data/features/features_final.csv", parse_dates=["order_date"])


def check_alerts(product_row, recommended_price, weekly_demand_avg=None, four_week_avg_demand=None):
    """
    Checks a single product against 5 alert conditions from the case study:
    Underpriced, Overpriced, Stockout Risk, Demand Spike, Competitor Price Drop
    Returns a list of triggered alerts (empty list = no issues).
    """
    alerts = []

    current_price = product_row["price"]
    competitor_price = product_row["competitor_price"]
    stock = product_row["stock_on_hand"]
    forecasted_demand = product_row["avg_daily_demand"] # or use a fresh model prediction if preferred

    # ---- 1. UNDERPRICED / OVERPRICED ----
     # compare current price to the model's recommended price — if the gap is large, flag it
    price_diff_pct = ((recommended_price - current_price) / current_price) * 100
# 15% is the alert threshold from the case study.
# If the price difference is greater than 15%,
# generate an alert because the gap is considered significant.
    if price_diff_pct > 15:
        alerts.append({
            # Name of the alert.
  # It tells what problem was found.
            "type": "underpriced",
             # Human-readable explanation.
                        # This message will be shown in the dashboard or API response.
            "message": f"Current price (${current_price:.2f}) is more than 15% below the recommended "
                       f"price (${recommended_price:.2f}) — potential lost revenue.",
                       # Indicates how serious the alert is.
    # Possible values:
                       # low, medium, high
            "severity": "medium"
        })
    elif price_diff_pct < -15:
        alerts.append({
            "type": "overpriced",
            "message": f"Current price (${current_price:.2f}) is more than 15% above the recommended "
                       f"price (${recommended_price:.2f}) — may be hurting conversion.",
            "severity": "medium"
        })

    # ---- 2. STOCKOUT RISK ----
      # if forecasted demand would consume stock faster than it can reasonably be replenished
    if forecasted_demand > 0:
        days_of_stock_left = stock / forecasted_demand
        if days_of_stock_left < 7: # less than a week of stock remaining, at current demand pace
            alerts.append({
                "type": "stockout_risk",
                "message": f"Only {days_of_stock_left:.1f} days of stock remaining at current demand pace.",
                "severity": "high"
            })

    # ---- 3. DEMAND SPIKE ----
      # if this week's demand is >50% above the trailing 4-week average
    
        # Check that both weekly demand and 4-week average exist.
        # Also make sure the 4-week average is greater than zero
        # to avoid division by zero.
    if weekly_demand_avg is not None and four_week_avg_demand is not None and four_week_avg_demand > 0:
        spike_pct = ((weekly_demand_avg - four_week_avg_demand) / four_week_avg_demand) * 100
        if spike_pct > 50:
                # If demand increased by more than 50%,
    # generate a Demand Spike alert.
            alerts.append({
                "type": "demand_spike",
                "message": f"This week's demand is {spike_pct:.1f}% above the 4-week average.",
                   # High priority because sudden demand
                            # may cause stock shortages.
                "severity": "high"
            })

    # ---- 4. COMPETITOR PRICE DROP ----
     # if the competitor is now meaningfully cheaper than us
        # If our price is more than 10% higher than the competitor's,
    # generate an alert because customers may prefer the cheaper competitor.
    competitor_diff_pct = ((current_price - competitor_price) / competitor_price) * 100
    if competitor_diff_pct > 10:# we're more than 10% pricier than the competitor
        alerts.append({
            "type": "competitor_price_drop",
            "message": f"Competitor price (${competitor_price:.2f}) is more than 10% below "
                       f"our price (${current_price:.2f}).",
            "severity": "medium"
        })

    return alerts# Return the complete list of all alerts generated.


# ============================================================
# API ENDPOINT — wraps check_alerts() for real-time use
# ============================================================
@router.get("/{product_id}")
def get_alerts(product_id: str): #product_id should be a string
    product_rows = df[df["product_id"] == product_id]
    if product_rows.empty:#.empty asks:"Is this DataFrame empty?"
        #parameter name = fixed
 #value           = you can choose
        raise HTTPException(status_code=404, detail="Product not found")

    row = product_rows.iloc[-1]
    price_result = recommend_base_price(row)

    alerts = check_alerts(
        row,
        recommended_price=price_result["base_price"],
        weekly_demand_avg=row.get("rolling_7d_demand"),
        four_week_avg_demand=row.get("rolling_30d_demand")
    )
    return {"product_id": product_id, "alerts": alerts}


# ============================================================
# QUICK STANDALONE TEST (unchanged — still runs outside the API)
# ============================================================
if __name__ == "__main__":
    df_test = pd.read_csv("data/features/features_final.csv", parse_dates=["order_date"])
    sample_product = df_test.iloc[0]

    price_result = recommend_base_price(sample_product)
    result = check_alerts(
        sample_product,
        recommended_price=price_result["base_price"],
        weekly_demand_avg=sample_product.get("rolling_7d_demand", None),
        four_week_avg_demand=sample_product.get("rolling_30d_demand", None)
    )

    # If alerts exist, print each one.
    if result:
        for alert in result:
            # Print each alert in a readable format.
            # Format:
            # [SEVERITY] ALERT_TYPE: ALERT_MESSAGE
            #
            # Example Output:
            # [HIGH] stockout_risk: Only 3.5 days of stock remaining.
            # [MEDIUM] underpriced: Current price is more than 15% below the recommended price.
            #
            # .upper() converts the severity to uppercase (e.g., "medium" -> "MEDIUM").
            # alert["type"] displays the alert category.
            # alert["message"] displays the detailed explanation.
            
            print(f"[{alert['severity'].upper()}] {alert['type']}: {alert['message']}")
    else:
        print("No alerts triggered for this product.")




       