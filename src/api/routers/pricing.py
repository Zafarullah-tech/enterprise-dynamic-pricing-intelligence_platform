from fastapi import APIRouter, HTTPException
import pandas as pd
import redis
import json
from src.models.pricing.optimize_price import recommend_base_price,pricing_confidence_score



# Create a router for pricing-related API endpoints.
router = APIRouter()


# Load the feature-engineered CSV into a pandas DataFrame.
# This data will be used when a price needs to be calculated.
df = pd.read_csv(
    "data/features/features_final.csv",
    parse_dates=["order_date"]
)


# Connect Python to the local Redis/Memurai server.
# host="localhost" → Redis is running on this computer.
# port=6379        → standard Redis port.
# decode_responses=True → return normal strings instead of bytes.
cache = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)
def to_native_types(d: dict) -> dict:
    """
    Convert NumPy numeric values into normal Python float values.

    Why?
    XGBoost, NumPy, and Pandas can produce special NumPy number types.
    json.dumps() works more reliably with normal Python types.

    Example input:
        {
            "product_id": "P001",
            "base_price": np.float64(120.5)
        }

    Example output:
        {
            "product_id": "P001",
            "base_price": 120.5
        }
    """

    # Create a new dictionary.
    # d.items() gives us each key and value from the dictionary.
    #
    # k = key
    # v = value
    #
    # Example:
    # k = "base_price"
    # v = np.float64(120.5)

    return {
        k:

        # Check whether the value has an attribute/method called "item".
        #
        # hasattr() is a built-in Python function.
        #
        # hasattr(v, "item") means:
        # "Does v have something called item?"
        #
        # If YES:
        #     convert v into a normal Python float.
        #
        # If NO:
        #     keep v unchanged.
        #
        # Example:
        # np.float64(120.5)
        #       ↓
        # hasattr(v, "item") → True
        #       ↓
        # float(v)
        #       ↓
        # 120.5

        (float(v) if hasattr(v, "item") else v)

        # Repeat this process for every key-value pair
        # inside the input dictionary.
        for k, v in d.items()
    }


# Register this function as a GET endpoint.
# The final URL will be:
# /recommend-price/{product_id}
#
# Example:
# /recommend-price/P001
@router.get("/{product_id}")
def recommend_price(product_id: str):

    # Create a unique Redis key for this product's price result.
    # Example:
    # product_id = "P001"
    # cache_key = "price:P001"
    #price:{product_id}"  This cached data is related to a price recommendation.
    cache_key = f"price:{product_id}"


    # ========================================================
    # STEP 1: CHECK REDIS CACHE FIRST
    # ========================================================

    # Ask Redis whether a result for this product already exists.
    # If found → returns the cached JSON string.
    # If not found → returns None.
    cached = cache.get(cache_key)


    # If Redis contains a cached result, use it.
    if cached:

        # Convert the JSON string stored in Redis
        # back into a Python dictionary.
        result = json.loads(cached)

        # Add a flag so we can see that Redis supplied the result.
        result["source"] = "cache"

        # Return the cached result immediately.
        # The pricing calculation does NOT run again.
        return result


    # ========================================================
    # STEP 2: RESULT NOT IN CACHE — CALCULATE IT
    # ========================================================

    # Find all rows belonging to the requested product.
    product_rows = df[df["product_id"] == product_id]


    # If no row was found, return HTTP 404.
    if product_rows.empty:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )


    # Select the last row for this product.
    # In our data this represents the most recent record.
    row = product_rows.iloc[-1]


    # Calculate the recommended price using
    # your existing pricing function.
    result = to_native_types(recommend_base_price(row))  # ← convert here, once

    result["confidence_score"] = pricing_confidence_score(row, df["product_popularity"])
    # Build the API response.
    # **result unpacks all key-value pairs from the result dictionary.
    # "source": "computed" tells us this result was calculated now.
    response = {"product_id": product_id, **result, "source": "computed" }


    # ========================================================
    # STEP 3: SAVE RESULT IN REDIS
    # ========================================================

    # Save the calculated result in Redis.
    #
    # setex() means:
    #   set the value + expiration time.
    #
    # 300 seconds = 5 minutes.
    #
    # json.dumps() converts the Python dictionary into JSON text
    # before storing it in Redis.
    cache.setex(
        cache_key,
        300,
        json.dumps({
            "product_id": product_id,
            **result
        })
    )


    # Return the newly calculated result to the API user.
    return response