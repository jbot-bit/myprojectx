"""
GAP FILL BEHAVIOR ANALYSIS

Analyzes whether gaps FILL (price returns to gap origin) or CONTINUE (price runs away).

Key Questions:
1. What % of gaps fill completely (price returns to prev_close)?
2. What % of gaps partially fill (>50% retrace toward origin)?
3. What % of gaps never fill (continue in gap direction)?
4. How does this vary by gap size and direction?
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime

DB_PATH = r"C:\Users\sydne\OneDrive\myprojectx\gold.db"

print("="*80)
print("GAP FILL BEHAVIOR ANALYSIS - MGC FUTURES")
print("="*80)

# Load data
print("\nLoading data...")
conn = duckdb.connect(DB_PATH, read_only=True)

bars_1m = conn.execute("""
    SELECT ts_utc, open, high, low, close, volume
    FROM bars_1m
    WHERE symbol = 'MGC'
        AND ts_utc >= '2024-01-01'
    ORDER BY ts_utc
""").fetchdf()
conn.close()

bars_1m['ts_utc'] = pd.to_datetime(bars_1m['ts_utc'], utc=True)
print(f"  Loaded {len(bars_1m):,} bars")
print(f"  Date range: {bars_1m['ts_utc'].min()} to {bars_1m['ts_utc'].max()}")

# Detect gaps (60+ minute time gaps)
print("\nDetecting gaps...")
bars_1m['time_diff_min'] = bars_1m['ts_utc'].diff().dt.total_seconds() / 60
bars_1m['prev_close'] = bars_1m['close'].shift(1)

gaps = bars_1m[bars_1m['time_diff_min'] > 60].copy()
gaps['gap_size'] = gaps['open'] - gaps['prev_close']
gaps['gap_size_abs'] = gaps['gap_size'].abs()
gaps['gap_direction'] = np.where(gaps['gap_size'] > 0, 'UP', 'DOWN')

print(f"  Found {len(gaps)} gaps")
print(f"  UP gaps: {(gaps['gap_direction'] == 'UP').sum()}")
print(f"  DOWN gaps: {(gaps['gap_direction'] == 'DOWN').sum()}")

# Analyze fill behavior for each gap
print("\nAnalyzing fill behavior...")
results = []

for idx, gap in gaps.iterrows():
    entry_time = gap['ts_utc']
    entry_price = gap['open']
    prev_close = gap['prev_close']
    gap_size = gap['gap_size_abs']
    gap_dir = gap['gap_direction']

    if gap_size < 0.01:  # Skip tiny gaps
        continue

    # Get future bars (up to 1 trading day = ~1440 minutes)
    future_bars = bars_1m[(bars_1m['ts_utc'] > entry_time) &
                           (bars_1m['ts_utc'] <= entry_time + pd.Timedelta(days=1))]

    if len(future_bars) == 0:
        continue

    # Track fill behavior
    filled = False
    max_retrace_pct = 0
    bars_to_fill = None

    for bar_idx, bar in future_bars.iterrows():
        # For UP gaps: check if price comes back down to prev_close
        # For DOWN gaps: check if price comes back up to prev_close

        if gap_dir == 'UP':
            # Gap opened ABOVE prev_close
            # Fill = price trades at or below prev_close
            if bar['low'] <= prev_close:
                filled = True
                bars_to_fill = len(future_bars.loc[:bar_idx])
                max_retrace_pct = 100.0  # Full fill
                break

            # Calculate retrace % (how far back toward prev_close)
            # Retrace % = (entry - current_low) / gap_size
            retrace = (entry_price - bar['low']) / gap_size * 100
            max_retrace_pct = max(max_retrace_pct, retrace)

        else:  # DOWN gap
            # Gap opened BELOW prev_close
            # Fill = price trades at or above prev_close
            if bar['high'] >= prev_close:
                filled = True
                bars_to_fill = len(future_bars.loc[:bar_idx])
                max_retrace_pct = 100.0  # Full fill
                break

            # Calculate retrace % (how far back toward prev_close)
            # Retrace % = (current_high - entry) / gap_size
            retrace = (bar['high'] - entry_price) / gap_size * 100
            max_retrace_pct = max(max_retrace_pct, retrace)

    # Classify fill behavior
    if filled:
        fill_category = "FULL_FILL"
    elif max_retrace_pct >= 50:
        fill_category = "PARTIAL_FILL"
    elif max_retrace_pct >= 25:
        fill_category = "MINOR_RETRACE"
    else:
        fill_category = "CONTINUATION"

    results.append({
        'entry_time': entry_time,
        'entry_date': entry_time.date(),
        'gap_direction': gap_dir,
        'gap_size': gap['gap_size'],
        'gap_size_abs': gap_size,
        'prev_close': prev_close,
        'entry_price': entry_price,
        'filled': filled,
        'max_retrace_pct': max_retrace_pct,
        'bars_to_fill': bars_to_fill if filled else None,
        'fill_category': fill_category
    })

results_df = pd.DataFrame(results)

print(f"  Analyzed {len(results_df)} gaps")

# Calculate statistics
print("\n" + "="*80)
print("FILL BEHAVIOR STATISTICS")
print("="*80)

total_gaps = len(results_df)
full_fills = len(results_df[results_df['filled'] == True])
partial_fills = len(results_df[results_df['fill_category'] == 'PARTIAL_FILL'])
minor_retraces = len(results_df[results_df['fill_category'] == 'MINOR_RETRACE'])
continuations = len(results_df[results_df['fill_category'] == 'CONTINUATION'])

print(f"\nOVERALL RESULTS ({total_gaps} gaps):")
print(f"  FULL FILL (100%):        {full_fills:4d} gaps ({full_fills/total_gaps*100:5.1f}%)")
print(f"  PARTIAL FILL (50-99%):   {partial_fills:4d} gaps ({partial_fills/total_gaps*100:5.1f}%)")
print(f"  MINOR RETRACE (25-49%):  {minor_retraces:4d} gaps ({minor_retraces/total_gaps*100:5.1f}%)")
print(f"  CONTINUATION (0-24%):    {continuations:4d} gaps ({continuations/total_gaps*100:5.1f}%)")

print(f"\nAVERAGE RETRACE: {results_df['max_retrace_pct'].mean():.1f}%")
print(f"MEDIAN RETRACE:  {results_df['max_retrace_pct'].median():.1f}%")

# Breakdown by gap direction
print("\n" + "="*80)
print("BREAKDOWN BY GAP DIRECTION")
print("="*80)

for direction in ['UP', 'DOWN']:
    subset = results_df[results_df['gap_direction'] == direction]
    n = len(subset)

    if n == 0:
        continue

    full = len(subset[subset['filled'] == True])
    partial = len(subset[subset['fill_category'] == 'PARTIAL_FILL'])
    minor = len(subset[subset['fill_category'] == 'MINOR_RETRACE'])
    cont = len(subset[subset['fill_category'] == 'CONTINUATION'])

    print(f"\n{direction} GAPS ({n} gaps):")
    print(f"  FULL FILL:        {full:4d} ({full/n*100:5.1f}%)")
    print(f"  PARTIAL FILL:     {partial:4d} ({partial/n*100:5.1f}%)")
    print(f"  MINOR RETRACE:    {minor:4d} ({minor/n*100:5.1f}%)")
    print(f"  CONTINUATION:     {cont:4d} ({cont/n*100:5.1f}%)")
    print(f"  Avg retrace:      {subset['max_retrace_pct'].mean():.1f}%")
    print(f"  Median retrace:   {subset['max_retrace_pct'].median():.1f}%")

# Breakdown by gap size
print("\n" + "="*80)
print("BREAKDOWN BY GAP SIZE")
print("="*80)

# Define size categories based on percentiles
results_df['gap_size_pct'] = (results_df['gap_size_abs'] / results_df['prev_close'] * 100)
size_median = results_df['gap_size_pct'].median()

print(f"\nMedian gap size: {size_median:.3f}%")

for label, condition in [
    ('SMALL gaps (<median)', results_df['gap_size_pct'] < size_median),
    ('LARGE gaps (>=median)', results_df['gap_size_pct'] >= size_median)
]:
    subset = results_df[condition]
    n = len(subset)

    if n == 0:
        continue

    full = len(subset[subset['filled'] == True])
    partial = len(subset[subset['fill_category'] == 'PARTIAL_FILL'])
    minor = len(subset[subset['fill_category'] == 'MINOR_RETRACE'])
    cont = len(subset[subset['fill_category'] == 'CONTINUATION'])

    print(f"\n{label} ({n} gaps):")
    print(f"  FULL FILL:        {full:4d} ({full/n*100:5.1f}%)")
    print(f"  PARTIAL FILL:     {partial:4d} ({partial/n*100:5.1f}%)")
    print(f"  MINOR RETRACE:    {minor:4d} ({minor/n*100:5.1f}%)")
    print(f"  CONTINUATION:     {cont:4d} ({cont/n*100:5.1f}%)")
    print(f"  Avg retrace:      {subset['max_retrace_pct'].mean():.1f}%")

# Time to fill analysis
filled_gaps = results_df[results_df['filled'] == True]
if len(filled_gaps) > 0:
    print("\n" + "="*80)
    print("TIME TO FILL ANALYSIS")
    print("="*80)
    print(f"\nFor gaps that filled ({len(filled_gaps)} gaps):")
    print(f"  Average bars to fill: {filled_gaps['bars_to_fill'].mean():.1f} bars")
    print(f"  Median bars to fill:  {filled_gaps['bars_to_fill'].median():.0f} bars")
    print(f"  Min bars to fill:     {filled_gaps['bars_to_fill'].min():.0f} bars")
    print(f"  Max bars to fill:     {filled_gaps['bars_to_fill'].max():.0f} bars")

# TRADING IMPLICATIONS
print("\n" + "="*80)
print("TRADING IMPLICATIONS")
print("="*80)

fill_rate = full_fills / total_gaps * 100
partial_or_full = (full_fills + partial_fills) / total_gaps * 100
continuation_rate = continuations / total_gaps * 100

print(f"\n[RESULT] {fill_rate:.1f}% of gaps FILL completely")
print(f"[RESULT] {partial_or_full:.1f}% of gaps retrace >50% (partial + full fills)")
print(f"[RESULT] {continuation_rate:.1f}% of gaps CONTINUE without meaningful retrace")

print("\nKEY INSIGHT:")
if fill_rate > 60:
    print("  >> GAPS TEND TO FILL")
    print("  Trading implication: Fade the gap (trade back to origin)")
    print("  Risk: Gap may continue first before filling")
elif continuation_rate > 60:
    print("  >> GAPS TEND TO CONTINUE")
    print("  Trading implication: Trade in gap direction (continuation)")
    print("  Risk: Gap may retrace first before continuing")
else:
    print("  >> NO CLEAR PATTERN")
    print("  Gaps show mixed behavior - neither strong fill nor continuation tendency")
    print("  Trading implication: Need additional filters (size, direction, context)")

# Save results
output_path = r"C:\Users\sydne\OneDrive\myprojectx\gap_fill_analysis.csv"
results_df.to_csv(output_path, index=False)
print(f"\nDetailed results saved: {output_path}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
