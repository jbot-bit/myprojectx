"""
Comprehensive London ORB Analysis - Find what makes it tradeable.

Tests:
1. Prior inventory (NY high/low resolution) with timing
2. Asia session characteristics (range, volatility, travel)
3. London ORB size filters
4. Pre-London travel (11:00-18:00)
5. Combination patterns

Goal: Find simple, actionable rules to trade London profitably.
"""

import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = "gold.db"
TICK_SIZE = 0.10

def analyze_prior_inventory_with_timing(con):
    """Test 1: Prior inventory resolution + timing of resolution"""

    print("=" * 80)
    print("TEST 1: PRIOR INVENTORY + RESOLUTION TIMING")
    print("=" * 80)
    print()

    query = f"""
    WITH daily AS (
        SELECT
            date_local,

            -- Prior NY inventory
            LAG(orb_2300_high) OVER (ORDER BY date_local) as prior_ny_2300_high,
            LAG(orb_2300_low) OVER (ORDER BY date_local) as prior_ny_2300_low,
            LAG(orb_0030_high) OVER (ORDER BY date_local) as prior_ny_0030_high,
            LAG(orb_0030_low) OVER (ORDER BY date_local) as prior_ny_0030_low,

            -- Asia ORBs (to determine timing)
            orb_0900_high, orb_0900_low,
            orb_1000_high, orb_1000_low,
            orb_1100_high, orb_1100_low,
            asia_high, asia_low,

            -- London ORB
            orb_1800_high, orb_1800_low, orb_1800_size, orb_1800_break_dir

        FROM daily_features_v2
        WHERE instrument = 'MGC'
            AND orb_1800_break_dir IS NOT NULL
    ),

    labeled AS (
        SELECT
            date_local,

            -- Prior inventory levels (take max/min across NY ORBs)
            GREATEST(
                COALESCE(prior_ny_2300_high, -999999),
                COALESCE(prior_ny_0030_high, -999999)
            ) as prior_ny_high,

            LEAST(
                COALESCE(prior_ny_2300_low, 999999),
                COALESCE(prior_ny_0030_low, 999999)
            ) as prior_ny_low,

            asia_high, asia_low,
            orb_0900_high, orb_1000_high, orb_1100_high,
            orb_1800_break_dir,

            -- Resolution binary
            CASE
                WHEN asia_high >= GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999))
                    AND GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999)) > -999999
                THEN 1 ELSE 0
            END as resolved_ny_high,

            CASE
                WHEN asia_low <= LEAST(COALESCE(prior_ny_2300_low, 999999), COALESCE(prior_ny_0030_low, 999999))
                    AND LEAST(COALESCE(prior_ny_2300_low, 999999), COALESCE(prior_ny_0030_low, 999999)) < 999999
                THEN 1 ELSE 0
            END as resolved_ny_low,

            -- Timing: when did Asia resolve?
            CASE
                WHEN orb_0900_high >= GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999))
                    AND GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999)) > -999999
                THEN 'EARLY_0900'
                WHEN orb_1000_high >= GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999))
                    AND GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999)) > -999999
                THEN 'MID_1000'
                WHEN orb_1100_high >= GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999))
                    AND GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999)) > -999999
                THEN 'LATE_1100'
                ELSE NULL
            END as resolve_high_timing,

            CASE
                WHEN orb_0900_low <= LEAST(COALESCE(prior_ny_2300_low, 999999), COALESCE(prior_ny_0030_low, 999999))
                    AND LEAST(COALESCE(prior_ny_2300_low, 999999), COALESCE(prior_ny_0030_low, 999999)) < 999999
                THEN 'EARLY_0900'
                WHEN orb_1000_low <= LEAST(COALESCE(prior_ny_2300_low, 999999), COALESCE(prior_ny_0030_low, 999999))
                    AND LEAST(COALESCE(prior_ny_2300_low, 999999), COALESCE(prior_ny_0030_low, 999999)) < 999999
                THEN 'MID_1000'
                WHEN orb_1100_low <= LEAST(COALESCE(prior_ny_2300_low, 999999), COALESCE(prior_ny_0030_low, 999999))
                    AND LEAST(COALESCE(prior_ny_2300_low, 999999), COALESCE(prior_ny_0030_low, 999999)) < 999999
                THEN 'LATE_1100'
                ELSE NULL
            END as resolve_low_timing

        FROM daily
        WHERE prior_ny_2300_high IS NOT NULL
    )

    SELECT * FROM labeled
    """

    df = con.execute(query).df()

    # Get outcomes
    outcomes = con.execute("""
        SELECT date_local, orb, direction, outcome, r_multiple
        FROM orb_trades_5m_exec_orbr
        WHERE orb = '1800' AND outcome IN ('WIN', 'LOSS')
    """).df()

    df = df.merge(outcomes, on='date_local', how='inner')

    print(f"Total London trades: {len(df)}")
    print()

    # Analyze NY_HIGH with timing
    ny_high = df[df['resolved_ny_high'] == 1]

    if len(ny_high) > 0:
        print("NY_HIGH RESOLUTION BY TIMING:")
        print("-" * 80)

        for timing in ['EARLY_0900', 'MID_1000', 'LATE_1100']:
            timing_subset = ny_high[ny_high['resolve_high_timing'] == timing]

            if len(timing_subset) < 10:
                continue

            # UP (continuation)
            up = timing_subset[timing_subset['direction'] == 'UP']
            if len(up) > 0:
                up_wr = len(up[up['outcome'] == 'WIN']) / len(up) * 100
                up_avg_r = up['r_multiple'].mean()
                up_total_r = up['r_multiple'].sum()
            else:
                up_wr = up_avg_r = up_total_r = 0

            # DOWN (fade)
            down = timing_subset[timing_subset['direction'] == 'DOWN']
            if len(down) > 0:
                down_wr = len(down[down['outcome'] == 'WIN']) / len(down) * 100
                down_avg_r = down['r_multiple'].mean()
                down_total_r = down['r_multiple'].sum()
            else:
                down_wr = down_avg_r = down_total_r = 0

            print(f"\n{timing}:")
            print(f"  London UP:   {len(up)} trades, {up_wr:.1f}% WR, {up_avg_r:+.3f}R avg, {up_total_r:+.1f}R total")
            print(f"  London DOWN: {len(down)} trades, {down_wr:.1f}% WR, {down_avg_r:+.3f}R avg, {down_total_r:+.1f}R total")
            if len(up) > 0 and len(down) > 0:
                print(f"  Delta (UP - DOWN): {up_avg_r - down_avg_r:+.3f}R")

        print()

    # Analyze NY_LOW with timing
    ny_low = df[df['resolved_ny_low'] == 1]

    if len(ny_low) > 0:
        print("NY_LOW RESOLUTION BY TIMING:")
        print("-" * 80)

        for timing in ['EARLY_0900', 'MID_1000', 'LATE_1100']:
            timing_subset = ny_low[ny_low['resolve_low_timing'] == timing]

            if len(timing_subset) < 10:
                continue

            # DOWN (continuation)
            down = timing_subset[timing_subset['direction'] == 'DOWN']
            if len(down) > 0:
                down_wr = len(down[down['outcome'] == 'WIN']) / len(down) * 100
                down_avg_r = down['r_multiple'].mean()
                down_total_r = down['r_multiple'].sum()
            else:
                down_wr = down_avg_r = down_total_r = 0

            # UP (fade)
            up = timing_subset[timing_subset['direction'] == 'UP']
            if len(up) > 0:
                up_wr = len(up[up['outcome'] == 'WIN']) / len(up) * 100
                up_avg_r = up['r_multiple'].mean()
                up_total_r = up['r_multiple'].sum()
            else:
                up_wr = up_avg_r = up_total_r = 0

            print(f"\n{timing}:")
            print(f"  London DOWN: {len(down)} trades, {down_wr:.1f}% WR, {down_avg_r:+.3f}R avg, {down_total_r:+.1f}R total")
            print(f"  London UP:   {len(up)} trades, {up_wr:.1f}% WR, {up_avg_r:+.3f}R avg, {up_total_r:+.1f}R total")
            if len(up) > 0 and len(down) > 0:
                print(f"  Delta (DOWN - UP): {down_avg_r - up_avg_r:+.3f}R")

        print()

