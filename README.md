# Enterprise Dynamic Pricing Intelligence Platform
🔗 **Live Demo**: https://enterprise-dynamic-pricing-intelligenceplatform-appybrkaukxet2.streamlit.app/
An ML-powered dynamic pricing system built for the Ezitech Engineering Framework (EEF) case study ML-001. Predicts demand, recommends optimal prices, simulates revenue impact, and surfaces business alerts for an e-commerce product catalog — built on the Olist Brazilian E-Commerce public dataset.

## What this project does

Given a product, the system:
1. Forecasts next-day demand using a trained XGBoost model
2. Recommends an optimal price (base, discount, promotional, regional, peak, and bundle variants) that maximizes expected profit
3. Simulates the revenue/profit/conversion impact of that recommendation vs. the current price
4. Flags business alerts (underpriced, overpriced, stockout risk, demand spike, competitor price drop)
5. Displays all of the above on an interactive dashboard

## Tech Stack

**Backend**: Python, FastAPI, PostgreSQL, Redis
**ML**: XGBoost, Prophet, scikit-learn, SHAP, MLflow, Pandas, NumPy
**Dashboard**: Streamlit, Plotly

## Project Structure

```
dynamic-pricing-platform/
├── data/
│   ├── raw/                        # original Olist CSV files
│   │   ├── olist_customers_dataset.csv
│   │   ├── olist_geolocation_dataset.csv
│   │   ├── olist_order_items_dataset.csv
│   │   ├── olist_orders_dataset.csv
│   │   ├── olist_products_dataset.csv
│   │   └── product_category_name_translation.csv
│   ├── processed/                  # cleaned + synthetic/derived data
│   │   ├── cleaned_dataset_sales.csv
│   │   ├── competitor_prices.csv
│   │   ├── customer_segments.csv
│   │   ├── inventory.csv
│   │   ├── promotions.csv
│   │   └── seasonal_flags.csv
│   ├── external/
│   │   └── weather.csv             # real historical weather (Open-Meteo)
│   └── features/
│       ├── merged_raw.csv          # all sources joined, pre-feature-engineering
│       ├── features_final.csv      # final ML-ready feature table
│       ├── weekly_demand_forecast.csv
│       └── monthly_demand_forecast.csv
├── notebooks/
│   └── 01_explore_and_clean.ipynb
├── src/
│   ├── data_pipeline/
│   │   ├── cleaned_dataset_of_Sales.py    # builds cleaned_dataset_sales.csv
│   │   ├── generate_inventory.py
│   │   ├── generate_competitor_prices.py
│   │   ├── generate_promotions.py
│   │   ├── generate_seasonal_flags.py
│   │   ├── fetch_weather.py
│   │   ├── customer_segments.py            # builds customer_segments.csv
│   │   └── load_to_postgres.py
│   ├── features/
│   │   ├── build_features.py               # merges all sources -> merged_raw.csv
│   │   └── features_final.py               # feature engineering -> features_final.csv
│   ├── models/
│   │   ├── forecasting/
│   │   │   ├── train_xgboost.py
│   │   │   └── train_prophet.py
│   │   └── pricing/
│   │       └── optimize_price.py
│   ├── simulation/
│   │   └── simulate_revenue.py
│   ├── explainability/
│   │   └── explain.py
│   └── api/
│       ├── main.py
│       └── routers/
│           ├── forecast.py
│           ├── pricing.py
│           └── alerts.py
├── dashboard/
│   └── app.py
├── db/
│   └── postgres/
│       └── schema.sql
├── reports/
│   ├── model_evaluation.md
│   ├── deployment_guide.md
│   └── shap_summary_plot.png
├── mlruns/                          # MLflow experiment tracking (auto-generated)
├── mlflow.db                        # MLflow SQLite backend
├── xgmlruns_model.json              # saved, trained XGBoost model
├── venv/
├── requirements.txt
├── setup_project.py
└── README.md
```

## Setup

See `Deployment_Guide.md` for full step-by-step setup instructions, including PostgreSQL and Redis installation.

Quick start (assuming PostgreSQL and Redis/Memurai are already installed and running):

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Running the Pipeline (in order)

```bash
# 1. Data collection + cleaning
python src\data_pipeline\cleaned_dataset_of_Sales.py
python src\data_pipeline\generate_inventory.py
python src\data_pipeline\generate_competitor_prices.py
python src\data_pipeline\generate_promotions.py
python src\data_pipeline\generate_seasonal_flags.py
python src\data_pipeline\fetch_weather.py
python src\data_pipeline\customer_segments.py

# 2. Feature engineering
python src\features\build_features.py
python src\features\features_final.py

# 3. Model training
python src\models\forecasting\train_xgboost.py
python src\models\forecasting\train_prophet.py

# 4. Explainability
python src\explainability\explain.py
```

## Running the Application

Two servers must run simultaneously, in separate terminals:

```bash
# Terminal 1 — API
uvicorn src.api.main:app --reload

# Terminal 2 — Dashboard
streamlit run dashboard/app.py
```

- API docs: `http://127.0.0.1:8000/docs`
- Dashboard: `http://localhost:8501`

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /forecast-demand/{product_id}` | Predicted next-day demand |
| `GET /recommend-price/{product_id}` | Optimal price recommendation + confidence score |
| `GET /alerts/{product_id}` | Active business alerts for this product |

## Key Design Decisions & Assumptions

- **Synthetic data**: the Olist dataset lacks inventory, competitor pricing, and promotion data; these were simulated using documented rules (see Model Evaluation Report, Section 2). Weather and holiday data are real.
- **Assumed profit margin**: 30%, used throughout pricing/revenue calculations, since the dataset has no real product cost data.
- **PostgreSQL**: schema designed and populated with the full dataset (`db/postgres/schema.sql`, `src/data_pipeline/load_to_postgres.py`); the application currently reads from the processed feature CSV for development speed, with the database serving as the demonstrated system-of-record architecture.
- **Redis**: caches computed price recommendations for 5 minutes to avoid redundant model inference on repeat requests.

## Known Limitations

See `reports/Model_Evaluation_Report.md`, Section 9, for a full list including model performance on sparse-demand products, negative-prediction edge cases (mitigated), and scope decisions (e.g., LightGBM not implemented).

## Further Documentation

- `reports/Model_Evaluation_Report.md` — model comparisons, SHAP findings, validation
- `Deployment_Guide.md` — full environment setup from scratch
