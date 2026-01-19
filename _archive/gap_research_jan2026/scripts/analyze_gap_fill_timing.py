#!/usr/bin/env python3
"""
GAP FILL TIMING ANALYSIS
Determines optimal entry timing for fading gaps based on historical patterns.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def load_gap_data():
    """Load gap fill analysis CSV."""
    csv_path = Path("gap_fill_analysis.csv")
    df = pd.read_csv(csv_path)

    # Filter only filled gaps for timing analysis
    filled_df = df[df['filled'] == True].copy()

    return filled_df

def analyze_timing_distribution(df):
    """Analyze when gaps fill (time distribution)."""
    print("=" * 80)
    print("GAP FILL TIMING DISTRIBUTION")
    print("=" * 80)

    total_gaps = len(df)

    # Define timing buckets (in 5-min bars)
    timing_buckets = [
        (1, "0-5 minutes (1 bar)"),
        (3, "0-15 minutes (3 bars)"),
        (6, "0-30 minutes (6 bars)"),
        (12, "0-60 minutes (12 bars)"),
        (24, "0-2 hours (24 bars)"),
        (48, "0-4 hours (48 bars)"),
        (96, "0-8 hours (96 bars)"),
        (288, "0-24 hours (288 bars)"),
    ]

    print(f"\nTotal filled gaps analyzed: {total_gaps}\n")

    results = {}
    for max_bars, label in timing_buckets:
        count = len(df[df['bars_to_fill'] <= max_bars])
        pct = (count / total_gaps) * 100
        results[max_bars] = {'count': count, 'pct': pct}
        print(f"{label:30s}: {count:4d} gaps ({pct:5.1f}%)")

    # Immediate fills (1 bar = 5 minutes)
    immediate = len(df[df['bars_to_fill'] == 1])
    immediate_pct = (immediate / total_gaps) * 100

    print(f"\n{'IMMEDIATE FILLS (exactly 1 bar)':30s}: {immediate:4d} gaps ({immediate_pct:5.1f}%)")
    print(f"{'DELAYED FILLS (>1 bar)':30s}: {total_gaps - immediate:4d} gaps ({100 - immediate_pct:5.1f}%)")

    return results, immediate_pct

def analyze_by_gap_size(df):
    """Analyze timing patterns by gap size."""
    print("\n" + "=" * 80)
    print("TIMING ANALYSIS BY GAP SIZE")
    print("=" * 80)

    # Define gap size buckets (in ticks, 0.1 per tick)
    gap_size_buckets = [
        (0.0, 0.5, "Tiny (0.0-0.5 ticks)"),
        (0.5, 1.0, "Small (0.5-1.0 ticks)"),
        (1.0, 2.0, "Medium (1.0-2.0 ticks)"),
        (2.0, 5.0, "Large (2.0-5.0 ticks)"),
        (5.0, 999.0, "Huge (>5.0 ticks)"),
    ]

    for min_size, max_size, label in gap_size_buckets:
        subset = df[(df['gap_size_abs'] >= min_size) & (df['gap_size_abs'] < max_size)]

        if len(subset) == 0:
            continue

        print(f"\n{label} (n={len(subset)})")

        immediate = len(subset[subset['bars_to_fill'] == 1])
        immediate_pct = (immediate / len(subset)) * 100 if len(subset) > 0 else 0

        within_15min = len(subset[subset['bars_to_fill'] <= 3])
        within_15min_pct = (within_15min / len(subset)) * 100 if len(subset) > 0 else 0

        within_60min = len(subset[subset['bars_to_fill'] <= 12])
        within_60min_pct = (within_60min / len(subset)) * 100 if len(subset) > 0 else 0

        median_bars = subset['bars_to_fill'].median()
        median_minutes = median_bars * 5

        print(f"  Immediate (1 bar):  {immediate_pct:5.1f}%")
        print(f"  Within 15 min:      {within_15min_pct:5.1f}%")
        print(f"  Within 60 min:      {within_60min_pct:5.1f}%")
        print(f"  Median fill time:   {median_bars:.1f} bars ({median_minutes:.0f} minutes)")

def analyze_delayed_fills(df):
    """For gaps that don't fill immediately, analyze adverse excursion."""
    print("\n" + "=" * 80)
    print("DELAYED FILLS ANALYSIS (gaps that don't fill in first bar)")
    print("=" * 80)

    # Filter delayed fills (>1 bar to fill)
    delayed = df[df['bars_to_fill'] > 1].copy()

    if len(delayed) == 0:
        print("\nNo delayed fills found.")
        return

    print(f"\nTotal delayed fills: {len(delayed)}")
    print(f"As % of all fills: {(len(delayed) / len(df)) * 100:.1f}%\n")

    # Note: We don't have adverse excursion data in the CSV
    # We only have max_retrace_pct which shows how much of gap was retraced
    # This is always 100% since all these gaps filled

    print("Analysis of delayed fill patterns:")
    print(f"  Median bars to fill: {delayed['bars_to_fill'].median():.1f} bars")
    print(f"  Mean bars to fill:   {delayed['bars_to_fill'].mean():.1f} bars")
    print(f"  Max bars to fill:    {delayed['bars_to_fill'].max():.0f} bars")

    # Breakdown by time ranges
    quick_delayed = delayed[delayed['bars_to_fill'] <= 12]  # Fill within 1 hour
    slow_delayed = delayed[delayed['bars_to_fill'] > 12]    # Take >1 hour

    print(f"\n  Fill within 1 hour (2-12 bars): {len(quick_delayed)} ({(len(quick_delayed)/len(delayed))*100:.1f}%)")
    print(f"  Fill after 1 hour (>12 bars):   {len(slow_delayed)} ({(len(slow_delayed)/len(delayed))*100:.1f}%)")

    # Analyze by gap size
    print("\n  Delayed fill patterns by gap size:")

    size_categories = [
        (0.0, 0.5, "Tiny (0.0-0.5)"),
        (0.5, 1.0, "Small (0.5-1.0)"),
        (1.0, 2.0, "Medium (1.0-2.0)"),
        (2.0, 5.0, "Large (2.0-5.0)"),
        (5.0, 999.0, "Huge (>5.0)"),
    ]

    for min_size, max_size, label in size_categories:
        subset = delayed[(delayed['gap_size_abs'] >= min_size) & (delayed['gap_size_abs'] < max_size)]
        if len(subset) > 0:
            median_bars = subset['bars_to_fill'].median()
            print(f"    {label:20s}: {len(subset):3d} gaps, median {median_bars:5.1f} bars ({median_bars*5:5.0f} min)")

