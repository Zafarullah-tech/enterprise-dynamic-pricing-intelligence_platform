import pandas as pd
import holidays  # a library with pre-built holiday calendars for many countries, including Brazil

newdf = pd.read_csv("data/processed/cleaned_dataset_sales.csv", parse_dates=["order_date"])

# get every actual public holiday in Brazil for every year
br_holidays = holidays.Brazil(years=range(2016, 2019))

# get every unique date that appears in our sales data (no duplicates)
dates = newdf["order_date"].dt.date.unique() # unique remove the same or duplicate date

# build a small table: one row per unique date
flags = pd.DataFrame({"order_date": dates}) # it is a dictionary tranfer unique value from date into order_date

# check each date against the holiday calendar — True if it's a holiday, False if not
flags["is_holiday"] = flags["order_date"].isin(br_holidays)# Think of .isin() like asking: "Does this date exist in the holiday list?"If yes → True    If no → False

# also extract day of week as a number (0=Monday ... 6=Sunday) — useful since weekend demand often differs
#parse_dates = "Convert while loading the CSV."
#pd.to_datetime() = "Convert after the data is already in Python."
flags["day_of_week"] = pd.to_datetime(flags["order_date"]).dt.dayofweek # dayofweek 0,1,2,3,4,5,6

flags.to_csv("data/processed/seasonal_flags.csv", index=False)
print(flags.head())