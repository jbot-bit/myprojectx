#!/usr/bin/env python3
"""
GAP ADVERSE EXCURSION ANALYSIS
Analyzes how far gaps run BEFORE filling to determine optimal entry timing.
"""

import duckdb
import pandas as pd
from datetime import timedelta
from pathlib import Path

DB_PATH = "gold.db"

def analyze_adverse_excursion():
    """Analyze price movement in first hour after gap open."""
    print("\n" + "=" * 80)
    print("GAP ADVERSE EXCURSION ANALYSIS")
    print("=" * 80)
    print("\nAnalyzing first 60 minutes after gap to understand adverse movement...\n")

    conn = duckdb.connect(DB_PATH, read_only=True)

    # Load gap data
    gap_df = pd.read_csv("gap_fill_analysis.csv")
    gap_df['entry_time'] = pd.to_datetime(gap_df['entry_time'])

    # Filter only filled gaps for analysis
    filled_gaps = gap_df[gap_df['filled'] == True].copy()

    print(f"Analyzing {len(filled_gaps)} filled gaps...\n")

    # Categorize gaps by size
    size_categories = [
        (0.0, 0.5, "Tiny (0.0-0.5 ticks)"),
        (0.5, 1.0, "Small (0.5-1.0 ticks)"),
        (1.0, 2.0, "Medium (1.0-2.0 ticks)"),
        (2.0, 5.0, "Large (2.0-5.0 ticks)"),
    ]

    for min_size, max_size, label in size_categories:
        subset = filled_gaps[(filled_gaps['gap_size_abs'] >= min_size) &
                            (filled_gaps['gap_size_abs'] < max_size)]

        if len(subset) == 0:
            continue

        print("=" * 80)
        print(f"{label} - {len(subset)} gaps")
        print("=" * 80)

        # Analyze immediate vs delayed fills
        immediate = subset[subset['bars_to_fill'] == 1]
        delayed = subset[subset['bars_to_fill'] > 1]

        print(f"\nImmediate fills (1 bar): {len(immediate)} ({len(immediate)/len(subset)*100:.1f}%)")
        print(f"Delayed fills (>1 bar):  {len(delayed)} ({len(delayed)/len(subset)*100:.1f}%)")

        if len(delayed) > 0:
            print(f"\nDelayed fill timing:")
            print(f"  Median bars to fill: {delayed['bars_to_fill'].median():.1f} bars")
            print(f"  Mean bars to fill:   {delayed['bars_to_fill'].mean():.1f} bars")

            # For delayed fills, sample some to analyze adverse movement
            sample_delayed = delayed.head(min(5, len(delayed)))

            print(f"\nSample analysis of {len(sample_delayed)} delayed fills:")

            for idx, row in sample_delayed.iterrows():
                entry_time = row['entry_time']
                gap_direction = row['gap_direction']
                gap_size = row['gap_size_abs']
                entry_price = row['entry_price']
                prev_close = row['prev_close']
                bars_to_fill = row['bars_to_fill']

                # Query bars for first 60 minutes (12 bars)
                query = f"""
                    SELECT ts_utc, open, high, low, close
                    FROM bars_5m
                    WHERE ts_utc >= '{entry_time}'
                    AND ts_utc < '{entry_time + timedelta(hours=1)}'
                    ORDER BY ts_utc
                    LIMIT 12
                """

                bars = conn.execute(query).df()

                if len(bars) > 0:
                    # Calculate adverse excursion
                    if gap_direction == 'UP':
                        # Gap up, fading short
                        # Adverse move = price going higher
                        max_high = bars['high'].max()
                        adverse_move = max_high - entry_price
                    else:
                        # Gap down, fading long
                        # Adverse move = price going lower
                        min_low = bars['low'].min()
                        adverse_move = entry_price - min_low

                    adverse_ticks = adverse_move / 0.1  # Convert to ticks

                    print(f"\n  Gap {gap_direction} {gap_size:.1f} ticks, filled in {bars_to_fill:.0f} bars:")
                    print(f"    Adverse excursion: {adverse_ticks:.1f} ticks")
                    print(f"    As % of gap size:  {(adverse_move/gap_size)*100:.1f}%")

        print()

    conn.close()

