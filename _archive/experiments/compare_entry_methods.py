"""
COMPARE ENTRY METHODS

Compare three entry timing approaches:
1. ORB-edge theoretical (from worst_case_parameters.csv)
2. 5-minute close entry (from delayed_entry_results.csv)
3. 1-minute close entry (from orb_trades_1m_exec_nofilters)

All use worst-case intrabar resolution.
All use same RR/SL per ORB.
Isolates entry timing effect only.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def main():
    print("=" * 80)
    print("ENTRY METHOD COMPARISON")
    print("=" * 80)
    print()
    print("Three entry methods tested:")
    print("  1. ORB-edge theoretical: Entry at ORB high/low")
    print("  2. 5-minute close: First 5m close outside ORB")
    print("  3. 1-minute close: First 1m close outside ORB")
    print()
    print("All use:")
    print("  - Same RR/SL per ORB")
    print("  - Worst-case intrabar resolution")
    print("  - Same dataset (2024-01-02 to 2026-01-10)")
    print()

    # Load optimal parameters
    optimal_df = pd.read_csv('worst_case_parameters.csv', dtype={'orb': str})

    # Load 5-minute entry results
    delayed_df = pd.read_csv('delayed_entry_results.csv', dtype={'orb': str})
    delayed_baseline = delayed_df[delayed_df['delay_bars'] == 0]

    # Load 1-minute entry results from database
    con = duckdb.connect(DB_PATH, read_only=True)

    results = []

    for _, opt_row in optimal_df.iterrows():
        orb = opt_row['orb']
        optimal_rr = opt_row['optimal_rr']

        # 1. ORB-edge theoretical (from worst-case backtest)
        orb_edge_r = opt_row['avg_r']
        orb_edge_trades = opt_row['trades']

        # 2. 5-minute close (from delayed entry test)
        delayed_row = delayed_baseline[delayed_baseline['orb'] == orb]
        if len(delayed_row) > 0:
            five_min_r = delayed_row.iloc[0]['avg_r']
            five_min_trades = delayed_row.iloc[0]['trades']
        else:
            five_min_r = None
            five_min_trades = None

        # 3. 1-minute close (from database)
        one_min_result = con.execute("""
            SELECT
                COUNT(*) as trades,
                AVG(r_multiple) as avg_r,
                SUM(r_multiple) as total_r,
                SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as wr
            FROM orb_trades_1m_exec_nofilters
            WHERE orb = ?
                AND close_confirmations = 1
                AND rr = ?
        """, [orb, optimal_rr]).fetchone()

        if one_min_result and one_min_result[0] > 0:
            one_min_trades, one_min_r, one_min_total_r, one_min_wr = one_min_result
        else:
            one_min_r = None
            one_min_trades = None

        results.append({
            'orb': orb,
            'rr': optimal_rr,
            'orb_edge_r': orb_edge_r,
            'orb_edge_trades': orb_edge_trades,
            'five_min_r': five_min_r,
            'five_min_trades': five_min_trades,
            'one_min_r': one_min_r,
            'one_min_trades': one_min_trades
        })

    con.close()

    results_df = pd.DataFrame(results)

    print("=" * 80)
    print("RESULTS BY ORB")
    print("=" * 80)
    print()

    for _, row in results_df.iterrows():
        orb = row['orb']
        rr = row['rr']

        print(f"{orb} ORB (RR={rr}):")
        print("-" * 80)

        # ORB-edge theoretical
        print(f"  1. ORB-edge (theoretical):  {row['orb_edge_r']:+.3f}R avg ({int(row['orb_edge_trades'])} trades)")

        # 1-minute close
        if row['one_min_r'] is not None:
            one_min_r = row['one_min_r']
            degradation_1m = one_min_r - row['orb_edge_r']
            pct_1m = (degradation_1m / row['orb_edge_r'] * 100) if row['orb_edge_r'] != 0 else 0
            print(f"  2. 1-minute close:          {one_min_r:+.3f}R avg ({int(row['one_min_trades'])} trades) | {degradation_1m:+.3f}R ({pct_1m:+.1f}%)")
        else:
            print(f"  2. 1-minute close:          NO DATA")

        # 5-minute close
        if row['five_min_r'] is not None:
            five_min_r = row['five_min_r']
            degradation_5m = five_min_r - row['orb_edge_r']
            pct_5m = (degradation_5m / row['orb_edge_r'] * 100) if row['orb_edge_r'] != 0 else 0
            print(f"  3. 5-minute close:          {five_min_r:+.3f}R avg ({int(row['five_min_trades'])} trades) | {degradation_5m:+.3f}R ({pct_5m:+.1f}%)")
        else:
            print(f"  3. 5-minute close:          NO DATA")

        # Which is better?
        if row['one_min_r'] is not None and row['five_min_r'] is not None:
            if one_min_r > five_min_r:
                improvement = one_min_r - five_min_r
                print(f"  → 1-minute is BETTER by {improvement:+.3f}R")
            elif five_min_r > one_min_r:
                improvement = five_min_r - one_min_r
                print(f"  → 5-minute is BETTER by {improvement:+.3f}R")
            else:
                print(f"  → Same performance")

        print()

    print("=" * 80)
    print("SYSTEM-WIDE COMPARISON")
    print("=" * 80)
    print()

    # Calculate system-wide averages
    orb_edge_avg = results_df['orb_edge_r'].mean()
    one_min_avg = results_df['one_min_r'].mean()
    five_min_avg = results_df['five_min_r'].mean()

    orb_edge_total = (results_df['orb_edge_r'] * results_df['orb_edge_trades']).sum() / results_df['orb_edge_trades'].sum()
    one_min_total = (results_df['one_min_r'] * results_df['one_min_trades']).sum() / results_df['one_min_trades'].sum()
    five_min_total = (results_df['five_min_r'] * results_df['five_min_trades']).sum() / results_df['five_min_trades'].sum()

    print(f"System-wide average R per trade:")
    print(f"  1. ORB-edge (theoretical):  {orb_edge_total:+.3f}R")
    print(f"  2. 1-minute close:          {one_min_total:+.3f}R ({(one_min_total - orb_edge_total):+.3f}R, {((one_min_total - orb_edge_total) / orb_edge_total * 100):+.1f}%)")
    print(f"  3. 5-minute close:          {five_min_total:+.3f}R ({(five_min_total - orb_edge_total):+.3f}R, {((five_min_total - orb_edge_total) / orb_edge_total * 100):+.1f}%)")
    print()

    print("VERDICT:")
    print()

    if one_min_total > 0:
        print(f"✅ 1-MINUTE CLOSE: POSITIVE ({one_min_total:+.3f}R avg)")
        print(f"   Better than 5-minute by: {(one_min_total - five_min_total):+.3f}R ({((one_min_total - five_min_total) / abs(five_min_total) * 100):+.1f}%)")
        print()
        print("   REASON: Earlier entry captures more of the move")
        print("   TRADE-OFF: Slightly worse than ORB-edge theoretical, but REALISTIC")
    else:
        print(f"❌ 1-MINUTE CLOSE: NEGATIVE ({one_min_total:+.3f}R avg)")
        print(f"   Better than 5-minute by: {(one_min_total - five_min_total):+.3f}R")
        print()
        print("   CONCLUSION: Even earlier entry does not save the system")

    print()

    print("=" * 80)
    print("ENTRY TIMING ANALYSIS")
    print("=" * 80)
    print()

    print("Key insights:")
    print()
    print("1. THEORETICAL BEST (ORB-edge):")
    print(f"   - Avg R: {orb_edge_total:+.3f}R")
    print(f"   - Assumption: Entry at exact ORB high/low")
    print(f"   - Reality: IMPOSSIBLE (price has already moved)")
    print()

    print("2. REALISTIC BEST (1-minute close):")
    print(f"   - Avg R: {one_min_total:+.3f}R")
    print(f"   - Entry: First 1m close outside ORB")
    print(f"   - Degradation from theoretical: {(one_min_total - orb_edge_total):+.3f}R ({((one_min_total - orb_edge_total) / orb_edge_total * 100):+.1f}%)")
    print(f"   - Verdict: {'POSITIVE' if one_min_total > 0 else 'NEGATIVE'}")
    print()

    print("3. REALISTIC CONSERVATIVE (5-minute close):")
    print(f"   - Avg R: {five_min_total:+.3f}R")
    print(f"   - Entry: First 5m close outside ORB")
    print(f"   - Degradation from theoretical: {(five_min_total - orb_edge_total):+.3f}R ({((five_min_total - orb_edge_total) / orb_edge_total * 100):+.1f}%)")
    print(f"   - Verdict: NEGATIVE")
    print()

    print("CONCLUSION:")
    print()

    if one_min_total > 0:
        print("✅ SYSTEM IS VIABLE WITH 1-MINUTE ENTRY")
        print()
        print("Next steps:")
        print("  1. Use 1-minute entry as baseline")
        print("  2. Reoptimize RR/SL parameters for 1-minute entry")
        print("  3. Test with filters (MAX_STOP, TP_CAP)")
        print("  4. Complete pressure-test suite")
        print("  5. Deploy if all tests pass")
    else:
        print("❌ SYSTEM FAILS EVEN WITH 1-MINUTE ENTRY")
        print()
        print("Options:")
        print("  1. Test limit order entry (wait for pullback)")
        print("  2. Test tighter entry criteria (within X ticks of ORB)")
        print("  3. Test alternative strategies")
        print("  4. Abandon ORB breakout approach")

    print()

    # Save comparison
    results_df.to_csv('entry_method_comparison.csv', index=False)
    print("Files saved: entry_method_comparison.csv")
    print()

if __name__ == "__main__":
    main()
