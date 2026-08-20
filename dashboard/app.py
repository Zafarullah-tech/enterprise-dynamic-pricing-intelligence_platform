import streamlit as st
import pandas as pd
import plotly.express as px
import xgboost as xgb

# ---- make sure Python can find the "src" package ----
# Streamlit only adds the folder containing this file (dashboard/) to its
# import search path, not the project root above it — so "from src..."
# would fail without this. This adds the project root manually.
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---- import the pricing/alert logic directly, instead of calling an API ----
from src.models.pricing.optimize_price import recommend_base_price, pricing_confidence_score
from src.api.routers.alerts import check_alerts

# ---- basic page setup ----
st.set_page_config(page_title="Dynamic Pricing Dashboard", layout="wide")
st.title("Enterprise Dynamic Pricing Intelligence Platform")

# ---- load the trained model once, at startup ----
# Instead of asking a separate FastAPI server to run the model for us,
# we load the same trained model file directly inside this Streamlit app
# and call the same Python functions ourselves — no network request needed.
model = xgb.XGBRegressor()
model.load_model("xgmlruns_model.json")

# these must be the exact same feature columns used during training
feature_cols = [
    "price", "competitor_price", "stock_on_hand", "is_promo", "is_holiday",
    "day_of_week", "month", "temperature_2m_mean", "precipitation_sum",
    "product_popularity", "inventory_turnover", "price_elasticity",
    "holiday_impact_ratio", "regional_avg_demand"
]


# ---- load product list for the dropdown ----
@st.cache_data
def load_product_options():
    df = pd.read_csv("data/features/features_final.csv")

    product_summary = df.groupby("product_id").agg(
        category=("category", "first"),
        popularity=("product_popularity", "first")
    ).reset_index()

    product_summary["label"] = (
        product_summary["category"]
        + " — "
        + product_summary["product_id"].str[:8]
        + "... (popularity: "
        + product_summary["popularity"].astype(str)
        + ")"
    )

    product_summary = product_summary.sort_values("popularity", ascending=False)
    return product_summary


product_options = load_product_options()

selected_label = st.selectbox("Select a product", product_options["label"])

selected_product = product_options.loc[
    product_options["label"] == selected_label, "product_id"
].values[0]

