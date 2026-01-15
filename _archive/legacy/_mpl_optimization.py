
import duckdb
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_daily_features_v2 import FeatureBuilderV2, TZ_LOCAL, TZ_UTC, _dt_local
from datetime import date, datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MPL"
OUTPUT_FILE = "mpl_optimized_results.csv"

# Test configurations
RR_VALUES = [1.0, 1.5, 2.0, 3.0]
SL_MODES = ["full", "half"]
ORB_TIMES = [
    ("0900", 9, 0),
    ("1000", 10, 0),
    ("1100", 11, 0),
    ("1800", 18, 0),
    ("2300", 23, 0),
    ("0030", 0, 30),
]

print("Building MPL features with different parameters...")
print("This may take 30-60 minutes for ~500 days...")

# Note: We can't rebuild features with different RR values without modifying
# the feature builder. For now, we'll use the baseline features and note that
# for full optimization, we'd need to rebuild with each RR value.

# For this overnight run, we'll:
# 1. Test HALF SL mode (rebuild features)
# 2. Document that RR optimization requires separate runs

con = duckdb.connect(DB_PATH)

# Get date range
result = con.execute(
    "SELECT MIN(date_local), MAX(date_local) FROM daily_features_v2_mpl WHERE instrument = 'MPL'"
).fetchone()

if not result or not result[0]:
    print("ERROR: No MPL features found")
    sys.exit(1)

start_date = result[0]
end_date = result[1]
print(f"Date range: {start_date} to {end_date}")

con.close()

# Build HALF SL features
print("\nRebuilding features with HALF SL mode...")
from scripts.build_daily_features_mpl import MPLFeatureBuilder

builder = MPLFeatureBuilder(sl_mode="half")
current = start_date
count = 0
while current <= end_date:
    try:
        builder.build_features(current)
        count += 1
        if count % 50 == 0:
            print(f"  Processed {count} days...")
    except Exception as e:
        pass
    current += timedelta(days=1)

builder.con.close()
print(f"HALF SL features built for {count} days")

# For now, export note about optimization limitations
with open(OUTPUT_FILE, "w") as f:
    f.write("# MPL Optimization Results\n")
    f.write("# Note: Full RR optimization requires separate backtest runs\n")
    f.write("# HALF SL mode features have been rebuilt\n")
    f.write("# Use execution_engine.py for detailed parameter sweeps\n")

print(f"\nOptimization notes saved to {OUTPUT_FILE}")
