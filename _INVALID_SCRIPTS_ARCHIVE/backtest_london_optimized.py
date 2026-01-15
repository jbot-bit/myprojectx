"""
Backtest London ORB with optimized filters.

Tests:
- Asia range filters (tight, normal, wide)
- NY_HIGH directional filter
- Small ORB filter
- Multiple RR values (1.0 to 3.5)
- Multiple stop modes (half-SL, full-SL)

Goal: Find best RR and parameter combinations.
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta
import itertools

DB_PATH = "gold.db"
TICK_SIZE = 0.10

def get_london_data_with_filters(con):
    """Get all London setups with filter labels"""

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
            orb_0900_low, orb_1000_low, orb_1100_low,

            -- London
            orb_1800_high, orb_1800_low,
            (orb_1800_high - orb_1800_low) / {TICK_SIZE} as london_orb_ticks,
            orb_1800_break_dir

        FROM daily_features_v2
        WHERE instrument = 'MGC'
            AND orb_1800_break_dir IS NOT NULL
    ),

    labeled AS (
        SELECT
            date_local,
            orb_1800_high,
            orb_1800_low,
            london_orb_ticks,
            orb_1800_break_dir,
            asia_range_ticks,

            -- Prior NY high/low
            GREATEST(
                COALESCE(prior_ny_2300_high, -999999),
                COALESCE(prior_ny_0030_high, -999999)
            ) as prior_ny_high,

            LEAST(
                COALESCE(prior_ny_2300_low, 999999),
                COALESCE(prior_ny_0030_low, 999999)
            ) as prior_ny_low,

            asia_high, asia_low,

            -- NY_HIGH resolution
            CASE
                WHEN asia_high >= GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999))
                    AND GREATEST(COALESCE(prior_ny_2300_high, -999999), COALESCE(prior_ny_0030_high, -999999)) > -999999
                THEN 1 ELSE 0
            END as resolved_ny_high,

            -- NY_LOW resolution
            CASE
                WHEN asia_low <= LEAST(COALESCE(prior_ny_2300_low, 999999), COALESCE(prior_ny_0030_low, 999999))
                    AND LEAST(COALESCE(prior_ny_2300_low, 999999), COALESCE(prior_ny_0030_low, 999999)) < 999999
                THEN 1 ELSE 0
            END as resolved_ny_low,

            -- Asia range category
            CASE
                WHEN (asia_high - asia_low) / {TICK_SIZE} < 100 THEN 'TIGHT'
                WHEN (asia_high - asia_low) / {TICK_SIZE} >= 100 AND (asia_high - asia_low) / {TICK_SIZE} < 200 THEN 'NORMAL'
                WHEN (asia_high - asia_low) / {TICK_SIZE} >= 200 AND (asia_high - asia_low) / {TICK_SIZE} < 300 THEN 'WIDE'
                ELSE 'EXPANDED'
            END as asia_range_category,

            -- London ORB size category
            CASE
                WHEN (orb_1800_high - orb_1800_low) / {TICK_SIZE} < 10 THEN 'TINY'
                WHEN (orb_1800_high - orb_1800_low) / {TICK_SIZE} >= 10
                    AND (orb_1800_high - orb_1800_low) / {TICK_SIZE} < 20 THEN 'SMALL'
                WHEN (orb_1800_high - orb_1800_low) / {TICK_SIZE} >= 20
                    AND (orb_1800_high - orb_1800_low) / {TICK_SIZE} < 30 THEN 'NORMAL'
                WHEN (orb_1800_high - orb_1800_low) / {TICK_SIZE} >= 30
                    AND (orb_1800_high - orb_1800_low) / {TICK_SIZE} < 50 THEN 'LARGE'
                ELSE 'HUGE'
            END as london_orb_category

        FROM daily
        WHERE prior_ny_2300_high IS NOT NULL
    )

    SELECT * FROM labeled
    ORDER BY date_local
    """

    return con.execute(query).df()