def generate_entry_strategies(df):
    """Generate and evaluate different entry timing strategies."""
    print("\n" + "=" * 80)
    print("ENTRY STRATEGY RECOMMENDATIONS")
    print("=" * 80)

    total_gaps = len(df)

    # Strategy A: Immediate fade
    immediate_fills = len(df[df['bars_to_fill'] == 1])
    immediate_pct = (immediate_fills / total_gaps) * 100

    # Strategy B: Wait for pullback (assume fills in 2-6 bars represent "pullback then fill")
    pullback_fills = len(df[(df['bars_to_fill'] >= 2) & (df['bars_to_fill'] <= 6)])
    pullback_pct = (pullback_fills / total_gaps) * 100

    # Strategy C: Wait 30 minutes (6 bars)
    fills_after_30min = len(df[df['bars_to_fill'] <= 6])
    wait_30_success = (fills_after_30min / total_gaps) * 100

    # Strategy D: Only fade small gaps (<1.0 ticks)
    small_gaps = df[df['gap_size_abs'] < 1.0]
    small_immediate = len(small_gaps[small_gaps['bars_to_fill'] == 1])
    small_immediate_pct = (small_immediate / len(small_gaps)) * 100 if len(small_gaps) > 0 else 0

    print("\n**STRATEGY A: IMMEDIATE FADE (enter at gap open)**")
    print(f"  Success rate: {immediate_pct:.1f}% fill in first 5 minutes")
    print(f"  Risk: High adverse excursion if gap doesn't fill immediately")
    print(f"  Best for: Very small gaps (<0.5 ticks)")

    print("\n**STRATEGY B: WAIT FOR FIRST PULLBACK**")
    print(f"  Success rate: {pullback_pct:.1f}% fill in 10-30 minutes after initial move")
    print(f"  Risk: Medium - may miss immediate fills")
    print(f"  Best for: Medium gaps (1.0-2.0 ticks)")

    print("\n**STRATEGY C: WAIT 30 MINUTES**")
    print(f"  Success rate: {wait_30_success:.1f}% fill within 30 minutes")
    print(f"  Risk: Low - confirms gap isn't continuing")
    print(f"  Best for: Large gaps (>2.0 ticks)")

    print("\n**STRATEGY D: ONLY FADE SMALL GAPS (<1.0 ticks)**")
    print(f"  Immediate fill rate: {small_immediate_pct:.1f}%")
    print(f"  Risk: Lowest - small gaps fill most reliably")
    print(f"  Best for: Conservative traders")

    # Optimal strategy matrix
    print("\n" + "-" * 80)
    print("OPTIMAL STRATEGY MATRIX BY GAP SIZE")
    print("-" * 80)

    strategies = [
        (0.0, 0.5, "IMMEDIATE FADE", "Enter immediately at gap open"),
        (0.5, 1.0, "IMMEDIATE FADE", "Enter immediately at gap open"),
        (1.0, 2.0, "WAIT FOR PULLBACK", "Wait 5-15 minutes for initial move, then enter"),
        (2.0, 5.0, "WAIT 30 MINUTES", "Wait for confirmation gap isn't continuing"),
        (5.0, 999.0, "DON'T FADE", "Risk too high - gap likely to continue"),
    ]

    for min_size, max_size, strategy, notes in strategies:
        print(f"\nGap size {min_size:.1f}-{max_size:.1f} ticks:")
        print(f"  Strategy: {strategy}")
        print(f"  Entry rule: {notes}")