def analyze_asia_characteristics(con):
    """Test 2: Asia session characteristics that affect London"""

    print("=" * 80)
    print("TEST 2: ASIA SESSION CHARACTERISTICS")
    print("=" * 80)
    print()

    query = """
    SELECT
        d.date_local,
        d.asia_high,
        d.asia_low,
        d.asia_high - d.asia_low as asia_range,
        (d.asia_high - d.asia_low) / 0.10 as asia_range_ticks,
        d.pre_london_range as pre_london_travel,
        d.orb_1800_size,
        d.orb_1800_break_dir
    FROM daily_features_v2 d
    WHERE d.instrument = 'MGC'
        AND d.orb_1800_break_dir IS NOT NULL
    """

    df = con.execute(query).df()

    # Get outcomes
    outcomes = con.execute("""
        SELECT date_local, direction, outcome, r_multiple
        FROM orb_trades_5m_exec_orbr
        WHERE orb = '1800' AND outcome IN ('WIN', 'LOSS')
    """).df()

    df = df.merge(outcomes, on='date_local', how='inner')

    print(f"Total London trades: {len(df)}")
    print()

    # Test: Asia range size
    print("ASIA RANGE SIZE:")
    print("-" * 80)

    for label, min_val, max_val in [
        ('Tight (<100 ticks)', 0, 100),
        ('Normal (100-200 ticks)', 100, 200),
        ('Wide (200-300 ticks)', 200, 300),
        ('Expanded (>300 ticks)', 300, 999999)
    ]:
        subset = df[(df['asia_range_ticks'] >= min_val) & (df['asia_range_ticks'] < max_val)]

        if len(subset) < 20:
            continue

        wins = len(subset[subset['outcome'] == 'WIN'])
        wr = wins / len(subset) * 100
        avg_r = subset['r_multiple'].mean()
        total_r = subset['r_multiple'].sum()

        print(f"{label}: {len(subset)} trades, {wr:.1f}% WR, {avg_r:+.3f}R avg, {total_r:+.1f}R total")

    print()

    # Test: Pre-London travel (11:00-18:00)
    print("PRE-LONDON TRAVEL (11:00-18:00):")
    print("-" * 80)

    for label, min_val, max_val in [
        ('Quiet (<30 ticks)', 0, 30),
        ('Normal (30-60 ticks)', 30, 60),
        ('Active (60-100 ticks)', 60, 100),
        ('Volatile (>100 ticks)', 100, 999999)
    ]:
        subset = df[(df['pre_london_travel'] >= min_val) & (df['pre_london_travel'] < max_val)]

        if len(subset) < 20:
            continue

        wins = len(subset[subset['outcome'] == 'WIN'])
        wr = wins / len(subset) * 100
        avg_r = subset['r_multiple'].mean()
        total_r = subset['r_multiple'].sum()

        print(f"{label}: {len(subset)} trades, {wr:.1f}% WR, {avg_r:+.3f}R avg, {total_r:+.1f}R total")

    print()

