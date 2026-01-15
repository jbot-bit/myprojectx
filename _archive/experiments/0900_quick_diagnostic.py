"""
Quick diagnostic: Check if 1R dominates at 0900 (win rate perspective)
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

con = duckdb.connect(DB_PATH, read_only=True)

print("="*80)
print("0900 ORB BASELINE - CHECKING 1R DOMINANCE")
print("="*80)
print()

# Check baseline at different R:R ratios
for rr in [1.0, 1.5, 2.0]:
    result = con.execute("""
        SELECT
            COUNT(*) as n_trades,
            AVG(r_multiple) as avg_r,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
            SUM(CASE WHEN r_multiple >= 1.0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pct_reach_1r
        FROM orb_trades_1m_exec_nofilters
        WHERE orb = '0900'
            AND close_confirmations = 1
            AND rr = ?
    """, [rr]).fetchone()

    n_trades, avg_r, win_rate, pct_reach_1r = result

    print(f"R:R = {rr}:")
    print(f"  Trades: {n_trades}")
    print(f"  Avg R: {avg_r:+.3f}R")
    print(f"  Win rate: {win_rate:.1f}%")
    print(f"  % reaching 1R: {pct_reach_1r:.1f}%")
    print()

# Check direction bias
print("-"*80)
print("DIRECTIONAL ANALYSIS:")
print("-"*80)
print()

direction_check = con.execute("""
    SELECT
        direction,
        COUNT(*) as n_trades,
        AVG(r_multiple) as avg_r,
        SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
    FROM orb_trades_1m_exec_nofilters
    WHERE orb = '0900'
        AND close_confirmations = 1
        AND rr = 1.0
    GROUP BY direction
""").df()

for _, row in direction_check.iterrows():
    print(f"{row['direction']}:")
    print(f"  {row['n_trades']} trades, {row['avg_r']:+.3f}R avg, {row['win_rate']:.1f}% win rate")
    print()

con.close()
