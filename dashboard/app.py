import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# ---- basic page setup ----
# Configure the Streamlit page:
# page_title="Dynamic Pricing Dashboard" sets the title shown for the webpage/browser tab.
# layout="wide" makes the dashboard use the available browser width,
# giving more horizontal space to columns, metrics, and charts.
st.set_page_config(page_title="Dynamic Pricing Dashboard", layout="wide")
st.title("Enterprise Dynamic Pricing Intelligence Platform")
# Base URL of our FastAPI backend.
# "http://127.0.0.1:8000" means the FastAPI server is running
# on this same computer at port 8000.
# Streamlit uses this address to send requests to our FastAPI API.
#API_BASE → variable name; stores the base address of our FastAPI API.
API_BASE = "http://127.0.0.1:8000"

# ---- load product list for the dropdown ----
# @st.cache_data tells Streamlit to save/cache the result of this function.
# This prevents Streamlit from repeatedly reading and processing the CSV
# every time the dashboard reruns, as long as the cached result is valid.
@st.cache_data
def load_product_options():

    # Read the final feature dataset from the CSV file
    # and store all its rows in a pandas DataFrame called df.
    df = pd.read_csv("data/features/features_final.csv")

    # Group all rows belonging to the same product_id.
    # One product can have many sales/history rows.
    #
    # For each product:
    #   category = take the first category value for that product
    #   popularity = take the first product_popularity value
    #
    # Example:
    #   P001 → many rows → furniture, furniture, furniture
    #   We keep only:
    #   P001 → furniture
    #
    # reset_index() converts product_id back into a normal column.
    product_summary = df.groupby("product_id").agg(
        category=("category", "first"),
        popularity=("product_popularity", "first")
    ).reset_index()

    # Create a new column called "label".
    # This label is the user-friendly text that will be displayed
    # in the Streamlit product dropdown.
    #
    # Example output:
    # "furniture — abc12345... (popularity: 80)"
    product_summary["label"] = (

        # Add the product's category.
        # Example: "furniture"
        product_summary["category"]

        # Add a separator between category and product ID.
        + " — "

        # Take only the first 8 characters of the product_id
        # so a long product ID is easier to display.
        # Example: "abc123456789" → "abc12345"
        + product_summary["product_id"].str[:8]

        # Add "..." after the shortened product ID.
        + "... (popularity: "

        # Take the popularity value and convert it to a string
        # because we are building one text label.
        # Example: 80 → "80"
        + product_summary["popularity"].astype(str)

        # Close the popularity text.
        + ")"
    )

    # Sort the products by popularity.
    # ascending=False means highest popularity comes first.
    #
    # Example:
    # 90
    # 80
    # 50
    #
    # instead of:
    # 50
    # 80
    # 90
    product_summary = product_summary.sort_values(  "popularity", ascending=False )

    # Return the final product table to the code that called this function.
    return product_summary


# Call the function.
# The returned product_summary DataFrame is stored in product_options.
product_options = load_product_options()


# Create a dropdown menu in the Streamlit dashboard.
#
# "Select a product" → text shown above the dropdown.
# product_options["label"] → the choices displayed in the dropdown.
#
# The user's selected label is stored in selected_label.
selected_label = st.selectbox( "Select a product", product_options["label"])

# Find the actual product_id corresponding to the label selected by the user.
#
# product_options["label"] == selected_label
#     → checks every row and finds the matching product.
#
# .loc[condition, "product_id"]
#     → selects the product_id from the matching row.
#
# .values
#     → gets the actual values.
#
# [0]
#     → takes the first matching value.
# Example:
# User sees:
# "furniture — abc12345... (popularity: 80)"
# selected_label =
# "furniture — abc12345... (popularity: 80)"
# selected_product =
# "abc123456789"
# The real product_id is then used to call your FastAPI endpoints.
# Find the selected product's row, get its product_id, and extract the actual value.
# Example: "furniture — CHAIR1234..." → "CHAIR123456789"
selected_product = product_options.loc[ product_options["label"] == selected_label, "product_id"].values[0]
# ---- fetch data from your FastAPI endpoints when a product is selected ----
# ============================================================
# RUN THIS PART ONLY AFTER THE USER SELECTS A PRODUCT
# ============================================================

