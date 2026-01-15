"""
Simple Filter Testing - Universal (MGC & NQ)
===========================================

Tests basic filters to improve win rate/expectancy:
1. ORB Size filter (avoid ranges that are too small/large)
2. Session Range filter (require minimum volatility)
3. Time-of-day combinations

Usage:
  python scripts/test_filters.py NQ          # Test all ORBs for NQ
  python scripts/test_filters.py MGC        # Test all ORBs for MGC
  python scripts/test_filters.py NQ 0030    # Test specific ORB only
"""

import sys
import duckdb
import numpy as np
from typing import Dict, List, Optional

DB_PATH = "gold.db"

# ORB times to test
ORBS = ['0900', '1000', '1100', '1800', '2300', '0030']


def get_table_name(symbol: str) -> str:
    """Get feature table name for symbol"""
    if symbol == "MGC":
        return "daily_features_v2"
    elif symbol == "NQ":
        return "daily_features_v2_nq"
    else:
        raise ValueError(f"Unknown symbol: {symbol}")


def get_tick_size(symbol: str) -> float:
    """Get tick size for symbol"""
    if symbol == "MGC":
        return 0.1
    elif symbol == "NQ":
        return 0.25
    else:
        raise ValueError(f"Unknown symbol: {symbol}")


def test_orb_filters(con: duckdb.DuckDBPyConnection, symbol: str, orb: str) -> Dict:
    """
    Test various filters for a specific ORB.

    Returns dict with filter test results.
    """
    table = get_table_name(symbol)
    tick_size = get_tick_size(symbol)

    # Get baseline (no filter)
    baseline_query = f"""
        SELECT
            COUNT(*) as trades,
            SUM(CASE WHEN orb_{orb}_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            AVG(orb_{orb}_r_multiple) as avg_r,
            SUM(orb_{orb}_r_multiple) as total_r
        FROM {table}
        WHERE orb_{orb}_break_dir IN ('UP', 'DOWN')
            AND orb_{orb}_outcome IN ('WIN', 'LOSS')
    """

    baseline = con.execute(baseline_query).fetchone()
    baseline_results = {
        'filter': 'NONE (baseline)',
        'trades': baseline[0],
        'wins': baseline[1],
        'win_rate': (baseline[1] / baseline[0] * 100) if baseline[0] > 0 else 0,
        'avg_r': baseline[2] if baseline[2] else 0,
        'total_r': baseline[3] if baseline[3] else 0,
        'improvement': 0
    }

    results = [baseline_results]

    # Filter 1: ORB Size (medium-sized ranges only)
    # Get median ORB size
    size_query = f"""
        SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY orb_{orb}_size)
        FROM {table}
        WHERE orb_{orb}_size IS NOT NULL
    """
    median_size = con.execute(size_query).fetchone()[0]

    if median_size:
        # Test: ORB size between 50% and 150% of median
        size_filter_query = f"""
            SELECT
                COUNT(*) as trades,
                SUM(CASE WHEN orb_{orb}_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                AVG(orb_{orb}_r_multiple) as avg_r,
                SUM(orb_{orb}_r_multiple) as total_r
            FROM {table}
            WHERE orb_{orb}_break_dir IN ('UP', 'DOWN')
                AND orb_{orb}_outcome IN ('WIN', 'LOSS')
                AND orb_{orb}_size BETWEEN ? AND ?
        """
        size_result = con.execute(size_filter_query, [median_size * 0.5, median_size * 1.5]).fetchone()

        if size_result[0] > 0:
            win_rate = size_result[1] / size_result[0] * 100
            improvement = ((size_result[2] - baseline_results['avg_r']) / abs(baseline_results['avg_r']) * 100) if baseline_results['avg_r'] != 0 else 0

            results.append({
                'filter': f'ORB size 50-150% of median ({median_size / tick_size:.0f} ticks)',
                'trades': size_result[0],
                'wins': size_result[1],
                'win_rate': win_rate,
                'avg_r': size_result[2] if size_result[2] else 0,
                'total_r': size_result[3] if size_result[3] else 0,
                'improvement': improvement
            })

    # Filter 2: Large ORBs only (top 50%)
    large_orb_query = f"""
        SELECT
            COUNT(*) as trades,
            SUM(CASE WHEN orb_{orb}_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            AVG(orb_{orb}_r_multiple) as avg_r,
            SUM(orb_{orb}_r_multiple) as total_r
        FROM {table}
        WHERE orb_{orb}_break_dir IN ('UP', 'DOWN')
            AND orb_{orb}_outcome IN ('WIN', 'LOSS')
            AND orb_{orb}_size >= ?
    """
    large_result = con.execute(large_orb_query, [median_size]).fetchone()

    if large_result[0] > 0:
        win_rate = large_result[1] / large_result[0] * 100
        improvement = ((large_result[2] - baseline_results['avg_r']) / abs(baseline_results['avg_r']) * 100) if baseline_results['avg_r'] != 0 else 0

        results.append({
            'filter': f'Large ORBs only (>= median {median_size / tick_size:.0f} ticks)',
            'trades': large_result[0],
            'wins': large_result[1],
            'win_rate': win_rate,
            'avg_r': large_result[2] if large_result[2] else 0,
            'total_r': large_result[3] if large_result[3] else 0,
            'improvement': improvement
        })

    # Filter 3: Small ORBs only (bottom 50%)
    small_orb_query = f"""
        SELECT
            COUNT(*) as trades,
            SUM(CASE WHEN orb_{orb}_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            AVG(orb_{orb}_r_multiple) as avg_r,
            SUM(orb_{orb}_r_multiple) as total_r
        FROM {table}
        WHERE orb_{orb}_break_dir IN ('UP', 'DOWN')
            AND orb_{orb}_outcome IN ('WIN', 'LOSS')
            AND orb_{orb}_size < ?
    """
    small_result = con.execute(small_orb_query, [median_size]).fetchone()

    if small_result[0] > 0:
        win_rate = small_result[1] / small_result[0] * 100
        improvement = ((small_result[2] - baseline_results['avg_r']) / abs(baseline_results['avg_r']) * 100) if baseline_results['avg_r'] != 0 else 0

        results.append({
            'filter': f'Small ORBs only (< median {median_size / tick_size:.0f} ticks)',
            'trades': small_result[0],
            'wins': small_result[1],
            'win_rate': win_rate,
            'avg_r': small_result[2] if small_result[2] else 0,
            'total_r': small_result[3] if small_result[3] else 0,
            'improvement': improvement
        })

    return {
        'orb': orb,
        'symbol': symbol,
        'results': results,
        'best': max(results, key=lambda x: x['avg_r'])
    }