def analyze_london_orb_size(con):
    """Test 3: London ORB size filters"""

    print("=" * 80)
    print("TEST 3: LONDON ORB SIZE")
    print("=" * 80)
    print()

    query = """
    SELECT
        d.date_local,
        d.orb_1800_size,
        d.orb_1800_break_dir
    FROM daily_features_v2 d
    WHERE d.instrument = 'MGC'
        AND d.orb_1800_break_dir IS NOT NULL
    """

    df = con.execute(query).df()

    # Get outcomes
    outcomes = con.execute("""
        SELECT date_local, direction, outcome, r_multiple, orb_range_ticks
        FROM orb_trades_5m_exec_orbr
        WHERE orb = '1800' AND outcome IN ('WIN', 'LOSS')
    """).df()

    df = df.merge(outcomes, on='date_local', how='inner')

    print(f"Total London trades: {len(df)}")
    print()

    print("LONDON ORB SIZE:")
    print("-" * 80)

    for label, min_val, max_val in [
        ('Tiny (<10 ticks)', 0, 10),
        ('Small (10-20 ticks)', 10, 20),
        ('Normal (20-30 ticks)', 20, 30),
        ('Large (30-50 ticks)', 30, 50),
        ('Huge (>50 ticks)', 50, 999999)
    ]:
        subset = df[(df['orb_range_ticks'] >= min_val) & (df['orb_range_ticks'] < max_val)]

        if len(subset) < 20:
            continue

        wins = len(subset[subset['outcome'] == 'WIN'])
        wr = wins / len(subset) * 100
        avg_r = subset['r_multiple'].mean()
        total_r = subset['r_multiple'].sum()

        print(f"{label}: {len(subset)} trades, {wr:.1f}% WR, {avg_r:+.3f}R avg, {total_r:+.1f}R total")

    print()