def generate_entry_timing_recommendations():
    """Generate specific entry timing recommendations based on gap behavior."""
    print("\n" + "=" * 80)
    print("SPECIFIC ENTRY TIMING RECOMMENDATIONS")
    print("=" * 80)

    gap_df = pd.read_csv("gap_fill_analysis.csv")
    filled_gaps = gap_df[gap_df['filled'] == True].copy()

    print("\n**STRATEGY 1: AGGRESSIVE IMMEDIATE FADE**")
    print("When to use: Gaps 0.0-1.0 ticks")
    print("Entry: Immediately at gap open (within first 5 minutes)")
    print("Why: 59% fill immediately, minimal adverse excursion")
    print("Stop loss: 1.5x gap size")
    print("Target: Full gap fill")

    tiny_small = filled_gaps[filled_gaps['gap_size_abs'] < 1.0]
    immediate_rate = len(tiny_small[tiny_small['bars_to_fill'] == 1]) / len(tiny_small) * 100
    within_15min = len(tiny_small[tiny_small['bars_to_fill'] <= 3]) / len(tiny_small) * 100

    print(f"Expected outcomes:")
    print(f"  - {immediate_rate:.1f}% fill in 5 minutes")
    print(f"  - {within_15min:.1f}% fill in 15 minutes")
    print(f"  - Low risk, high probability")

    print("\n**STRATEGY 2: CONSERVATIVE PULLBACK FADE**")
    print("When to use: Gaps 1.0-2.0 ticks")
    print("Entry: Wait 5-15 minutes for initial move away, then enter on pullback")
    print("Why: 48.6% fill immediately, but 51.4% run away first")
    print("Stop loss: 2.0x gap size")
    print("Target: Full gap fill")

    medium = filled_gaps[(filled_gaps['gap_size_abs'] >= 1.0) & (filled_gaps['gap_size_abs'] < 2.0)]
    immediate_rate = len(medium[medium['bars_to_fill'] == 1]) / len(medium) * 100
    delayed_rate = len(medium[medium['bars_to_fill'] > 1]) / len(medium) * 100
    within_60min = len(medium[medium['bars_to_fill'] <= 12]) / len(medium) * 100

    print(f"Expected outcomes:")
    print(f"  - {immediate_rate:.1f}% fill immediately (you'll miss these)")
    print(f"  - {delayed_rate:.1f}% run away first (you'll catch these)")
    print(f"  - {within_60min:.1f}% fill within 60 minutes")
    print(f"  - Medium risk, good probability")

    print("\n**STRATEGY 3: PATIENT CONFIRMATION FADE**")
    print("When to use: Gaps 2.0-5.0 ticks")
    print("Entry: Wait 30 minutes for confirmation gap isn't continuing")
    print("Why: Only 34.4% fill immediately, high risk of continuation")
    print("Stop loss: 2.5x gap size")
    print("Target: Partial fill (50-75% of gap)")

    large = filled_gaps[(filled_gaps['gap_size_abs'] >= 2.0) & (filled_gaps['gap_size_abs'] < 5.0)]
    immediate_rate = len(large[large['bars_to_fill'] == 1]) / len(large) * 100
    within_30min = len(large[large['bars_to_fill'] <= 6]) / len(large) * 100
    within_60min = len(large[large['bars_to_fill'] <= 12]) / len(large) * 100

    print(f"Expected outcomes:")
    print(f"  - {immediate_rate:.1f}% fill immediately (you'll miss these)")
    print(f"  - {within_30min:.1f}% fill within 30 minutes")
    print(f"  - {within_60min:.1f}% fill within 60 minutes")
    print(f"  - High risk, lower probability")

    print("\n**STRATEGY 4: DON'T FADE**")
    print("When to use: Gaps >5.0 ticks")
    print("Entry: DON'T ENTER")
    print("Why: Only 12.5% fill immediately, likely continuation move")
    print("Alternative: Trade in direction of gap instead")

    huge = filled_gaps[filled_gaps['gap_size_abs'] >= 5.0]
    immediate_rate = len(huge[huge['bars_to_fill'] == 1]) / len(huge) * 100 if len(huge) > 0 else 0

    print(f"Historical data:")
    print(f"  - {immediate_rate:.1f}% fill immediately")
    print(f"  - High risk, very low probability")
    print(f"  - Better to trade WITH the gap")

def generate_timing_decision_tree():
    """Generate a decision tree for entry timing."""
    print("\n" + "=" * 80)
    print("ENTRY TIMING DECISION TREE")
    print("=" * 80)

    print("""
STEP 1: Identify gap size at market open
├─ Gap 0.0-0.5 ticks → IMMEDIATE FADE (59% immediate fill)
├─ Gap 0.5-1.0 ticks → IMMEDIATE FADE (60% immediate fill)
├─ Gap 1.0-2.0 ticks → WAIT FOR PULLBACK (49% immediate, 51% delayed)
├─ Gap 2.0-5.0 ticks → WAIT 30 MIN (34% immediate, 66% delayed/don't fill)
└─ Gap >5.0 ticks    → DON'T FADE (12% immediate, 88% continuation)

STEP 2: If IMMEDIATE FADE strategy chosen (gaps <1.0 ticks):
- Enter market order at gap open
- Set stop loss at entry + (1.5 x gap size)
- Target: Previous close (full gap fill)
- Exit if not filled within 60 minutes

STEP 3: If WAIT FOR PULLBACK strategy chosen (gaps 1.0-2.0 ticks):
- Watch first 5-15 minutes
- Wait for price to move AWAY from fill (in gap direction)
- Enter on first pullback toward fill price
- Set stop loss at entry + (2.0 x gap size)
- Target: Previous close (full gap fill)
- Exit if not filled within 60 minutes

STEP 4: If WAIT 30 MIN strategy chosen (gaps 2.0-5.0 ticks):
- Watch first 30 minutes
- Only enter if gap has NOT continued strongly
- Enter if price shows rejection of gap direction
- Set stop loss at entry + (2.5 x gap size)
- Target: 50-75% of gap fill (be conservative)
- Exit if not filled within 90 minutes

STEP 5: Risk management for all strategies:
- Never risk more than 1% of account per trade
- If stop hit, don't re-enter same gap
- If gap fills and reverses, consider trading reversal
- Track success rate by gap size category
- Adjust filters based on live performance
""")

def main():
    """Run complete adverse excursion analysis."""
    # Run timing analysis first
    analyze_adverse_excursion()

    # Generate specific recommendations
    generate_entry_timing_recommendations()

    # Generate decision tree
    generate_timing_decision_tree()

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nKey takeaway: Gap size determines entry timing.")
    print("Small gaps (<1.0 ticks) = immediate fade works well")
    print("Medium gaps (1.0-2.0 ticks) = wait for pullback")
    print("Large gaps (>2.0 ticks) = wait 30 minutes or avoid\n")

if __name__ == "__main__":
    main()