# ============================================================
# RUN THIS PART ONLY AFTER THE USER SELECTS A PRODUCT
# ============================================================
if selected_product:

    col1, col2, col3 = st.columns(3)

    # ========================================================
    # LOAD THE ORIGINAL DATASET AND FIND THE PRODUCT'S ROW
    # ========================================================
    # (moved up, before the calculations below, since we now need
    # current_row BEFORE calling the pricing/forecast/alert functions
    # — previously this happened after the API calls; now our
    # "API calls" are just function calls that need this row as input)
    df = pd.read_csv("data/features/features_final.csv", parse_dates=["order_date"])

    product_rows = df[df["product_id"] == selected_product].sort_values("order_date")

    current_row = product_rows.iloc[-1]

    # ========================================================
    # RUN THE PRICING ENGINE DIRECTLY (replaces the FastAPI call)
    # ========================================================
    # Instead of:
    #   price_resp = requests.get(f"{API_BASE}/recommend-price/{selected_product}").json()
    # we call the same underlying function directly:
    price_result = recommend_base_price(current_row)
    confidence = pricing_confidence_score(current_row, df["product_popularity"])
    price_resp = {
        "base_price": float(price_result["base_price"]),
        "expected_demand": float(price_result["expected_demand"]),
        "expected_profit": float(price_result["expected_profit"]),
        "confidence_score": float(confidence),
    }

    # ========================================================
    # RUN THE DEMAND FORECAST DIRECTLY (replaces the FastAPI call)
    # ========================================================
    # Instead of:
    #   forecast_resp = requests.get(f"{API_BASE}/forecast-demand/{selected_product}").json()
    # we ask the model directly for tomorrow's demand at the CURRENT price:
    predicted = model.predict(pd.DataFrame([current_row[feature_cols]]))[0]
    predicted = max(float(predicted), 0)  # demand can't be negative
    forecast_resp = {"predicted_next_day_demand": predicted}

    # ========================================================
    # RUN THE ALERT CHECKS DIRECTLY (replaces the FastAPI call)
    # ========================================================
    # Instead of:
    #   alerts_resp = requests.get(f"{API_BASE}/alerts/{selected_product}").json()
    # we call check_alerts() directly with the same inputs the API used:
    alerts_list = check_alerts(
        current_row,
        recommended_price=price_resp["base_price"],
        weekly_demand_avg=current_row.get("rolling_7d_demand"),
        four_week_avg_demand=current_row.get("rolling_30d_demand"),
    )
    alerts_resp = {"alerts": alerts_list}

    # ============================================================
    # CURRENT PRICE & RECOMMENDED PRICE
    # ============================================================
    with col1:
        st.metric(
            "Current Price",
            f"${current_row['price']:.2f}"
        )

        st.metric(
            "Recommended Price",
            f"${price_resp['base_price']:.2f}",
            delta=f"{price_resp['base_price'] - current_row['price']:.2f}"
        )

    # ============================================================
    # EXPECTED REVENUE / PROFIT / DEMAND
    # ============================================================
    with col2:
        expected_revenue = price_resp["base_price"] * price_resp["expected_demand"]

        st.metric(
            "Expected Revenue",
            f"${expected_revenue:.2f}"
        )

        st.metric(
            "Expected Profit",
            f"${price_resp['expected_profit']:.2f}"
        )

        st.metric(
            "Expected Demand",
            f"{price_resp['expected_demand']:.1f} units"
        )

    # ============================================================
    # PRICING CONFIDENCE & NEXT-DAY FORECAST
    # ============================================================
    with col3:
        confidence = price_resp.get("confidence_score", None)

        if confidence is not None:
            st.metric(
                "Pricing Confidence",
                f"{confidence:.1f}/100"
            )

        st.metric(
            "Next-Day Demand Forecast",
            f"{forecast_resp['predicted_next_day_demand']:.1f} units"
        )

    st.divider()

    # ============================================================
    # ALERTS & INVENTORY RISK
    # ============================================================
    st.subheader("Alerts & Inventory Risk")

    alerts = alerts_resp.get("alerts", [])

    if alerts:
        for alert in alerts:
            severity = alert["severity"]

            color = {
                "high": "🔴",
                "medium": "🟠",
                "low": "🟡"
            }.get(severity, "⚪")

            safe_message = alert["message"].replace("$", "\\$")

            st.write(
                f"{color} "
                f"**{alert['type'].replace('_', ' ').title()}**: "
                f"{safe_message}"
            )
    else:
        st.success("No alerts — this product is in good shape.")

    st.divider()

    # ============================================================
    # SALES TREND
    # ============================================================
    st.subheader("Sales Trend")

    trend_df = (
        product_rows
        .groupby("order_date")
        .size()
        .reset_index(name="units_sold")
    )

    fig_trend = px.line(
        trend_df,
        x="order_date",
        y="units_sold",
        title="Daily Units Sold Over Time"
    )

    st.plotly_chart(
        fig_trend,
        use_container_width=True
    )

    # ============================================================
    # DEMAND FORECAST (7-DAY ROLLING AVERAGE)
    # ============================================================
    # NOTE: moved inside the "if selected_product:" block —
    # it referenced product_rows, which only exists after a product
    # is selected, so it belongs here rather than outside the block.
    st.subheader("Demand Forecast (7-Day Rolling Average)")

    if "rolling_7d_demand" in product_rows.columns:
        fig_forecast = px.line(
            product_rows,
            x="order_date",
            y="rolling_7d_demand",
            title="7-Day Rolling Average Demand"
        )

        st.plotly_chart(
            fig_forecast,
            use_container_width=True
        )
