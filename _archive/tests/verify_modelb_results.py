"""
Verify Model B results are correct (entry-anchored risk, not ORB-anchored)
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"
SYMBOL = "MGC"

con = duckdb.connect(DB_PATH, read_only=True)

print("="*80)
print("MODEL B VERIFICATION")
print("="*80)
print()

# Check if tables exist
tables = con.execute("SHOW TABLES").fetchall()
table_names = [t[0] for t in tables]

if 'daily_features_v3_modelb' not in table_names:
    print("ERROR: daily_features_v3_modelb table not found!")
    print("Run: python build_daily_features_v3_modelb.py 2024-01-01 2026-01-10")
    con.close()
    exit(1)

if 'daily_features_v3_modelb_half' not in table_names:
    print("ERROR: daily_features_v3_modelb_half table not found!")
    print("Run: python build_daily_features_v3_modelb.py 2024-01-01 2026-01-10 --sl-mode half")
    con.close()
    exit(1)

print("[OK] Model B tables exist")
print()

# Check row counts
full_count = con.execute("SELECT COUNT(*) FROM daily_features_v3_modelb").fetchone()[0]
half_count = con.execute("SELECT COUNT(*) FROM daily_features_v3_modelb_half").fetchone()[0]

print(f"Rows in daily_features_v3_modelb: {full_count}")
print(f"Rows in daily_features_v3_modelb_half: {half_count}")
print()

if full_count < 700:
    print("WARNING: Expected ~740 rows for 2024-01-01 to 2026-01-10")
    print(f"         Got only {full_count} rows")
    print()

# Sample verification: Check a few trades
print("="*80)
print("SAMPLE TRADES VERIFICATION")
print("="*80)
print()

sample = con.execute("""
    SELECT
        date_local,
        orb_0900_high,
        orb_0900_low,
        orb_0900_size,
        orb_0900_break_dir,
        orb_0900_entry_price,
        orb_0900_stop_price,
        orb_0900_target_price,
        orb_0900_risk_ticks,
        orb_0900_reward_ticks,
        orb_0900_outcome,
        orb_0900_r_multiple
    FROM daily_features_v3_modelb_half
    WHERE orb_0900_break_dir IN ('UP', 'DOWN')
        AND orb_0900_outcome IN ('WIN', 'LOSS')
    LIMIT 5
""").df()

print("Sample 0900 trades with HALF-SL (Model B):")
print()

for idx, row in sample.iterrows():
    date_local = row['date_local']
    orb_high = row['orb_0900_high']
    orb_low = row['orb_0900_low']
    orb_size = row['orb_0900_size']
    orb_mid = (orb_high + orb_low) / 2.0
    break_dir = row['orb_0900_break_dir']
    entry_price = row['orb_0900_entry_price']
    stop_price = row['orb_0900_stop_price']
    target_price = row['orb_0900_target_price']
    risk_ticks = row['orb_0900_risk_ticks']
    reward_ticks = row['orb_0900_reward_ticks']
    outcome = row['orb_0900_outcome']
    r_multiple = row['orb_0900_r_multiple']

    print(f"Date: {date_local}")
    print(f"  ORB: {orb_low:.2f} - {orb_high:.2f} (size={orb_size:.2f}, mid={orb_mid:.2f})")
    print(f"  Break: {break_dir}")
    print(f"  Entry: {entry_price:.2f}")
    print(f"  Stop: {stop_price:.2f}")
    print(f"  Target: {target_price:.2f}")
    print()

    # Verify entry-anchored risk
    expected_risk = abs(entry_price - stop_price) / 0.1
    expected_reward = abs(target_price - entry_price) / 0.1

    print(f"  Risk (ticks): {risk_ticks:.1f}")
    print(f"  Expected risk (entry to stop): {expected_risk:.1f}")

    if abs(risk_ticks - expected_risk) > 0.5:
        print(f"  [ERROR] Risk mismatch! Expected {expected_risk:.1f}, got {risk_ticks:.1f}")
        print(f"          This means risk is NOT entry-anchored!")
    else:
        print(f"  [OK] Risk is entry-anchored")

    print()
    print(f"  Reward (ticks): {reward_ticks:.1f}")
    print(f"  Expected reward: {expected_reward:.1f}")

    if abs(reward_ticks - expected_reward) > 0.5:
        print(f"  [ERROR] Reward mismatch!")
    else:
        print(f"  [OK] Reward is entry-anchored")

    print()
    print(f"  R:R ratio: {reward_ticks/risk_ticks:.2f}:1" if risk_ticks > 0 else "  R:R ratio: N/A")
    print(f"  Outcome: {outcome} ({r_multiple:+.2f}R)")
    print()
    print("-"*80)
    print()

# Compare with old (incorrect) table
print("="*80)
print("COMPARISON WITH OLD (INCORRECT) TABLE")
print("="*80)
print()

if 'daily_features_v2_half' in table_names:
    old_0900 = con.execute("""
        SELECT
            COUNT(*) as n_trades,
            AVG(orb_0900_r_multiple) as avg_r
        FROM daily_features_v2_half
        WHERE orb_0900_break_dir IN ('UP', 'DOWN')
            AND orb_0900_outcome IN ('WIN', 'LOSS')
    """).fetchone()

    new_0900 = con.execute("""
        SELECT
            COUNT(*) as n_trades,
            AVG(orb_0900_r_multiple) as avg_r
        FROM daily_features_v3_modelb_half
        WHERE orb_0900_break_dir IN ('UP', 'DOWN')
            AND orb_0900_outcome IN ('WIN', 'LOSS')
    """).fetchone()

    print("0900 ORB with HALF-SL:")
    print(f"  OLD (ORB-anchored): {old_0900[0]} trades, {old_0900[1]:+.3f}R avg")
    print(f"  NEW (entry-anchored): {new_0900[0]} trades, {new_0900[1]:+.3f}R avg")
    print()

    if old_0900[1] is not None and new_0900[1] is not None:
        delta = new_0900[1] - old_0900[1]
        print(f"  Delta: {delta:+.3f}R")
        print()

        if delta < -0.1:
            print("  [EXPECTED] New (correct) results are worse than old (inflated) results")
            print("             This confirms old table used ORB-anchored risk (fake edge)")
        elif abs(delta) < 0.05:
            print("  [WARNING] Results are similar - verify calculation is truly different")
        else:
            print("  [UNEXPECTED] New results are BETTER than old - verify logic")
    print()
else:
    print("Old table (daily_features_v2_half) not found - skipping comparison")
    print()

con.close()

print("="*80)
print("VERIFICATION COMPLETE")
print("="*80)
print()
print("If all checks passed, Model B tables are ready to use!")
print()
print("Next steps:")
print("  1. Use v_orb_trades_v3_modelb_half for analysis")
print("  2. Re-run edge discovery with new tables")
print("  3. Compare results to old (ORB-anchored) edges")
print()
print("IMPORTANT: Do NOT use old tables (daily_features_v2_half, v_orb_trades_half)")
print("           They use incorrect ORB-anchored risk calculation!")
print()
