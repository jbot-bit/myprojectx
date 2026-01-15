"""
PROP-SAFE ASIA ORB BACKTEST

Tests Asia ORBs under prop firm constraints:
1. MAX 1 TRADE PER DAY (no clustered losses)
2. WORST-CASE same-bar resolution (if both TP/SL hit in bar -> LOSS)
3. Track max losing streak, max drawdown, daily loss limits

Selection modes:
- BEST_EDGE: Always trade 10:00 (highest historical edge)
- FIRST_BREAK: Take first ORB that breaks (09:00, then 10:00, then 11:00)
- HIGHEST_RR: Take ORB with best RR on that day (based on range)
- RANGE_FILTERED: Only trade when Asia range 40-100 ticks
"""

import duckdb
import pandas as pd
from datetime import datetime

DB_PATH = "gold.db"
TICK_SIZE = 0.10

def simulate_trade_worst_case(bars, entry, stop, target, direction):
    """
    Simulate trade with WORST-CASE same-bar resolution.
    If both TP and SL reachable in same bar, assume LOSS.

    Returns: ('WIN', R) or ('LOSS', -1.0) or ('NO_DECISION', 0.0)
    """
    for idx, bar in bars.iterrows():
        if direction == 'UP':
            # Check if BOTH are reachable in this bar
            stop_hit = bar['low'] <= stop
            target_hit = bar['high'] >= target

            if stop_hit and target_hit:
                # WORST CASE: Assume stop hit first
                return ('LOSS', -1.0)
            elif stop_hit:
                return ('LOSS', -1.0)
            elif target_hit:
                return ('WIN', target, stop)  # Return actual prices for R calc
        else:  # DOWN
            stop_hit = bar['high'] >= stop
            target_hit = bar['low'] <= target

            if stop_hit and target_hit:
                # WORST CASE: Assume stop hit first
                return ('LOSS', -1.0)
            elif stop_hit:
                return ('LOSS', -1.0)
            elif target_hit:
                return ('WIN', target, stop)

    return ('NO_DECISION', 0.0)

def simulate_orb_trade(con, date, orb_time, rr, filters=None):
    """
    Simulate ONE ORB trade for a given day with worst-case resolution.
    Returns: dict with outcome or None if no trade
    """
    if filters is None:
        filters = {}

    # Get ORB for this day
    query = f"""
    SELECT
        date_local,
        orb_{orb_time}_high as orb_high,
        orb_{orb_time}_low as orb_low,
        orb_{orb_time}_break_dir as break_dir,
        (orb_{orb_time}_high - orb_{orb_time}_low) / {TICK_SIZE} as orb_range_ticks
    FROM daily_features_v2
    WHERE instrument = 'MGC'
        AND date_local = '{date}'
        AND orb_{orb_time}_break_dir IS NOT NULL
    """

    result = con.execute(query).fetchone()
    if not result:
        return None

    date_local, orb_high, orb_low, break_dir, orb_range_ticks = result

    # Apply filters
    if 'max_stop' in filters and orb_range_ticks > filters['max_stop']:
        return None
    if 'min_stop' in filters and orb_range_ticks < filters['min_stop']:
        return None

    # Calculate entry/stop/target
    if break_dir == 'UP':
        entry = orb_high
        stop = orb_low  # FULL SL
        risk = entry - stop
        target = entry + rr * risk
    else:  # DOWN
        entry = orb_low
        stop = orb_high  # FULL SL
        risk = stop - entry
        target = entry - rr * risk

    risk_ticks = risk / TICK_SIZE

    # Apply TP_CAP filter if present
    if 'asia_tp_cap' in filters:
        max_target_ticks = filters['asia_tp_cap']
        target_ticks = abs(target - entry) / TICK_SIZE
        if target_ticks > max_target_ticks:
            return None

    # Get bars for simulation
    hour_map = {'0900': 9, '1000': 10, '1100': 11}
    orb_hour = hour_map[orb_time]

    query_bars = f"""
    SELECT
        ts_utc,
        high,
        low,
        close
    FROM bars_5m
    WHERE symbol = 'MGC'
        AND DATE(ts_utc AT TIME ZONE 'Australia/Brisbane') = '{date}'
        AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') >= {orb_hour}
        AND EXTRACT(HOUR FROM ts_utc AT TIME ZONE 'Australia/Brisbane') < 18
    ORDER BY ts_utc
    """

    bars = con.execute(query_bars).df()
    if len(bars) == 0:
        return None

    # Find entry bar (first close outside ORB)
    entry_bar_idx = None
    for idx, bar in bars.iterrows():
        if break_dir == 'UP' and bar['close'] > orb_high:
            entry_bar_idx = idx
            break
        elif break_dir == 'DOWN' and bar['close'] < orb_low:
            entry_bar_idx = idx
            break

    if entry_bar_idx is None:
        return None

    # Simulate from entry with WORST-CASE resolution
    entry_bars = bars.loc[entry_bar_idx:].copy()
    outcome_data = simulate_trade_worst_case(entry_bars, entry, stop, target, break_dir)

    if outcome_data[0] == 'NO_DECISION':
        return None

    outcome = outcome_data[0]
    if outcome == 'WIN':
        r_multiple = rr
    else:
        r_multiple = -1.0

    return {
        'date_local': date,
        'orb_time': orb_time,
        'direction': break_dir,
        'outcome': outcome,
        'r_multiple': r_multiple,
        'rr': rr,
        'orb_range_ticks': orb_range_ticks,
        'risk_ticks': risk_ticks
    }

