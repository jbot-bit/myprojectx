"""
MPL Filter Testing - Find Optimal Entry Filters
================================================

Test various filters to improve MPL ORB performance:
1. ORB size filters (skip large/small ORBs)
2. ATR filters (volatility regime)
3. Time-of-day filters (avoid specific patterns)
4. Pre-move travel filters (avoid exhaustion)

Uses same methodology as MGC/NQ optimization.

Usage:
  python test_mpl_filters.py
"""

import duckdb
import csv
from collections import defaultdict

DB_PATH = "gold.db"
SYMBOL = "MPL"
OUTPUT_FILE = "mpl_filter_results.csv"


def test_orb_size_filters():
    """Test ORB size as percentage of ATR"""
    con = duckdb.connect(DB_PATH)

    # Test thresholds: skip if ORB size > X * ATR
    thresholds = [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20]

    results = []

    for orb_time in ["0900", "1000", "1100", "1800", "2300", "0030"]:
        print(f"\nTesting ORB size filters for {orb_time}...")

        # Baseline (no filter)
        query = f"""
        SELECT
            COUNT(CASE WHEN orb_{orb_time}_outcome = 'WIN' THEN 1 END) as wins,
            COUNT(CASE WHEN orb_{orb_time}_outcome IN ('WIN', 'LOSS') THEN 1 END) as trades,
            SUM(COALESCE(orb_{orb_time}_r_multiple, 0)) as total_r
        FROM daily_features_v2_mpl
        WHERE instrument = 'MPL'
        """

        baseline = con.execute(query).fetchone()
        baseline_trades = baseline[1] if baseline else 0
        baseline_wins = baseline[0] if baseline else 0
        baseline_avg_r = (baseline[2] / baseline[1]) if baseline and baseline[1] > 0 else 0

        print(f"  Baseline: {baseline_trades} trades, {baseline_avg_r:+.3f}R avg")

        results.append({
            "orb": orb_time,
            "filter_type": "orb_size",
            "threshold": "none",
            "trades": baseline_trades,
            "wins": baseline_wins,
            "avg_r": baseline_avg_r
        })

        # Test each threshold
        for threshold in thresholds:
            query = f"""
            SELECT
                COUNT(CASE WHEN orb_{orb_time}_outcome = 'WIN' THEN 1 END) as wins,
                COUNT(CASE WHEN orb_{orb_time}_outcome IN ('WIN', 'LOSS') THEN 1 END) as trades,
                SUM(COALESCE(orb_{orb_time}_r_multiple, 0)) as total_r
            FROM daily_features_v2_mpl
            WHERE instrument = 'MPL'
              AND orb_{orb_time}_size / NULLIF(atr_20, 0) <= ?
            """

            filtered = con.execute(query, [threshold]).fetchone()
            filtered_trades = filtered[1] if filtered else 0
            filtered_wins = filtered[0] if filtered else 0
            filtered_avg_r = (filtered[2] / filtered[1]) if filtered and filtered[1] > 0 else 0

            improvement = filtered_avg_r - baseline_avg_r

            if filtered_trades >= baseline_trades * 0.3:  # Keep at least 30% of trades
                print(f"    Threshold {threshold:.2f}: {filtered_trades} trades ({filtered_trades/baseline_trades*100:.0f}%), {filtered_avg_r:+.3f}R ({improvement:+.3f}R)")

                results.append({
                    "orb": orb_time,
                    "filter_type": "orb_size",
                    "threshold": threshold,
                    "trades": filtered_trades,
                    "wins": filtered_wins,
                    "avg_r": filtered_avg_r,
                    "improvement": improvement
                })

    con.close()
    return results


