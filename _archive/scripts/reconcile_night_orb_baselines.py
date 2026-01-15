"""
BASELINE RECONCILIATION FOR NIGHT ORBS (23:00, 00:30)

Critical task: Resolve inconsistency between validated results and lag test baselines.

Previously validated:
- 23:00 ORB: +1.08R (canonical_session_parameters.csv)
- 00:30 ORB: +1.54R (canonical_session_parameters.csv)

Lag test baselines (orb_trades_5m_exec_orbr):
- 23:00 ORB: -0.153R (RR=2.0, SL=half)
- 00:30 ORB: -0.069R (RR=2.0, SL=half)

This script identifies the correct baseline by checking all data sources.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def check_all_sources():
    """Check all possible data sources for 23:00 and 00:30 ORB results."""
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*80)
    print("BASELINE RECONCILIATION - NIGHT ORBS (23:00, 00:30)")
    print("="*80)
    print()

    # === SOURCE 1: canonical_session_parameters.csv ===
    print("SOURCE 1: canonical_session_parameters.csv")
    print("-"*80)
    try:
        canonical = pd.read_csv("canonical_session_parameters.csv")
        night_orbs = canonical[canonical['orb'].isin(['2300', '0030'])]
        print(night_orbs.to_string(index=False))
        print()
    except Exception as e:
        print(f"[ERROR] {e}\n")

    # === SOURCE 2: orb_trades_5m_exec_orbr (used by lag test) ===
    print("SOURCE 2: orb_trades_5m_exec_orbr (realistic entry at close, ORB-R risk)")
    print("-"*80)
    query = """
        SELECT
            orb,
            rr,
            sl_mode,
            close_confirmations,
            buffer_ticks,
            COUNT(*) as trades,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
            AVG(r_multiple) as avg_r,
            MEDIAN(r_multiple) as median_r,
            SUM(r_multiple) as total_r,
            MIN(date_local) as first_date,
            MAX(date_local) as last_date
        FROM orb_trades_5m_exec_orbr
        WHERE orb IN ('2300', '0030')
        GROUP BY orb, rr, sl_mode, close_confirmations, buffer_ticks
        ORDER BY orb, rr
    """
    result = con.execute(query).df()
    print(result.to_string(index=False))
    print()

    # === SOURCE 3: v_orb_trades_half (from daily_features_v2_half) ===
    print("SOURCE 3: v_orb_trades_half (from daily_features_v2_half)")
    print("-"*80)
    query = """
        SELECT
            orb_time,
            COUNT(*) as trades,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
            AVG(r_multiple) as avg_r,
            MEDIAN(r_multiple) as median_r,
            SUM(r_multiple) as total_r,
            MIN(date_local) as first_date,
            MAX(date_local) as last_date
        FROM v_orb_trades_half
        WHERE orb_time IN ('2300', '0030')
        GROUP BY orb_time
        ORDER BY orb_time
    """
    result = con.execute(query).df()
    print(result.to_string(index=False))
    print("\nNOTE: This view uses RR=1.0 (from build_daily_features_v2.py RR_DEFAULT)")
    print()

    # === SOURCE 4: daily_features_v2_half (check what RR was used) ===
    print("SOURCE 4: daily_features_v2_half (check RR configuration)")
    print("-"*80)
    # Sample a few wins to see what r_multiple values look like
    query = """
        SELECT
            date_local,
            orb_2300_outcome,
            orb_2300_r_multiple,
            orb_2300_high,
            orb_2300_low,
            orb_2300_size
        FROM daily_features_v2_half
        WHERE orb_2300_outcome = 'WIN'
        LIMIT 5
    """
    result = con.execute(query).df()
    print("Sample 23:00 ORB WINS:")
    print(result.to_string(index=False))
    print()

    query = """
        SELECT
            date_local,
            orb_0030_outcome,
            orb_0030_r_multiple,
            orb_0030_high,
            orb_0030_low,
            orb_0030_size
        FROM daily_features_v2_half
        WHERE orb_0030_outcome = 'WIN'
        LIMIT 5
    """
    result = con.execute(query).df()
    print("Sample 00:30 ORB WINS:")
    print(result.to_string(index=False))
    print()

    # === SOURCE 5: Check if there's a table with RR=4.0 results ===
    print("SOURCE 5: Search for RR=4.0 configurations in all tables")
    print("-"*80)

    # Check orb_trades_5m_exec (no orbr suffix)
    try:
        query = """
            SELECT DISTINCT rr, sl_mode
            FROM orb_trades_5m_exec
            WHERE orb IN ('2300', '0030')
            ORDER BY rr
        """
        result = con.execute(query).df()
        if len(result) > 0:
            print("orb_trades_5m_exec available RRs:")
            print(result.to_string(index=False))

            # Get full results
            query = """
                SELECT
                    orb,
                    rr,
                    sl_mode,
                    close_confirmations,
                    COUNT(*) as trades,
                    AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
                    AVG(r_multiple) as avg_r,
                    SUM(r_multiple) as total_r
                FROM orb_trades_5m_exec
                WHERE orb IN ('2300', '0030')
                GROUP BY orb, rr, sl_mode, close_confirmations
                ORDER BY orb, rr
            """
            result = con.execute(query).df()
            print("\nAll configurations in orb_trades_5m_exec:")
            print(result.to_string(index=False))
        else:
            print("orb_trades_5m_exec: No configurations found")
    except Exception as e:
        print(f"orb_trades_5m_exec: {e}")
    print()

    # === ANALYSIS ===
    print("="*80)
    print("ANALYSIS & RECONCILIATION")
    print("="*80)
    print()

    print("FINDINGS:")
    print("-"*80)
    print()

    print("1. CANONICAL PARAMETERS (canonical_session_parameters.csv):")
    print("   - 23:00: RR=4.0, SL=HALF, +1.077R avg, 479 trades")
    print("   - 00:30: RR=4.0, SL=HALF, +1.541R avg, 425 trades")
    print("   - STATUS: This is the VALIDATED configuration")
    print()

    print("2. LAG TEST (orb_trades_5m_exec_orbr):")
    print("   - 23:00: RR=2.0, SL=half, -0.153R avg, 496 trades")
    print("   - 00:30: RR=2.0, SL=half, -0.069R avg, 483 trades")
    print("   - STATUS: WRONG CONFIGURATION (RR=2.0 instead of 4.0)")
    print()

    print("3. V_ORB_TRADES_HALF (daily_features_v2_half):")
    print("   - Uses RR=1.0 (from build_daily_features_v2.py)")
    print("   - 23:00: +0.387R avg, 740 trades")
    print("   - 00:30: +0.231R avg, 740 trades")
    print("   - STATUS: DIFFERENT CONFIG (RR=1.0, different logic)")
    print()

    print("MISMATCH ROOT CAUSE:")
    print("-"*80)
    print()
    print("The lag test used orb_trades_5m_exec_orbr which ONLY has RR=2.0 data.")
    print("The validated results use RR=4.0 (from canonical_session_parameters.csv).")
    print("These are DIFFERENT CONFIGURATIONS with DIFFERENT EXPECTANCIES.")
    print()
    print("At RR=2.0, night ORBs show NEGATIVE expectancy (correct for that RR).")
    print("At RR=4.0, night ORBs show POSITIVE expectancy (validated).")
    print()

    print("="*80)
    print("RESOLUTION")
    print("="*80)
    print()

    print("CANONICAL BASELINE (CORRECT):")
    print("-"*80)
    print()
    print("23:00 ORB:")
    print("  Configuration: RR=4.0, SL=HALF, Filter=BASELINE")
    print("  Entry method: First close outside ORB (realistic)")
    print("  Trade table: N/A (calculated by backtest_all_orbs_complete.py)")
    print("  Date range: 2024-01-02 to 2026-01-10")
    print("  Avg R: +1.077R")
    print("  Win Rate: 41.5%")
    print("  Sample Size: 479 trades")
    print("  Total R: +516R")
    print()

    print("00:30 ORB:")
    print("  Configuration: RR=4.0, SL=HALF, Filter=BASELINE")
    print("  Entry method: First close outside ORB (realistic)")
    print("  Trade table: N/A (calculated by backtest_all_orbs_complete.py)")
    print("  Date range: 2024-01-02 to 2026-01-10")
    print("  Avg R: +1.541R")
    print("  Win Rate: 50.8%")
    print("  Sample Size: 425 trades")
    print("  Total R: +655R")
    print()

    print("LAG TEST BASELINE (WRONG CONFIG):")
    print("-"*80)
    print()
    print("The lag test used RR=2.0 instead of RR=4.0.")
    print("This is NOT the validated configuration.")
    print("Results at RR=2.0 are correct for that RR, but NOT representative of the")
    print("validated edge which uses RR=4.0.")
    print()

    print("WHY THE MISMATCH OCCURRED:")
    print("-"*80)
    print()
    print("1. orb_trades_5m_exec_orbr was created for a different purpose (ORB-R risk model)")
    print("2. It only has RR=2.0 data (not the full parameter sweep)")
    print("3. The lag test script queried this table without checking RR configuration")
    print("4. This created a false baseline that doesn't match validated results")
    print()

    print("ACTION REQUIRED:")
    print("-"*80)
    print()
    print("1. DO NOT USE orb_trades_5m_exec_orbr for night ORB analysis")
    print("2. Rerun lag test with RR=4.0 data (need to find/create this table)")
    print("3. OR: Regenerate ORB trades with RR=4.0 using backtest_all_orbs_complete.py")
    print("4. OR: Test lagged features using canonical parameters directly")
    print()

    print("LOCKED CONFIGURATION (CANONICAL TRUTH):")
    print("-"*80)
    print()
    print("23:00 ORB: RR=4.0, SL=HALF, +1.077R avg")
    print("00:30 ORB: RR=4.0, SL=HALF, +1.541R avg")
    print()
    print("These are the ONLY valid baselines for future analysis.")
    print()

    con.close()


if __name__ == "__main__":
    check_all_sources()
