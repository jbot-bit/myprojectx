"""
Analyze distribution of liquidity reaction results to check for outcome inflation.
"""

import duckdb
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
import sys

sys.path.insert(0, '.')
from test_liquidity_reaction_minimal import LiquidityReactionTest

def analyze_distribution():
    test = LiquidityReactionTest()

    start_date = date(2024, 1, 1)
    end_date = date(2026, 1, 10)

    trades = []
    cur = start_date

    while cur <= end_date:
        result = test.test_single_day(cur)
        if result:
            trades.append(result)
        cur += timedelta(days=1)

    test.close()

    if not trades:
        print("No trades found")
        return

    r_values = sorted([t["r_multiple"] for t in trades])

    print("="*80)
    print("DISTRIBUTION ANALYSIS")
    print("="*80)
    print()

    print(f"Total trades: {len(trades)}")
    print(f"Total R: {sum(r_values):.2f}R")
    print(f"Average R: {sum(r_values)/len(r_values):.2f}R")
    print()

    # Percentiles
    def percentile(data, pct):
        idx = int(len(data) * pct / 100)
        return data[min(idx, len(data)-1)]

    print(f"Min R: {r_values[0]:.2f}R")
    print(f"10th percentile: {percentile(r_values, 10):.2f}R")
    print(f"25th percentile: {percentile(r_values, 25):.2f}R")
    print(f"Median (50th): {percentile(r_values, 50):.2f}R")
    print(f"75th percentile: {percentile(r_values, 75):.2f}R")
    print(f"90th percentile: {percentile(r_values, 90):.2f}R")
    print(f"Max R: {r_values[-1]:.2f}R")
    print()

    # Top 5 trades
    top_5 = sorted(trades, key=lambda t: t["r_multiple"], reverse=True)[:5]
    top_5_r = sum(t["r_multiple"] for t in top_5)
    top_5_pct = (top_5_r / sum(r_values)) * 100

    print("Top 5 trades:")
    for i, t in enumerate(top_5, 1):
        print(f"  #{i}: {t['date']} | {t['r_multiple']:+.2f}R | {t['outcome']}")
    print()
    print(f"Top 5 contribute: {top_5_r:.2f}R ({top_5_pct:.1f}% of total)")
    print()

    # Bottom 5 trades
    bottom_5 = sorted(trades, key=lambda t: t["r_multiple"])[:5]
    print("Bottom 5 trades:")
    for i, t in enumerate(bottom_5, 1):
        print(f"  #{i}: {t['date']} | {t['r_multiple']:+.2f}R | {t['outcome']}")
    print()

    # Fragility check
    print("="*80)
    print("FRAGILITY CHECK")
    print("="*80)
    print()

    if percentile(r_values, 50) <= 0:
        print("[!] WARNING: Median R <= 0 - edge is driven by outliers")
    else:
        print("[+] Median R > 0 - edge is distributed")
    print()

    if top_5_pct > 40:
        print(f"[!] WARNING: Top 5 trades = {top_5_pct:.1f}% of total - edge is fragile")
    else:
        print(f"[+] Top 5 trades = {top_5_pct:.1f}% of total - edge is robust")
    print()

if __name__ == "__main__":
    analyze_distribution()
