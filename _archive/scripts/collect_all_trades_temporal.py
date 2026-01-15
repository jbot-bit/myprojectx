"""
Collect all 49 trades from 3 states with dates for temporal analysis.
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MGC"

# State definitions
STATES = [
    {
        'name': 'State #1',
        'range_bucket': 'NORMAL',
        'disp_bucket': 'D_SMALL',
        'close_pos_bucket': 'HIGH',
        'impulse_bucket': 'MID'
    },
    {
        'name': 'State #2',
        'range_bucket': 'NORMAL',
        'disp_bucket': 'D_SMALL',
        'close_pos_bucket': 'MID',
        'impulse_bucket': 'MID'
    },
    {
        'name': 'State #3',
        'range_bucket': 'NORMAL',
        'disp_bucket': 'D_SMALL',
        'close_pos_bucket': 'MID',
        'impulse_bucket': 'LOW'
    }
]


def get_state_dates(con, state):
    """Get dates matching state definition."""
    query = """
        SELECT date_local
        FROM day_state_features
        WHERE orb_code = '1800'
            AND range_bucket = ?
            AND disp_bucket = ?
            AND close_pos_bucket = ?
            AND impulse_bucket = ?
        ORDER BY date_local
    """
    dates = con.execute(query, [
        state['range_bucket'],
        state['disp_bucket'],
        state['close_pos_bucket'],
        state['impulse_bucket']
    ]).df()
    return dates['date_local'].tolist()


def test_liquidity_reaction(con, date_local):
    """Test liquidity reaction on single date - simplified for speed."""

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    replay_start = datetime.combine(date_obj, datetime.min.time()).replace(hour=17, minute=45)
    replay_end = datetime.combine(date_obj, datetime.min.time()).replace(hour=19, minute=0)

    bars_1m = con.execute("""
        SELECT
            ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local,
            open, high, low, close, volume
        FROM bars_1m
        WHERE symbol = ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, replay_start, replay_end]).df()

    bars_5m = con.execute("""
        SELECT
            ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local,
            open, high, low, close, volume
        FROM bars_5m
        WHERE symbol = ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, replay_start, replay_end]).df()

    bars_1m['ts_local'] = bars_1m['ts_local'].astype(str)
    bars_5m['ts_local'] = bars_5m['ts_local'].astype(str)

    orb_data = con.execute("""
        SELECT orb_1800_high, orb_1800_low
        FROM daily_features
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars_1m.empty or bars_5m.empty or orb_data is None:
        return None

    orb_high, orb_low = orb_data
    if orb_high is None or orb_low is None:
        return None

    # Invalidation check
    initial_bars = bars_1m[bars_1m['ts_local'].str.contains('18:0[0-9]')]
    if not initial_bars.empty:
        initial_low = initial_bars['low'].min()
        initial_high = initial_bars['high'].max()
        initial_close = initial_bars.iloc[-1]['close']
        range_initial = initial_high - initial_low
        close_position = (initial_close - initial_low) / range_initial if range_initial > 0 else 0.5
        down_move = orb_high - initial_low
        if close_position < 0.3 and down_move > 5.0:
            return None

    # Get reaction low
    reaction_bars = bars_1m[bars_1m['ts_local'].str.contains('18:0[0-9]|18:1[0-4]')]
    reaction_low = reaction_bars['low'].min() if not reaction_bars.empty else orb_low

    # Entry trigger
    pre_orb_5m = bars_5m[bars_5m['ts_local'].str.contains('17:[4-5][0-9]|18:00')]
    range_high_5m = pre_orb_5m['high'].max() if not pre_orb_5m.empty else orb_high

    entry_window_5m = bars_5m[bars_5m['ts_local'].str.contains('18:10|18:15|18:20')]

    entry_price = None
    entry_bar_time = None

    for idx, bar in entry_window_5m.iterrows():
        if bar['close'] > range_high_5m:
            entry_price = bar['close']
            entry_bar_time = bar['ts_local']
            break

    if entry_price is None:
        return None

    # Stop and outcome
    stop_price = reaction_low - 0.5

    entry_idx = None
    for idx, bar in bars_1m.iterrows():
        if entry_bar_time.split()[1][:5] in str(bar['ts_local']):
            entry_idx = idx
            break

    if entry_idx is not None:
        outcome_bars = bars_1m.iloc[entry_idx:entry_idx+60]
        if not outcome_bars.empty:
            max_profit = outcome_bars['high'].max() - entry_price
            max_loss = entry_price - outcome_bars['low'].min()
            stop_hit = (outcome_bars['low'].min() <= stop_price)
            target_hit = (max_profit >= 2.5)
            risk = entry_price - stop_price if entry_price > stop_price else 1.0

            if stop_hit and target_hit:
                outcome = 'LOSS'
                r_multiple = -1.0
            elif stop_hit:
                outcome = 'LOSS'
                r_multiple = -max_loss / risk
            elif target_hit:
                outcome = 'WIN'
                r_multiple = max_profit / risk
            else:
                exit_price = outcome_bars.iloc[-1]['close']
                pnl = exit_price - entry_price
                outcome = 'TIMEOUT'
                r_multiple = pnl / risk

            return {
                'date': str(date_local).split()[0],
                'outcome': outcome,
                'r_multiple': r_multiple
            }

    return None


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*80)
    print("COLLECTING ALL TRADES FROM 3 STATES (WITH DATES)")
    print("="*80)
    print()

    all_trades = []

    for state in STATES:
        print(f"Processing {state['name']}...")

        state_dates = get_state_dates(con, state)

        for date in state_dates:
            result = test_liquidity_reaction(con, date)
            if result:
                result['state'] = state['name']
                all_trades.append(result)

    print()
    print(f"Total trades collected: {len(all_trades)}")
    print()

    if len(all_trades) == 0:
        print("[ERROR] No trades found")
        con.close()
        return

    # Create DataFrame and sort by date
    df = pd.DataFrame(all_trades)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    # Save
    df.to_csv('all_trades_with_dates.csv', index=False)
    print(f"Saved to: all_trades_with_dates.csv")
    print()

    # Now do temporal split
    print("="*80)
    print("TEMPORAL STABILITY TEST")
    print("="*80)
    print()

    n_trades = len(df)
    chunk_size = n_trades // 3

    # Split into 3 chunks
    chunk1 = df.iloc[:chunk_size]
    chunk2 = df.iloc[chunk_size:2*chunk_size]
    chunk3 = df.iloc[2*chunk_size:]

    print(f"Total trades: {n_trades}")
    print(f"Chunk size: ~{chunk_size} trades each")
    print()

    print(f"{'Chunk':<15} {'Dates':<30} {'Trades':<10} {'Avg R':<12} {'Total R':<12}")
    print("-"*80)

    chunks = [
        ('EARLY', chunk1),
        ('MIDDLE', chunk2),
        ('LATE', chunk3)
    ]

    results = []

    for name, chunk in chunks:
        date_range = f"{chunk['date'].min().strftime('%Y-%m-%d')} to {chunk['date'].max().strftime('%Y-%m-%d')}"
        n = len(chunk)
        avg_r = chunk['r_multiple'].mean()
        total_r = chunk['r_multiple'].sum()

        print(f"{name:<15} {date_range:<30} {n:<10} {avg_r:+.3f}R      {total_r:+.2f}R")

        results.append({
            'chunk': name,
            'n_trades': n,
            'avg_r': avg_r,
            'total_r': total_r,
            'positive': avg_r > 0
        })

    print()
    print("="*80)
    print("VERDICT")
    print("="*80)
    print()

    positive_chunks = sum(1 for r in results if r['positive'])

    print(f"Positive chunks: {positive_chunks}/3")
    print()

    if positive_chunks == 3:
        print("[VERY STRONG] All 3 chunks positive - edge is consistent across time")
        print()
        print("RECOMMENDATION: Edge is robust, proceed with confidence")
    elif positive_chunks == 2:
        # Check if the negative one is close to zero
        negative_chunks = [r for r in results if not r['positive']]
        if len(negative_chunks) > 0 and negative_chunks[0]['avg_r'] > -0.10:
            print("[ACCEPTABLE] 2 positive, 1 flat/small negative - edge is likely real")
            print()
            print("RECOMMENDATION: Edge is acceptable, proceed with caution")
        else:
            print("[MARGINAL] 2 positive, 1 significantly negative - edge may be time-dependent")
            print()
            print("RECOMMENDATION: Proceed with caution, monitor closely")
    elif positive_chunks == 1:
        print("[LIKELY NOISE] Only 1 positive chunk - edge may be spurious")
        print()
        print("RECOMMENDATION: Do NOT trade, likely curve-fitting or luck")
    else:
        print("[FAILURE] No positive chunks - system is broken")
        print()
        print("RECOMMENDATION: Abandon immediately")

    print()

    # Additional analysis: Check if any chunk is VERY negative
    most_negative = min(r['avg_r'] for r in results)
    most_positive = max(r['avg_r'] for r in results)

    print(f"Range: {most_negative:+.3f}R to {most_positive:+.3f}R")
    print()

    if most_negative < -0.20:
        print(f"[WARNING] One chunk shows significant negative ({most_negative:+.3f}R)")
        print("This suggests potential regime changes or overfitting")
        print()

    con.close()


if __name__ == '__main__':
    main()
