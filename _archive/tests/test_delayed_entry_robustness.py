"""
DELAYED ENTRY ROBUSTNESS TEST

Test how system performs if entry is delayed by:
- +1 bar (realistic: manual execution delay)
- +2 bars (conservative: slow execution or distraction)

Measures Avg R degradation to assess execution sensitivity.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"
TICK_SIZE = 0.10

def simulate_orb_delayed(con, orb_time, rr, sl_mode, delay_bars, filters=None):
    """
    Simulate ORB with delayed entry.

    delay_bars: 0 (immediate), 1, or 2
    """
    if filters is None:
        filters = {}

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

    if 'max_stop' in filters:
        df_setups = df_setups[df_setups['orb_range_ticks'] <= filters['max_stop']]

    if len(df_setups) == 0:
        return pd.DataFrame()

    dates_str = "', '".join(df_setups['date_local'].astype(str).unique())

    hour_map = {'0900': 9, '1000': 10, '1100': 11, '1800': 18, '2300': 23, '0030': 0}
    orb_hour = hour_map[orb_time]

    if orb_time in ['0900', '1000', '1100']:
        end_hour = 18
    elif orb_time == '1800':
        end_hour = 23
    elif orb_time in ['2300', '0030']:
        end_hour = 2

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

    results = []

    for _, setup in df_setups.iterrows():
        date = setup['date_local']
        orb_high = setup['orb_high']
        orb_low = setup['orb_low']
        direction = setup['break_dir']
        orb_midpoint = (orb_high + orb_low) / 2

        if direction == 'UP':
            if sl_mode == 'HALF':
                stop = orb_midpoint
            else:
                stop = orb_low
        else:
            if sl_mode == 'HALF':
                stop = orb_midpoint
            else:
                stop = orb_high

        trade_bars = bars[bars['date_local'] == date].sort_values('ts_utc')

        if len(trade_bars) == 0:
            continue

        # Find signal bar (first close outside ORB)
        signal_bar_idx = None
        for idx, bar in trade_bars.iterrows():
            if direction == 'UP' and bar['close'] > orb_high:
                signal_bar_idx = idx
                break
            elif direction == 'DOWN' and bar['close'] < orb_low:
                signal_bar_idx = idx
                break

        if signal_bar_idx is None:
            continue

        # Delayed entry: skip delay_bars after signal
        signal_position = trade_bars.index.get_loc(signal_bar_idx)

        if signal_position + delay_bars >= len(trade_bars):
            continue  # Not enough bars for delayed entry

        entry_bar_idx = trade_bars.index[signal_position + delay_bars]
        entry_bar = trade_bars.loc[entry_bar_idx]

        # Entry price = close of delayed bar
        entry_price = entry_bar['close']

        # Recalculate risk from actual entry
        if direction == 'UP':
            risk = entry_price - stop
            target = entry_price + rr * risk
        else:
            risk = stop - entry_price
            target = entry_price - rr * risk

        if risk <= 0:
            continue  # Invalid (entry already past stop)

        risk_ticks = risk / TICK_SIZE

        # Apply ASIA_TP_CAP
        if 'asia_tp_cap' in filters and orb_time in ['0900', '1000', '1100']:
            max_target_ticks = filters['asia_tp_cap']
            target_ticks = abs(target - entry_price) / TICK_SIZE
            if target_ticks > max_target_ticks:
                continue

        # Simulate from entry
        entry_bars = trade_bars.loc[entry_bar_idx:].copy()

        outcome = None
        r_multiple = None

        # FIXED R DEFINITION: R = ORB range (fixed per setup)
        orb_range = orb_high - orb_low

        for idx, bar in entry_bars.iterrows():
            if direction == 'UP':
                stop_hit = bar['low'] <= stop
                target_hit = bar['high'] >= target

                if stop_hit and target_hit:
                    outcome = 'LOSS'  # Worst case
                    actual_loss = entry_price - stop  # Can exceed orb_range
                    r_multiple = -actual_loss / orb_range  # Can exceed -1R
                    break
                elif stop_hit:
                    outcome = 'LOSS'
                    actual_loss = entry_price - stop
                    r_multiple = -actual_loss / orb_range
                    break
                elif target_hit:
                    outcome = 'WIN'
                    r_multiple = rr
                    break
            else:
                stop_hit = bar['high'] >= stop
                target_hit = bar['low'] <= target

                if stop_hit and target_hit:
                    outcome = 'LOSS'  # Worst case
                    actual_loss = stop - entry_price  # Can exceed orb_range
                    r_multiple = -actual_loss / orb_range  # Can exceed -1R
                    break
                elif stop_hit:
                    outcome = 'LOSS'
                    actual_loss = stop - entry_price
                    r_multiple = -actual_loss / orb_range
                    break
                elif target_hit:
                    outcome = 'WIN'
                    r_multiple = rr
                    break

        if outcome in ['WIN', 'LOSS']:
            results.append({
                'date_local': date,
                'orb_time': orb_time,
                'direction': direction,
                'outcome': outcome,
                'r_multiple': r_multiple,
                'rr': rr,
                'sl_mode': sl_mode,
                'delay_bars': delay_bars,
                'orb_range_ticks': setup['orb_range_ticks'],
                'risk_ticks': risk_ticks
            })

    return pd.DataFrame(results)

def main():
    print("=" * 80)
    print("DELAYED ENTRY ROBUSTNESS TEST")
    print("=" * 80)
    print()
    print("Testing entry delays:")
    print("  +0 bars: Immediate (baseline)")
    print("  +1 bar:  5 minutes late (realistic manual execution)")
    print("  +2 bars: 10 minutes late (conservative)")
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Use optimal params from worst-case test
    try:
        optimal_df = pd.read_csv('worst_case_parameters.csv', dtype={'orb': str})
        print("Using optimal parameters from worst-case test")
    except FileNotFoundError:
        print("Warning: worst_case_parameters.csv not found, using canonical")
        optimal_df = pd.read_csv('canonical_session_parameters.csv', dtype={'orb': str})

    print()

    delay_tests = [0, 1, 2]
    all_results = []

    for delay in delay_tests:
        print(f"Testing +{delay} bar delay...")

        for _, opt_row in optimal_df.iterrows():
            orb = opt_row['orb']
            rr = opt_row['optimal_rr']
            sl_mode = opt_row['optimal_sl']
            filter_name = opt_row['optimal_filter']

            # Map filter name to dict
            if filter_name == 'MAX_STOP_100':
                filters = {'max_stop': 100}
            elif filter_name == 'MAX_STOP_100_TP_CAP_150':
                filters = {'max_stop': 100, 'asia_tp_cap': 150}
            else:
                filters = {}

            trades = simulate_orb_delayed(con, orb, rr, sl_mode, delay, filters)

            if len(trades) > 0:
                total_r = trades['r_multiple'].sum()
                avg_r = trades['r_multiple'].mean()
                wr = len(trades[trades['outcome'] == 'WIN']) / len(trades) * 100

                all_results.append({
                    'orb': orb,
                    'delay_bars': delay,
                    'trades': len(trades),
                    'wr': wr,
                    'avg_r': avg_r,
                    'total_r': total_r
                })

    con.close()

    results_df = pd.DataFrame(all_results)
    results_df.to_csv('delayed_entry_results.csv', index=False)

    print()
    print("=" * 80)
    print("DELAYED ENTRY IMPACT")
    print("=" * 80)
    print()

    # Pivot to show degradation per ORB
    for orb in optimal_df['orb'].unique():
        orb_results = results_df[results_df['orb'] == orb]

        if len(orb_results) == 0:
            continue

        print(f"{orb} ORB:")
        print("-" * 80)

        baseline = orb_results[orb_results['delay_bars'] == 0]
        delay1 = orb_results[orb_results['delay_bars'] == 1]
        delay2 = orb_results[orb_results['delay_bars'] == 2]

        if len(baseline) > 0:
            baseline_r = baseline.iloc[0]['avg_r']
            print(f"  Baseline (+0 bars): {baseline_r:+.3f}R avg")

            if len(delay1) > 0:
                delay1_r = delay1.iloc[0]['avg_r']
                degradation1 = delay1_r - baseline_r
                pct1 = (degradation1 / baseline_r * 100) if baseline_r != 0 else 0
                print(f"  +1 bar delay:       {delay1_r:+.3f}R avg ({degradation1:+.3f}R, {pct1:+.1f}%)")

            if len(delay2) > 0:
                delay2_r = delay2.iloc[0]['avg_r']
                degradation2 = delay2_r - baseline_r
                pct2 = (degradation2 / baseline_r * 100) if baseline_r != 0 else 0
                print(f"  +2 bar delay:       {delay2_r:+.3f}R avg ({degradation2:+.3f}R, {pct2:+.1f}%)")

        print()

    print("=" * 80)
    print("ROBUSTNESS ASSESSMENT")
    print("=" * 80)
    print()

    # Calculate average degradation
    baseline_avg = results_df[results_df['delay_bars'] == 0]['avg_r'].mean()
    delay1_avg = results_df[results_df['delay_bars'] == 1]['avg_r'].mean()
    delay2_avg = results_df[results_df['delay_bars'] == 2]['avg_r'].mean()

    print(f"System-wide average:")
    print(f"  Baseline:   {baseline_avg:+.3f}R")
    print(f"  +1 bar:     {delay1_avg:+.3f}R ({(delay1_avg - baseline_avg):+.3f}R, {((delay1_avg - baseline_avg) / baseline_avg * 100):+.1f}%)")
    print(f"  +2 bars:    {delay2_avg:+.3f}R ({(delay2_avg - baseline_avg):+.3f}R, {((delay2_avg - baseline_avg) / baseline_avg * 100):+.1f}%)")
    print()

    # Verdict
    degradation_1bar_pct = abs((delay1_avg - baseline_avg) / baseline_avg * 100)
    degradation_2bar_pct = abs((delay2_avg - baseline_avg) / baseline_avg * 100)

    print("VERDICT:")
    if delay1_avg > 0 and degradation_1bar_pct < 20:
        print(f"  +1 bar delay: ACCEPTABLE ({degradation_1bar_pct:.1f}% degradation)")
    elif delay1_avg > 0:
        print(f"  +1 bar delay: MARGINAL ({degradation_1bar_pct:.1f}% degradation)")
    else:
        print(f"  +1 bar delay: FAILS (edge disappears)")

    if delay2_avg > 0 and degradation_2bar_pct < 30:
        print(f"  +2 bar delay: ACCEPTABLE ({degradation_2bar_pct:.1f}% degradation)")
    elif delay2_avg > 0:
        print(f"  +2 bar delay: MARGINAL ({degradation_2bar_pct:.1f}% degradation)")
    else:
        print(f"  +2 bar delay: FAILS (edge disappears)")

    print()
    print("Recommendation:")
    if delay1_avg > 0:
        print("  System is EXECUTION-ROBUST (tolerates realistic delays)")
    else:
        print("  System is EXECUTION-SENSITIVE (requires immediate fills)")
        print("  WARNING: Real-world performance may differ significantly")

    print()
    print("Files saved: delayed_entry_results.csv")
    print()

if __name__ == "__main__":
    main()
