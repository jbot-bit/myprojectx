"""
Date-matched comparison for 1800 ORB State #1.

State: NORMAL + D_SMALL + HIGH + MID (28 days)
Expected: 71.4% UP-favored, +3.2 tick median tail skew

CRITICAL: Compare on SAME 28 dates:
  Method A: Liquidity Reaction approach
  Method B: Baseline Breakout approach
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MGC"

# State definition
STATE_FILTERS = {
    'orb_code': '1800',
    'range_bucket': 'NORMAL',
    'disp_bucket': 'D_SMALL',
    'close_pos_bucket': 'HIGH',
    'impulse_bucket': 'MID'
}

def get_state_dates(con):
    """Get the 28 dates matching state definition."""

    query = """
        SELECT date_local
        FROM day_state_features
        WHERE orb_code = ?
            AND range_bucket = ?
            AND disp_bucket = ?
            AND close_pos_bucket = ?
            AND impulse_bucket = ?
        ORDER BY date_local
    """

    dates = con.execute(query, [
        STATE_FILTERS['orb_code'],
        STATE_FILTERS['range_bucket'],
        STATE_FILTERS['disp_bucket'],
        STATE_FILTERS['close_pos_bucket'],
        STATE_FILTERS['impulse_bucket']
    ]).df()

    return dates['date_local'].tolist()


def test_liquidity_reaction(con, date_local):
    """Test liquidity reaction approach on single date."""

    # Convert to datetime
    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    # ORB window: 18:00-18:05 same day
    # Replay window: 17:45-19:00 (15min before ORB + 60min after)
    replay_start = datetime.combine(date_obj, datetime.min.time()).replace(hour=17, minute=45)
    replay_end = datetime.combine(date_obj, datetime.min.time()).replace(hour=19, minute=0)

    # Get bars
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

    # Convert ts_local to string for filtering
    bars_1m['ts_local'] = bars_1m['ts_local'].astype(str)
    bars_5m['ts_local'] = bars_5m['ts_local'].astype(str)

    # Get ORB boundaries
    orb_data = con.execute("""
        SELECT orb_1800_high, orb_1800_low, orb_1800_size
        FROM daily_features
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars_1m.empty or bars_5m.empty or orb_data is None:
        return None

    orb_high, orb_low, orb_size = orb_data

    if orb_high is None or orb_low is None:
        return None

    result = {
        'date': str(date_local),
        'method': 'LIQUIDITY_REACTION',
        'orb_high': orb_high,
        'orb_low': orb_low,
        'orb_size': orb_size,
        'invalidation': 'NO',
        'reaction_pattern': 'NONE',
        'entry_triggered': 'NO',
        'entry_price': None,
        'stop_price': None,
        'outcome': None,
        'r_multiple': None
    }

    # STEP 1: INVALIDATION CHECK (18:00-18:10)
    initial_bars = bars_1m[bars_1m['ts_local'].str.contains('18:0[0-9]')]

    if not initial_bars.empty:
        initial_low = initial_bars['low'].min()
        initial_high = initial_bars['high'].max()
        initial_close = initial_bars.iloc[-1]['close']

        range_initial = initial_high - initial_low
        close_position = (initial_close - initial_low) / range_initial if range_initial > 0 else 0.5
        down_move = orb_high - initial_low

        # Strong DOWN drive = close in bottom 30% AND down move > 5 ticks
        if close_position < 0.3 and down_move > 5.0:
            result['invalidation'] = 'YES'
            return result

    # STEP 2: REACTION PATTERN (18:00-18:15)
    reaction_bars = bars_1m[bars_1m['ts_local'].str.contains('18:0[0-9]|18:1[0-4]')]

    if not reaction_bars.empty:
        # Calculate wick ratios
        reaction_bars = reaction_bars.copy()
        reaction_bars['body'] = abs(reaction_bars['close'] - reaction_bars['open'])
        reaction_bars['upper_wick'] = reaction_bars['high'] - reaction_bars[['open', 'close']].max(axis=1)
        reaction_bars['lower_wick'] = reaction_bars[['open', 'close']].min(axis=1) - reaction_bars['low']
        reaction_bars['total_wick'] = reaction_bars['upper_wick'] + reaction_bars['lower_wick']
        reaction_bars['bar_range'] = reaction_bars['high'] - reaction_bars['low']
        reaction_bars['wick_pct'] = reaction_bars['total_wick'] / reaction_bars['bar_range']

        avg_wick_pct = reaction_bars['wick_pct'].mean()
        reaction_high = reaction_bars['high'].max()
        reaction_low = reaction_bars['low'].min()

        # Pattern classification
        if avg_wick_pct > 0.6:
            result['reaction_pattern'] = 'A'  # Absorption
        elif reaction_low <= orb_low + 1.0 and reaction_high >= orb_high - 2.0:
            result['reaction_pattern'] = 'B'  # Fake Downside
        else:
            late_bars = bars_1m[bars_1m['ts_local'].str.contains('18:1[5-9]|18:2[0-4]')]
            if not late_bars.empty:
                late_high = late_bars['high'].max()
                if late_high > reaction_high + 3.0:
                    result['reaction_pattern'] = 'C'  # Delayed Lift
    else:
        reaction_low = orb_low

    # STEP 3: ENTRY TRIGGER (5m close above 5m range high)
    pre_orb_5m = bars_5m[bars_5m['ts_local'].str.contains('17:[4-5][0-9]|18:00')]
    if not pre_orb_5m.empty:
        range_high_5m = pre_orb_5m['high'].max()
    else:
        range_high_5m = orb_high

    entry_window_5m = bars_5m[bars_5m['ts_local'].str.contains('18:10|18:15|18:20')]

    entry_price = None
    entry_bar_time = None

    for idx, bar in entry_window_5m.iterrows():
        if bar['close'] > range_high_5m:
            entry_price = bar['close']
            entry_bar_time = bar['ts_local']
            result['entry_triggered'] = 'YES'
            result['entry_price'] = entry_price
            break

    if result['entry_triggered'] == 'NO':
        return result

    # STEP 4: STOP PLACEMENT
    stop_price = reaction_low - 0.5  # 5 ticks below reaction low
    result['stop_price'] = stop_price

    # STEP 5: OUTCOME (60 minutes from entry)
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
            target_hit = (max_profit >= 2.5)  # +25 ticks target

            risk = entry_price - stop_price
            if risk <= 0:
                risk = 1.0

            if stop_hit and target_hit:
                result['outcome'] = 'LOSS'
                result['r_multiple'] = -1.0
            elif stop_hit:
                result['outcome'] = 'LOSS'
                result['r_multiple'] = -max_loss / risk
            elif target_hit:
                result['outcome'] = 'WIN'
                result['r_multiple'] = max_profit / risk
            else:
                exit_price = outcome_bars.iloc[-1]['close']
                pnl = exit_price - entry_price
                result['outcome'] = 'TIMEOUT'
                result['r_multiple'] = pnl / risk

    return result