def backtest_prop_safe(con, mode, rr_config, filters=None):
    """
    Backtest with MAX 1 TRADE PER DAY.

    mode: 'BEST_EDGE' (10:00 only), 'FIRST_BREAK', 'ONLY_0900', 'ONLY_1100'
    rr_config: dict mapping orb_time -> rr value
    """
    # Get all dates
    dates = con.execute("""
        SELECT DISTINCT date_local
        FROM daily_features_v2
        WHERE instrument = 'MGC'
        ORDER BY date_local
    """).df()['date_local'].tolist()

    trades = []
    daily_results = []

    for date in dates:
        date_str = str(date)
        trade_taken = None

        if mode == 'BEST_EDGE':
            # Always try 10:00 (historically best)
            trade_taken = simulate_orb_trade(con, date_str, '1000', rr_config['1000'], filters)

        elif mode == 'FIRST_BREAK':
            # Take first ORB that breaks
            for orb in ['0900', '1000', '1100']:
                trade_taken = simulate_orb_trade(con, date_str, orb, rr_config[orb], filters)
                if trade_taken:
                    break

        elif mode == 'ONLY_0900':
            trade_taken = simulate_orb_trade(con, date_str, '0900', rr_config['0900'], filters)

        elif mode == 'ONLY_1100':
            trade_taken = simulate_orb_trade(con, date_str, '1100', rr_config['1100'], filters)

        # Record daily result
        if trade_taken:
            trades.append(trade_taken)
            daily_results.append({
                'date': date_str,
                'r_pnl': trade_taken['r_multiple']
            })
        else:
            daily_results.append({
                'date': date_str,
                'r_pnl': 0.0
            })

    return pd.DataFrame(trades), pd.DataFrame(daily_results)

def calculate_risk_metrics(trades_df, daily_df):
    """
    Calculate prop-critical risk metrics.
    """
    if len(trades_df) == 0:
        return None

    # Basic stats
    total_trades = len(trades_df)
    wins = len(trades_df[trades_df['outcome'] == 'WIN'])
    losses = len(trades_df[trades_df['outcome'] == 'LOSS'])
    wr = wins / total_trades * 100

    total_r = trades_df['r_multiple'].sum()
    avg_r = trades_df['r_multiple'].mean()

    # Max losing streak
    max_losing_streak = 0
    current_streak = 0
    for outcome in trades_df['outcome']:
        if outcome == 'LOSS':
            current_streak += 1
            max_losing_streak = max(max_losing_streak, current_streak)
        else:
            current_streak = 0

    # Max intraday loss (should be -1R with our 1 trade/day limit)
    max_daily_loss = daily_df['r_pnl'].min()

    # Drawdown analysis
    cumulative_r = daily_df['r_pnl'].cumsum()
    running_max = cumulative_r.cummax()
    drawdown = cumulative_r - running_max
    max_drawdown = drawdown.min()

    # Worst 5 losing streaks
    streaks = []
    current_streak_r = 0
    for r in trades_df['r_multiple']:
        if r < 0:
            current_streak_r += r
        else:
            if current_streak_r < 0:
                streaks.append(current_streak_r)
            current_streak_r = 0
    if current_streak_r < 0:
        streaks.append(current_streak_r)
    streaks.sort()

    return {
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'win_rate': wr,
        'total_r': total_r,
        'avg_r': avg_r,
        'max_losing_streak': max_losing_streak,
        'max_daily_loss_r': max_daily_loss,
        'max_drawdown_r': max_drawdown,
        'worst_5_streaks': streaks[:5]
    }

