"""
VOLATILITY REGIME SEGMENTATION TEST

Segment backtest results by ATR (Average True Range) volatility regime:
- Low volatility tercile (bottom 33%)
- Medium volatility tercile (middle 33%)
- High volatility tercile (top 33%)

Tests if edge exists across ALL regimes or only in specific conditions.
Critical for deployment: edge must not be regime-dependent.
"""

import duckdb
import pandas as pd
import numpy as np

DB_PATH = "gold.db"
TICK_SIZE = 0.10
ATR_PERIOD = 14

def calculate_atr(con, date_local):
    """
    Calculate ATR(14) for a given date using 5m bars from previous 14 days.
    """
    query = f"""
    WITH recent_bars AS (
        SELECT
            DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') as date_local,
            high,
            low,
            close,
            LAG(close) OVER (ORDER BY ts_utc) as prev_close
        FROM bars_5m
        WHERE symbol = 'MGC'
            AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') <= '{date_local}'
            AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') > '{date_local}'::DATE - INTERVAL '20 days'
        ORDER BY ts_utc
    ),
    true_ranges AS (
        SELECT
            date_local,
            GREATEST(
                high - low,
                ABS(high - prev_close),
                ABS(low - prev_close)
            ) as tr
        FROM recent_bars
        WHERE prev_close IS NOT NULL
    )
    SELECT AVG(tr) as atr
    FROM (
        SELECT tr
        FROM true_ranges
        WHERE date_local <= '{date_local}'
        ORDER BY date_local DESC
        LIMIT {ATR_PERIOD * 288}  -- 14 days of 5m bars (~288 per day)
    )
    """

    result = con.execute(query).fetchone()
    return result[0] if result[0] else None

