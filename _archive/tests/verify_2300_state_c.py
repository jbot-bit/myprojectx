"""
VERIFY: 2300 State C potential edge

Delta: +0.521R (16 trades, 37.2% selectivity)

Must verify:
1. Temporal stability (3 chunks)
2. Sample size adequacy
3. Date-matched baseline comparison
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MGC"

STATE_C = {
    'range_bucket': 'NORMAL',
    'disp_bucket': 'D_SMALL',
    'close_pos_bucket': 'MID',
    'impulse_bucket': 'LOW'
}

def get_state_dates(con):
    """Get State C dates."""
    query = """
        SELECT date_local
        FROM day_state_features
        WHERE orb_code = '2300'
            AND range_bucket = ?
            AND disp_bucket = ?
            AND close_pos_bucket = ?
            AND impulse_bucket = ?
        ORDER BY date_local
    """
    dates = con.execute(query, [
        STATE_C['range_bucket'],
        STATE_C['disp_bucket'],
        STATE_C['close_pos_bucket'],
        STATE_C['impulse_bucket']
    ]).df()
    return dates['date_local'].tolist()


def test_liquidity_reaction(con, date_local):
    """Test reaction (same as before)."""
    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    test_start = datetime.combine(date_obj, datetime.min.time()).replace(hour=22, minute=45)
    test_end = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=0)

    bars_1m = con.execute("""
        SELECT ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local, open, high, low, close
        FROM bars_1m
        WHERE symbol = ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    bars_5m = con.execute("""
        SELECT ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local, open, high, low, close
        FROM bars_5m
        WHERE symbol = ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    orb_data = con.execute("""
        SELECT orb_2300_high, orb_2300_low
        FROM daily_features
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars_1m.empty or bars_5m.empty or orb_data is None:
        return None

    orb_high, orb_low = orb_data
    if orb_high is None or orb_low is None:
        return None

    bars_1m['ts_local'] = bars_1m['ts_local'].astype(str)
    bars_5m['ts_local'] = bars_5m['ts_local'].astype(str)

    # Invalidation
    initial_bars = bars_1m[bars_1m['ts_local'].str.contains('23:0[0-9]')]
    if not initial_bars.empty:
        initial_low = initial_bars['low'].min()
        initial_high = initial_bars['high'].max()
        initial_close = initial_bars.iloc[-1]['close']
        range_initial = initial_high - initial_low
        close_position = (initial_close - initial_low) / range_initial if range_initial > 0 else 0.5
        down_move = orb_high - initial_low
        if close_position < 0.3 and down_move > 5.0:
            return None

    # Reaction low
    reaction_bars = bars_1m[bars_1m['ts_local'].str.contains('23:0[0-9]|23:1[0-4]')]
    reaction_low = reaction_bars['low'].min() if not reaction_bars.empty else orb_low

    # Entry
    pre_orb_5m = bars_5m[bars_5m['ts_local'].str.contains('22:[4-5][0-9]|23:00')]
    range_high_5m = pre_orb_5m['high'].max() if not pre_orb_5m.empty else orb_high

    entry_window_5m = bars_5m[bars_5m['ts_local'].str.contains('23:10|23:15|23:20')]

    entry_price = None
    entry_bar_time = None

    for idx, bar in entry_window_5m.iterrows():
        if bar['close'] > range_high_5m:
            entry_price = bar['close']
            entry_bar_time = bar['ts_local']
            break

    if entry_price is None:
        return None

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
    print("VERIFYING: 2300 State C")
    print("="*80)
    print()

    state_dates = get_state_dates(con)
    print(f"State dates: {len(state_dates)}")
    print()

    # Collect all trades
    results = []
    for date in state_dates:
        result = test_liquidity_reaction(con, date)
        if result:
            results.append(result)

    df = pd.DataFrame(results)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    print(f"Reaction trades: {len(df)}")
    print(f"Selectivity: {len(df)}/{len(state_dates)} = {len(df)/len(state_dates)*100:.1f}%")
    print()

    if len(df) < 15:
        print(f"[INSUFFICIENT SAMPLE] Only {len(df)} trades")
        print("VERDICT: Cannot validate edge")
        con.close()
        return

    # Overall stats
    avg_r = df['r_multiple'].mean()
    total_r = df['r_multiple'].sum()

    print(f"Overall avg R: {avg_r:+.3f}R")
    print(f"Total R: {total_r:+.2f}R")
    print()

    # TEMPORAL STABILITY (CRITICAL TEST)
    print("="*80)
    print("TEMPORAL STABILITY TEST")
    print("="*80)
    print()

    n_trades = len(df)
    chunk_size = n_trades // 3

    chunk1 = df.iloc[:chunk_size]
    chunk2 = df.iloc[chunk_size:2*chunk_size]
    chunk3 = df.iloc[2*chunk_size:]

    print(f"{'Chunk':<15} {'Dates':<35} {'Trades':<10} {'Avg R':<12}")
    print("-"*80)

    chunks = [
        ('EARLY', chunk1),
        ('MIDDLE', chunk2),
        ('LATE', chunk3)
    ]

    positive_chunks = 0

    for name, chunk in chunks:
        date_range = f"{chunk['date'].min().strftime('%Y-%m-%d')} to {chunk['date'].max().strftime('%Y-%m-%d')}"
        n = len(chunk)
        avg_r_chunk = chunk['r_multiple'].mean()

        print(f"{name:<15} {date_range:<35} {n:<10} {avg_r_chunk:+.3f}R")

        if avg_r_chunk > 0:
            positive_chunks += 1

    print()
    print(f"Positive chunks: {positive_chunks}/3")
    print()

    # VERDICT
    print("="*80)
    print("FINAL VERDICT")
    print("="*80)
    print()

    if positive_chunks < 2:
        print(f"[DISPROVED] Temporal instability ({positive_chunks}/3 positive)")
        print("VERDICT: Edge is likely noise/luck")
        print()
    elif avg_r < 0.10:
        print(f"[WEAK] Avg R too low ({avg_r:+.3f}R)")
        print("VERDICT: Edge too thin to trade")
        print()
    elif len(df) < 20:
        print(f"[INCONCLUSIVE] Sample too small ({len(df)} trades)")
        print("VERDICT: Need more data")
        print()
    else:
        print(f"[EDGE EXISTS] 2300 State C shows {avg_r:+.3f}R avg")
        print(f"Temporal stability: {positive_chunks}/3 chunks positive")
        print(f"Sample: {len(df)} trades, {len(df)/len(state_dates)*100:.1f}% selectivity")
        print()
        print("Edge: Liquidity reaction on NORMAL + D_SMALL + MID + LOW state")

    print()

    # Save
    df.to_csv('2300_state_c_trades.csv', index=False)
    print("Results saved to: 2300_state_c_trades.csv")
    print()

    con.close()


if __name__ == '__main__':
    main()