def backtest_london_config(df_setups, rr, sl_mode, filters):
    """
    Backtest a single configuration.

    filters dict can contain:
    - asia_range: 'TIGHT', 'NORMAL', 'WIDE', 'EXPANDED', or list
    - london_orb: 'TINY', 'SMALL', 'NORMAL', 'LARGE', 'HUGE', or list
    - ny_high_dir: True = only UP if ny_high, False = no filter
    - skip_ny_low: True = skip if ny_low resolved
    """

    results = []

    for _, row in df_setups.iterrows():
        date = row['date_local']
        orb_high = row['orb_1800_high']
        orb_low = row['orb_1800_low']
        direction = row['orb_1800_break_dir']

        # Apply filters
        if 'asia_range' in filters:
            allowed_ranges = filters['asia_range'] if isinstance(filters['asia_range'], list) else [filters['asia_range']]
            if row['asia_range_category'] not in allowed_ranges:
                continue  # Skip this trade

        if 'london_orb' in filters:
            allowed_orbs = filters['london_orb'] if isinstance(filters['london_orb'], list) else [filters['london_orb']]
            if row['london_orb_category'] not in allowed_orbs:
                continue

        # NY_HIGH directional filter
        if filters.get('ny_high_dir', False):
            if row['resolved_ny_high'] == 1 and direction == 'DOWN':
                continue  # Skip DOWN if NY_HIGH resolved (toxic pattern)

        # Skip NY_LOW
        if filters.get('skip_ny_low', False):
            if row['resolved_ny_low'] == 1:
                continue  # Skip all trades if NY_LOW resolved (broken pattern)

        # Calculate entry/stop/target
        orb_range = orb_high - orb_low
        orb_midpoint = (orb_high + orb_low) / 2

        if direction == 'UP':
            entry = orb_high
            if sl_mode == 'HALF':
                stop = orb_midpoint
            else:  # FULL
                stop = orb_low
            target = entry + rr * (entry - stop)
        else:  # DOWN
            entry = orb_low
            if sl_mode == 'HALF':
                stop = orb_midpoint
            else:  # FULL
                stop = orb_high
            target = entry - rr * (stop - entry)

        risk_ticks = abs(entry - stop) / TICK_SIZE

        # For now, just record the setup (we'll match with actual outcomes later)
        results.append({
            'date_local': date,
            'direction': direction,
            'entry': entry,
            'stop': stop,
            'target': target,
            'risk_ticks': risk_ticks,
            'rr': rr,
            'sl_mode': sl_mode,
            'orb_high': orb_high,
            'orb_low': orb_low,
            'asia_range_cat': row['asia_range_category'],
            'london_orb_cat': row['london_orb_category'],
            'resolved_ny_high': row['resolved_ny_high'],
            'resolved_ny_low': row['resolved_ny_low']
        })

    return pd.DataFrame(results)

def simulate_outcomes(trades_df, con):
    """Simulate trade outcomes using 5m bars"""

    if len(trades_df) == 0:
        return trades_df

    # Get 5m bars for all trade dates
    dates_str = "', '".join(trades_df['date_local'].astype(str).unique())

    query = f"""
    SELECT
        DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') as date_local,
        ts_utc,
        high,
        low,
        close
    FROM bars_5m
    WHERE symbol = 'MGC'
        AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') IN ('{dates_str}')
        AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') >= 18
    ORDER BY ts_utc
    """

    bars = con.execute(query).df()

    # Simulate each trade
    outcomes = []

    for _, trade in trades_df.iterrows():
        date = trade['date_local']
        direction = trade['direction']
        entry = trade['entry']
        stop = trade['stop']
        target = trade['target']

        # Get bars for this date after 18:05
        trade_bars = bars[bars['date_local'] == date].sort_values('ts_utc')

        if len(trade_bars) == 0:
            continue

        # Find entry bar (first close outside ORB)
        orb_high = trade['orb_high']
        orb_low = trade['orb_low']

        entry_bar_idx = None
        for idx, bar in trade_bars.iterrows():
            if direction == 'UP' and bar['close'] > orb_high:
                entry_bar_idx = idx
                break
            elif direction == 'DOWN' and bar['close'] < orb_low:
                entry_bar_idx = idx
                break

        if entry_bar_idx is None:
            continue  # No entry

        # Simulate from entry bar onwards
        entry_bars = trade_bars.loc[entry_bar_idx:].copy()

        outcome = None
        exit_bar = None
        r_multiple = None

        for idx, bar in entry_bars.iterrows():
            if direction == 'UP':
                # Check stop first (conservative)
                if bar['low'] <= stop:
                    outcome = 'LOSS'
                    exit_bar = idx
                    r_multiple = -1.0
                    break
                # Check target
                if bar['high'] >= target:
                    outcome = 'WIN'
                    exit_bar = idx
                    r_multiple = trade['rr']
                    break
            else:  # DOWN
                # Check stop first
                if bar['high'] >= stop:
                    outcome = 'LOSS'
                    exit_bar = idx
                    r_multiple = -1.0
                    break
                # Check target
                if bar['low'] <= target:
                    outcome = 'WIN'
                    exit_bar = idx
                    r_multiple = trade['rr']
                    break

        if outcome is None:
            outcome = 'NO_DECISION'
            r_multiple = 0.0

        outcomes.append({
            **trade.to_dict(),
            'outcome': outcome,
            'r_multiple': r_multiple
        })

    return pd.DataFrame(outcomes)