def main():
    print("=" * 80)
    print("PROP-SAFE ASIA ORB BACKTEST")
    print("=" * 80)
    print()
    print("Constraints:")
    print("- MAX 1 TRADE PER DAY (no clustered losses)")
    print("- WORST-CASE same-bar resolution (both TP/SL hit -> assume LOSS)")
    print("- Full risk metrics (losing streaks, max DD, daily loss)")
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Check date range
    date_range = con.execute("""
        SELECT MIN(date_local), MAX(date_local)
        FROM daily_features_v2
    """).fetchone()
    print(f"Database date range: {date_range[0]} to {date_range[1]}")
    print()

    # Filters (from previous analysis)
    filters = {
        'max_stop': 100,
        'asia_tp_cap': 150
    }

    # Test configurations
    configs = [
        {
            'name': 'BEST_EDGE (10:00 only, RR 2.5)',
            'mode': 'BEST_EDGE',
            'rr_config': {'0900': 1.0, '1000': 2.5, '1100': 1.0}
        },
        {
            'name': 'FIRST_BREAK (09:00 -> 10:00 -> 11:00, optimal RRs)',
            'mode': 'FIRST_BREAK',
            'rr_config': {'0900': 1.0, '1000': 2.5, '1100': 1.0}
        },
        {
            'name': 'ONLY_0900 (RR 1.0)',
            'mode': 'ONLY_0900',
            'rr_config': {'0900': 1.0, '1000': 2.5, '1100': 1.0}
        },
        {
            'name': 'ONLY_1100 (RR 1.0)',
            'mode': 'ONLY_1100',
            'rr_config': {'0900': 1.0, '1000': 2.5, '1100': 1.0}
        }
    ]

    all_results = []

    for config in configs:
        print("=" * 80)
        print(f"Testing: {config['name']}")
        print("-" * 80)

        trades_df, daily_df = backtest_prop_safe(
            con,
            config['mode'],
            config['rr_config'],
            filters
        )

        metrics = calculate_risk_metrics(trades_df, daily_df)

        if metrics:
            print(f"Total Trades: {metrics['total_trades']}")
            print(f"Win Rate: {metrics['win_rate']:.1f}%")
            print(f"Total R: {metrics['total_r']:+.1f}")
            print(f"Avg R per Trade: {metrics['avg_r']:+.3f}")
            print()
            print("PROP-CRITICAL METRICS:")
            print(f"  Max Losing Streak: {metrics['max_losing_streak']} trades")
            print(f"  Max Daily Loss: {metrics['max_daily_loss_r']:.1f}R")
            print(f"  Max Drawdown: {metrics['max_drawdown_r']:.1f}R")
            print(f"  Worst 5 Losing Streaks (R): {[f'{x:.1f}' for x in metrics['worst_5_streaks']]}")
            print()

            # Prop safety assessment
            print("PROP SAFETY ASSESSMENT:")
            if metrics['max_daily_loss_r'] >= -1.0:
                print("  [PASS] Max daily loss: -1R (single trade limit enforced)")
            else:
                print(f"  [FAIL] Max daily loss: {metrics['max_daily_loss_r']:.1f}R (should be -1R)")

            if metrics['max_losing_streak'] <= 8:
                print(f"  [GOOD] Max losing streak: {metrics['max_losing_streak']} (manageable)")
            elif metrics['max_losing_streak'] <= 12:
                print(f"  [CAUTION] Max losing streak: {metrics['max_losing_streak']} (high)")
            else:
                print(f"  [WARNING] Max losing streak: {metrics['max_losing_streak']} (very high)")

            if metrics['max_drawdown_r'] >= -20:
                print(f"  [GOOD] Max drawdown: {metrics['max_drawdown_r']:.1f}R (recoverable)")
            elif metrics['max_drawdown_r'] >= -30:
                print(f"  [CAUTION] Max drawdown: {metrics['max_drawdown_r']:.1f}R (significant)")
            else:
                print(f"  [WARNING] Max drawdown: {metrics['max_drawdown_r']:.1f}R (severe)")

            print()

            all_results.append({
                'config': config['name'],
                'mode': config['mode'],
                **metrics
            })
        else:
            print("No trades executed")
            print()

    con.close()

    # Summary comparison
    print("=" * 80)
    print("SUMMARY: PROP-SAFE ASIA MODES")
    print("=" * 80)
    print()

    results_df = pd.DataFrame(all_results)

    print("Comparison Table:")
    print()
    print(f"{'Mode':<45} {'Trades':<8} {'WR%':<8} {'Avg R':<10} {'Max Streak':<12} {'Max DD':<10}")
    print("-" * 100)

    for _, row in results_df.iterrows():
        print(f"{row['config']:<45} {row['total_trades']:<8} {row['win_rate']:<8.1f} {row['avg_r']:<+10.3f} {row['max_losing_streak']:<12} {row['max_drawdown_r']:<+10.1f}")

    print()
    print("=" * 80)
    print("RECOMMENDATION:")
    print("=" * 80)
    print()

    # Find best by avg R
    best = results_df.loc[results_df['avg_r'].idxmax()]

    print(f"Best Mode: {best['config']}")
    print(f"  Avg R: {best['avg_r']:+.3f}")
    print(f"  Win Rate: {best['win_rate']:.1f}%")
    print(f"  Max Losing Streak: {best['max_losing_streak']} trades")
    print(f"  Max Drawdown: {best['max_drawdown_r']:.1f}R")
    print()

    if best['max_losing_streak'] <= 8 and best['max_drawdown_r'] >= -20:
        print("[PROP-SAFE] This configuration is suitable for prop accounts.")
    else:
        print("[CAUTION] Review losing streaks and drawdown against your prop firm's limits.")

    print()
    print("Save results:")
    results_df.to_csv('asia_prop_safe_results.csv', index=False)
    print("  asia_prop_safe_results.csv")
    print()

if __name__ == "__main__":
    main()
