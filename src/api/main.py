from fastapi import FastAPI
# Import the FastAPI class.
# FastAPI is the main class used to create the API application.

from src.api.routers import pricing, forecast, alerts
# Import the router objects from each module.
# Each router contains a group of related API endpoints.

app = FastAPI(title="Dynamic Pricing Intelligence Platform")
# Create the FastAPI application object.
# 'title' is metadata shown in the Swagger documentation (/docs).

# ----------------------------------------------------------
# Register Forecast Router
# ----------------------------------------------------------
app.include_router(
    forecast.router,                  # Router object imported from forecast.py
    prefix="/forecast-demand",        # Add this prefix before every endpoint in forecast.py
    tags=["Forecasting"]              # Group these endpoints under "Forecasting" in Swagger UI
)

# Example:
# forecast.py
# @router.get("/{product_id}")
#
# Final URL becomes:
# /forecast-demand/{product_id}


# ----------------------------------------------------------
# Register Pricing Router
# ----------------------------------------------------------
app.include_router(
    pricing.router,                   # Router object imported from pricing.py
    prefix="/recommend-price",        # Prefix added to every pricing endpoint
    tags=["Pricing"]                  # Display under "Pricing" section in Swagger
)

# Example:
# @router.get("/{product_id}")
#
# Final URL:
# /recommend-price/{product_id}


# ----------------------------------------------------------
# Register Alerts Router
# ----------------------------------------------------------
app.include_router(
    alerts.router,                    # Router object imported from alerts.py
    prefix="/alerts",                 # Prefix for alert-related endpoints
    tags=["Alerts"]                   # Display under "Alerts" section in Swagger
)

# Example:
# @router.get("/{product_id}")
#
# Final URL:
# /alerts/{product_id}


# ----------------------------------------------------------
# Root Endpoint
# ----------------------------------------------------------
# Register the root endpoint with the FastAPI application.
# When a client sends a GET request to "/", FastAPI will execute root().
# The "/" represents the root/home path of the API.
@app.get("/")
# Register this function as the GET endpoint for "/".
# Whenever someone visits:
# http://127.0.0.1:8000/
# FastAPI automatically calls root().

def root():

    # Return a Python dictionary.
    # FastAPI automatically converts it into JSON.
    # Return a Python dictionary.
    # FastAPI automatically converts this dictionary into JSON
    # and sends it back as the API response.
    return {
        "message": "Dynamic Pricing Intelligence Platform API is running"
    }
#uvicorn src.api.main:app --reload
#   ↑        ↑       ↑
# server   Python   FastAPI
 #         module   object
 #Automatically restart the server when you change your Python code.