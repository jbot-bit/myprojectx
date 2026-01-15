"""
Compare old (ORB-anchored risk) vs new (entry-anchored risk) Model B results

This shows the impact of correct risk calculation on all sessions.
"""

import duckdb

DB_PATH = "gold.db"

con = duckdb.connect(DB_PATH, read_only=True)

print("="*80)
print("OLD VS NEW COMPARISON (ORB-Anchored vs Entry-Anchored Risk)")
print("="*80)
print()

# Check if old tables exist
tables = con.execute("SHOW TABLES").fetchall()
table_names = [t[0] for t in tables]

if 'daily_features_v2_half' not in table_names or 'v_orb_trades_half' not in table_names:
    print("WARNING: Old tables not found (daily_features_v2_half, v_orb_trades_half)")
    print("         This is expected if you've deleted them.")
    print()
    print("Comparison cannot be performed.")
    con.close()
    exit(0)

print("Comparing HALF-SL results (old ORB-anchored vs new entry-anchored):")
print("-"*80)
print(f"{'Session':<10} {'Old Trades':<12} {'Old Avg R':<12} {'New Trades':<12} {'New Avg R':<12} {'Delta':<12}")
print("-"*80)

sessions = ['0900', '1000', '1100', '1800', '2300', '0030']

for orb in sessions:
    # Old (ORB-anchored)
    old = con.execute("""
        SELECT
            COUNT(*) as n_trades,
            AVG(r_multiple) as avg_r
        FROM v_orb_trades_half
        WHERE orb_time = ?
            AND break_dir IN ('UP', 'DOWN')
            AND outcome IN ('WIN', 'LOSS')
    """, [orb]).fetchone()

    # New (entry-anchored)
    new = con.execute("""
        SELECT
            COUNT(*) as n_trades,
            AVG(r_multiple) as avg_r
        FROM v_orb_trades_v3_modelb_half
        WHERE orb_time = ?
            AND break_dir IN ('UP', 'DOWN')
            AND outcome IN ('WIN', 'LOSS')
    """, [orb]).fetchone()

    if old and new and old[0] > 0 and new[0] > 0:
        delta = new[1] - old[1]
        print(f"{orb:<10} {old[0]:<12} {old[1]:+.3f}R      {new[0]:<12} {new[1]:+.3f}R      {delta:+.3f}R")
    elif new and new[0] > 0:
        print(f"{orb:<10} {'N/A':<12} {'N/A':<12} {new[0]:<12} {new[1]:+.3f}R      N/A")
    else:
        print(f"{orb:<10} No data")

print()

# Detailed analysis for 0900 (the most problematic)
print("="*80)
print("DETAILED 0900 COMPARISON")
print("="*80)
print()

old_0900 = con.execute("""
    SELECT
        COUNT(*) as n_trades,
        AVG(r_multiple) as avg_r,
        SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
        AVG(risk_ticks) as avg_risk_ticks
    FROM v_orb_trades_half
    WHERE orb_time = '0900'
        AND break_dir IN ('UP', 'DOWN')
        AND outcome IN ('WIN', 'LOSS')
""").fetchone()

new_0900 = con.execute("""
    SELECT
        COUNT(*) as n_trades,
        AVG(r_multiple) as avg_r,
        SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
        AVG(risk_ticks) as avg_risk_ticks
    FROM v_orb_trades_v3_modelb_half
    WHERE orb_time = '0900'
        AND break_dir IN ('UP', 'DOWN')
        AND outcome IN ('WIN', 'LOSS')
""").fetchone()

if old_0900 and new_0900:
    print("OLD (ORB-anchored risk):")
    print(f"  Trades: {old_0900[0]}")
    print(f"  Avg R: {old_0900[1]:+.3f}R")
    print(f"  Win rate: {old_0900[2]:.1f}%")
    print(f"  Avg risk: {old_0900[3]:.1f} ticks")
    print()

    print("NEW (entry-anchored risk):")
    print(f"  Trades: {new_0900[0]}")
    print(f"  Avg R: {new_0900[1]:+.3f}R")
    print(f"  Win rate: {new_0900[2]:.1f}%")
    print(f"  Avg risk: {new_0900[3]:.1f} ticks")
    print()

    print("ANALYSIS:")
    print(f"  R delta: {new_0900[1] - old_0900[1]:+.3f}R")
    print(f"  Risk inflation: {new_0900[3] / old_0900[3]:.2f}x" if old_0900[3] > 0 else "  Risk inflation: N/A")
    print()

    if new_0900[1] < old_0900[1]:
        print("  [EXPECTED] New results are worse - old results were inflated by")
        print("             incorrect ORB-anchored risk calculation.")
        print()
        print("  Why:")
        print("    - Old: Risk = ORB_mid to ORB_edge (tiny for 0900)")
        print("    - New: Risk = Entry to Stop (includes slippage)")
        print("    - Entry slippage often exceeded ORB size for tiny ORBs")
        print("    - This made targets unrealistically easy to hit in old backtest")
    elif new_0900[1] > old_0900[1]:
        print("  [UNEXPECTED] New results are BETTER than old.")
        print("               Verify calculation logic!")
    else:
        print("  Results are similar - may indicate calculation issue")

print()

con.close()

print("="*80)
print("COMPARISON COMPLETE")
print("="*80)
print()
print("Key takeaway:")
print("  - Old (ORB-anchored) results were FAKE EDGES for tiny ORBs")
print("  - New (entry-anchored) results are HONEST")
print("  - Expect worse performance on small ORBs (0900, 1000, 1100)")
print("  - Larger ORBs (1800, 0030) should be less affected")
print()