def generate_actionable_rules(df):
    """Generate clear, actionable timing rules."""
    print("\n" + "=" * 80)
    print("ACTIONABLE TIMING RULES")
    print("=" * 80)

    total_gaps = len(df)

    # Calculate key metrics
    immediate = len(df[df['bars_to_fill'] == 1])
    immediate_pct = (immediate / total_gaps) * 100

    within_15min = len(df[df['bars_to_fill'] <= 3])
    within_15min_pct = (within_15min / total_gaps) * 100

    within_60min = len(df[df['bars_to_fill'] <= 12])
    within_60min_pct = (within_60min / total_gaps) * 100

    delayed = total_gaps - immediate
    delayed_pct = (delayed / total_gaps) * 100

    print("\n**KEY FINDINGS:**")
    print(f"\n1. {immediate_pct:.1f}% of gaps fill IMMEDIATELY (within 5 minutes)")
    print(f"   -> For gaps <0.5 ticks: IMMEDIATE FADE works")

    print(f"\n2. {delayed_pct:.1f}% of gaps take LONGER to fill")
    print(f"   -> These run away first, then return")
    print(f"   -> WAIT for pullback confirmation")

    print(f"\n3. {within_15min_pct:.1f}% of gaps fill within 15 minutes")
    print(f"   -> Most fades resolve quickly")

    print(f"\n4. {within_60min_pct:.1f}% of gaps fill within 60 minutes")
    print(f"   -> If not filled in 1 hour, reconsider thesis")

    # Gap size specific rules
    small_gaps = df[df['gap_size_abs'] < 1.0]
    small_immediate_pct = (len(small_gaps[small_gaps['bars_to_fill'] == 1]) / len(small_gaps)) * 100

    medium_gaps = df[(df['gap_size_abs'] >= 1.0) & (df['gap_size_abs'] < 2.0)]
    medium_immediate_pct = (len(medium_gaps[medium_gaps['bars_to_fill'] == 1]) / len(medium_gaps)) * 100 if len(medium_gaps) > 0 else 0

    large_gaps = df[df['gap_size_abs'] >= 2.0]
    large_immediate_pct = (len(large_gaps[large_gaps['bars_to_fill'] == 1]) / len(large_gaps)) * 100 if len(large_gaps) > 0 else 0

    print("\n**ENTRY TIMING BY GAP SIZE:**")
    print(f"\n- Gaps <1.0 ticks: {small_immediate_pct:.1f}% fill immediately")
    print(f"  -> ENTER IMMEDIATELY at gap open")

    print(f"\n- Gaps 1.0-2.0 ticks: {medium_immediate_pct:.1f}% fill immediately")
    print(f"  -> WAIT 5-15 minutes for pullback confirmation")

    print(f"\n- Gaps >2.0 ticks: {large_immediate_pct:.1f}% fill immediately")
    print(f"  -> WAIT 30 minutes OR DON'T FADE (high risk)")

    print("\n**RISK MANAGEMENT:**")
    print("\n- Set stop loss at 1.5x gap size")
    print("- If gap doesn't fill within 1 hour, exit for small loss")
    print("- Never fade gaps during major news events")
    print("- Avoid fading gaps >5 ticks (likely continuation)")

def main():
    """Run complete gap fill timing analysis."""
    print("\n" + "=" * 80)
    print("GAP FILL TIMING ANALYSIS - WHEN TO FADE")
    print("=" * 80)
    print("\nAnalyzing historical gap fill patterns to determine optimal entry timing...\n")

    # Load data
    df = load_gap_data()

    # Run analyses
    timing_results, immediate_pct = analyze_timing_distribution(df)
    analyze_by_gap_size(df)
    analyze_delayed_fills(df)
    generate_entry_strategies(df)
    generate_actionable_rules(df)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nRecommendation: Focus on gaps <1.0 ticks with immediate fade strategy.")
    print("For larger gaps, wait for pullback confirmation before entering.\n")

if __name__ == "__main__":
    main()