def main():
    print("=" * 80)
    print("LONDON ORB OPTIMIZATION BACKTEST")
    print("=" * 80)
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Get all London setups with labels
    print("Loading London setups...")
    df_setups = get_london_data_with_filters(con)
    print(f"Total London ORB days: {len(df_setups)}")
    print()

    # Define configurations to test
    configs = []

    # RR values to test
    rr_values = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

    # Stop modes
    sl_modes = ['HALF', 'FULL']

    # Filter combinations
    filter_sets = [
        {'name': 'BASELINE', 'filters': {}},
        {'name': 'ASIA_NORMAL', 'filters': {'asia_range': 'NORMAL'}},
        {'name': 'ASIA_NORMAL_WIDE', 'filters': {'asia_range': ['NORMAL', 'WIDE']}},
        {'name': 'SMALL_ORB', 'filters': {'london_orb': ['TINY', 'SMALL']}},
        {'name': 'ASIA_NORMAL_SMALL_ORB', 'filters': {'asia_range': 'NORMAL', 'london_orb': ['TINY', 'SMALL']}},
        {'name': 'NY_HIGH_DIR', 'filters': {'ny_high_dir': True}},
        {'name': 'ASIA_NORMAL_NY_HIGH', 'filters': {'asia_range': 'NORMAL', 'ny_high_dir': True}},
        {'name': 'ASIA_NORMAL_NY_HIGH_SKIP_LOW', 'filters': {'asia_range': 'NORMAL', 'ny_high_dir': True, 'skip_ny_low': True}},
        {'name': 'ALL_FILTERS', 'filters': {'asia_range': 'NORMAL', 'london_orb': ['TINY', 'SMALL'], 'ny_high_dir': True, 'skip_ny_low': True}},
    ]

    # Generate all combinations
    for fset in filter_sets:
        for rr in rr_values:
            for sl_mode in sl_modes:
                configs.append({
                    'name': f"{fset['name']}_RR{rr}_SL{sl_mode}",
                    'rr': rr,
                    'sl_mode': sl_mode,
                    'filters': fset['filters'],
                    'filter_name': fset['name']
                })

    print(f"Testing {len(configs)} configurations...")
    print()

    # Run all backtests
    all_results = []

    for i, config in enumerate(configs):
        if (i + 1) % 10 == 0:
            print(f"Progress: {i+1}/{len(configs)} configurations...")

        # Generate trades for this config
        trades = backtest_london_config(df_setups, config['rr'], config['sl_mode'], config['filters'])

        if len(trades) == 0:
            continue

        # Simulate outcomes
        trades_with_outcomes = simulate_outcomes(trades, con)

        if len(trades_with_outcomes) == 0:
            continue

        # Filter to decided trades
        decided = trades_with_outcomes[trades_with_outcomes['outcome'].isin(['WIN', 'LOSS'])]

        if len(decided) == 0:
            continue

        # Calculate stats
        total_trades = len(decided)
        wins = len(decided[decided['outcome'] == 'WIN'])
        losses = len(decided[decided['outcome'] == 'LOSS'])
        wr = wins / total_trades * 100

        total_r = decided['r_multiple'].sum()
        avg_r = decided['r_multiple'].mean()

        # Expectancy
        if wins > 0 and losses > 0:
            avg_win = decided[decided['outcome'] == 'WIN']['r_multiple'].mean()
            avg_loss = decided[decided['outcome'] == 'LOSS']['r_multiple'].mean()
            expectancy = (wr / 100) * avg_win + ((100 - wr) / 100) * avg_loss
        else:
            expectancy = avg_r

        all_results.append({
            'config': config['name'],
            'filter_name': config['filter_name'],
            'rr': config['rr'],
            'sl_mode': config['sl_mode'],
            'trades': total_trades,
            'wins': wins,
            'losses': losses,
            'wr': wr,
            'total_r': total_r,
            'avg_r': avg_r,
            'expectancy': expectancy
        })

    print()
    print("=" * 80)
    print("BACKTEST COMPLETE")
    print("=" * 80)
    print()

    # Convert to DataFrame
    results_df = pd.DataFrame(all_results)

    # Sort by total_r descending
    results_df = results_df.sort_values('total_r', ascending=False)

    # Print top 20
    print("TOP 20 CONFIGURATIONS (by Total R):")
    print("=" * 80)
    print(results_df.head(20).to_string(index=False))
    print()

    # Best by expectancy
    print("\nTOP 20 CONFIGURATIONS (by Expectancy):")
    print("=" * 80)
    results_sorted_exp = results_df.sort_values('expectancy', ascending=False)
    print(results_sorted_exp.head(20).to_string(index=False))
    print()

    # Best by win rate (min 50 trades)
    print("\nTOP 20 CONFIGURATIONS (by Win Rate, min 50 trades):")
    print("=" * 80)
    results_wr = results_df[results_df['trades'] >= 50].sort_values('wr', ascending=False)
    print(results_wr.head(20).to_string(index=False))
    print()

    # Analysis by filter
    print("\nBEST CONFIG FOR EACH FILTER SET:")
    print("=" * 80)
    for fname in results_df['filter_name'].unique():
        subset = results_df[results_df['filter_name'] == fname].sort_values('total_r', ascending=False)
        if len(subset) > 0:
            best = subset.iloc[0]
            print(f"\n{fname}:")
            print(f"  Best: RR={best['rr']}, SL={best['sl_mode']}")
            print(f"  Trades: {best['trades']}, WR: {best['wr']:.1f}%, Avg R: {best['avg_r']:+.3f}, Total R: {best['total_r']:+.1f}")

    print()

    # Save full results
    results_df.to_csv('london_backtest_results.csv', index=False)
    print("Full results saved to: london_backtest_results.csv")

    con.close()

    print()
    print("=" * 80)
    print("DONE!")
    print("=" * 80)

if __name__ == "__main__":
    main()