def test_baseline_breakout(con, date_local):
    """Test baseline breakout approach on single date."""

    # Query from existing backtest results
    result = con.execute("""
        SELECT
            orb,
            date_local,
            rr,
            outcome,
            r_multiple,
            entry_price,
            stop_price,
            target_price
        FROM orb_trades_1m_exec_nofilters
        WHERE orb = '1800'
            AND date_local = ?
            AND close_confirmations = 1
            AND rr = 1.5
        LIMIT 1
    """, [date_local]).fetchone()

    if result is None:
        return None

    orb, date, rr, outcome, r_mult, entry, stop, target = result

    return {
        'date': str(date),
        'method': 'BASELINE_BREAKOUT',
        'entry_price': entry,
        'stop_price': stop,
        'target_price': target,
        'outcome': outcome,
        'r_multiple': r_mult
    }


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*80)
    print("DATE-MATCHED COMPARISON: 1800 ORB STATE #1")
    print("="*80)
    print()
    print("State: NORMAL + D_SMALL + HIGH + MID")
    print("Expected: 71.4% UP-favored, +3.2 tick median tail skew")
    print()

    # Get state dates
    print("STEP 1: Get state dates")
    print("-"*80)

    state_dates = get_state_dates(con)
    print(f"State dates found: {len(state_dates)}")
    print()

    if len(state_dates) == 0:
        print("[ERROR] No dates found for state")
        con.close()
        return

    # Test both methods on same dates
    print("STEP 2: Test both methods on same dates")
    print("-"*80)
    print()

    results_reaction = []
    results_baseline = []

    for date in state_dates:
        print(f"Testing {date}...", end=" ")

        # Method A: Liquidity Reaction
        result_a = test_liquidity_reaction(con, date)
        if result_a:
            results_reaction.append(result_a)

        # Method B: Baseline Breakout
        result_b = test_baseline_breakout(con, date)
        if result_b:
            results_baseline.append(result_b)

        status_a = f"R={result_a['outcome']}" if result_a and result_a['outcome'] else "NO_ENTRY"
        status_b = f"B={result_b['outcome']}" if result_b else "NO_DATA"
        print(f"[{status_a} | {status_b}]")

    print()

    # Analyze results
    print("="*80)
    print("RESULTS: METHOD A - LIQUIDITY REACTION")
    print("="*80)
    print()

    df_reaction = pd.DataFrame(results_reaction)

    entries_reaction = df_reaction[df_reaction['entry_triggered'] == 'YES']
    print(f"Dates analyzed: {len(df_reaction)}")
    print(f"Entry triggers: {len(entries_reaction)} ({len(entries_reaction)/len(df_reaction)*100:.1f}%)")

    if len(entries_reaction) > 0:
        outcomes = entries_reaction['outcome'].value_counts()
        wins = outcomes.get('WIN', 0)
        losses = outcomes.get('LOSS', 0)
        timeouts = outcomes.get('TIMEOUT', 0)

        win_rate = wins / len(entries_reaction) * 100

        r_values = entries_reaction[entries_reaction['r_multiple'].notna()]['r_multiple']
        avg_r = r_values.mean()

        print(f"Outcomes: WIN={wins}, LOSS={losses}, TIMEOUT={timeouts}")
        print(f"Win rate: {win_rate:.1f}%")
        print(f"Avg R: {avg_r:+.3f}R")
        print(f"Total R: {r_values.sum():+.2f}R")
    else:
        print("No entries triggered")
        avg_r = 0.0

    print()

    # Baseline results
    print("="*80)
    print("RESULTS: METHOD B - BASELINE BREAKOUT (SAME DATES)")
    print("="*80)
    print()

    df_baseline = pd.DataFrame(results_baseline)

    print(f"Dates analyzed: {len(df_baseline)}")
    print(f"Trades: {len(df_baseline)}")

    if len(df_baseline) > 0:
        outcomes_b = df_baseline['outcome'].value_counts()
        wins_b = outcomes_b.get('WIN', 0)
        losses_b = outcomes_b.get('LOSS', 0)

        win_rate_b = wins_b / len(df_baseline) * 100

        avg_r_b = df_baseline['r_multiple'].mean()

        print(f"Outcomes: WIN={wins_b}, LOSS={losses_b}")
        print(f"Win rate: {win_rate_b:.1f}%")
        print(f"Avg R: {avg_r_b:+.3f}R")
        print(f"Total R: {df_baseline['r_multiple'].sum():+.2f}R")
    else:
        print("No baseline data")
        avg_r_b = 0.0

    print()

    # COMPARISON
    print("="*80)
    print("DATE-MATCHED COMPARISON")
    print("="*80)
    print()

    print(f"{'Method':<25} {'Trades':<10} {'Avg R':<12} {'Total R':<12}")
    print("-"*80)
    print(f"{'Liquidity Reaction':<25} {len(entries_reaction) if len(entries_reaction) > 0 else 0:<10} {avg_r:+.3f}R      {r_values.sum() if len(entries_reaction) > 0 else 0:+.2f}R")
    print(f"{'Baseline Breakout':<25} {len(df_baseline):<10} {avg_r_b:+.3f}R      {df_baseline['r_multiple'].sum() if len(df_baseline) > 0 else 0:+.2f}R")
    print()

    delta_r = avg_r - avg_r_b

    print(f"Difference (Reaction - Baseline): {delta_r:+.3f}R per trade")
    print()

    # VERDICT
    print("="*80)
    print("VERDICT")
    print("="*80)
    print()

    if delta_r > 0.10:
        print(f"[REACTION WINS] Liquidity reaction outperforms by {delta_r:+.3f}R")
        print()
        print("RECOMMENDATION: Use Liquidity Reaction approach for 1800 State #1")
    elif delta_r > 0.03:
        print(f"[MARGINAL] Liquidity reaction slightly better by {delta_r:+.3f}R")
        print()
        print("RECOMMENDATION: Either approach viable, prefer simpler baseline")
    elif delta_r > -0.03:
        print(f"[EQUIVALENT] Methods perform similarly (delta: {delta_r:+.3f}R)")
        print()
        print("RECOMMENDATION: Use simpler baseline breakout")
    else:
        print(f"[BASELINE WINS] Baseline outperforms by {abs(delta_r):+.3f}R")
        print()
        print("RECOMMENDATION: Use baseline breakout, abandon reaction approach")

    print()

    # Save results
    df_reaction.to_csv('1800_state1_reaction_results.csv', index=False)
    df_baseline.to_csv('1800_state1_baseline_results.csv', index=False)

    print("Results saved to:")
    print("  1800_state1_reaction_results.csv")
    print("  1800_state1_baseline_results.csv")
    print()

    con.close()


if __name__ == '__main__':
    main()
