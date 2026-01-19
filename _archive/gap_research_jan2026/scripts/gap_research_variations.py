"""
Gap Continuation - Test Multiple Variations

Test robustness across:
- Stop types: gap_midpoint, gap_origin, 50% gap, 75% gap
- Target R: 1R, 1.5R, 2R, 3R, 5R
- Entry filters: none, only large gaps (>0.1%), only small gaps

This validates whether the edge is robust or parameter-sensitive.
"""

import duckdb
import pandas as pd
import numpy as np
import sys

DB_PATH = r"C:\Users\sydne\OneDrive\myprojectx\gold.db"

print("="*70)
print("GAP CONTINUATION - ROBUSTNESS TESTING")
print("="*70)

# Load data
try:
    conn = duckdb.connect(DB_PATH, read_only=True)
except Exception as e:
    print(f"\nDatabase locked. Run: taskkill /PID 17164 /F")
    sys.exit(1)

print("\nLoading data (sampled)...")
query = """
WITH numbered AS (
    SELECT ts_utc, open, high, low, close,
        ROW_NUMBER() OVER (ORDER BY ts_utc) as rn
    FROM bars_1m
    WHERE symbol = 'MGC' AND ts_utc >= '2024-01-01'
)
SELECT ts_utc, open, high, low, close
FROM numbered WHERE rn % 5 = 0
ORDER BY ts_utc
"""

sample = conn.execute(query).fetchdf()
conn.close()

print(f"  Loaded {len(sample):,} bars")

# Detect gaps
sample['ts'] = pd.to_datetime(sample['ts_utc'], utc=True)
sample['time_diff_min'] = sample['ts'].diff().dt.total_seconds() / 60
sample['prev_close'] = sample['close'].shift(1)

gaps = sample[sample['time_diff_min'] > 60].copy()
gaps['gap_size'] = gaps['open'] - gaps['prev_close']
gaps['gap_pct'] = (gaps['gap_size'] / gaps['prev_close'] * 100).abs()
gaps['direction'] = np.where(gaps['gap_size'] > 0, 1, -1)

print(f"  Found {len(gaps)} gaps")

# IS/OOS split
split_date = pd.to_datetime('2025-06-15', utc=True)

def test_variation(gaps_subset, stop_pct, target_r, name):
    """Test a specific configuration"""

    trades = []

    for idx, gap in gaps_subset.iterrows():
        entry_time = gap['ts']
        entry_px = gap['open']
        direction = gap['direction']
        prev_close = gap['prev_close']

        # Calculate stop based on stop_pct (0.5 = midpoint, 1.0 = origin)
        gap_range = abs(entry_px - prev_close)
        stop_px = entry_px - direction * gap_range * stop_pct

        stop_dist = abs(entry_px - stop_px)
        if stop_dist < 0.01:
            continue

        target_px = entry_px + direction * stop_dist * target_r

        # Get future bars
        future = sample[sample['ts'] > entry_time].head(200)
        if len(future) == 0:
            continue

        # Simulate
        hit = False
        for _, bar in future.iterrows():
            if direction == 1:
                if bar['low'] <= stop_px:
                    trades.append({'entry': entry_time, 'pnl_r': -1.0})
                    hit = True
                    break
                if bar['high'] >= target_px:
                    trades.append({'entry': entry_time, 'pnl_r': target_r})
                    hit = True
                    break
            else:
                if bar['high'] >= stop_px:
                    trades.append({'entry': entry_time, 'pnl_r': -1.0})
                    hit = True
                    break
                if bar['low'] <= target_px:
                    trades.append({'entry': entry_time, 'pnl_r': target_r})
                    hit = True
                    break

        if not hit and len(future) > 0:
            exit_px = future.iloc[-1]['close']
            pnl_r = (exit_px - entry_px) / stop_dist * direction
            trades.append({'entry': entry_time, 'pnl_r': pnl_r})

    if len(trades) < 20:
        return None

    df = pd.DataFrame(trades)
    df['date'] = pd.to_datetime(df['entry']).dt.date

    # IS/OOS split
    is_df = df[df['entry'] < split_date]
    oos_df = df[df['entry'] >= split_date]

    if len(is_df) < 20 or len(oos_df) < 10:
        return None

    is_avgr = is_df['pnl_r'].mean()
    oos_avgr = oos_df['pnl_r'].mean()

    return {
        'name': name,
        'total_trades': len(df),
        'is_trades': len(is_df),
        'oos_trades': len(oos_df),
        'is_winrate': (is_df['pnl_r'] > 0).sum() / len(is_df),
        'oos_winrate': (oos_df['pnl_r'] > 0).sum() / len(oos_df),
        'is_avgr': is_avgr,
        'oos_avgr': oos_avgr,
        'full_avgr': df['pnl_r'].mean(),
        'passes': is_avgr > 0 and oos_avgr > 0
    }

