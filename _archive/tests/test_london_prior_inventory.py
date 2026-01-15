"""
Test London ORB performance based on Asia's resolution of prior inventory.

Tests:
1. Which prior session matters more? (NY vs London)
2. Does resolution depth affect London edge?
3. Does resolution timing (early vs late Asia) matter?

Engine A validation - liquidity/inventory logic only.
"""

import duckdb
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path

# Config
DB_PATH = "gold.db"
TICK_SIZE = 0.10

def main():
    print("=" * 80)
    print("LONDON PRIOR INVENTORY TEST - Engine A Validation")
    print("=" * 80)
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Step 1: Get all trading days with required sessions
    print("Step 1: Building session labels...")
    print("-" * 80)

    # Build comprehensive session labels
    query_labels = f"""
    WITH daily_sessions AS (
        SELECT
            date_local,
            instrument,

            -- Prior day sessions (for inventory)
            LAG(orb_1800_high) OVER (PARTITION BY instrument ORDER BY date_local) as prior_london_high,
            LAG(orb_1800_low) OVER (PARTITION BY instrument ORDER BY date_local) as prior_london_low,
            LAG(orb_2300_high) OVER (PARTITION BY instrument ORDER BY date_local) as prior_ny_2300_high,
            LAG(orb_2300_low) OVER (PARTITION BY instrument ORDER BY date_local) as prior_ny_2300_low,
            LAG(orb_0030_high) OVER (PARTITION BY instrument ORDER BY date_local) as prior_ny_0030_high,
            LAG(orb_0030_low) OVER (PARTITION BY instrument ORDER BY date_local) as prior_ny_0030_low,

            -- Also try prior day high/low (full prior day)
            LAG(asia_high) OVER (PARTITION BY instrument ORDER BY date_local) as prior_asia_high,
            LAG(asia_low) OVER (PARTITION BY instrument ORDER BY date_local) as prior_asia_low,

            -- Current Asia session
            orb_0900_high, orb_0900_low,
            orb_1000_high, orb_1000_low,
            orb_1100_high, orb_1100_low,
            asia_high, asia_low,

            -- Current London session
            orb_1800_high, orb_1800_low, orb_1800_size, orb_1800_break_dir

        FROM daily_features_v2
        WHERE instrument = 'MGC'
            AND orb_1800_break_dir IS NOT NULL  -- London ORB traded
        ORDER BY date_local
    ),

    labeled AS (
        SELECT
            date_local,

            -- Prior inventory levels
            prior_london_high, prior_london_low,
            prior_ny_2300_high, prior_ny_2300_low,
            prior_ny_0030_high, prior_ny_0030_low,
            prior_asia_high, prior_asia_low,

            -- Asia session
            asia_high, asia_low,

            -- London ORB
            orb_1800_high, orb_1800_low, orb_1800_size, orb_1800_break_dir,

            -- Resolution labels (binary: did Asia sweep this level?)
            CASE
                WHEN prior_ny_2300_high IS NOT NULL AND asia_high >= prior_ny_2300_high THEN 1
                WHEN prior_ny_0030_high IS NOT NULL AND asia_high >= prior_ny_0030_high THEN 1
                ELSE 0
            END as resolved_prior_ny_high,

            CASE
                WHEN prior_ny_2300_low IS NOT NULL AND asia_low <= prior_ny_2300_low THEN 1
                WHEN prior_ny_0030_low IS NOT NULL AND asia_low <= prior_ny_0030_low THEN 1
                ELSE 0
            END as resolved_prior_ny_low,

            CASE
                WHEN prior_london_high IS NOT NULL AND asia_high >= prior_london_high THEN 1
                ELSE 0
            END as resolved_prior_london_high,

            CASE
                WHEN prior_london_low IS NOT NULL AND asia_low <= prior_london_low THEN 1
                ELSE 0
            END as resolved_prior_london_low,

            -- Prior day (full day high/low)
            CASE
                WHEN prior_asia_high IS NOT NULL AND asia_high >= prior_asia_high THEN 1
                ELSE 0
            END as resolved_prior_day_high,

            CASE
                WHEN prior_asia_low IS NOT NULL AND asia_low <= prior_asia_low THEN 1
                ELSE 0
            END as resolved_prior_day_low,

            -- Resolution depth (how far beyond the level)
            CASE
                WHEN prior_ny_2300_high IS NOT NULL AND asia_high >= prior_ny_2300_high
                    THEN (asia_high - prior_ny_2300_high) / {TICK_SIZE}
                WHEN prior_ny_0030_high IS NOT NULL AND asia_high >= prior_ny_0030_high
                    THEN (asia_high - prior_ny_0030_high) / {TICK_SIZE}
                ELSE NULL
            END as ny_high_depth_ticks,

            CASE
                WHEN prior_ny_2300_low IS NOT NULL AND asia_low <= prior_ny_2300_low
                    THEN (prior_ny_2300_low - asia_low) / {TICK_SIZE}
                WHEN prior_ny_0030_low IS NOT NULL AND asia_low <= prior_ny_0030_low
                    THEN (prior_ny_0030_low - asia_low) / {TICK_SIZE}
                ELSE NULL
            END as ny_low_depth_ticks,

            CASE
                WHEN prior_london_high IS NOT NULL AND asia_high >= prior_london_high
                    THEN (asia_high - prior_london_high) / {TICK_SIZE}
                ELSE NULL
            END as london_high_depth_ticks,

            CASE
                WHEN prior_london_low IS NOT NULL AND asia_low <= prior_london_low
                    THEN (prior_london_low - asia_low) / {TICK_SIZE}
                ELSE NULL
            END as london_low_depth_ticks

        FROM daily_sessions
        WHERE prior_london_high IS NOT NULL  -- Must have prior session data
    )

    SELECT * FROM labeled
    ORDER BY date_local
    """

    df = con.execute(query_labels).df()
    print(f"Total days with London ORB: {len(df)}")
    print()

    # Step 2: Classify Asia state
    print("Step 2: Classifying Asia state...")
    print("-" * 80)

    def classify_asia_state(row):
        """
        Classify into mutually exclusive categories:
        1. NY_HIGH - resolved prior NY high only
        2. NY_LOW - resolved prior NY low only
        3. LONDON_HIGH - resolved prior London high only (not NY)
        4. LONDON_LOW - resolved prior London low only (not NY)
        5. DAY_HIGH - resolved prior day high only (not NY or London)
        6. DAY_LOW - resolved prior day low only (not NY or London)
        7. BOTH_NY - resolved both NY high and low
        8. BOTH_LONDON - resolved both London high and low
        9. FAILED - no prior inventory resolved
        """
        ny_h = row['resolved_prior_ny_high']
        ny_l = row['resolved_prior_ny_low']
        ldn_h = row['resolved_prior_london_high']
        ldn_l = row['resolved_prior_london_low']
        day_h = row['resolved_prior_day_high']
        day_l = row['resolved_prior_day_low']

        # Priority order: NY > London > Day
        if ny_h and ny_l:
            return 'BOTH_NY'
        elif ny_h and not ny_l:
            return 'NY_HIGH'
        elif ny_l and not ny_h:
            return 'NY_LOW'
        elif ldn_h and ldn_l:
            return 'BOTH_LONDON'
        elif ldn_h and not ldn_l:
            return 'LONDON_HIGH'
        elif ldn_l and not ldn_h:
            return 'LONDON_LOW'
        elif day_h and not day_l:
            return 'DAY_HIGH'
        elif day_l and not day_h:
            return 'DAY_LOW'
        else:
            return 'FAILED'

    df['asia_state'] = df.apply(classify_asia_state, axis=1)

    print("Asia State Distribution:")
    print(df['asia_state'].value_counts().sort_index())
    print()

    # Step 3: Get London ORB outcomes from trades table
    print("Step 3: Loading London ORB outcomes...")
    print("-" * 80)

    query_outcomes = """
    SELECT
        date_local,
        orb,
        direction,
        outcome,
        r_multiple
    FROM orb_trades_5m_exec_orbr
    WHERE orb = '1800'
        AND outcome IN ('WIN', 'LOSS')
    """

    outcomes = con.execute(query_outcomes).df()
    print(f"London trades with outcomes: {len(outcomes)}")
    print()

    # Merge
    df = df.merge(outcomes, on='date_local', how='left')

    # Filter to only rows with outcomes
    df_with_outcome = df[df['outcome'].notna()].copy()
    print(f"Days with both labels and outcomes: {len(df_with_outcome)}")
    print()

    # Step 4: Analyze by Asia state
    print("=" * 80)
    print("RESULTS: London ORB Performance by Asia Prior Inventory Resolution")
    print("=" * 80)
    print()

    results = []

    for state in sorted(df_with_outcome['asia_state'].unique()):
        subset = df_with_outcome[df_with_outcome['asia_state'] == state]

        if len(subset) < 20:  # Skip small samples
            continue

        total = len(subset)
        wins = len(subset[subset['outcome'] == 'WIN'])
        wr = wins / total * 100
        avg_r = subset['r_multiple'].mean()
        total_r = subset['r_multiple'].sum()

        # Break down by direction
        up_subset = subset[subset['direction'] == 'UP']
        down_subset = subset[subset['direction'] == 'DOWN']

        up_count = len(up_subset)
        down_count = len(down_subset)

        up_wr = len(up_subset[up_subset['outcome'] == 'WIN']) / up_count * 100 if up_count > 0 else 0
        down_wr = len(down_subset[down_subset['outcome'] == 'WIN']) / down_count * 100 if down_count > 0 else 0

        up_avg_r = up_subset['r_multiple'].mean() if up_count > 0 else 0
        down_avg_r = down_subset['r_multiple'].mean() if down_count > 0 else 0

        up_total_r = up_subset['r_multiple'].sum() if up_count > 0 else 0
        down_total_r = down_subset['r_multiple'].sum() if down_count > 0 else 0

        results.append({
            'asia_state': state,
            'total': total,
            'wr': wr,
            'avg_r': avg_r,
            'total_r': total_r,
            'up_count': up_count,
            'up_wr': up_wr,
            'up_avg_r': up_avg_r,
            'up_total_r': up_total_r,
            'down_count': down_count,
            'down_wr': down_wr,
            'down_avg_r': down_avg_r,
            'down_total_r': down_total_r
        })

    results_df = pd.DataFrame(results)

    # Calculate baseline
    baseline_total = len(df_with_outcome)
    baseline_wins = len(df_with_outcome[df_with_outcome['outcome'] == 'WIN'])
    baseline_wr = baseline_wins / baseline_total * 100
    baseline_avg_r = df_with_outcome['r_multiple'].mean()

    print(f"BASELINE (All London ORBs):")
    print(f"  Total: {baseline_total}")
    print(f"  Win Rate: {baseline_wr:.1f}%")
    print(f"  Avg R: {baseline_avg_r:+.3f}R")
    print(f"  Total R: {df_with_outcome['r_multiple'].sum():+.1f}R")
    print()
    print("-" * 80)
    print()

    # Sort by total_r descending
    results_df = results_df.sort_values('total_r', ascending=False)

    print("DETAILED RESULTS:")
    print()
    for _, row in results_df.iterrows():
        state = row['asia_state']
        print(f"{'=' * 80}")
        print(f"Asia State: {state}")
        print(f"{'=' * 80}")
        print(f"Overall Performance:")
        print(f"  Total Trades: {row['total']}")
        print(f"  Win Rate: {row['wr']:.1f}% (Delta {row['wr']-baseline_wr:+.1f}%)")
        print(f"  Avg R: {row['avg_r']:+.3f}R (Delta {row['avg_r']-baseline_avg_r:+.3f}R)")
        print(f"  Total R: {row['total_r']:+.1f}R")
        print()

        print(f"UP Breakouts:")
        print(f"  Count: {row['up_count']}")
        print(f"  Win Rate: {row['up_wr']:.1f}%")
        print(f"  Avg R: {row['up_avg_r']:+.3f}R")
        print(f"  Total R: {row['up_total_r']:+.1f}R")
        print()

        print(f"DOWN Breakouts:")
        print(f"  Count: {row['down_count']}")
        print(f"  Win Rate: {row['down_wr']:.1f}%")
        print(f"  Avg R: {row['down_avg_r']:+.3f}R")
        print(f"  Total R: {row['down_total_r']:+.1f}R")
        print()

    # Step 5: Continuation vs Fade analysis
    print("=" * 80)
    print("CONTINUATION vs FADE ANALYSIS")
    print("=" * 80)
    print()

    continuation_results = []

    for state in ['NY_HIGH', 'NY_LOW', 'LONDON_HIGH', 'LONDON_LOW', 'DAY_HIGH', 'DAY_LOW']:
        subset = df_with_outcome[df_with_outcome['asia_state'] == state]

        if len(subset) < 20:
            continue

        # Determine expected direction for continuation
        if 'HIGH' in state:
            cont_dir = 'UP'
            fade_dir = 'DOWN'
        else:
            cont_dir = 'DOWN'
            fade_dir = 'UP'

        cont_subset = subset[subset['direction'] == cont_dir]
        fade_subset = subset[subset['direction'] == fade_dir]

        cont_count = len(cont_subset)
        fade_count = len(fade_subset)

        if cont_count > 0:
            cont_wr = len(cont_subset[cont_subset['outcome'] == 'WIN']) / cont_count * 100
            cont_avg_r = cont_subset['r_multiple'].mean()
            cont_total_r = cont_subset['r_multiple'].sum()
        else:
            cont_wr = cont_avg_r = cont_total_r = 0

        if fade_count > 0:
            fade_wr = len(fade_subset[fade_subset['outcome'] == 'WIN']) / fade_count * 100
            fade_avg_r = fade_subset['r_multiple'].mean()
            fade_total_r = fade_subset['r_multiple'].sum()
        else:
            fade_wr = fade_avg_r = fade_total_r = 0

        continuation_results.append({
            'state': state,
            'cont_dir': cont_dir,
            'cont_count': cont_count,
            'cont_wr': cont_wr,
            'cont_avg_r': cont_avg_r,
            'cont_total_r': cont_total_r,
            'fade_dir': fade_dir,
            'fade_count': fade_count,
            'fade_wr': fade_wr,
            'fade_avg_r': fade_avg_r,
            'fade_total_r': fade_total_r,
            'delta_wr': cont_wr - fade_wr,
            'delta_avg_r': cont_avg_r - fade_avg_r
        })

    cont_df = pd.DataFrame(continuation_results)

    for _, row in cont_df.iterrows():
        print(f"Asia State: {row['state']}")
        print(f"  Continuation ({row['cont_dir']}): {row['cont_count']} trades, {row['cont_wr']:.1f}% WR, {row['cont_avg_r']:+.3f}R avg, {row['cont_total_r']:+.1f}R total")
        print(f"  Fade ({row['fade_dir']}):        {row['fade_count']} trades, {row['fade_wr']:.1f}% WR, {row['fade_avg_r']:+.3f}R avg, {row['fade_total_r']:+.1f}R total")
        print(f"  Delta (Cont - Fade):    DeltaWR = {row['delta_wr']:+.1f}%, DeltaAvgR = {row['delta_avg_r']:+.3f}R")

        # Verdict
        if row['delta_avg_r'] > 0.10 and row['cont_count'] >= 20:
            verdict = "[YES] CONTINUATION EDGE"
        elif row['delta_avg_r'] < -0.10 and row['fade_count'] >= 20:
            verdict = "[WARN] FADE EDGE (unexpected)"
        else:
            verdict = "~ NEUTRAL"

        print(f"  Verdict: {verdict}")
        print()

    # Step 6: Resolution depth analysis
    print("=" * 80)
    print("RESOLUTION DEPTH ANALYSIS")
    print("=" * 80)
    print()

    # Only for resolved states
    for state, depth_col in [
        ('NY_HIGH', 'ny_high_depth_ticks'),
        ('NY_LOW', 'ny_low_depth_ticks'),
        ('LONDON_HIGH', 'london_high_depth_ticks'),
        ('LONDON_LOW', 'london_low_depth_ticks')
    ]:
        subset = df_with_outcome[
            (df_with_outcome['asia_state'] == state) &
            (df_with_outcome[depth_col].notna())
        ]

        if len(subset) < 20:
            continue

        # Split into shallow (<10 ticks) and deep (>=10 ticks)
        shallow = subset[subset[depth_col] < 10]
        deep = subset[subset[depth_col] >= 10]

        print(f"{state}:")

        if len(shallow) > 0:
            shallow_wr = len(shallow[shallow['outcome'] == 'WIN']) / len(shallow) * 100
            shallow_avg_r = shallow['r_multiple'].mean()
            print(f"  Shallow (<10 ticks): {len(shallow)} trades, {shallow_wr:.1f}% WR, {shallow_avg_r:+.3f}R avg")

        if len(deep) > 0:
            deep_wr = len(deep[deep['outcome'] == 'WIN']) / len(deep) * 100
            deep_avg_r = deep['r_multiple'].mean()
            print(f"  Deep (>=10 ticks):   {len(deep)} trades, {deep_wr:.1f}% WR, {deep_avg_r:+.3f}R avg")

        if len(shallow) > 0 and len(deep) > 0:
            delta_wr = deep_wr - shallow_wr
            delta_avg_r = deep_avg_r - shallow_avg_r
            print(f"  Delta (Deep - Shallow): DeltaWR = {delta_wr:+.1f}%, DeltaAvgR = {delta_avg_r:+.3f}R")

        print()

    # Step 7: Summary and recommendations
    print("=" * 80)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 80)
    print()

    print("KEY FINDINGS:")
    print()

    # Find best continuation patterns
    best_cont = cont_df.nlargest(3, 'cont_total_r')
    print("Best Continuation Patterns (by Total R):")
    for i, (_, row) in enumerate(best_cont.iterrows(), 1):
        print(f"{i}. {row['state']} -> London {row['cont_dir']}: {row['cont_total_r']:+.1f}R ({row['cont_count']} trades, {row['cont_wr']:.1f}% WR)")
    print()

    # Find worst fade patterns
    worst_fade = cont_df.nsmallest(3, 'fade_total_r')
    print("Worst Fade Patterns (AVOID - by Total R):")
    for i, (_, row) in enumerate(worst_fade.iterrows(), 1):
        print(f"{i}. {row['state']} -> London {row['fade_dir']}: {row['fade_total_r']:+.1f}R ({row['fade_count']} trades, {row['fade_wr']:.1f}% WR)")
    print()

    print("NEXT STEPS:")
    print("1. Validate top patterns with out-of-sample testing")
    print("2. Test resolution timing (early vs late Asia)")
    print("3. Consider combining NY + London resolution states")
    print()

    con.close()

    print("=" * 80)
    print("Test complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
