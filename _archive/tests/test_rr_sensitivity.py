"""
RR SENSITIVITY TEST

Test if optimal RR parameters are stable or brittle.

For each ORB's optimal RR, test:
- RR - 0.25
- RR (optimal)
- RR + 0.25

Measures performance degradation when RR deviates from optimal.

Critical: If small RR changes cause large performance swings, parameters are BRITTLE.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"
TICK_SIZE = 0.10

def simulate_orb_rr(con, orb_time, rr, sl_mode, filters=None):
    """
    Simulate ORB with specific RR using worst-case execution.
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

        trade_bars = bars[bars['date_local'] == date].sort_values('ts_utc')

        if len(trade_bars) == 0:
            continue

        # Find entry bar
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
                'direction': direction,
                'outcome': outcome,
                'r_multiple': r_multiple,
                'rr': rr,
                'orb_range_ticks': setup['orb_range_ticks'],
                'risk_ticks': risk_ticks
            })

    return pd.DataFrame(results)

def main():
    print("=" * 80)
    print("RR SENSITIVITY TEST")
    print("=" * 80)
    print()
    print("Testing RR stability around optimal:")
    print("  RR - 0.25")
    print("  RR (optimal)")
    print("  RR + 0.25")
    print()
    print("Measures parameter brittleness.")
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

    all_results = []

    for _, opt_row in optimal_df.iterrows():
        orb = opt_row['orb']
        optimal_rr = opt_row['optimal_rr']
        sl_mode = opt_row['optimal_sl']
        filter_name = opt_row['optimal_filter']

        # Map filter
        if filter_name == 'MAX_STOP_100':
            filters = {'max_stop': 100}
        elif filter_name == 'MAX_STOP_100_TP_CAP_150':
            filters = {'max_stop': 100, 'asia_tp_cap': 150}
        else:
            filters = {}

        # Test RR - 0.25, optimal, RR + 0.25
        test_rrs = [
            max(0.5, optimal_rr - 0.25),  # Don't go below 0.5
            optimal_rr,
            optimal_rr + 0.25
        ]

        print(f"Testing {orb} ORB (optimal RR={optimal_rr})...")

        for test_rr in test_rrs:
            trades = simulate_orb_rr(con, orb, test_rr, sl_mode, filters)

            if len(trades) > 0:
                total_r = trades['r_multiple'].sum()
                avg_r = trades['r_multiple'].mean()
                wr = len(trades[trades['outcome'] == 'WIN']) / len(trades) * 100

                all_results.append({
                    'orb': orb,
                    'rr': test_rr,
                    'is_optimal': (test_rr == optimal_rr),
                    'trades': len(trades),
                    'wr': wr,
                    'avg_r': avg_r,
                    'total_r': total_r
                })

    con.close()

    results_df = pd.DataFrame(all_results)
    results_df.to_csv('rr_sensitivity_results.csv', index=False)

    print()
    print("=" * 80)
    print("RR SENSITIVITY RESULTS")
    print("=" * 80)
    print()

    for orb in results_df['orb'].unique():
        orb_results = results_df[results_df['orb'] == orb].sort_values('rr')

        print(f"{orb} ORB:")
        print("-" * 80)

        optimal_row = orb_results[orb_results['is_optimal'] == True].iloc[0]
        optimal_r = optimal_row['avg_r']

        for _, row in orb_results.iterrows():
            rr = row['rr']
            avg_r = row['avg_r']
            is_opt = row['is_optimal']
            degradation = avg_r - optimal_r
            pct_change = (degradation / optimal_r * 100) if optimal_r != 0 else 0

            marker = " (OPTIMAL)" if is_opt else ""
            print(f"  RR {rr:.2f}: {avg_r:+.3f}R avg ({degradation:+.3f}R, {pct_change:+.1f}%){marker}")

        print()

    print("=" * 80)
    print("SENSITIVITY ASSESSMENT")
    print("=" * 80)
    print()

    # Calculate max degradation for each ORB
    sensitivities = []

    for orb in results_df['orb'].unique():
        orb_results = results_df[results_df['orb'] == orb]
        optimal_r = orb_results[orb_results['is_optimal'] == True].iloc[0]['avg_r']

        max_degradation_pct = 0
        for _, row in orb_results.iterrows():
            if not row['is_optimal']:
                degradation = row['avg_r'] - optimal_r
                degradation_pct = abs((degradation / optimal_r * 100)) if optimal_r != 0 else 0
                max_degradation_pct = max(max_degradation_pct, degradation_pct)

        sensitivities.append({
            'orb': orb,
            'max_degradation_pct': max_degradation_pct
        })

        verdict = "STABLE" if max_degradation_pct < 20 else "SENSITIVE" if max_degradation_pct < 50 else "BRITTLE"
        print(f"{orb} ORB: {verdict} (max {max_degradation_pct:.1f}% degradation)")

    print()

    avg_sensitivity = sum(s['max_degradation_pct'] for s in sensitivities) / len(sensitivities)

    print(f"Average sensitivity: {avg_sensitivity:.1f}%")
    print()

    if avg_sensitivity < 20:
        print("✅ PASS: Parameters are STABLE")
        print("   Small RR changes cause minimal performance impact")
        print("   System is NOT brittle to parameter selection")
    elif avg_sensitivity < 50:
        print("⚠️ WARNING: Parameters are MODERATELY SENSITIVE")
        print("   RR deviations cause noticeable degradation")
        print("   Recommend sticking to optimal RR values")
    else:
        print("❌ FAIL: Parameters are BRITTLE")
        print("   Small RR changes cause large performance swings")
        print("   RISK: Overfitting to specific RR values")
        print("   System may not be robust in live trading")

    print()
    print("Files saved: rr_sensitivity_results.csv")
    print()

if __name__ == "__main__":
    main()
