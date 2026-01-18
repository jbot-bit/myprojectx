#!/usr/bin/env python3
"""
Consolidate daily_features_v2 tables and remove unused v1.
"""

import duckdb
from datetime import datetime

conn = duckdb.connect('gold.db')

print("=" * 70)
print("CONSOLIDATING DAILY_FEATURES_V2 TABLES")
print("=" * 70)

# Check what we have
print("\n[1/5] Checking source tables...")
mgc_count = conn.execute("SELECT COUNT(*) FROM daily_features_v2").fetchone()[0]
nq_count = conn.execute("SELECT COUNT(*) FROM daily_features_v2_nq").fetchone()[0]
mpl_count = conn.execute("SELECT COUNT(*) FROM daily_features_v2_mpl").fetchone()[0]
v1_count = conn.execute("SELECT COUNT(*) FROM daily_features").fetchone()[0]

print(f"  daily_features_v2 (MGC): {mgc_count:,} rows")
print(f"  daily_features_v2_nq (NQ): {nq_count:,} rows")
print(f"  daily_features_v2_mpl (MPL): {mpl_count:,} rows")
print(f"  daily_features (v1, UNUSED): {v1_count:,} rows")

expected = mgc_count + nq_count + mpl_count
print(f"  Expected total: {expected:,} rows")

# Check schemas - NQ might be missing rsi_at_orb
print("\n[2/5] Checking schemas...")
mgc_cols = len(conn.execute("DESCRIBE daily_features_v2").fetchall())
nq_cols = len(conn.execute("DESCRIBE daily_features_v2_nq").fetchall())
mpl_cols = len(conn.execute("DESCRIBE daily_features_v2_mpl").fetchall())

print(f"  daily_features_v2: {mgc_cols} columns")
print(f"  daily_features_v2_nq: {nq_cols} columns")
print(f"  daily_features_v2_mpl: {mpl_cols} columns")

if nq_cols < mgc_cols:
    print(f"  [WARN] NQ missing {mgc_cols - nq_cols} columns - will add NULLs")

# Consolidate v2 tables
print("\n[3/5] Consolidating daily_features_v2...")

if nq_cols == 85:  # Missing rsi_at_orb
    conn.execute("""
        CREATE TABLE daily_features_v2_consolidated AS
        SELECT * FROM daily_features_v2
        UNION ALL
        SELECT * FROM daily_features_v2_mpl
        UNION ALL
        SELECT
            date_local, instrument, pre_asia_high, pre_asia_low, pre_asia_range,
            pre_london_high, pre_london_low, pre_london_range, pre_ny_high, pre_ny_low, pre_ny_range,
            asia_high, asia_low, asia_range, london_high, london_low, london_range,
            ny_high, ny_low, ny_range, asia_type_code, london_type_code, pre_ny_type_code,
            orb_0900_high, orb_0900_low, orb_0900_size, orb_0900_break_dir, orb_0900_outcome, orb_0900_r_multiple,
            orb_1000_high, orb_1000_low, orb_1000_size, orb_1000_break_dir, orb_1000_outcome, orb_1000_r_multiple,
            orb_1100_high, orb_1100_low, orb_1100_size, orb_1100_break_dir, orb_1100_outcome, orb_1100_r_multiple,
            orb_1800_high, orb_1800_low, orb_1800_size, orb_1800_break_dir, orb_1800_outcome, orb_1800_r_multiple,
            orb_2300_high, orb_2300_low, orb_2300_size, orb_2300_break_dir, orb_2300_outcome, orb_2300_r_multiple,
            orb_0030_high, orb_0030_low, orb_0030_size, orb_0030_break_dir, orb_0030_outcome, orb_0030_r_multiple,
            rsi_at_0030, atr_20,
            orb_0900_mae, orb_0900_mfe, orb_0900_stop_price, orb_0900_risk_ticks,
            orb_1000_mae, orb_1000_mfe, orb_1000_stop_price, orb_1000_risk_ticks,
            orb_1100_mae, orb_1100_mfe, orb_1100_stop_price, orb_1100_risk_ticks,
            orb_1800_mae, orb_1800_mfe, orb_1800_stop_price, orb_1800_risk_ticks,
            orb_2300_mae, orb_2300_mfe, orb_2300_stop_price, orb_2300_risk_ticks,
            orb_0030_mae, orb_0030_mfe, orb_0030_stop_price, orb_0030_risk_ticks,
            NULL as rsi_at_orb
        FROM daily_features_v2_nq
    """)
else:
    # All schemas match
    conn.execute("""
        CREATE TABLE daily_features_v2_consolidated AS
        SELECT * FROM daily_features_v2
        UNION ALL
        SELECT * FROM daily_features_v2_nq
        UNION ALL
        SELECT * FROM daily_features_v2_mpl
    """)

actual = conn.execute("SELECT COUNT(*) FROM daily_features_v2_consolidated").fetchone()[0]
print(f"  Consolidated: {actual:,} rows")

if actual != expected:
    raise ValueError(f"Mismatch! Expected {expected:,}, got {actual:,}")

print(f"  [OK] Verified")

# Show breakdown
print("\n  Breakdown by instrument:")
breakdown = conn.execute("""
    SELECT instrument, COUNT(*) as cnt
    FROM daily_features_v2_consolidated
    GROUP BY instrument
    ORDER BY instrument
""").fetchall()

for inst, cnt in breakdown:
    print(f"    {inst}: {cnt:,} rows")

# Archive old tables
print("\n[4/5] Archiving old tables...")
timestamp = datetime.now().strftime("%Y%m%d_%H%M")

old_tables = [
    'daily_features',  # v1 - unused
    'daily_features_v2',
    'daily_features_v2_nq',
    'daily_features_v2_mpl',
    'daily_features_v2_half',  # Experimental
]

for table in old_tables:
    try:
        conn.execute(f"ALTER TABLE {table} RENAME TO _archive_{timestamp}_{table}")
        print(f"  Archived: {table}")
    except:
        print(f"  Skipped: {table} (doesn't exist)")

# Promote consolidated
print("\n[5/5] Promoting consolidated table...")
conn.execute("ALTER TABLE daily_features_v2_consolidated RENAME TO daily_features_v2")
print(f"  [OK] Renamed to: daily_features_v2")

# Final verification
final_count = conn.execute("SELECT COUNT(*) FROM daily_features_v2").fetchone()[0]
instruments = conn.execute("""
    SELECT instrument, COUNT(*), MIN(date_local), MAX(date_local)
    FROM daily_features_v2
    GROUP BY instrument
    ORDER BY instrument
""").fetchall()

print("\n" + "=" * 70)
print("CONSOLIDATION COMPLETE")
print("=" * 70)
print(f"\ndaily_features_v2: {final_count:,} total rows")
for inst, cnt, min_date, max_date in instruments:
    print(f"  {inst}: {cnt:,} rows ({min_date} to {max_date})")

conn.close()

print("\n[NEXT] Update data_loader.py to use unified table")
