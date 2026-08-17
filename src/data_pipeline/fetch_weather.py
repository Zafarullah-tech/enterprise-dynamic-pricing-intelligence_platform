import pandas as pd
import requests #requests is a Python library used to communicate with websites and APIs.

# map a few Brazilian states to representative lat/lng (state capitals) — expand as needed
state_coords = {
    "AC": (-9.97, -67.81), "AL": (-9.65, -35.73), "AP": (0.03, -51.07),
    "AM": (-3.10, -60.02), "BA": (-12.97, -38.51), "CE": (-3.72, -38.54),
    "DF": (-15.79, -47.88), "ES": (-20.32, -40.34), "GO": (-16.68, -49.25),
    "MA": (-2.53, -44.30), "MT": (-15.60, -56.10), "MS": (-20.44, -54.65),
    "MG": (-19.92, -43.93), "PA": (-1.46, -48.50), "PB": (-7.12, -34.86),
    "PR": (-25.43, -49.27), "PE": (-8.05, -34.90), "PI": (-5.09, -42.80),
    "RJ": (-22.90, -43.20), "RN": (-5.79, -35.21), "RS": (-30.03, -51.23),
    "RO": (-8.76, -63.90), "RR": (2.82, -60.67), "SC": (-27.60, -48.55),
    "SP": (-23.55, -46.63), "SE": (-10.91, -37.07), "TO": (-10.25, -48.25),
}
#imaginary grid lines used to find any exact spot on Earth. Latitude measures distance north or south of the Equator, longitude measures distance east or west of the Prime Meridian, and together they form geographic coordinates.
frames = []
for state, (lat, lon) in state_coords.items():
    url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
           f"&start_date=2016-09-01&end_date=2018-10-31&daily=temperature_2m_mean,precipitation_sum&timezone=auto")
    #https://api.open-meteo.com/v1/forecast?...          ← forecast (future weather)
    #https://archive-api.open-meteo.com/v1/archive?...   ← archive (past weather)
    # temperature_2m_mean means measure temperature 2 meter above the earth and calculate the average
    # precipitation_sum means anything fall from sky rain snow hail but actually it means there how much rain fall  from sky all day
    resp = requests.get(url).json()
    df = pd.DataFrame(resp["daily"])
    df["region"] = state
    frames.append(df)

weather = pd.concat(frames)#Logic: we now have 6 separate small tables sitting in the frames list (one per state); this glues them all into a single table with all states' weather data together.
weather.to_csv("data/external/weather.csv", index=False)
print(weather.head())