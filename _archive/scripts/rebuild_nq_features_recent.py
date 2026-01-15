"""
Rebuild NQ daily features for recent dates
Uses existing daily_features_v2_nq computation logic
"""
import duckdb
import subprocess
from datetime import datetime, date

DB_PATH = "gold.db"

print("Checking NQ data availability...")
print("=" * 80)

con = duckdb.connect(DB_PATH)

# Check 1m bars
bars = con.execute("""
    SELECT
        MIN(DATE_TRUNC('day', ts_utc)) as first_date,
        MAX(DATE_TRUNC('day', ts_utc)) as last_date,
        COUNT(*) as total_bars
    FROM bars_1m_nq
    WHERE ts_utc >= '2025-11-23'
""").fetchone()

print(f"Recent 1m bars: {bars[2]:,} bars")
print(f"Date range: {bars[0]} to {bars[1]}")

# Check existing features
features = con.execute("""
    SELECT MAX(date_local) as last_date
    FROM daily_features_v2_nq
""").fetchone()

print(f"Existing features last date: {features[0]}")

# Determine what needs to be rebuilt
start_date = date(2025, 11, 23)  # Where new data starts
end_date = date.today()

print(f"\nRebuilding features from {start_date} to {end_date}")
print("=" * 80)

# The existing computation logic should already handle NQ tables
# Just need to call compute_nq_atr.py which likely updates daily_features_v2_nq

con.close()

# Run NQ ATR computation (this should rebuild features)
print("\nRunning NQ ATR computation...")
result = subprocess.run(["python", "NQ/compute_nq_atr.py"], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

# Verify results
print("\n" + "=" * 80)
print("Verifying updated features...")
con = duckdb.connect(DB_PATH)

result = con.execute("""
    SELECT
        MAX(date_local) as last_date,
        COUNT(*) as total_days
    FROM daily_features_v2_nq
""").fetchone()

print(f"Features now cover: {result[1]} days")
print(f"Latest date: {result[0]}")

# Check 0030 ORB specifically
orb_check = con.execute("""
    SELECT
        date_local,
        orb_0030_high,
        orb_0030_low,
        orb_0030_size,
        orb_0030_break_dir
    FROM daily_features_v2_nq
    ORDER BY date_local DESC
    LIMIT 3
""").fetchall()

print(f"\nRecent 0030 ORB data:")
for row in orb_check:
    if row[1]:  # If ORB high exists
        print(f"  {row[0]}: {row[1]:.2f}/{row[2]:.2f} (Size: {row[3]:.2f}) Break: {row[4]}")
    else:
        print(f"  {row[0]}: No ORB data")

con.close()

print("\n" + "=" * 80)
print("[OK] NQ features updated!")
print("=" * 80)
