"""
ORB WINDOW SENSITIVITY TEST

Test if system performance is sensitive to ORB window duration.

For each ORB, test:
- 3-minute window (3 bars)
- 5-minute window (5 bars) - BASELINE
- 7-minute window (7 bars)

Uses same optimal RR/SL/filters, only changes ORB calculation window.

Critical: If edge only exists at exactly 5 minutes, it may be data-mined.
Robust systems should work across similar window sizes.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"
TICK_SIZE = 0.10

def calculate_orb_custom(con, date_local, orb_time, window_minutes):
    """
    Calculate ORB with custom window duration.

    orb_time: '0900', '1000', etc.
    window_minutes: 3, 5, or 7
    """
    hour_map = {'0900': 9, '1000': 10, '1100': 11, '1800': 18, '2300': 23, '0030': 0}
    orb_hour = hour_map[orb_time]

    # Calculate end time
    if orb_time == '0030':
        # Special case: 00:30 + window wraps past midnight
        query = f"""
        WITH orb_bars AS (
            SELECT high, low, close
            FROM bars_5m
            WHERE symbol = 'MGC'
                AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') = '{date_local}'
                AND (
                    (EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') = 0
                     AND EXTRACT(MINUTE FROM ts_utc AT TIME ZONE 'Australia/Brisbane') >= 30)
                    OR
                    (EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') = 1
                     AND EXTRACT(MINUTE FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < 30)
                )
            ORDER BY ts_utc
            LIMIT {window_minutes}
        )
        SELECT
            MAX(high) as orb_high,
            MIN(low) as orb_low,
            (SELECT close FROM orb_bars ORDER BY rowid DESC LIMIT 1) as orb_close
        FROM orb_bars
        """
    else:
        query = f"""
        WITH orb_bars AS (
            SELECT high, low, close
            FROM bars_5m
            WHERE symbol = 'MGC'
                AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') = '{date_local}'
                AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') = {orb_hour}
                AND EXTRACT(MINUTE FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < {window_minutes * 5}
            ORDER BY ts_utc
        )
        SELECT
            MAX(high) as orb_high,
            MIN(low) as orb_low,
            (SELECT close FROM orb_bars ORDER BY rowid DESC LIMIT 1) as orb_close
        FROM orb_bars
        """

    result = con.execute(query).fetchone()

    if result and result[0] is not None and result[1] is not None:
        orb_high, orb_low, orb_close = result

        # Determine breakout direction
        if orb_close > orb_high:
            break_dir = 'UP'
        elif orb_close < orb_low:
            break_dir = 'DOWN'
        else:
            break_dir = None

        return {
            'orb_high': orb_high,
            'orb_low': orb_low,
            'orb_close': orb_close,
            'break_dir': break_dir,
            'orb_range_ticks': (orb_high - orb_low) / TICK_SIZE
        }

    return None

def simulate_orb_custom_window(con, orb_time, rr, sl_mode, window_minutes, filters=None):
    """
    Simulate ORB with custom window duration using worst-case execution.
    """
    if filters is None:
        filters = {}

    # Get all trading days
    query = """
    SELECT DISTINCT date_local
    FROM daily_features_v2
    WHERE instrument = 'MGC'
    ORDER BY date_local
    """

    dates_df = con.execute(query).df()

    results = []

    for date in dates_df['date_local']:
        # Calculate custom ORB
        orb_data = calculate_orb_custom(con, date, orb_time, window_minutes)

        if not orb_data or orb_data['break_dir'] is None:
            continue

        orb_high = orb_data['orb_high']
        orb_low = orb_data['orb_low']
        direction = orb_data['break_dir']
        orb_range_ticks = orb_data['orb_range_ticks']

        # Apply max_stop filter
        if 'max_stop' in filters and orb_range_ticks > filters['max_stop']:
            continue

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
        else:
            entry = orb_low
            if sl_mode == 'HALF':
                stop = orb_midpoint
            else:
                stop = orb_high
            risk = stop - entry
            target = entry - rr * risk

        risk_ticks = risk / TICK_SIZE

        # Apply ASIA_TP_CAP
        if 'asia_tp_cap' in filters and orb_time in ['0900', '1000', '1100']:
            max_target_ticks = filters['asia_tp_cap']
            target_ticks = abs(target - entry) / TICK_SIZE
            if target_ticks > max_target_ticks:
                continue

        # Get bars for simulation
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
            SELECT ts_utc, high, low, close
            FROM bars_5m
            WHERE symbol = 'MGC'
                AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') = '{date}'
                AND (
                    EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') >= {orb_hour}
                    OR EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < {end_hour}
                )
            ORDER BY ts_utc
            """
        else:
            query_bars = f"""
            SELECT ts_utc, high, low, close
            FROM bars_5m
            WHERE symbol = 'MGC'
                AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') = '{date}'
                AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') >= {orb_hour}
                AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < {end_hour}
            ORDER BY ts_utc
            """

        trade_bars = con.execute(query_bars).df()

        if len(trade_bars) == 0:
            continue

        # Find entry bar (first close outside ORB AFTER window completes)
        entry_bar_idx = None
        for idx, bar in trade_bars.iterrows():
            # Skip bars within the ORB window
            bar_minute = bar['ts_utc'].minute + bar['ts_utc'].hour * 60
            orb_start_minute = orb_hour * 60 + (30 if orb_time == '0030' else 0)
            orb_end_minute = orb_start_minute + window_minutes * 5

            if bar_minute < orb_end_minute:
                continue

            if direction == 'UP' and bar['close'] > orb_high:
                entry_bar_idx = idx
                break
            elif direction == 'DOWN' and bar['close'] < orb_low:
                entry_bar_idx = idx
                break

        if entry_bar_idx is None:
            continue

        # Simulate (worst-case)
        entry_bars = trade_bars.loc[entry_bar_idx:].copy()

        outcome = None
        r_multiple = None

        for idx, bar in entry_bars.iterrows():
            if direction == 'UP':
                stop_hit = bar['low'] <= stop
                target_hit = bar['high'] >= target

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
            else:
                stop_hit = bar['high'] >= stop
                target_hit = bar['low'] <= target

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

        if outcome in ['WIN', 'LOSS']:
            results.append({
                'date_local': date,
                'orb_time': orb_time,
                'window_minutes': window_minutes,
                'direction': direction,
                'outcome': outcome,
                'r_multiple': r_multiple,
                'orb_range_ticks': orb_range_ticks,
                'risk_ticks': risk_ticks
            })

    return pd.DataFrame(results)

def main():
    print("=" * 80)
    print("ORB WINDOW SENSITIVITY TEST")
    print("=" * 80)
    print()
    print("Testing ORB window durations:")
    print("  3 minutes (3 bars)")
    print("  5 minutes (5 bars) - BASELINE")
    print("  7 minutes (7 bars)")
    print()
    print("Tests if edge is specific to 5-minute window or generalizes.")
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Load optimal params
    try:
        optimal_df = pd.read_csv('worst_case_parameters.csv', dtype={'orb': str})
        print("Using parameters from worst-case test")
    except FileNotFoundError:
        print("Warning: worst_case_parameters.csv not found")
        return

    print()

    window_tests = [3, 5, 7]
    all_results = []

    for window in window_tests:
        print(f"Testing {window}-minute window...")

        for _, opt_row in optimal_df.iterrows():
            orb = opt_row['orb']
            rr = opt_row['optimal_rr']
            sl_mode = opt_row['optimal_sl']
            filter_name = opt_row['optimal_filter']

            # Map filter
            if filter_name == 'MAX_STOP_100':
                filters = {'max_stop': 100}
            elif filter_name == 'MAX_STOP_100_TP_CAP_150':
                filters = {'max_stop': 100, 'asia_tp_cap': 150}
            else:
                filters = {}

            trades = simulate_orb_custom_window(con, orb, rr, sl_mode, window, filters)

            if len(trades) > 0:
                total_r = trades['r_multiple'].sum()
                avg_r = trades['r_multiple'].mean()
                wr = len(trades[trades['outcome'] == 'WIN']) / len(trades) * 100

                all_results.append({
                    'orb': orb,
                    'window_minutes': window,
                    'trades': len(trades),
                    'wr': wr,
                    'avg_r': avg_r,
                    'total_r': total_r
                })

    con.close()

    results_df = pd.DataFrame(all_results)
    results_df.to_csv('orb_window_sensitivity_results.csv', index=False)

    print()
    print("=" * 80)
    print("ORB WINDOW SENSITIVITY RESULTS")
    print("=" * 80)
    print()

    for orb in optimal_df['orb'].unique():
        orb_results = results_df[results_df['orb'] == orb].sort_values('window_minutes')

        if len(orb_results) == 0:
            continue

        print(f"{orb} ORB:")
        print("-" * 80)

        baseline = orb_results[orb_results['window_minutes'] == 5]

        if len(baseline) == 0:
            continue

        baseline_r = baseline.iloc[0]['avg_r']

        for _, row in orb_results.iterrows():
            window = row['window_minutes']
            avg_r = row['avg_r']
            degradation = avg_r - baseline_r
            pct_change = (degradation / baseline_r * 100) if baseline_r != 0 else 0

            marker = " (BASELINE)" if window == 5 else ""
            print(f"  {window} minutes: {avg_r:+.3f}R avg ({degradation:+.3f}R, {pct_change:+.1f}%){marker}")

        print()

    print("=" * 80)
    print("WINDOW ROBUSTNESS ASSESSMENT")
    print("=" * 80)
    print()

    # Calculate max degradation
    max_degradations = []

    for orb in optimal_df['orb'].unique():
        orb_results = results_df[results_df['orb'] == orb]

        if len(orb_results) == 0:
            continue

        baseline = orb_results[orb_results['window_minutes'] == 5]

        if len(baseline) == 0:
            continue

        baseline_r = baseline.iloc[0]['avg_r']

        max_degradation_pct = 0
        for _, row in orb_results.iterrows():
            if row['window_minutes'] != 5:
                degradation = row['avg_r'] - baseline_r
                degradation_pct = abs((degradation / baseline_r * 100)) if baseline_r != 0 else 0
                max_degradation_pct = max(max_degradation_pct, degradation_pct)

        max_degradations.append(max_degradation_pct)

        verdict = "ROBUST" if max_degradation_pct < 30 else "MODERATE" if max_degradation_pct < 60 else "BRITTLE"
        print(f"{orb} ORB: {verdict} (max {max_degradation_pct:.1f}% degradation)")

    print()

    avg_degradation = sum(max_degradations) / len(max_degradations) if len(max_degradations) > 0 else 0

    print(f"Average window sensitivity: {avg_degradation:.1f}%")
    print()

    if avg_degradation < 30:
        print("✅ PASS: System is WINDOW-ROBUST")
        print("   Edge generalizes across window sizes")
        print("   Not overfit to 5-minute duration")
    elif avg_degradation < 60:
        print("⚠️ WARNING: System is MODERATELY WINDOW-SENSITIVE")
        print("   Performance varies with window duration")
        print("   Recommend sticking to 5-minute baseline")
    else:
        print("❌ FAIL: System is WINDOW-BRITTLE")
        print("   Edge only exists at specific window duration")
        print("   RISK: May be data-mined artifact")
        print("   System may not generalize in live trading")

    print()
    print("Files saved: orb_window_sensitivity_results.csv")
    print()

if __name__ == "__main__":
    main()