def print_results(symbol: str, filter_results: List[Dict]):
    """Print formatted filter test results"""

    print("=" * 120)
    print(f"FILTER TESTING - {symbol}")
    print("=" * 120)
    print()

    for orb_result in filter_results:
        orb = orb_result['orb']
        results = orb_result['results']
        best = orb_result['best']

        print(f"{orb} ORB:")
        print("-" * 120)
        print(f"{'Filter':<60} {'Trades':<10} {'Win Rate':<12} {'Avg R':<12} {'Total R':<12} {'vs Baseline':<12}")
        print("-" * 120)

        for r in results:
            improvement_str = f"{r['improvement']:+.1f}%" if r['improvement'] != 0 else "-"
            marker = " <-- BEST" if r == best and r['improvement'] > 0 else ""
            print(f"{r['filter']:<60} {r['trades']:<10} {r['win_rate']:<12.1f}% {r['avg_r']:<+12.3f} {r['total_r']:<+12.1f} {improvement_str:<12}{marker}")

        print()

        # Summary
        if best['improvement'] > 0:
            print(f"  BEST FILTER: {best['filter']}")
            print(f"    Improvement: {best['improvement']:+.1f}% ({results[0]['avg_r']:+.3f}R -> {best['avg_r']:+.3f}R)")
            if best['improvement'] > 15:
                print(f"    Status: SIGNIFICANT (>15%)")
            elif best['improvement'] > 5:
                print(f"    Status: MODERATE (5-15%)")
            else:
                print(f"    Status: MARGINAL (<5%, likely noise)")
        else:
            print(f"  NO FILTER IMPROVES - Use baseline (no filter)")

        print()


def main():
    """Run filter testing"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    symbol = sys.argv[1].upper()
    if symbol not in ['MGC', 'NQ']:
        print(f"Error: Symbol must be MGC or NQ, got: {symbol}")
        sys.exit(1)

    # Optional: specific ORB
    specific_orb = None
    if len(sys.argv) >= 3 and sys.argv[2] in ORBS:
        specific_orb = sys.argv[2]

    # Determine which ORBs to test
    orbs_to_test = [specific_orb] if specific_orb else ORBS

    # Connect to database
    con = duckdb.connect(DB_PATH, read_only=True)

    try:
        # Test each ORB
        all_results = []
        for orb in orbs_to_test:
            print(f"Testing filters for {orb} ORB ({symbol})...")
            result = test_orb_filters(con, symbol, orb)
            all_results.append(result)

        # Print results
        print()
        print_results(symbol, all_results)

        # Save to CSV
        import csv
        output_file = f"outputs/{symbol}_filter_tests.csv"
        with open(output_file, 'w', newline='') as f:
            fieldnames = ['orb', 'filter', 'trades', 'wins', 'win_rate', 'avg_r', 'total_r', 'improvement']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for orb_result in all_results:
                for r in orb_result['results']:
                    writer.writerow({
                        'orb': orb_result['orb'],
                        'filter': r['filter'],
                        'trades': r['trades'],
                        'wins': r['wins'],
                        'win_rate': r['win_rate'],
                        'avg_r': r['avg_r'],
                        'total_r': r['total_r'],
                        'improvement': r['improvement']
                    })

        print(f"Results saved to: {output_file}")
        print()

    finally:
        con.close()


if __name__ == "__main__":
    main()
