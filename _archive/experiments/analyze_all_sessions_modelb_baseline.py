"""
Baseline analysis for all 6 sessions with Model B execution
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

con = duckdb.connect(DB_PATH, read_only=True)

print("="*80)
print("MODEL B BASELINE ANALYSIS - ALL 6 SESSIONS")
print("="*80)
print()

sessions = ['0900', '1000', '1100', '1800', '2300', '0030']

print("FULL-SL (stop at opposite ORB edge):")
print("-"*80)
print(f"{'Session':<10} {'Trades':<10} {'Avg R':<12} {'Total R':<12} {'Win%':<10}")
print("-"*80)

for orb in ['0900', '1000', '1100', '1800', '2300', '0030']:
    result = con.execute(f"""
        SELECT
            COUNT(*) as n_trades,
            AVG(r_multiple) as avg_r,
            SUM(r_multiple) as total_r,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
        FROM v_orb_trades_v3_modelb
        WHERE orb_time = ?
            AND break_dir IN ('UP', 'DOWN')
            AND outcome IN ('WIN', 'LOSS')
    """, [orb]).fetchone()

    if not result or result[0] == 0:
        print(f"  {orb}: No trades")
        continue

    n_trades, avg_r, win_rate = result
    print(f"{orb}:")
    print(f"  Trades: {n_trades}")
    print(f"  Avg R: {avg_r:+.3f}R")
    print(f"  Win rate: {win_rate:.1f}%")
    print()

print("="*80)
print("HALF-SL BASELINE (stop at ORB mid)")
print("="*80)
print()

for orb in ['0900', '1000', '1100', '1800', '2300', '0030']:
    result = con.execute("""
        SELECT
            COUNT(*) as n_trades,
            AVG(r_multiple) as avg_r,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
        FROM v_orb_trades_v3_modelb_half
        WHERE orb_time = ?
            AND break_dir IN ('UP', 'DOWN')
            AND outcome IN ('WIN', 'LOSS')
    """, [orb]).fetchone()

    if not result or result[0] == 0:
        print(f"  {orb}: No trades")
        continue

    n_trades, avg_r, win_rate = result
    print(f"{orb} ORB:")
    print(f"  Trades: {n_trades}")
    print(f"  Avg R: {avg_r:+.3f}R")
    print(f"  Win rate: {win_rate:.1f}%")
    print()

con.close()

print("="*80)
print("BASELINE ANALYSIS COMPLETE")
print("="*80)
print()
print("Next step: Run state-filtered analysis for each session")
print()