# Test variations
print("\n" + "="*70)
print("TESTING VARIATIONS")
print("="*70)

results = []

# Original baseline
configs = [
    # (stop_pct, target_r, name)
    (0.5, 2.0, "baseline_midpoint_2R"),
    (1.0, 2.0, "origin_2R"),
    (0.5, 1.5, "midpoint_1.5R"),
    (0.5, 3.0, "midpoint_3R"),
    (0.75, 2.0, "75pct_2R"),
    (0.5, 1.0, "midpoint_1R"),
    (0.5, 5.0, "midpoint_5R"),
]

for stop_pct, target_r, name in configs:
    print(f"\nTesting: {name}")
    result = test_variation(gaps, stop_pct, target_r, name)

    if result is None:
        print("  Insufficient trades")
        continue

    print(f"  Total: {result['total_trades']} trades")
    print(f"  IS: {result['is_avgr']:+.3f}R ({result['is_winrate']:.1%} win)")
    print(f"  OOS: {result['oos_avgr']:+.3f}R ({result['oos_winrate']:.1%} win)")
    print(f"  Status: {'PASS' if result['passes'] else 'FAIL'}")

    results.append(result)

# Filter variations: large gaps only (>0.1%)
large_gaps = gaps[gaps['gap_pct'] > 0.1]
print(f"\n\nTesting with LARGE GAPS ONLY (>{0.1}%, n={len(large_gaps)}):")
if len(large_gaps) >= 50:
    result = test_variation(large_gaps, 0.5, 2.0, "large_gaps_midpoint_2R")
    if result:
        print(f"  IS: {result['is_avgr']:+.3f}R | OOS: {result['oos_avgr']:+.3f}R")
        print(f"  Status: {'PASS' if result['passes'] else 'FAIL'}")
        results.append(result)

# Filter variations: small gaps only (<=0.1%)
small_gaps = gaps[gaps['gap_pct'] <= 0.1]
print(f"\nTesting with SMALL GAPS ONLY (<={0.1}%, n={len(small_gaps)}):")
if len(small_gaps) >= 50:
    result = test_variation(small_gaps, 0.5, 2.0, "small_gaps_midpoint_2R")
    if result:
        print(f"  IS: {result['is_avgr']:+.3f}R | OOS: {result['oos_avgr']:+.3f}R")
        print(f"  Status: {'PASS' if result['passes'] else 'FAIL'}")
        results.append(result)

# Summary
print("\n" + "="*70)
print("ROBUSTNESS SUMMARY")
print("="*70)

passing = [r for r in results if r['passes']]
failing = [r for r in results if not r['passes']]

print(f"\nPassing variations: {len(passing)}/{len(results)}")

if len(passing) > 0:
    print("\nPASSING STRATEGIES:")
    for r in sorted(passing, key=lambda x: x['oos_avgr'], reverse=True):
        print(f"  {r['name']:30s} | IS: {r['is_avgr']:+.3f}R | OOS: {r['oos_avgr']:+.3f}R | N={r['total_trades']}")

if len(failing) > 0:
    print("\nFAILING STRATEGIES:")
    for r in failing:
        print(f"  {r['name']:30s} | IS: {r['is_avgr']:+.3f}R | OOS: {r['oos_avgr']:+.3f}R")

# Verdict
print("\n" + "="*70)
print("FINAL VERDICT")
print("="*70)

if len(passing) >= 3:
    print("\n[ROBUST EDGE CONFIRMED]")
    print(f"\n{len(passing)} variations passed IS/OOS validation.")
    print("The gap continuation edge appears ROBUST across:")
    print("  - Multiple stop configurations")
    print("  - Multiple target R multiples")
    print("\nRecommended configuration:")
    best = sorted(passing, key=lambda x: x['oos_avgr'], reverse=True)[0]
    print(f"  {best['name']}")
    print(f"  OOS Expectancy: {best['oos_avgr']:+.3f}R")
    print(f"  OOS Win Rate: {best['oos_winrate']:.1%}")
    print(f"  Total Trades: {best['total_trades']}")
elif len(passing) > 0:
    print("\n[MARGINAL EDGE]")
    print(f"\nOnly {len(passing)} variation(s) passed.")
    print("Edge may be parameter-sensitive. Use with caution.")
    print("\nPassing configs:")
    for r in passing:
        print(f"  {r['name']}: OOS {r['oos_avgr']:+.3f}R")
else:
    print("\n[NO ROBUST EDGE]")
    print("\nNo variations passed IS/OOS validation.")
    print("Gap continuation does NOT provide a robust trading edge.")

print("\n" + "="*70)
print("ROBUSTNESS TESTING COMPLETE")
print("="*70)
