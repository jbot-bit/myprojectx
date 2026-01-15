"""
Comprehensive Robustness Analysis

Analyzes orb_robustness_results to determine:
1. Which configs (if any) have positive expectancy unfiltered
2. How performance degraded from filtered to unfiltered
3. Which ORB sessions, R:R ratios, and parameters are most robust
4. Strategic recommendations for next steps
"""

import duckdb
import pandas as pd
import json

DB_PATH = "gold.db"

def analyze_robustness_results():
    print("="*100)
    print("ROBUSTNESS ANALYSIS REPORT")
    print("="*100)
    print()

    con = duckdb.connect(DB_PATH)

    # ============================================================================
    # 1. OVERALL SUMMARY
    # ============================================================================
    print("1. OVERALL SUMMARY")
    print("-" * 100)

    summary = con.execute("""
        SELECT
            COUNT(DISTINCT CONCAT(orb, '-', close_confirmations, '-', rr, '-', sl_mode, '-', buffer_ticks)) as total_configs,
            COUNT(*) as total_rows,
            SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as actual_trades,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
            ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) /
                  NULLIF(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END), 0), 1) as win_rate,
            ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r,
            ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE NULL END), 2) as avg_r
        FROM orb_robustness_results
    """).fetchone()

    print(f"Total configs tested: {summary[0]}")
    print(f"Total rows: {summary[1]:,}")
    print(f"Actual trades (WIN/LOSS): {summary[2]:,}")
    print(f"Wins: {summary[3]:,}")
    print(f"Losses: {summary[4]:,}")
    print(f"Win rate: {summary[5]}%")
    print(f"Total R: {summary[6]:+.1f}R")
    print(f"Average R per trade: {summary[7]:+.2f}R")
    print()

    # ============================================================================
    # 2. BEST PERFORMING CONFIGS (TOP 20)
    # ============================================================================
    print("2. BEST PERFORMING CONFIGS (TOP 20)")
    print("-" * 100)

    best_configs = con.execute("""
        SELECT
            orb,
            close_confirmations as cc,
            rr,
            sl_mode,
            buffer_ticks as buffer,
            COUNT(*) as days,
            SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as trades,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) /
                  NULLIF(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END), 0), 1) as wr,
            ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r,
            ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE NULL END), 3) as avg_r
        FROM orb_robustness_results
        GROUP BY orb, close_confirmations, rr, sl_mode, buffer_ticks
        ORDER BY total_r DESC
        LIMIT 20
    """).df()

    print(best_configs.to_string(index=False))
    print()

    # ============================================================================
    # 3. POSITIVE EXPECTANCY CONFIGS (if any)
    # ============================================================================
    print("3. POSITIVE EXPECTANCY CONFIGS")
    print("-" * 100)

    positive_configs = con.execute("""
        SELECT
            orb,
            close_confirmations as cc,
            rr,
            sl_mode,
            buffer_ticks as buffer,
            SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as trades,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) /
                  NULLIF(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END), 0), 1) as wr,
            ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r,
            ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE NULL END), 3) as avg_r
        FROM orb_robustness_results
        GROUP BY orb, close_confirmations, rr, sl_mode, buffer_ticks
        HAVING SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END) > 0
        ORDER BY total_r DESC
    """).df()

    if len(positive_configs) > 0:
        print(f"Found {len(positive_configs)} configs with positive expectancy!")
        print()
        print(positive_configs.to_string(index=False))
    else:
        print("WARNING: NO CONFIGS WITH POSITIVE EXPECTANCY FOUND")
        print("All 69 configs lose money without filters applied.")
    print()

    # ============================================================================
    # 4. PERFORMANCE BY ORB SESSION
    # ============================================================================
    print("4. PERFORMANCE BY ORB SESSION")
    print("-" * 100)

    by_orb = con.execute("""
        SELECT
            orb,
            COUNT(DISTINCT CONCAT(close_confirmations, '-', rr, '-', sl_mode, '-', buffer_ticks)) as configs,
            SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as trades,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) /
                  NULLIF(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END), 0), 1) as wr,
            ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r,
            ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE NULL END), 3) as avg_r
        FROM orb_robustness_results
        GROUP BY orb
        ORDER BY total_r DESC
    """).df()

    print(by_orb.to_string(index=False))
    print()

    # ============================================================================
    # 5. PERFORMANCE BY R:R RATIO
    # ============================================================================
    print("5. PERFORMANCE BY R:R RATIO")
    print("-" * 100)

    by_rr = con.execute("""
        SELECT
            rr,
            COUNT(DISTINCT CONCAT(orb, '-', close_confirmations, '-', sl_mode, '-', buffer_ticks)) as configs,
            SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as trades,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) /
                  NULLIF(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END), 0), 1) as wr,
            ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r,
            ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE NULL END), 3) as avg_r
        FROM orb_robustness_results
        GROUP BY rr
        ORDER BY rr
    """).df()

    print(by_rr.to_string(index=False))
    print()

    # ============================================================================
    # 6. PERFORMANCE BY CLOSE CONFIRMATIONS
    # ============================================================================
    print("6. PERFORMANCE BY CLOSE CONFIRMATIONS")
    print("-" * 100)

    by_cc = con.execute("""
        SELECT
            close_confirmations as cc,
            COUNT(DISTINCT CONCAT(orb, '-', rr, '-', sl_mode, '-', buffer_ticks)) as configs,
            SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as trades,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) /
                  NULLIF(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END), 0), 1) as wr,
            ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r,
            ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE NULL END), 3) as avg_r
        FROM orb_robustness_results
        GROUP BY close_confirmations
        ORDER BY cc
    """).df()

    print(by_cc.to_string(index=False))
    print()

    # ============================================================================
    # 7. PERFORMANCE BY SL MODE
    # ============================================================================
    print("7. PERFORMANCE BY STOP LOSS MODE")
    print("-" * 100)

    by_sl = con.execute("""
        SELECT
            CASE WHEN sl_mode = '' THEN 'full' ELSE sl_mode END as sl_mode,
            COUNT(DISTINCT CONCAT(orb, '-', close_confirmations, '-', rr, '-', buffer_ticks)) as configs,
            SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as trades,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) /
                  NULLIF(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END), 0), 1) as wr,
            ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r,
            ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE NULL END), 3) as avg_r
        FROM orb_robustness_results
        GROUP BY sl_mode
        ORDER BY total_r DESC
    """).df()

    print(by_sl.to_string(index=False))
    print()

    # ============================================================================
    # 8. LOAD FILTERED RESULTS FOR COMPARISON
    # ============================================================================
    print("8. FILTERED VS UNFILTERED DEGRADATION")
    print("-" * 100)

    # Load candidate configs with original filtered performance
    with open('candidate_configs.json', 'r') as f:
        candidates = json.load(f)

    print(f"Loaded {len(candidates)} candidate configs from filtered backtest")
    print()

    print("NOTE: Filtered results table (orb_exec_results) uses different schema")
    print("Cannot directly compare due to schema mismatch (variant field vs individual params)")
    print("These candidate configs were extracted from filtered backtests that looked promising WITH filters.")
    print("The robustness test shows they do NOT hold up without filters.")
    print()

    # ============================================================================
    # 9. WORST PERFORMING CONFIGS (BOTTOM 20)
    # ============================================================================
    print("9. WORST PERFORMING CONFIGS (BOTTOM 20)")
    print("-" * 100)

    worst_configs = con.execute("""
        SELECT
            orb,
            close_confirmations as cc,
            rr,
            sl_mode,
            buffer_ticks as buffer,
            SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as trades,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) /
                  NULLIF(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END), 0), 1) as wr,
            ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r,
            ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE NULL END), 3) as avg_r
        FROM orb_robustness_results
        GROUP BY orb, close_confirmations, rr, sl_mode, buffer_ticks
        ORDER BY total_r ASC
        LIMIT 20
    """).df()

    print(worst_configs.to_string(index=False))
    print()

    con.close()

    # ============================================================================
    # 10. STRATEGIC RECOMMENDATIONS
    # ============================================================================
    print("="*100)
    print("STRATEGIC RECOMMENDATIONS")
    print("="*100)
    print()

    if len(positive_configs) == 0:
        print("WARNING: CRITICAL FINDING - Zero configs show positive expectancy without filters")
        print()
        print("This means:")
        print("  1. The candidate configs extracted from filtered backtests do NOT have real edge")
        print("  2. The filters (MAX_STOP, ASIA_TP_CAP) were masking the true performance")
        print("  3. High R:R ratios (2.5x-3.0x) appear too aggressive for these ORB strategies")
        print()
        print("RECOMMENDED NEXT STEPS:")
        print()
        print("Option A: SEARCH FOR UNFILTERED EDGE (Recommended)")
        print("  - Run exhaustive parameter sweep WITHOUT filters from the start")
        print("  - Test lower R:R ratios (1.0x, 1.5x, 2.0x)")
        print("  - Test different ORB sessions (1800 shows better performance)")
        print("  - Look for configs that are profitable BEFORE applying any filters")
        print()
        print("Option B: ACCEPT FILTERS AS PART OF STRATEGY")
        print("  - If you believe the filters represent legitimate trading constraints")
        print("  - Re-run with filters (MAX_STOP, ASIA_TP_CAP) included")
        print("  - Understand that edge depends on consistently applying these filters")
        print()
        print("Option C: INVESTIGATE 1800 ORB DEEPER")
        print("  - Only 3 configs tested for 1800 ORB, but it shows least losses")
        print("  - Run dedicated sweep on 1800 with more parameter combinations")
        print("  - Test 1800 with lower R:R ratios")
        print()
        print("Option D: RETHINK STRATEGY ENTIRELY")
        print("  - Consider that momentum ORB breakouts may not be the right approach")
        print("  - Explore mean reversion (fade ORB breaks)")
        print("  - Test different entry mechanisms beyond close confirmations")
        print("  - Look at different timeframes or ORB durations")
        print()
    else:
        print(f"SUCCESS: GOOD NEWS - Found {len(positive_configs)} configs with positive expectancy!")
        print()
        print("RECOMMENDED NEXT STEPS:")
        print("  1. Further test these positive configs with walk-forward validation")
        print("  2. Analyze trade quality and distribution")
        print("  3. Consider ensemble approach using multiple positive configs")
        print("  4. Run Monte Carlo simulations on these configs")
        print()

    print("="*100)

if __name__ == "__main__":
    analyze_robustness_results()
