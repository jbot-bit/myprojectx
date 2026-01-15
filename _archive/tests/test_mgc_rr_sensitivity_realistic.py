"""
MGC RR Sensitivity Test - Realistic Execution
Tests RR 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0 with realistic 1m execution
Half SL mode (stop at ORB midpoint)

RR mapping to ORB size multiples (with HALF SL):
- RR 1.5 = 0.75x ORB size
- RR 2.0 = 1.0x ORB size
- RR 3.0 = 1.5x ORB size
- RR 4.0 = 2.0x ORB size
- RR 5.0 = 2.5x ORB size
- RR 6.0 = 3.0x ORB size
"""

import duckdb
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

TZ_LOCAL = ZoneInfo("Australia/Brisbane")
DB_PATH = "gold.db"
SYMBOL = "MGC"

# Test all 6 ORBs
ORB_TIMES = ["0900", "1000", "1100", "1800", "2300", "0030"]
RR_VALUES = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0]

def test_rr_for_orb(conn, orb_time: str, rr: float):
    """
    Test a specific RR ratio for one ORB using MAE/MFE data
    """
    query = f"""
    WITH orb_data AS (
        SELECT
            date_local,
            orb_{orb_time}_high as orb_high,
            orb_{orb_time}_low as orb_low,
            orb_{orb_time}_break_dir as break_dir,
            orb_{orb_time}_mae as mae_r,
            orb_{orb_time}_mfe as mfe_r,
            orb_{orb_time}_outcome as baseline_outcome
        FROM daily_features_v2_half
        WHERE instrument = 'MGC'
        AND orb_{orb_time}_break_dir IN ('UP', 'DOWN')
    ),
    outcomes AS (
        SELECT
            date_local,
            break_dir,
            mae_r,
            mfe_r,
            baseline_outcome,
            -- Outcome based on MAE/MFE
            CASE
                WHEN mfe_r >= {rr} AND mae_r < 1.0 THEN 'WIN'
                WHEN mfe_r >= {rr} AND mae_r >= 1.0 THEN 'LOSS'  -- hit stop first (same bar)
                WHEN mae_r >= 1.0 THEN 'LOSS'
                ELSE 'OPEN'  -- never hit target
            END as outcome,
            -- R multiple
            CASE
                WHEN mfe_r >= {rr} AND mae_r < 1.0 THEN {rr}
                WHEN mfe_r >= {rr} AND mae_r >= 1.0 THEN -1.0
                WHEN mae_r >= 1.0 THEN -1.0
                ELSE -1.0  -- treat OPEN as loss (conservative)
            END as r_multiple
        FROM orb_data
    )
    SELECT
        COUNT(*) as trades,
        SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
        ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
        ROUND(AVG(r_multiple), 4) as avg_r,
        ROUND(SUM(r_multiple), 2) as total_r
    FROM outcomes
    """

    result = conn.execute(query).fetchone()
    return {
        'orb': orb_time,
        'rr': rr,
        'trades': result[0],
        'wins': result[1],
        'win_rate': result[2],
        'avg_r': result[3],
        'total_r': result[4]
    }

def main():
    print("=" * 80)
    print("MGC RR SENSITIVITY TEST - REALISTIC EXECUTION")
    print("=" * 80)
    print(f"Stop Loss Mode: HALF (ORB midpoint)")
    print(f"Entry Method: First 1m close outside ORB (realistic)")
    print(f"RR Values: {RR_VALUES}")
    print()
    print("RR to ORB size mapping (with HALF SL):")
    print("  RR 1.0 = 0.50x ORB size (CURRENT PRODUCTION)")
    print("  RR 1.5 = 0.75x ORB size")
    print("  RR 2.0 = 1.0x ORB size")
    print("  RR 3.0 = 1.5x ORB size")
    print("  RR 4.0 = 2.0x ORB size")
    print("  RR 5.0 = 2.5x ORB size")
    print("  RR 6.0 = 3.0x ORB size")
    print("  RR 8.0 = 4.0x ORB size")
    print("=" * 80)
    print()

    conn = duckdb.connect(DB_PATH, read_only=True)

    results = []

    for orb_time in ORB_TIMES:
        print(f"\n{'=' * 80}")
        print(f"Testing {orb_time} ORB")
        print(f"{'=' * 80}")

        orb_results = []
        for rr in RR_VALUES:
            result = test_rr_for_orb(conn, orb_time, rr)
            orb_results.append(result)
            results.append(result)

        # Display results for this ORB
        df = pd.DataFrame(orb_results)
        print(df.to_string(index=False))

        # Find optimal
        optimal = df.loc[df['avg_r'].idxmax()]
        print(f"\nOptimal for {orb_time}: RR {optimal['rr']} -> {optimal['avg_r']:.4f}R avg, {optimal['win_rate']:.1f}% WR")

        # Show ORB size equivalent
        orb_multiple = optimal['rr'] / 2.0  # because HALF SL means 1R = 0.5x ORB
        print(f"  (This is {orb_multiple:.2f}x ORB size)")

    conn.close()

    # Overall summary
    print(f"\n\n{'=' * 80}")
    print("OVERALL SUMMARY - OPTIMAL RR BY ORB")
    print(f"{'=' * 80}")

    df_all = pd.DataFrame(results)
    optimal_by_orb = df_all.loc[df_all.groupby('orb')['avg_r'].idxmax()]
    optimal_by_orb = optimal_by_orb.sort_values('avg_r', ascending=False)

    print(optimal_by_orb[['orb', 'rr', 'trades', 'win_rate', 'avg_r', 'total_r']].to_string(index=False))

    print(f"\n{'=' * 80}")
    print("KEY FINDINGS")
    print(f"{'=' * 80}")

    # Compare to current production (RR 1.0)
    current_prod = df_all[df_all['rr'] == 1.0]
    current_avg = current_prod['avg_r'].mean()
    optimal_avg = optimal_by_orb['avg_r'].mean()

    print(f"\nCurrent Production (RR 1.0 across all ORBs):")
    print(f"  Average expectancy: {current_avg:.4f}R")
    print(f"  (Targeting 0.5x ORB size)")

    print(f"\nOptimal RR Configuration (best for each ORB):")
    print(f"  Average expectancy: {optimal_avg:.4f}R")
    print(f"  Improvement: {((optimal_avg / current_avg - 1) * 100):.1f}%")

    # Check if higher RR helps
    high_rr = df_all[df_all['rr'] >= 4.0]
    if high_rr['avg_r'].max() > current_avg:
        print(f"\nYES: Higher RR targets (2-3x ORB size) ARE profitable!")
        best_high = high_rr.loc[high_rr['avg_r'].idxmax()]
        print(f"  Best: {best_high['orb']} ORB at RR {best_high['rr']} = {best_high['avg_r']:.4f}R")
    else:
        print(f"\nNO: Higher RR targets (2-3x ORB size) NOT worth it")
        print(f"  Best high RR: {high_rr['avg_r'].max():.4f}R vs current {current_avg:.4f}R")

    # Save results
    df_all.to_csv('mgc_rr_sensitivity_realistic.csv', index=False)
    print(f"\nResults saved to: mgc_rr_sensitivity_realistic.csv")

    print(f"\n{'=' * 80}")

if __name__ == "__main__":
    main()
