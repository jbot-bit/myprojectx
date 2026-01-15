"""
MANDATORY SANITY CHECKS FOR CYCLE_DATE LOGIC

Verifies that:
1. All 00:30 ORB trades use cycle_date (not calendar date)
2. cycle_date = calendar_date - 1 day for 00:30 ORBs
3. Joins to session_labels work correctly
4. No data loss in joins
"""

import duckdb
import pandas as pd
from zoneinfo import ZoneInfo

TZ_LOCAL = ZoneInfo("Australia/Brisbane")
conn = duckdb.connect("gold.db")

print("="*80)
print("CYCLE_DATE LOGIC VERIFICATION")
print("="*80)

# CHECK 1: Verify 00:30 ORB cycle_date logic
print("\n1. VERIFY 00:30 ORB CYCLE_DATE LOGIC")
print("-" * 80)

result = conn.execute("""
    SELECT
        COUNT(*) as total_0030_trades,
        SUM(CASE WHEN date_local = DATE(entry_ts AT TIME ZONE 'Australia/Brisbane') - INTERVAL '1 day' THEN 1 ELSE 0 END) as correct_cycle_date,
        SUM(CASE WHEN date_local = DATE(entry_ts AT TIME ZONE 'Australia/Brisbane') THEN 1 ELSE 0 END) as wrong_cycle_date
    FROM orb_trades_5m_exec
    WHERE orb = '0030'
    AND entry_ts IS NOT NULL
""").fetchdf()

print(result)

if result['correct_cycle_date'].iloc[0] == result['total_0030_trades'].iloc[0]:
    print("\n[PASS] All 00:30 trades use correct cycle_date (date_local = entry_date - 1)")
else:
    print("\n[FAIL] Some 00:30 trades have incorrect cycle_date")
    exit(1)

# CHECK 2: Sample 5 random 00:30 trades with detailed timestamp breakdown
print("\n\n2. SAMPLE 5 RANDOM 00:30 TRADES")
print("-" * 80)

sample = conn.execute("""
    SELECT
        date_local as cycle_date,
        entry_ts as ts_utc,
        entry_ts AT TIME ZONE 'Australia/Brisbane' as ts_local,
        DATE(entry_ts AT TIME ZONE 'Australia/Brisbane') as trade_date_local,
        entry_price,
        direction
    FROM orb_trades_5m_exec
    WHERE orb = '0030'
    AND entry_ts IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 5
""").fetchdf()

print(sample.to_string(index=False))

# Verify: cycle_date == trade_date_local - 1 day
for idx, row in sample.iterrows():
    cycle_date = row['cycle_date']
    trade_date_local = row['trade_date_local']
    expected_cycle_date = trade_date_local - pd.Timedelta(days=1)

    if cycle_date == expected_cycle_date:
        print(f"\n[PASS] Row {idx+1}: cycle_date={cycle_date} == trade_date_local-1={expected_cycle_date}")
    else:
        print(f"\n[FAIL] Row {idx+1}: cycle_date={cycle_date} != trade_date_local-1={expected_cycle_date}")
        exit(1)

# CHECK 3: Verify join to session_labels (no data loss)
print("\n\n3. VERIFY JOIN TO SESSION_LABELS")
print("-" * 80)

join_check = conn.execute("""
    SELECT
        COUNT(t.date_local) as total_0030_trades,
        COUNT(sl.date_local) as trades_with_labels,
        COUNT(t.date_local) - COUNT(sl.date_local) as missing_labels
    FROM orb_trades_5m_exec t
    LEFT JOIN session_labels sl ON t.date_local = sl.date_local
    WHERE t.orb = '0030'
""").fetchdf()

print(join_check)

if join_check['missing_labels'].iloc[0] == 0:
    print("\n[PASS] PASS: All 00:30 trades successfully joined to session_labels (no data loss)")
else:
    missing = join_check['missing_labels'].iloc[0]
    print(f"\n[WARN] WARNING: {missing} trades missing labels (expected if session_labels has gaps)")

# CHECK 4: Verify other ORBs use same-day cycle_date
print("\n\n4. VERIFY OTHER ORBs USE SAME-DAY CYCLE_DATE")
print("-" * 80)

for orb_time in ['0900', '1000', '1100', '1800', '2300']:
    result = conn.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN date_local = DATE(entry_ts AT TIME ZONE 'Australia/Brisbane') THEN 1 ELSE 0 END) as same_day,
            SUM(CASE WHEN date_local != DATE(entry_ts AT TIME ZONE 'Australia/Brisbane') THEN 1 ELSE 0 END) as different_day
        FROM orb_trades_5m_exec
        WHERE orb = '{orb_time}'
        AND entry_ts IS NOT NULL
    """).fetchdf()

    same_day_pct = (result['same_day'].iloc[0] / result['total'].iloc[0] * 100) if result['total'].iloc[0] > 0 else 0

    print(f"\n{orb_time} ORB: {result['same_day'].iloc[0]:,} / {result['total'].iloc[0]:,} ({same_day_pct:.1f}%) use same-day cycle_date")

    if same_day_pct < 95:
        print(f"  [WARN] WARNING: Expected ~100% same-day for {orb_time} ORB")

# CHECK 5: Verify session_labels coverage
print("\n\n5. SESSION_LABELS COVERAGE")
print("-" * 80)

coverage = conn.execute("""
    SELECT
        COUNT(DISTINCT date_local) as days_in_labels,
        MIN(date_local) as first_date,
        MAX(date_local) as last_date
    FROM session_labels
""").fetchdf()

print(coverage)

orb_date_range = conn.execute("""
    SELECT
        COUNT(DISTINCT date_local) as days_in_trades,
        MIN(date_local) as first_date,
        MAX(date_local) as last_date
    FROM orb_trades_5m_exec
    WHERE orb = '0030'
""").fetchdf()

print("\nORB Trades date range:")
print(orb_date_range)

# CHECK 6: Sample joined data with label verification
print("\n\n6. SAMPLE JOINED DATA (0030 ORB + NY LABELS)")
print("-" * 80)

joined_sample = conn.execute("""
    SELECT
        t.date_local as trade_cycle_date,
        t.entry_ts AT TIME ZONE 'Australia/Brisbane' as entry_local,
        t.direction,
        t.r_multiple,
        sl.ny_net_direction,
        sl.ny_sweep_london_high,
        sl.ny_sweep_london_low,
        sl.ny_exhaustion
    FROM orb_trades_5m_exec t
    LEFT JOIN session_labels sl ON t.date_local = sl.date_local
    WHERE t.orb = '0030'
    AND t.entry_ts IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 5
""").fetchdf()

print(joined_sample.to_string(index=False))

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)

conn.close()
