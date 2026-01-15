"""
SQL checks for Half SL data quality
- Per-ORB counts
- MAE/MFE non-null rates
"""

import duckdb

con = duckdb.connect("gold.db")

print("=" * 100)
print("SQL CHECKS: Half SL Mode (daily_features_v2_half)")
print("=" * 100)
print()

# Check 1: Total row count
total_days = con.execute("SELECT COUNT(DISTINCT date_local) FROM daily_features_v2_half").fetchone()[0]
print(f"Total days in table: {total_days}")
print()

# Check 2: Per-ORB counts and non-null MAE/MFE rates
print("=" * 100)
print("Per-ORB Counts and Non-Null Rates")
print("=" * 100)
print()

result = con.execute("""
    SELECT
        orb_time,
        COUNT(*) AS n_days,
        SUM(CASE WHEN orb_high IS NOT NULL THEN 1 ELSE 0 END) AS orb_exists,
        SUM(CASE WHEN break_dir IS NOT NULL AND break_dir != 'NONE' THEN 1 ELSE 0 END) AS n_breaks,
        SUM(CASE WHEN mae IS NOT NULL THEN 1 ELSE 0 END) AS mae_ok,
        SUM(CASE WHEN mfe IS NOT NULL THEN 1 ELSE 0 END) AS mfe_ok
    FROM v_orb_trades_half
    GROUP BY orb_time
    ORDER BY orb_time
""").fetchall()

print(f"{'ORB':<8} {'Days':<8} {'ORB Exists':<12} {'Breaks':<10} {'MAE OK':<10} {'MFE OK':<10} {'MAE%':<10} {'MFE%':<10}")
print("-" * 100)

for row in result:
    orb_time, n_days, orb_exists, n_breaks, mae_ok, mfe_ok = row
    mae_pct = (mae_ok / n_breaks * 100) if n_breaks > 0 else 0
    mfe_pct = (mfe_ok / n_breaks * 100) if n_breaks > 0 else 0

    print(f"{orb_time:<8} {n_days:<8} {orb_exists:<12} {n_breaks:<10} {mae_ok:<10} {mfe_ok:<10} {mae_pct:<10.1f} {mfe_pct:<10.1f}")

print()
print("Expected:")
print("- Days should equal total days in table")
print("- ORB Exists should be high (missing only on holidays/weekends)")
print("- MAE% and MFE% should be ~100% for days with breaks")
print()

# Check 3: Sample of recent trades
print("=" * 100)
print("Sample Recent Trades (Last 10 Breaks per Asia ORB)")
print("=" * 100)
print()

for orb_time in ['0900', '1000', '1100']:
    print(f"--- ORB {orb_time} ---")

    sample = con.execute(f"""
        SELECT
            date_local,
            break_dir,
            outcome,
            ROUND(orb_size / 0.1, 1) as orb_ticks,
            ROUND(risk_ticks, 1) as risk_ticks,
            ROUND(mae, 3) as mae_r,
            ROUND(mfe, 3) as mfe_r
        FROM v_orb_trades_half
        WHERE orb_time = '{orb_time}'
          AND break_dir IS NOT NULL
          AND break_dir != 'NONE'
        ORDER BY date_local DESC
        LIMIT 10
    """).fetchall()

    if sample:
        for row in sample:
            date_local, break_dir, outcome, orb_ticks, risk_ticks, mae_r, mfe_r = row
            print(f"  {date_local} | {break_dir:>4} | {outcome:<8} | ORB:{orb_ticks:>5} ticks | R:{risk_ticks:>5} ticks | MAE:{mae_r:>6}R | MFE:{mfe_r:>6}R")
    else:
        print("  No breaks found")

    print()

# Check 4: Verify ORB-anchored R = 0.5 * ORB size for Half SL
print("=" * 100)
print("Verify Half SL: R = 0.5 * ORB size")
print("=" * 100)
print()

verification = con.execute("""
    SELECT
        orb_time,
        COUNT(*) as n,
        AVG(ABS(risk_ticks - (orb_size / 0.1 / 2.0))) as avg_diff
    FROM v_orb_trades_half
    WHERE orb_high IS NOT NULL
    GROUP BY orb_time
    ORDER BY orb_time
""").fetchall()

print(f"{'ORB':<8} {'Count':<10} {'Avg Diff (ticks)':<20}")
print("-" * 50)

for row in verification:
    orb_time, n, avg_diff = row
    print(f"{orb_time:<8} {n:<10} {avg_diff:<20.6f}")

print()
print("Expected: Avg diff should be ~0.0 (within floating point precision)")
print()

con.close()

print("=" * 100)
print("CHECKS COMPLETE")
print("=" * 100)