def test_pre_travel_filters():
    """Test pre-ORB travel as exhaustion indicator"""
    con = duckdb.connect(DB_PATH)

    # Test thresholds: skip if pre_orb_travel > X * ATR
    thresholds = [0.5, 1.0, 1.5, 2.0, 2.5]

    results = []

    for orb_time in ["0900", "1000", "1100"]:  # Day ORBs only
        print(f"\nTesting pre-travel filters for {orb_time}...")

        # Baseline
        query = f"""
        SELECT
            COUNT(CASE WHEN orb_{orb_time}_outcome = 'WIN' THEN 1 END) as wins,
            COUNT(CASE WHEN orb_{orb_time}_outcome IN ('WIN', 'LOSS') THEN 1 END) as trades,
            SUM(COALESCE(orb_{orb_time}_r_multiple, 0)) as total_r
        FROM daily_features_v2_mpl
        WHERE instrument = 'MPL'
        """

        baseline = con.execute(query).fetchone()
        baseline_avg_r = (baseline[2] / baseline[1]) if baseline and baseline[1] > 0 else 0

        # Test each threshold
        for threshold in thresholds:
            query = f"""
            SELECT
                COUNT(CASE WHEN orb_{orb_time}_outcome = 'WIN' THEN 1 END) as wins,
                COUNT(CASE WHEN orb_{orb_time}_outcome IN ('WIN', 'LOSS') THEN 1 END) as trades,
                SUM(COALESCE(orb_{orb_time}_r_multiple, 0)) as total_r
            FROM daily_features_v2_mpl
            WHERE instrument = 'MPL'
              AND pre_orb_travel / NULLIF(atr_20, 0) <= ?
            """

            filtered = con.execute(query, [threshold]).fetchone()
            filtered_trades = filtered[1] if filtered else 0
            filtered_avg_r = (filtered[2] / filtered[1]) if filtered and filtered[1] > 0 else 0

            improvement = filtered_avg_r - baseline_avg_r

            if filtered_trades >= baseline[1] * 0.3:
                results.append({
                    "orb": orb_time,
                    "filter_type": "pre_travel",
                    "threshold": threshold,
                    "trades": filtered_trades,
                    "avg_r": filtered_avg_r,
                    "improvement": improvement
                })

    con.close()
    return results


def main():
    print("MPL Filter Testing")
    print("="*80)

    all_results = []

    # Test ORB size filters
    print("\n1. Testing ORB Size Filters...")
    orb_size_results = test_orb_size_filters()
    all_results.extend(orb_size_results)

    # Test pre-travel filters
    print("\n2. Testing Pre-Travel Filters...")
    pre_travel_results = test_pre_travel_filters()
    all_results.extend(pre_travel_results)

    # Save results
    print(f"\n3. Saving results to {OUTPUT_FILE}...")

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["orb", "filter_type", "threshold", "trades", "wins", "avg_r", "improvement"])

        for result in all_results:
            writer.writerow([
                result.get("orb", ""),
                result.get("filter_type", ""),
                result.get("threshold", ""),
                result.get("trades", 0),
                result.get("wins", 0),
                f"{result.get('avg_r', 0):.3f}",
                f"{result.get('improvement', 0):+.3f}"
            ])

    print(f"Results saved to {OUTPUT_FILE}")

    # Print best filters
    print("\n" + "="*80)
    print("BEST FILTERS (by improvement)")
    print("="*80)

    # Find best filter per ORB
    best_by_orb = {}
    for result in all_results:
        orb = result.get("orb")
        improvement = result.get("improvement", 0)

        if orb not in best_by_orb or improvement > best_by_orb[orb].get("improvement", 0):
            best_by_orb[orb] = result

    for orb in ["0900", "1000", "1100", "1800", "2300", "0030"]:
        if orb in best_by_orb:
            result = best_by_orb[orb]
            print(f"\n{orb}: {result.get('filter_type')} <= {result.get('threshold')}")
            print(f"  {result.get('trades')} trades, {result.get('avg_r'):.3f}R avg ({result.get('improvement'):+.3f}R improvement)")

    print("\nDONE")


if __name__ == "__main__":
    main()
