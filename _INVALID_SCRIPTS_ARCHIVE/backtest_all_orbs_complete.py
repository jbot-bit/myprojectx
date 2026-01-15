"""
COMPLETE ORB PARAMETER SWEEP

Test ALL 6 ORBs with ALL parameter combinations to find optimal configuration for each.
Do NOT declare any session "bad" until we've tested it with every RR/SL combination.

Sessions: 09:00, 10:00, 11:00, 18:00, 23:00, 00:30
RR values: 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0
SL modes: HALF, FULL
Filters: BASELINE, MAX_STOP=100, MAX_STOP=100+TP_CAP=150

Output: Optimal parameters for each session (lock these as canonical)
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"
TICK_SIZE = 0.10

def simulate_orb_trades(con, orb_time, rr, sl_mode, filters=None):
    """
    Simulate ORB trades for a given configuration.

    orb_time: '0900', '1000', '1100', '1800', '2300', '0030'
    rr: 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0
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
    hour_map = {'0900': 9, '1000': 10, '1100': 11, '1800': 18, '2300': 23, '0030': 0}
    orb_hour = hour_map[orb_time]

    # End hour depends on session
    if orb_time in ['0900', '1000', '1100']:
        end_hour = 18  # Asia session ends at London open
    elif orb_time == '1800':
        end_hour = 23  # London session ends at NY open
    elif orb_time == '2300':
        end_hour = 2  # NY session ends at 02:00
    elif orb_time == '0030':
        end_hour = 2  # NY session ends at 02:00

    # Query bars (handle wraparound for NY session)
    if orb_time in ['2300', '0030']:
        # NY session spans midnight - need special handling
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

        # Apply ASIA_TP_CAP filter if present (only for Asia ORBs)
        if 'asia_tp_cap' in filters and orb_time in ['0900', '1000', '1100']:
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
    print("COMPLETE ORB PARAMETER SWEEP")
    print("=" * 80)
    print()
    print("Testing ALL 6 ORBs with ALL parameter combinations")
    print("Goal: Find optimal parameters for each session")
    print("Rule: Only mark session 'SKIP' if negative at BEST configuration")
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Check date range
    date_range = con.execute("SELECT MIN(date_local), MAX(date_local) FROM daily_features_v2").fetchone()
    print(f"Database date range: {date_range[0]} to {date_range[1]}")
    print()

    # Test configurations
    orb_times = ['0900', '1000', '1100', '1800', '2300', '0030']
    rr_values = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    sl_modes = ['HALF', 'FULL']

    # Filter sets
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
        print(f"Processing {orb_time} ORB...")
        for rr in rr_values:
            for sl_mode in sl_modes:
                for fset in filter_sets:
                    config_count += 1

                    if config_count % 50 == 0:
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
    print("CANONICAL SESSION PARAMETERS (LOCKED)")
    print("=" * 80)
    print()

    results_df = pd.DataFrame(all_results)

    # Find BEST configuration for each ORB (by total R)
    session_verdicts = []

    for orb in orb_times:
        orb_results = results_df[results_df['orb_time'] == orb].sort_values('total_r', ascending=False)

        if len(orb_results) == 0:
            print(f"{orb} ORB: NO DATA")
            continue

        # Best config
        best = orb_results.iloc[0]

        # Verdict
        if best['total_r'] > 0:
            verdict = "TRADE"
        else:
            verdict = "SKIP"

        session_verdicts.append({
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
        print(f"  OPTIMAL CONFIG: RR={best['rr']}, SL={best['sl_mode']}, Filter={best['filter_set']}")
        print(f"  Performance: {best['trades']} trades, {best['wr']:.1f}% WR, {best['avg_r']:+.3f}R avg, {best['total_r']:+.1f}R total")
        print()

        # Show top 3 configs
        print(f"  Top 3 configurations:")
        for idx, (_, row) in enumerate(orb_results.head(3).iterrows(), 1):
            print(f"    {idx}. RR={row['rr']}, SL={row['sl_mode']}, Filter={row['filter_set']}: {row['total_r']:+.1f}R")
        print()

    # Save results
    results_df.to_csv('complete_orb_sweep_results.csv', index=False)

    verdicts_df = pd.DataFrame(session_verdicts)
    verdicts_df.to_csv('canonical_session_parameters.csv', index=False)

    print("=" * 80)
    print("SUMMARY: CANONICAL SESSION VERDICTS")
    print("=" * 80)
    print()

    print(f"{'ORB':<8} {'Verdict':<8} {'RR':<6} {'SL':<6} {'Filter':<25} {'Trades':<8} {'WR%':<8} {'Avg R':<10} {'Total R':<10}")
    print("-" * 110)

    for _, row in verdicts_df.iterrows():
        print(f"{row['orb']:<8} {row['verdict']:<8} {row['optimal_rr']:<6} {row['optimal_sl']:<6} {row['optimal_filter']:<25} {row['trades']:<8} {row['wr']:<8.1f} {row['avg_r']:<+10.3f} {row['total_r']:<+10.1f}")

    print()
    print("=" * 80)
    print("FILES SAVED:")
    print("=" * 80)
    print("  complete_orb_sweep_results.csv - All configurations tested")
    print("  canonical_session_parameters.csv - Locked optimal parameters")
    print()
    print("RULE: These are now CANONICAL. Sessions are not 'good' or 'bad' - they")
    print("      have optimal parameters. Only skip if negative at BEST config.")
    print()

if __name__ == "__main__":
    main()