# "if" means: check a condition.
# selected_product contains the product_id selected from the dropdown.
#
# If selected_product has a value, Python enters this block.
#
# Syntax:
# if condition:
#     code to run
#
if selected_product:

    # --------------------------------------------------------
    # CREATE 3 COLUMNS FOR THE DASHBOARD
    # --------------------------------------------------------

    # st = Streamlit
    # columns(3) = create 3 equal-width columns.
    #
    # The 3 returned column objects are stored in:
    # col1, col2, col3
    #
    # Syntax:
    # variable1, variable2, variable3 = function()
    #
    col1, col2, col3 = st.columns(3)


    # ========================================================
    # CALL THE FASTAPI PRICE API
    # ========================================================

    # requests.get() sends an HTTP GET request to FastAPI.
    #
    # f"..." is an f-string.
    # It allows us to put a variable inside a string using { }.
    #
    # Example:
    # selected_product = "CHAIR123"
    #
    # API_BASE = "http://127.0.0.1:8000"
    #
    # The final URL becomes:
    # http://127.0.0.1:8000/recommend-price/CHAIR123
    #
    price_resp = requests.get(
        f"{API_BASE}/recommend-price/{selected_product}"
    ).json()

    # .json() converts the JSON response from FastAPI
    # into a Python dictionary.
    #
    # Example API response:
    #
    # {
    #     "base_price": 55,
    #     "expected_demand": 20,
    #     "expected_profit": 300
    # }
    #
    # After .json(), Python can access:
    #
    # price_resp["base_price"]
    #
    # price_resp["expected_demand"]


    # ========================================================
    # CALL THE FASTAPI DEMAND FORECAST API
    # ========================================================

    # Send another GET request to the demand forecasting endpoint.
    #
    # Example final URL:
    # http://127.0.0.1:8000/forecast-demand/CHAIR123
    #
    forecast_resp = requests.get(
        f"{API_BASE}/forecast-demand/{selected_product}"
    ).json()

    # forecast_resp now contains the response from the
    # demand forecasting API.
    #
    # Example:
    # {
    #     "predicted_next_day_demand": 23.5
    # }


    # ========================================================
    # CALL THE FASTAPI ALERTS API
    # ========================================================

    # Send a GET request to the alerts endpoint.
    #
    # Example:
    # http://127.0.0.1:8000/alerts/CHAIR123
    #
    alerts_resp = requests.get(
        f"{API_BASE}/alerts/{selected_product}"
    ).json()

    # alerts_resp contains the alert information
    # returned by FastAPI.


    # ========================================================
    # LOAD THE ORIGINAL DATASET
    # ========================================================

    # pd = pandas
    # read_csv() reads a CSV file and creates a DataFrame.
    #
    # parse_dates=["order_date"] means:
    # Convert the order_date column into a real date format
    # instead of keeping it as normal text.
    #
    df = pd.read_csv(
        "data/features/features_final.csv",
        parse_dates=["order_date"]
    )


    # ========================================================
    # FILTER DATA FOR THE SELECTED PRODUCT
    # ========================================================

    # We only want rows belonging to the selected product.
    #
    # df["product_id"] == selected_product
    #
    # compares every product_id with the selected product.
    #
    # Example:
    #
    # product_id
    # ----------
    # CHAIR123   → True
    # TABLE456   → False
    # CHAIR123   → True
    #
    # df[...] keeps only the rows where the condition is True.
    #
    product_rows = df[
        df["product_id"] == selected_product
    ].sort_values("order_date")

    # .sort_values("order_date")
    # sorts the selected product's records by date.
    #
    # Example:
    #
    # Before:
    # 10 July
    # 5 July
    # 8 July
    #
    # After:
    # 5 July
    # 8 July
    # 10 July


    # ========================================================
    # GET THE MOST RECENT ROW
    # ========================================================

    # .iloc[] is used to access rows by their position.
    #
    # [-1] means the LAST row.
    #
    # Because we sorted by date from oldest → newest,
    # the last row contains the latest information.
    #
    current_row = product_rows.iloc[-1]


    # ============================================================
    # CURRENT PRICE & RECOMMENDED PRICE
    # ============================================================

    # "with col1:" means:
    # Put the Streamlit elements inside column 1.
    #
    # with creates a temporary context.
    #with means show under code on screen
    with col1:

        # --------------------------------------------------------
        # SHOW CURRENT PRICE
        # --------------------------------------------------------

        # st.metric() displays an important value/KPI
        # in a large dashboard-style format.
        #
        # First argument:
        # "Current Price" = label shown on screen.
        #
        # Second argument:
        # f"${current_row['price']:.2f}"
        #
        # means:
        # Get price from current_row.
        #
        # :.2f means show exactly 2 decimal places.
        #
        # Example:
        # price = 49
        # output = $49.00
        #
        st.metric(
            "Current Price",
            f"${current_row['price']:.2f}"
        )


        # --------------------------------------------------------
        # SHOW RECOMMENDED PRICE
        # --------------------------------------------------------

        # price_resp["base_price"]
        # gets the recommended/base price from FastAPI.
        #
        # delta=
        # tells Streamlit to display the difference/change
        # compared with the current price.
        #
        # Example:
        #
        # Current price = $50
        # Recommended = $55
        #
        # delta = 55 - 50 = +5
        # metric show calclation on scrren it different style on screen
        st.metric(
            "Recommended Price",
            f"${price_resp['base_price']:.2f}",
            delta=f"{price_resp['base_price'] - current_row['price']:.2f}"
        )

        # IMPORTANT:
        # delta= is the Streamlit parameter name.
        # We keep the name "delta".
        #it show arrow option on screen up and down
        # delta means:
        # difference/change between two values.


    # ============================================================
    # EXPECTED REVENUE / PROFIT / DEMAND
    # ============================================================

    # Put these outputs inside column 2.
    with col2:

        # --------------------------------------------------------
        # CALCULATE EXPECTED REVENUE
        # --------------------------------------------------------

        # Revenue = price × expected number of units sold.
        #
        # price_resp["base_price"]
        # = recommended price
        #
        # price_resp["expected_demand"]
        # = expected number of units customers will buy.
        #
        # Example:
        #
        # Recommended price = $50
        # Expected demand = 20 units
        #
        # Revenue = 50 × 20
        #         = $1000
        #
        expected_revenue = (
            price_resp["base_price"]
            * price_resp["expected_demand"]
        )


        # --------------------------------------------------------
        # DISPLAY EXPECTED REVENUE
        # --------------------------------------------------------

        st.metric(
            "Expected Revenue",
            f"${expected_revenue:.2f}"
        )

        # st.metric()
        # displays the calculated revenue .


        # --------------------------------------------------------
        # DISPLAY EXPECTED PROFIT
        # --------------------------------------------------------

        # expected_profit comes directly from the pricing API.
        #
        st.metric(
            "Expected Profit",
            f"${price_resp['expected_profit']:.2f}"
        )


        # --------------------------------------------------------
        # DISPLAY EXPECTED DEMAND
        # --------------------------------------------------------

        # expected_demand = expected number of units.
        #
        # :.1f means show one decimal place.
        #
        # Example:
        # 20 → 20.0 units
        #
        st.metric(
            "Expected Demand",
            f"{price_resp['expected_demand']:.1f} units"
        )


    # ============================================================
    # PRICING CONFIDENCE & NEXT-DAY FORECAST
    # ============================================================

    # Put confidence and forecast information inside column 3.
    with col3:

        # --------------------------------------------------------
        # GET CONFIDENCE SCORE
        # --------------------------------------------------------

        # .get() safely gets a value from a dictionary.
        #
        # Syntax:
        # dictionary.get(key, default_value)
        #
        # If "confidence_score" exists:
        #     return its value.
        #
        # If it does not exist:
        #     return None.
        #
        confidence = price_resp.get(
            "confidence_score",
            None
        )


        # --------------------------------------------------------
        # DISPLAY CONFIDENCE ONLY IF IT EXISTS
        # --------------------------------------------------------

        # Check whether confidence contains a value.
        #
        # None means "no value".
        #
        if confidence is not None:

            # Show confidence as something like:
            #
            # Pricing Confidence
            # 85/100
            #
            st.metric(
                "Pricing Confidence",
                f"{confidence}/100"
            )

        # IMPORTANT:
        # f"{confidence}/100" does NOT divide confidence by 100.
        #
        # If confidence = 85:
        #
        # f"{confidence}/100"
        #
        # becomes:
        #
        # "85/100"
        #
        # It is simply displaying:
        # 85 out of 100.


        # --------------------------------------------------------
        # DISPLAY NEXT-DAY DEMAND
        # --------------------------------------------------------

        # Get predicted_next_day_demand from the forecast API.
        #
        st.metric(
            "Next-Day Demand Forecast",
            f"{forecast_resp['predicted_next_day_demand']:.1f} units"
        )


    # ============================================================
    # DIVIDER
    # ============================================================

    # st.divider() creates a horizontal line.
    #
    # It separates different sections of the dashboard.
    #
    st.divider()


    # ============================================================
    # ALERTS & INVENTORY RISK
    # ============================================================

    # st.subheader() creates a section heading.
    #
    st.subheader("Alerts & Inventory Risk")


    # ------------------------------------------------------------
    # GET ALERTS FROM API
    # ------------------------------------------------------------

    # alerts_resp is a dictionary returned by FastAPI.
    #
    # .get("alerts", [])
    #
    # means:
    #
    # If "alerts" exists → get its value.
    #
    # If "alerts" does not exist → use [].
    #
    # [] means an empty list.
    #
    alerts = alerts_resp.get("alerts", [])


    # ------------------------------------------------------------
    # CHECK WHETHER ALERTS EXIST
    # ------------------------------------------------------------

    # if alerts:
    #
    # means:
    # "If the alerts list contains at least one alert."
    #
    if alerts:

        # --------------------------------------------------------
        # PROCESS EACH ALERT ONE BY ONE
        # --------------------------------------------------------

        # for loop takes each alert from the list.
        #
        # Example:
        #
        # alerts = [
        #     alert1,
        #     alert2,
        #     alert3
        # ]
        #
        # The loop processes:
        # alert1 → then alert2 → then alert3
        #
        for alert in alerts:

            # Get severity from the current alert.
            #
            # Example:
            # alert["severity"] = "high"
            #
            severity = alert["severity"]


            # ----------------------------------------------------
            # CONVERT SEVERITY INTO A SYMBOL
            # ----------------------------------------------------

            # This dictionary connects severity with an icon.
            #
            # high   → 🔴
            # medium → 🟠
            # low    → 🟡
            #
            # .get(severity, "⚪")
            #
            # means:
            # Find severity in the dictionary.
            #
            # If it doesn't exist, use ⚪.
            #
            color = {
                "high": "🔴",
                "medium": "🟠",
                "low": "🟡"
            }.get(severity, "⚪")


            # ----------------------------------------------------
            # PREPARE THE ALERT MESSAGE
            # ----------------------------------------------------

            # alert["message"] gets the message.
            #
            # .replace("$", "\\$")
            #
            # replaces $ with \$.
            #
            # This was originally used to prevent Markdown/LaTeX
            # interpretation of the dollar sign.
            #
            safe_message = alert["message"].replace("$", "\\$")


            # ----------------------------------------------------
            # DISPLAY THE ALERT
            # ----------------------------------------------------

            # st.write() displays normal/general information.
            #
            # alert["type"]
            # might contain:
            #
            # "low_stock"
            #
            # .replace("_", " ")
            # changes it to:
            #
            # "low stock"
            #
            # .title()
            # changes it to:
            #
            # "Low Stock"
            #
            # ** ** is Markdown syntax for bold text.
            #
            # Final example:
            #
            # 🔴 Low Stock: Only 5 units remaining
            #
            st.write(
                f"{color} "
                f"**{alert['type'].replace('_', ' ').title()}**: "
                f"{safe_message}"
            )


    # ------------------------------------------------------------
    # IF THERE ARE NO ALERTS
    # ------------------------------------------------------------

    # else runs when the "if alerts" condition is False.
    #
    # In other words:
    #
    # alerts = []
    #
    # means there are no alerts.
    #
    else:

        # st.success() displays a positive/success-style message.
        #
        st.success(
            "No alerts — this product is in good shape."
        )


    # Separate alerts section from the chart section.
    st.divider()


    # ============================================================
    # SALES TREND
    # ============================================================

    # Create a heading for the sales chart.
    st.subheader("Sales Trend")


    # ------------------------------------------------------------
    # GROUP SALES BY DATE
    # ------------------------------------------------------------

    # groupby("order_date")
    #
    # groups all sales having the same date.
    #
    # Example:
    #
    # July 1 → 5 sales
    # July 2 → 8 sales
    # July 3 → 4 sales
    #
    # .size()
    # counts how many rows/sales are in each date group.
    #
    # .reset_index()
    # converts the grouped result back into a normal DataFrame.
    #
    # name="units_sold"
    # gives the calculated count column the name "units_sold".
    #
    trend_df = (
        product_rows
        .groupby("order_date")
        .size()
        .reset_index(name="units_sold")
    )


    # ============================================================
    # CREATE THE SALES LINE CHART
    # ============================================================

    # px = plotly.express
    #
    # px.line() creates a line chart.
    #
    # trend_df = data used by the chart.
    #
    # x="order_date"
    # puts dates on the X-axis.
    #
    # y="units_sold"
    # puts number of sold units on the Y-axis.
    #
    # title= gives the chart a heading.
    #
    fig_trend = px.line(
        trend_df,
        x="order_date",
        y="units_sold",
        title="Daily Units Sold Over Time"
    )


    # ============================================================
    # DISPLAY THE CHART
    # ============================================================

    # st.plotly_chart() displays the Plotly chart in Streamlit.
    #
    # fig_trend = the chart we created above.
    #
    # use_container_width=True
    # means:
    # make the chart use the available width.
    #
    st.plotly_chart(
        fig_trend,
        use_container_width=True
    )


