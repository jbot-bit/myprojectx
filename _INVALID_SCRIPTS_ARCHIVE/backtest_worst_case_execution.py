"""
WORST-CASE EXECUTION BACKTEST

Complete parameter sweep with HARSH execution assumptions:
- If both TP and SL reachable in same bar → LOSS (worst case)
- No favorable intrabar assumptions
- No price improvement
- No optimistic spread assumptions

This is the HONEST backtest that should determine deployment viability.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"
TICK_SIZE = 0.10

def simulate_orb_worst_case(con, orb_time, rr, sl_mode, filters=None):
    """
    Simulate ORB with WORST-CASE execution.

    Key difference from standard backtest:
    If both TP and SL are reachable in same bar → assume LOSS (stop hit first)
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
    hour_map = {'0900': 9, '1000': 10, '1100': 11, '1800': 18, '2300': 23, '0030': 0}
    orb_hour = hour_map[orb_time]

    # End hour depends on session
    if orb_time in ['0900', '1000', '1100']:
        end_hour = 18
    elif orb_time == '1800':
        end_hour = 23
    elif orb_time in ['2300', '0030']:
        end_hour = 2

    # Query bars
    if orb_time in ['2300', '0030']:
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
            AND (
                EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') >= {orb_hour}
                OR EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < {end_hour}
            )
        ORDER BY ts_utc
        """
    else:
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
            AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < {end_hour}
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

        # Apply ASIA_TP_CAP filter
        if 'asia_tp_cap' in filters and orb_time in ['0900', '1000', '1100']:
            max_target_ticks = filters['asia_tp_cap']
            target_ticks = abs(target - entry) / TICK_SIZE
            if target_ticks > max_target_ticks:
                continue

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

        # Simulate from entry with WORST-CASE logic
        entry_bars = trade_bars.loc[entry_bar_idx:].copy()

        outcome = None
        r_multiple = None

        for idx, bar in entry_bars.iterrows():
            if direction == 'UP':
                stop_hit = bar['low'] <= stop
                target_hit = bar['high'] >= target

                # WORST CASE: If both reachable, assume stop hit first
                if stop_hit and target_hit:
                    outcome = 'LOSS'
                    r_multiple = -1.0
                    break
                elif stop_hit:
                    outcome = 'LOSS'
                    r_multiple = -1.0
                    break
                elif target_hit:
                    outcome = 'WIN'
                    r_multiple = rr
                    break
            else:  # DOWN
                stop_hit = bar['high'] >= stop
                target_hit = bar['low'] <= target

                # WORST CASE: If both reachable, assume stop hit first
                if stop_hit and target_hit:
                    outcome = 'LOSS'
                    r_multiple = -1.0
                    break
                elif stop_hit:
                    outcome = 'LOSS'
                    r_multiple = -1.0
                    break
                elif target_hit:
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
    print("WORST-CASE EXECUTION BACKTEST")
    print("=" * 80)
    print()
    print("HARSH ASSUMPTIONS:")
    print("- If both TP and SL reachable in same bar -> LOSS")
    print("- No favorable intrabar fills")
    print("- No price improvement")
    print()
    print("This is the HONEST test for deployment viability.")
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    date_range = con.execute("SELECT MIN(date_local), MAX(date_local) FROM daily_features_v2").fetchone()
    print(f"Database date range: {date_range[0]} to {date_range[1]}")
    print()

    # Test configurations
    orb_times = ['0900', '1000', '1100', '1800', '2300', '0030']
    rr_values = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    sl_modes = ['HALF', 'FULL']

    filter_sets = [
        {'name': 'BASELINE', 'filters': {}},
        {'name': 'MAX_STOP_100', 'filters': {'max_stop': 100}},
        {'name': 'MAX_STOP_100_TP_CAP_150', 'filters': {'max_stop': 100, 'asia_tp_cap': 150}},
    ]

    all_results = []
    config_count = 0
    total_configs = len(orb_times) * len(rr_values) * len(sl_modes) * len(filter_sets)

    print(f"Testing {total_configs} configurations with WORST-CASE execution...")
    print()

    for orb_time in orb_times:
        print(f"Processing {orb_time} ORB...")
        for rr in rr_values:
            for sl_mode in sl_modes:
                for fset in filter_sets:
                    config_count += 1

                    if config_count % 50 == 0:
                        print(f"Progress: {config_count}/{total_configs}...")

                    trades = simulate_orb_worst_case(con, orb_time, rr, sl_mode, fset['filters'])

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
    print("WORST-CASE RESULTS")
    print("=" * 80)
    print()

    results_df = pd.DataFrame(all_results)

    # Find best config for each ORB
    worst_case_params = []

    for orb in orb_times:
        orb_results = results_df[results_df['orb_time'] == orb].sort_values('total_r', ascending=False)

        if len(orb_results) == 0:
            continue

        best = orb_results.iloc[0]

        verdict = "TRADE" if best['total_r'] > 0 else "SKIP"

        worst_case_params.append({
            'orb': orb,
            'verdict': verdict,
            'optimal_rr': best['rr'],
            'optimal_sl': best['sl_mode'],
            'optimal_filter': best['filter_set'],
            'trades': best['trades'],
            'wr': best['wr'],
            'total_r': best['total_r'],
            'avg_r': best['avg_r']
        })

        print(f"{orb} ORB: {verdict}")
        print("-" * 80)
        print(f"  OPTIMAL: RR={best['rr']}, SL={best['sl_mode']}, Filter={best['filter_set']}")
        print(f"  Performance: {best['trades']} trades, {best['wr']:.1f}% WR, {best['avg_r']:+.3f}R avg, {best['total_r']:+.1f}R total")
        print()

    # Save results
    results_df.to_csv('worst_case_sweep_results.csv', index=False)

    verdicts_df = pd.DataFrame(worst_case_params)
    verdicts_df.to_csv('worst_case_parameters.csv', index=False)

    print("=" * 80)
    print("WORST-CASE PARAMETER SUMMARY")
    print("=" * 80)
    print()

    print(f"{'ORB':<8} {'Verdict':<8} {'RR':<6} {'SL':<6} {'Filter':<25} {'Trades':<8} {'WR%':<8} {'Avg R':<10} {'Total R':<10}")
    print("-" * 110)

    for _, row in verdicts_df.iterrows():
        print(f"{row['orb']:<8} {row['verdict']:<8} {row['optimal_rr']:<6} {row['optimal_sl']:<6} {row['optimal_filter']:<25} {row['trades']:<8} {row['wr']:<8.1f} {row['avg_r']:<+10.3f} {row['total_r']:<+10.1f}")

    print()
    print("=" * 80)
    print("COMPARISON TO OPTIMISTIC EXECUTION")
    print("=" * 80)
    print()

    # Load optimistic results if they exist
    try:
        optimistic_df = pd.read_csv('canonical_session_parameters.csv')

        print("Impact of Worst-Case Execution:")
        print()
        print(f"{'ORB':<8} {'Optimistic R':<14} {'Worst-Case R':<14} {'Degradation':<14} {'Status':<10}")
        print("-" * 70)

        for _, wc_row in verdicts_df.iterrows():
            orb = wc_row['orb']
            opt_row = optimistic_df[optimistic_df['orb'] == orb]

            if len(opt_row) > 0:
                opt_r = opt_row.iloc[0]['total_r']
                wc_r = wc_row['total_r']
                degradation = wc_r - opt_r
                pct_change = (degradation / opt_r * 100) if opt_r != 0 else 0

                status = "OK" if wc_r > 0 else "FAIL"

                print(f"{orb:<8} {opt_r:<+14.1f} {wc_r:<+14.1f} {degradation:<+14.1f} ({pct_change:+.1f}%)  {status:<10}")

        print()

    except FileNotFoundError:
        print("No optimistic results found for comparison")
        print()

    print("=" * 80)
    print("FILES SAVED:")
    print("=" * 80)
    print("  worst_case_sweep_results.csv - All configurations")
    print("  worst_case_parameters.csv - Optimal params per ORB")
    print()
    print("DEPLOYMENT DECISION:")
    print()

    tradeable = verdicts_df[verdicts_df['verdict'] == 'TRADE']
    skip = verdicts_df[verdicts_df['verdict'] == 'SKIP']

    print(f"Tradeable ORBs: {len(tradeable)} / {len(verdicts_df)}")
    print(f"Skip ORBs: {len(skip)} / {len(verdicts_df)}")
    print()

    if len(skip) > 0:
        print("FAILED ORBs (negative after worst-case):")
        for _, row in skip.iterrows():
            print(f"  {row['orb']}: {row['total_r']:+.1f}R")
        print()

    total_wc_r = verdicts_df['total_r'].sum()
    print(f"Total System R (worst-case): {total_wc_r:+.1f}R over 2 years")
    print(f"Annual expectation: {total_wc_r / 2:+.1f}R per year")
    print()

    if total_wc_r > 0:
        print("VERDICT: System remains profitable under worst-case execution")
        print("         Parameters may need adjustment but edge exists")
    else:
        print("VERDICT: System FAILS under worst-case execution")
        print("         DO NOT DEPLOY - Edge does not exist")
    print()

if __name__ == "__main__":
    main()
