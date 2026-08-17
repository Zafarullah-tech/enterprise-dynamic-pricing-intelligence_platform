# Deployment Guide
## Enterprise Dynamic Pricing Intelligence Platform

This guide walks through setting up the full local environment from scratch, on Windows, in the order it must be done.

---

## 1. Prerequisites

- Python 3.13
- Git (optional, for cloning)
- Internet access (for downloading packages and calling the Open-Meteo weather API)

## 2. Python Environment Setup

```bash
cd dynamic-pricing-platform
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Windows-specific note**: if PowerShell blocks the activation script, run this once first:
```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

## 3. PostgreSQL Setup

1. Download and install PostgreSQL 17 from [postgresql.org/download/windows](https://www.postgresql.org/download/windows/). Keep the default port `5432`. Set and remember a password for the `postgres` user.
2. Open **pgAdmin** (installed alongside PostgreSQL). Connect using the password from Step 1.
3. Create a new database named **`pricing_db`**.
4. Open the Query Tool against `pricing_db`, and run the contents of `db/postgres/schema.sql` to create the 5 required tables (`products`, `customers`, `sales_history`, `daily_product_conditions`, `price_recommendations`).
5. Load the processed dataset into PostgreSQL:
   ```bash
   python src\data_pipeline\load_to_postgres.py
   ```
   **Before running**: open this file and replace `yourpassword` in the connection string with your actual PostgreSQL password.

   Expected output:
   ```
   Loaded 32216 products
   Loaded 93358 customers
   Loaded 519067 sales records
   Loaded 92587 daily product condition records
   All tables loaded successfully.
   ```

## 4. Redis Setup (via Memurai, Windows-compatible Redis)

Native Redis does not officially support Windows, so this project uses **Memurai** (Redis-protocol-compatible).

1. Download the free Developer Edition of **"Memurai for Redis"** from [memurai.com](https://www.memurai.com/) (not the Valkey variant — the Python `redis` library expects standard Redis protocol).
2. Run the installer with default settings (port `6379`). It installs as a Windows service and starts automatically.
3. Verify it's running:
   ```bash
   & "C:\Program Files\Memurai\memurai-cli.exe" ping
   ```
   Expected response: `PONG`

   If `memurai-cli` isn't found in a plain terminal, either use the full path above, or add `C:\Program Files\Memurai` to your system PATH and restart the terminal.

## 5. Data Pipeline — Build the Dataset from Scratch

Only needed if rebuilding from raw data (skip if `data/features/features_final.csv` already exists).

1. Download the Olist Brazilian E-Commerce dataset from Kaggle and place the CSVs in `data/raw/`.
2. Run the pipeline scripts in order (see `README.md` for the full command list) — data cleaning → synthetic/external enrichment → feature engineering → model training → explainability.

## 6. Running the Application

Two servers must run **simultaneously**, in two separate terminals, both with the venv activated.

**Terminal 1 — API server:**
```bash
venv\Scripts\activate
uvicorn src.api.main:app --reload
```
Wait for:
```
INFO:     Application startup complete.
```
Verify at: `http://127.0.0.1:8000/docs`

**Terminal 2 — Dashboard:**
```bash
venv\Scripts\activate
streamlit run dashboard/app.py
```
Opens automatically at: `http://localhost:8501`

**Important**: both terminals must stay open and running the entire time the application is in use. Closing either one will break the dashboard (it depends on the API) or make the API unreachable.

## 7. Verifying a Successful Setup

1. At `http://127.0.0.1:8000/docs`, test `/forecast-demand/{product_id}` with any real `product_id` from `features_final.csv` — should return a `200` with a predicted demand value.
2. Test `/recommend-price/{product_id}` twice in a row with the same ID — the second response should show `"source": "cache"` (confirming Redis is working) and respond faster than the first.
3. At `http://localhost:8501`, select any product from the dropdown — all 7 dashboard fields (Current Price, Recommended Price, Expected Revenue, Pricing Confidence, Inventory Risk/Alerts, Sales Trend chart, Demand Forecast chart) should populate.

## 8. Common Issues Encountered During Development

| Issue | Cause | Fix |
|---|---|---|
| `KeyboardInterrupt` during a CSV write | Clicking inside the Windows terminal while a script is running triggers "QuickEdit mode," pausing execution | Don't click inside the terminal while a script runs, or disable QuickEdit Mode in terminal Properties |
| `TypeError: Object of type float32/float64 is not JSON serializable` | Pandas/NumPy numeric types aren't natively JSON-serializable by FastAPI or `json.dumps()` | Convert with `float(value)` before returning/caching any numeric result derived from a DataFrame |
| MLflow `FileNotFoundError` / `PermissionError` with `%20` in the path | Windows username containing a space (`Zafrullah Khan`) breaks MLflow's default file-store path resolution | Set `mlflow.set_tracking_uri("sqlite:///mlflow.db")` to use a SQLite backend instead of the file store |
| `ModuleNotFoundError: No module named 'src'` | Running a script with `python path\to\file.py` doesn't add the project root to Python's import path | Run as a module instead: `python -m src.simulation.simulate_revenue`, and ensure `__init__.py` exists in each package folder |
| `500 Internal Server Error` with no detail in the browser | FastAPI hides internal exceptions from the client by default | Check the `uvicorn` terminal window for the full Python traceback |

## 9. Deploying to a Remote Server (Notes)

This project currently runs entirely locally. To deploy to a real server, the following would additionally be required:
- A PostgreSQL instance and Redis instance running on (or reachable from) the server
- `data/features/features_final.csv`, `mlflow.db`, and `xgmlruns_model.json` copied to the server, or regenerated by re-running the pipeline there
- All Python dependencies installed via `requirements.txt`
- Environment-specific connection strings (PostgreSQL password, Redis host) updated accordingly, ideally moved to environment variables rather than hardcoded in source files