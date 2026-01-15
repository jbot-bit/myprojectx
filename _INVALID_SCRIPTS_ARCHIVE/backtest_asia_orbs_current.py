"""
Backtest Asia ORBs (09:00, 10:00, 11:00) with current 2024-2026 data.

This will update TRADING_RULESET.md with accurate results.
Tests multiple RR values and configurations.
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "gold.db"
TICK_SIZE = 0.10

def simulate_orb_trades(con, orb_time, rr, sl_mode, filters=None):
    """
    Simulate ORB trades for a given configuration.

    orb_time: '0900', '1000', '1100'
    rr: 1.0, 1.5, 2.0, 2.5, 3.0, etc.
    sl_mode: 'HALF' or 'FULL'
    filters: dict with 'max_stop', 'asia_tp_cap', etc.
    """

    if filters is None:
        filters = {}

    # Get all days with this ORB
    query = f"""
    SELECT
        date_local,
        orb_{orb_time}_high as orb_high,
        orb_{orb_time}_low as orb_low,
        orb_{orb_time}_break_dir as break_dir,
        (orb_{orb_time}_high - orb_{orb_time}_low) / {TICK_SIZE} as orb_range_ticks
    FROM daily_features_v2
    WHERE instrument = 'MGC'
        AND orb_{orb_time}_break_dir IS NOT NULL
    ORDER BY date_local
    """

    df_setups = con.execute(query).df()

    # Apply filters
    if 'max_stop' in filters:
        df_setups = df_setups[df_setups['orb_range_ticks'] <= filters['max_stop']]

    if len(df_setups) == 0:
        return pd.DataFrame()

    # Get bars for simulation
    dates_str = "', '".join(df_setups['date_local'].astype(str).unique())

    # Query bars after ORB close
    hour_map = {'0900': 9, '1000': 10, '1100': 11}
    orb_hour = hour_map[orb_time]

    query_bars = f"""
    SELECT
        DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') as date_local,
        ts_utc,
        high,
        low,
        close
    FROM bars_5m
    WHERE symbol = 'MGC'
        AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') IN ('{dates_str}')
        AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') >= {orb_hour}
        AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < 18
    ORDER BY ts_utc
    """

    bars = con.execute(query_bars).df()

    # Simulate each trade
    results = []

    for _, setup in df_setups.iterrows():
        date = setup['date_local']
        orb_high = setup['orb_high']
        orb_low = setup['orb_low']
        direction = setup['break_dir']
        orb_range = orb_high - orb_low
        orb_midpoint = (orb_high + orb_low) / 2

        # Calculate entry/stop/target
        if direction == 'UP':
            entry = orb_high
            if sl_mode == 'HALF':
                stop = orb_midpoint
            else:
                stop = orb_low
            risk = entry - stop
            target = entry + rr * risk
        else:  # DOWN
            entry = orb_low
            if sl_mode == 'HALF':
                stop = orb_midpoint
            else:
                stop = orb_high
            risk = stop - entry
            target = entry - rr * risk

        risk_ticks = risk / TICK_SIZE

        # Apply ASIA_TP_CAP filter if present
        if 'asia_tp_cap' in filters:
            max_target_ticks = filters['asia_tp_cap']
            target_ticks = abs(target - entry) / TICK_SIZE
            if target_ticks > max_target_ticks:
                continue  # Skip this trade

        # Get bars for this date
        trade_bars = bars[bars['date_local'] == date].sort_values('ts_utc')

        if len(trade_bars) == 0:
            continue

        # Find entry bar (first close outside ORB)
        entry_bar_idx = None
        for idx, bar in trade_bars.iterrows():
            if direction == 'UP' and bar['close'] > orb_high:
                entry_bar_idx = idx
                break
            elif direction == 'DOWN' and bar['close'] < orb_low:
                entry_bar_idx = idx
                break

        if entry_bar_idx is None:
            continue

        # Simulate from entry
        entry_bars = trade_bars.loc[entry_bar_idx:].copy()

        outcome = None
        r_multiple = None

        for idx, bar in entry_bars.iterrows():
            if direction == 'UP':
                if bar['low'] <= stop:
                    outcome = 'LOSS'
                    r_multiple = -1.0
                    break
                if bar['high'] >= target:
                    outcome = 'WIN'
                    r_multiple = rr
                    break
            else:  # DOWN
                if bar['high'] >= stop:
                    outcome = 'LOSS'
                    r_multiple = -1.0
                    break
                if bar['low'] <= target:
                    outcome = 'WIN'
                    r_multiple = rr
                    break

        if outcome is None:
            outcome = 'NO_DECISION'
            r_multiple = 0.0

        if outcome in ['WIN', 'LOSS']:
            results.append({
                'date_local': date,
                'orb_time': orb_time,
                'direction': direction,
                'outcome': outcome,
                'r_multiple': r_multiple,
                'rr': rr,
                'sl_mode': sl_mode,
                'orb_range_ticks': setup['orb_range_ticks'],
                'risk_ticks': risk_ticks
            })

    return pd.DataFrame(results)

def main():
    print("=" * 80)
    print("ASIA ORB BACKTEST - Current Data (2024-2026)")
    print("=" * 80)
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Check date range
    date_range = con.execute("SELECT MIN(date_local), MAX(date_local) FROM daily_features_v2").fetchone()
    print(f"Database date range: {date_range[0]} to {date_range[1]}")
    print()

    # Test configurations
    orb_times = ['0900', '1000', '1100']
    rr_values = [1.0, 1.5, 2.0, 2.5, 3.0]
    sl_modes = ['HALF', 'FULL']

    # Filter sets to test
    filter_sets = [
        {'name': 'BASELINE', 'filters': {}},
        {'name': 'MAX_STOP_100', 'filters': {'max_stop': 100}},
        {'name': 'MAX_STOP_100_TP_CAP_150', 'filters': {'max_stop': 100, 'asia_tp_cap': 150}},
    ]

    all_results = []
    config_count = 0
    total_configs = len(orb_times) * len(rr_values) * len(sl_modes) * len(filter_sets)

    print(f"Testing {total_configs} configurations...")
    print()

    for orb_time in orb_times:
        for rr in rr_values:
            for sl_mode in sl_modes:
                for fset in filter_sets:
                    config_count += 1

                    if config_count % 10 == 0:
                        print(f"Progress: {config_count}/{total_configs}...")

                    trades = simulate_orb_trades(con, orb_time, rr, sl_mode, fset['filters'])

                    if len(trades) == 0:
                        continue

                    # Calculate stats
                    total_trades = len(trades)
                    wins = len(trades[trades['outcome'] == 'WIN'])
                    losses = len(trades[trades['outcome'] == 'LOSS'])
                    wr = wins / total_trades * 100

                    total_r = trades['r_multiple'].sum()
                    avg_r = trades['r_multiple'].mean()

                    all_results.append({
                        'orb_time': orb_time,
                        'rr': rr,
                        'sl_mode': sl_mode,
                        'filter_set': fset['name'],
                        'trades': total_trades,
                        'wins': wins,
                        'losses': losses,
                        'wr': wr,
                        'total_r': total_r,
                        'avg_r': avg_r
                    })

    con.close()

    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    results_df = pd.DataFrame(all_results)

    # Best configs for each ORB
    print("BEST CONFIGURATION FOR EACH ORB (by Total R):")
    print("=" * 80)
    print()

    for orb in ['0900', '1000', '1100']:
        orb_results = results_df[results_df['orb_time'] == orb].sort_values('total_r', ascending=False)

        if len(orb_results) == 0:
            continue

        print(f"{orb} ORB:")
        print("-" * 80)

        # Top 5
        top5 = orb_results.head(5)
        for idx, (_, row) in enumerate(top5.iterrows(), 1):
            print(f"{idx}. RR={row['rr']}, SL={row['sl_mode']}, Filter={row['filter_set']}")
            print(f"   Trades: {row['trades']}, WR: {row['wr']:.1f}%, Avg R: {row['avg_r']:+.3f}, Total R: {row['total_r']:+.1f}")

        print()

    # Summary by filter set
    print("=" * 80)
    print("SUMMARY BY FILTER SET (All Asia ORBs Combined):")
    print("=" * 80)
    print()

    for fset_name in results_df['filter_set'].unique():
        subset = results_df[results_df['filter_set'] == fset_name]

        print(f"{fset_name}:")
        print("-" * 80)

        total_trades = subset['trades'].sum()
        total_r = subset['total_r'].sum()
        weighted_avg_r = total_r / total_trades if total_trades > 0 else 0

        print(f"  Total Trades: {total_trades}")
        print(f"  Total R: {total_r:+.1f}")
        print(f"  Weighted Avg R: {weighted_avg_r:+.3f}")

        # Best RR for this filter set
        best = subset.sort_values('total_r', ascending=False).iloc[0]
        print(f"  Best: {best['orb_time']} ORB, RR={best['rr']}, SL={best['sl_mode']} ({best['total_r']:+.1f}R)")
        print()

    # Save full results
    results_df.to_csv('asia_orb_backtest_current.csv', index=False)
    print("Full results saved to: asia_orb_backtest_current.csv")
    print()

    # Comparison: Skip 09:00 vs Trade All
    print("=" * 80)
    print("SKIP 09:00 ANALYSIS:")
    print("=" * 80)
    print()

    # Best config for each ORB in MAX_STOP_100_TP_CAP_150
    filtered = results_df[results_df['filter_set'] == 'MAX_STOP_100_TP_CAP_150']

    for orb in ['0900', '1000', '1100']:
        orb_best = filtered[filtered['orb_time'] == orb].sort_values('total_r', ascending=False).iloc[0]
        print(f"{orb}: RR={orb_best['rr']}, SL={orb_best['sl_mode']}")
        print(f"  {orb_best['trades']} trades, {orb_best['wr']:.1f}% WR, {orb_best['total_r']:+.1f}R")

    print()

    # Compare: All 3 vs Just 10:00 + 11:00
    all_three = filtered['total_r'].sum()
    skip_0900 = filtered[filtered['orb_time'].isin(['1000', '1100'])]['total_r'].sum()

    print(f"Trade all 3 ORBs: {all_three:+.1f}R")
    print(f"Skip 09:00, trade 10:00+11:00: {skip_0900:+.1f}R")
    print(f"Difference: {skip_0900 - all_three:+.1f}R")

    if skip_0900 > all_three:
        print("[YES] Skipping 09:00 improves results")
    else:
        print("[NO] Trading all 3 ORBs is better")

    print()
    print("=" * 80)
    print("DONE!")
    print("=" * 80)

if __name__ == "__main__":
    main()