# ============================================================
# DEMAND FORECAST
# ============================================================

# Display the demand forecast section heading.
#
# NOTE:
# In your current code, this section is outside the
# "if selected_product:" block.
#
st.subheader(
    "Demand Forecast (7-Day Rolling Average)"
)


# ------------------------------------------------------------
# CHECK WHETHER THE COLUMN EXISTS
# ------------------------------------------------------------

# "in" checks whether something exists inside another object.
#
# product_rows.columns = all column names in the DataFrame.
#
# So this asks:
#
# "Does product_rows have a column called
#  rolling_7d_demand?"
#
if "rolling_7d_demand" in product_rows.columns:


    # --------------------------------------------------------
    # CREATE DEMAND ROLLING-AVERAGE CHART
    # --------------------------------------------------------

    # px.line() creates a line chart.
    #
    # x = date
    # y = 7-day rolling demand
    #
    fig_forecast = px.line(
        product_rows,
        x="order_date",
        y="rolling_7d_demand",
        title="7-Day Rolling Average Demand"
    )


    # --------------------------------------------------------
    # DISPLAY THE CHART
    # --------------------------------------------------------

    # Show the Plotly chart on the Streamlit dashboard.
    #
    # True means use the available width.
    #
    st.plotly_chart(
        fig_forecast,
        use_container_width=True
    )