def simulate_orb_with_regime(con, orb_time, rr, sl_mode, filters=None):
    """
    Simulate ORB with worst-case execution and ATR regime tagging.
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

    # Calculate ATR for each date
    print(f"  Calculating ATR for {len(df_setups)} dates...")
    df_setups['atr'] = df_setups['date_local'].apply(lambda d: calculate_atr(con, d))
    df_setups = df_setups.dropna(subset=['atr'])

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
        atr = setup['atr']

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
                'atr': atr,
                'orb_range_ticks': setup['orb_range_ticks'],
                'risk_ticks': risk_ticks
            })

    return pd.DataFrame(results)

def main():
    print("=" * 80)
    print("VOLATILITY REGIME SEGMENTATION TEST")
    print("=" * 80)
    print()
    print("Segmenting results by ATR(14) terciles:")
    print("  Low volatility:    Bottom 33%")
    print("  Medium volatility: Middle 33%")
    print("  High volatility:   Top 33%")
    print()
    print("Critical test: Edge must exist across ALL regimes.")
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Use worst-case parameters
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
        rr = opt_row['optimal_rr']
        sl_mode = opt_row['optimal_sl']
        filter_name = opt_row['optimal_filter']

        print(f"Processing {orb} ORB...")

        if filter_name == 'MAX_STOP_100':
            filters = {'max_stop': 100}
        elif filter_name == 'MAX_STOP_100_TP_CAP_150':
            filters = {'max_stop': 100, 'asia_tp_cap': 150}
        else:
            filters = {}

        trades = simulate_orb_with_regime(con, orb, rr, sl_mode, filters)

        if len(trades) > 0:
            all_results.append(trades)

    con.close()

    if len(all_results) == 0:
        print("ERROR: No trades found")
        return

    all_trades = pd.concat(all_results, ignore_index=True)

    print()
    print(f"Total trades collected: {len(all_trades)}")
    print()

    # Segment by ATR terciles
    atr_terciles = all_trades['atr'].quantile([0.333, 0.667])

    low_vol = all_trades[all_trades['atr'] <= atr_terciles.iloc[0]]
    med_vol = all_trades[(all_trades['atr'] > atr_terciles.iloc[0]) & (all_trades['atr'] <= atr_terciles.iloc[1])]
    high_vol = all_trades[all_trades['atr'] > atr_terciles.iloc[1]]

    print("=" * 80)
    print("VOLATILITY REGIME RESULTS")
    print("=" * 80)
    print()

    # Summary by regime
    regimes = [
        ('LOW VOLATILITY', low_vol, atr_terciles.iloc[0]),
        ('MEDIUM VOLATILITY', med_vol, atr_terciles.iloc[1]),
        ('HIGH VOLATILITY', high_vol, None)
    ]

    regime_summary = []

    for regime_name, regime_df, threshold in regimes:
        if len(regime_df) == 0:
            continue

        trades_count = len(regime_df)
        wins = len(regime_df[regime_df['outcome'] == 'WIN'])
        wr = wins / trades_count * 100
        total_r = regime_df['r_multiple'].sum()
        avg_r = regime_df['r_multiple'].mean()
        avg_atr = regime_df['atr'].mean()

        regime_summary.append({
            'regime': regime_name,
            'trades': trades_count,
            'wr': wr,
            'avg_r': avg_r,
            'total_r': total_r,
            'avg_atr': avg_atr
        })

        print(f"{regime_name}:")
        print("-" * 80)
        print(f"  ATR threshold: {'<= ' + str(threshold) if threshold else '> ' + str(atr_terciles.iloc[1])}")
        print(f"  Avg ATR: {avg_atr:.2f}")
        print(f"  Trades: {trades_count}")
        print(f"  Win Rate: {wr:.1f}%")
        print(f"  Avg R: {avg_r:+.3f}R")
        print(f"  Total R: {total_r:+.1f}R")
        print()

    # Breakdown by ORB and regime
    print("=" * 80)
    print("PER-ORB REGIME BREAKDOWN")
    print("=" * 80)
    print()

    for orb in all_trades['orb_time'].unique():
        orb_trades = all_trades[all_trades['orb_time'] == orb]

        print(f"{orb} ORB:")
        print("-" * 80)

        for regime_name, regime_df, _ in regimes:
            regime_orb = orb_trades[orb_trades['atr'].isin(regime_df['atr'])]

            if len(regime_orb) == 0:
                continue

            avg_r = regime_orb['r_multiple'].mean()
            wr = len(regime_orb[regime_orb['outcome'] == 'WIN']) / len(regime_orb) * 100

            print(f"  {regime_name:20} {len(regime_orb):4} trades | {wr:5.1f}% WR | {avg_r:+.3f}R avg")

        print()

    # Save results
    all_trades.to_csv('volatility_regime_results.csv', index=False)

    regime_summary_df = pd.DataFrame(regime_summary)
    regime_summary_df.to_csv('regime_summary.csv', index=False)

    print("=" * 80)
    print("REGIME ROBUSTNESS VERDICT")
    print("=" * 80)
    print()

    all_positive = all([r['avg_r'] > 0 for r in regime_summary])

    if all_positive:
        print("✅ PASS: Edge exists across ALL volatility regimes")
        print()
        print("System is REGIME-ROBUST:")
        print("  - Low vol: Works")
        print("  - Med vol: Works")
        print("  - High vol: Works")
        print()
        print("Deployment is NOT regime-dependent.")
    else:
        print("⚠️ WARNING: Edge is regime-dependent")
        print()
        failing_regimes = [r['regime'] for r in regime_summary if r['avg_r'] <= 0]
        print(f"Failing regimes: {', '.join(failing_regimes)}")
        print()
        print("RISK: System may fail when market enters specific volatility conditions")
        print("RECOMMENDATION: Monitor ATR and reduce/stop trading in failing regimes")

    print()
    print("Files saved:")
    print("  volatility_regime_results.csv")
    print("  regime_summary.csv")
    print()

if __name__ == "__main__":
    main()
