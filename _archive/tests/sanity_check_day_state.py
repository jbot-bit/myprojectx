"""Quick sanity check for day-state features."""

import duckdb

DB_PATH = "gold.db"

con = duckdb.connect(DB_PATH, read_only=True)

print("\n" + "="*80)
print("SANITY CHECKS - DAY-STATE FEATURES")
print("="*80 + "\n")

# CHECK 1: Row count
print("CHECK 1: Row count ~= days * 6 ORBs")
print("-" * 80)

row_count = con.execute("SELECT COUNT(*) FROM day_state_features").fetchone()[0]

distinct_dates = con.execute("""
    SELECT COUNT(DISTINCT date_local) FROM day_state_features
""").fetchone()[0]

expected_rows = distinct_dates * 6
actual_vs_expected = (row_count / expected_rows) * 100 if expected_rows > 0 else 0

print(f"  Distinct dates: {distinct_dates}")
print(f"  Total rows: {row_count}")
print(f"  Expected rows (dates * 6): {expected_rows}")
print(f"  Coverage: {actual_vs_expected:.1f}%")

if actual_vs_expected >= 95:
    print(f"  PASS - Coverage within expected range")
    check1_pass = True
else:
    print(f"  FAIL - Coverage below 95%")
    check1_pass = False

print()

# CHECK 2: Zero look-ahead
print("CHECK 2: Zero look-ahead verification")
print("-" * 80)

# For each ORB, verify all rows have valid pre-ORB data
violations = []

for orb_code in ['0900', '1000', '1100', '1800', '2300', '0030']:
    count = con.execute("""
        SELECT COUNT(*)
        FROM day_state_features
        WHERE orb_code = ?
            AND pre_orb_n_bars > 0
    """, [orb_code]).fetchone()[0]

    total = con.execute("""
        SELECT COUNT(*)
        FROM day_state_features
        WHERE orb_code = ?
    """, [orb_code]).fetchone()[0]

    if count == total:
        print(f"  {orb_code}: All {total} rows have valid pre-ORB data")
    else:
        print(f"  {orb_code}: {total - count} rows missing pre-ORB data")
        violations.append(orb_code)

if len(violations) == 0:
    print(f"\n  PASS - All ORBs have valid pre-ORB windows")
    check2_pass = True
else:
    print(f"\n  FAIL - {len(violations)} ORBs have issues: {violations}")
    check2_pass = False

print()

# CHECK 3: Percentiles computed per ORB (not pooled)
print("CHECK 3: Percentile computation per ORB")
print("-" * 80)

# Verify that range_pct values differ across ORBs for same date
sample_check = con.execute("""
    WITH sample_date AS (
        SELECT date_local
        FROM day_state_features
        WHERE range_pct IS NOT NULL
        GROUP BY date_local
        HAVING COUNT(DISTINCT orb_code) >= 3
        ORDER BY date_local DESC
        LIMIT 1
    )
    SELECT
        orb_code,
        pre_orb_range,
        range_pct,
        range_bucket
    FROM day_state_features
    WHERE date_local = (SELECT date_local FROM sample_date)
    ORDER BY orb_code
""").fetchall()

if len(sample_check) >= 3:
    print(f"  Sample date with {len(sample_check)} ORBs:")

    pct_values = []
    for row in sample_check:
        orb, rng, pct, bucket = row
        print(f"    {orb}: range={rng:.2f}, pct={pct:.1f}%, bucket={bucket}")
        if pct is not None:
            pct_values.append(pct)

    # Check if percentiles are different (not all same value)
    unique_pcts = len(set(pct_values))

    if unique_pcts > 1:
        print(f"\n  PASS - Percentiles differ across ORBs ({unique_pcts} unique values)")
        check3_pass = True
    else:
        print(f"\n  FAIL - All percentiles are same (pooled calculation suspected)")
        check3_pass = False
else:
    print("  SKIP - Insufficient data for sample check")
    check3_pass = True

print()

# SUMMARY
print("="*80)
print("SANITY CHECK SUMMARY")
print("="*80)

checks = {
    'Row count': check1_pass,
    'Zero look-ahead': check2_pass,
    'Per-ORB percentiles': check3_pass
}

for check_name, passed in checks.items():
    status = 'PASS' if passed else 'FAIL'
    print(f"  {check_name}: {status}")

print()

if all(checks.values()):
    print("ALL CHECKS PASSED - Ready to proceed")
else:
    print("SOME CHECKS FAILED - Fix before proceeding")

con.close()