def analyze_combinations(con):
    """Test 4: Best combinations"""

    print("=" * 80)
    print("TEST 4: COMBINATION PATTERNS")
    print("=" * 80)
    print()

    query = f"""
    WITH daily AS (
        SELECT
            date_local,

            -- Prior NY inventory
            LAG(orb_2300_high) OVER (ORDER BY date_local) as prior_ny_2300_high,
            LAG(orb_2300_low) OVER (ORDER BY date_local) as prior_ny_2300_low,
            LAG(orb_0030_high) OVER (ORDER BY date_local) as prior_ny_0030_high,
            LAG(orb_0030_low) OVER (ORDER BY date_local) as prior_ny_0030_low,

            -- Asia
            asia_high, asia_low,
            (asia_high - asia_low) / {TICK_SIZE} as asia_range_ticks,
            orb_0900_high, orb_1000_high, orb_1100_high,
            pre_london_range as pre_london_travel,

            -- London
            orb_1800_size, orb_1800_break_dir

        FROM daily_features_v2
        WHERE instrument = 'MGC'
            AND orb_1800_break_dir IS NOT NULL
    ),

    labeled AS (
        SELECT
            date_local,
            asia_range_ticks,
            pre_london_travel,
            orb_1800_break_dir,

            -- NY_HIGH resolution
            CASE
                WHEN asia_high >= GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999))
                    AND GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999)) > -999999
                THEN 1 ELSE 0
            END as resolved_ny_high,

            -- Timing
            CASE
                WHEN orb_1000_high >= GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999))
                    AND GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999)) > -999999
                THEN 1 ELSE 0
            END as resolved_by_1000

        FROM daily
        WHERE prior_ny_2300_high IS NOT NULL
    )

    SELECT * FROM labeled
    """

    df = con.execute(query).df()

    # Get outcomes
    outcomes = con.execute("""
        SELECT date_local, direction, outcome, r_multiple, orb_range_ticks
        FROM orb_trades_5m_exec_orbr
        WHERE orb = '1800' AND outcome IN ('WIN', 'LOSS')
    """).df()

    df = df.merge(outcomes, on='date_local', how='inner')

    print(f"Total London trades: {len(df)}")
    print()

    # Test combo: NY_HIGH + Small London ORB
    print("PATTERN 1: NY_HIGH Resolution + Small London ORB (<20 ticks)")
    print("-" * 80)

    subset = df[
        (df['resolved_ny_high'] == 1) &
        (df['orb_range_ticks'] < 20) &
        (df['direction'] == 'UP')
    ]

    if len(subset) >= 10:
        wins = len(subset[subset['outcome'] == 'WIN'])
        wr = wins / len(subset) * 100
        avg_r = subset['r_multiple'].mean()
        total_r = subset['r_multiple'].sum()
        print(f"London UP: {len(subset)} trades, {wr:.1f}% WR, {avg_r:+.3f}R avg, {total_r:+.1f}R total")
    else:
        print("Insufficient sample (<10 trades)")

    print()

    # Test combo: NY_HIGH + Wide Asia Range
    print("PATTERN 2: NY_HIGH Resolution + Wide Asia (>200 ticks)")
    print("-" * 80)

    subset = df[
        (df['resolved_ny_high'] == 1) &
        (df['asia_range_ticks'] > 200) &
        (df['direction'] == 'UP')
    ]

    if len(subset) >= 10:
        wins = len(subset[subset['outcome'] == 'WIN'])
        wr = wins / len(subset) * 100
        avg_r = subset['r_multiple'].mean()
        total_r = subset['r_multiple'].sum()
        print(f"London UP: {len(subset)} trades, {wr:.1f}% WR, {avg_r:+.3f}R avg, {total_r:+.1f}R total")
    else:
        print("Insufficient sample (<10 trades)")

    print()

    # Test combo: NY_HIGH + Resolved by 1000
    print("PATTERN 3: NY_HIGH Resolution by 10:00 ORB")
    print("-" * 80)

    subset = df[
        (df['resolved_ny_high'] == 1) &
        (df['resolved_by_1000'] == 1) &
        (df['direction'] == 'UP')
    ]

    if len(subset) >= 10:
        wins = len(subset[subset['outcome'] == 'WIN'])
        wr = wins / len(subset) * 100
        avg_r = subset['r_multiple'].mean()
        total_r = subset['r_multiple'].sum()
        print(f"London UP: {len(subset)} trades, {wr:.1f}% WR, {avg_r:+.3f}R avg, {total_r:+.1f}R total")
    else:
        print("Insufficient sample (<10 trades)")

    print()

def main():
    print("=" * 80)
    print("COMPREHENSIVE LONDON ANALYSIS")
    print("Goal: Find how to trade London profitably")
    print("=" * 80)
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Run all tests
    analyze_prior_inventory_with_timing(con)
    analyze_asia_characteristics(con)
    analyze_london_orb_size(con)
    analyze_combinations(con)

    con.close()

    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
