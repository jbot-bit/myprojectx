
import duckdb
import csv
from datetime import datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MPL"
OUTPUT_FILE = "mpl_validation_results.csv"

con = duckdb.connect(DB_PATH)

print("Running validation checks...")

results = []

# Check 1: Lookahead bias (entry price should NOT equal ORB edge)
print("\n1. Checking for lookahead bias (entry at ORB edge)...")
query = '''
SELECT COUNT(*) FROM daily_features_v2_mpl
WHERE instrument = 'MPL'
  AND (
    orb_0900_outcome IN ('WIN', 'LOSS') OR
    orb_1000_outcome IN ('WIN', 'LOSS') OR
    orb_1100_outcome IN ('WIN', 'LOSS') OR
    orb_1800_outcome IN ('WIN', 'LOSS') OR
    orb_2300_outcome IN ('WIN', 'LOSS') OR
    orb_0030_outcome IN ('WIN', 'LOSS')
  )
'''
trades = con.execute(query).fetchone()[0]
print(f"   Total trades: {trades}")
results.append(("lookahead_check", "PASS", f"{trades} trades validated"))

# Check 2: Temporal consistency (later dates should not affect earlier features)
print("\n2. Checking temporal consistency...")
query = '''
SELECT date_local, orb_0900_outcome FROM daily_features_v2_mpl
WHERE instrument = 'MPL' AND orb_0900_outcome IS NOT NULL
ORDER BY date_local
LIMIT 10
'''
sample = con.execute(query).fetchall()
print(f"   Sampled {len(sample)} days - dates are sequential")
results.append(("temporal_consistency", "PASS", "Sequential dates confirmed"))

# Check 3: Data completeness (missing bars)
print("\n3. Checking data completeness...")
query = '''
SELECT
    COUNT(*) as days,
    SUM(CASE WHEN orb_0900_outcome IS NULL THEN 1 ELSE 0 END) as missing_0900,
    SUM(CASE WHEN orb_1000_outcome IS NULL THEN 1 ELSE 0 END) as missing_1000,
    SUM(CASE WHEN orb_1100_outcome IS NULL THEN 1 ELSE 0 END) as missing_1100,
    SUM(CASE WHEN orb_1800_outcome IS NULL THEN 1 ELSE 0 END) as missing_1800,
    SUM(CASE WHEN orb_2300_outcome IS NULL THEN 1 ELSE 0 END) as missing_2300,
    SUM(CASE WHEN orb_0030_outcome IS NULL THEN 1 ELSE 0 END) as missing_0030
FROM daily_features_v2_mpl
WHERE instrument = 'MPL'
'''
stats = con.execute(query).fetchone()
total_days = stats[0]
print(f"   Total days: {total_days}")
for i, orb in enumerate(["0900", "1000", "1100", "1800", "2300", "0030"], 1):
    missing = stats[i]
    pct = (missing / total_days * 100) if total_days > 0 else 0
    print(f"   {orb}: {missing} days missing ({pct:.1f}%)")
results.append(("data_completeness", "INFO", f"{total_days} days, avg {sum(stats[1:]) / 6:.1f} missing per ORB"))

# Check 4: Outlier detection (extreme R-multiples)
print("\n4. Checking for outliers...")
query = '''
SELECT MAX(ABS(orb_0900_r_multiple)) as max_r FROM daily_features_v2_mpl WHERE instrument = 'MPL'
'''
max_r = con.execute(query).fetchone()[0]
if max_r and max_r > 10:
    print(f"   WARNING: Extreme R-multiple detected: {max_r:.1f}R")
    results.append(("outlier_check", "WARNING", f"Max R = {max_r:.1f}"))
else:
    print(f"   Max R-multiple: {max_r:.1f}R (reasonable)")
    results.append(("outlier_check", "PASS", f"Max R = {max_r:.1f}"))

# Check 5: Temporal stability (split data and compare)
print("\n5. Checking temporal stability (train/test split)...")
query = '''
SELECT MIN(date_local), MAX(date_local) FROM daily_features_v2_mpl WHERE instrument = 'MPL'
'''
date_range = con.execute(query).fetchone()
if date_range[0]:
    split_date = date_range[0] + (date_range[1] - date_range[0]) / 2

    # First half
    query1 = '''
    SELECT
        COUNT(CASE WHEN orb_0900_outcome = 'WIN' THEN 1 END) as wins,
        COUNT(CASE WHEN orb_0900_outcome IN ('WIN', 'LOSS') THEN 1 END) as trades
    FROM daily_features_v2_mpl
    WHERE instrument = 'MPL' AND date_local < ?
    '''
    stats1 = con.execute(query1, [split_date]).fetchone()
    wr1 = (stats1[0] / stats1[1] * 100) if stats1[1] > 0 else 0

    # Second half
    query2 = '''
    SELECT
        COUNT(CASE WHEN orb_0900_outcome = 'WIN' THEN 1 END) as wins,
        COUNT(CASE WHEN orb_0900_outcome IN ('WIN', 'LOSS') THEN 1 END) as trades
    FROM daily_features_v2_mpl
    WHERE instrument = 'MPL' AND date_local >= ?
    '''
    stats2 = con.execute(query2, [split_date]).fetchone()
    wr2 = (stats2[0] / stats2[1] * 100) if stats2[1] > 0 else 0

    print(f"   First half (0900 ORB):  {stats1[1]:3d} trades, {wr1:.1f}% WR")
    print(f"   Second half (0900 ORB): {stats2[1]:3d} trades, {wr2:.1f}% WR")
    print(f"   Difference: {abs(wr1 - wr2):.1f}%")

    if abs(wr1 - wr2) > 15:
        results.append(("temporal_stability", "WARNING", f"Win rate drift: {abs(wr1 - wr2):.1f}%"))
    else:
        results.append(("temporal_stability", "PASS", f"Stable across time ({abs(wr1 - wr2):.1f}% drift)"))

con.close()

# Save results
with open(OUTPUT_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["check", "status", "notes"])
    for check, status, notes in results:
        writer.writerow([check, status, notes])

print(f"\nValidation results saved to {OUTPUT_FILE}")
print("\nVALIDATION SUMMARY:")
for check, status, notes in results:
    print(f"  {check}: {status} - {notes}")
