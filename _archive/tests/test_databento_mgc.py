import databento as db
from dotenv import load_dotenv
import os

load_dotenv()

client = db.Historical(os.getenv("DATABENTO_API_KEY"))

data = client.timeseries.get_range(
    dataset="GLBX.MDP3",
    schema="ohlcv-1m",
    stype_in="parent",
    symbols=["MGC.FUT"],
    start="2022-01-01",
    end="2022-01-02",
)

df = data.to_df()
print(df.head())
print("rows:", len(df))
print("contracts:", df["instrument_id"].nunique())
