"""
PHASE 2 — PROPER TEST: 2300 ORB

Using SAME research framework as 1800:
1. State filtering (pre-ORB only)
2. Liquidity reaction patterns
3. <50% selectivity
4. Date-matched comparison

STRICT RULES:
- Use ONLY existing day_state_features fields
- Pre-ORB information only
- 1m execution, worst-case resolution
- Report failures honestly
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MGC"
ORB_CODE = "2300"

def get_state_dates(con):
    """
    Find 2300 states using ONLY pre-ORB information.

    Looking for states with potential UP asymmetry (like 1800).
    Use existing day_state_features for 2300 ORB.
    """

    # Query existing states for 2300
    query = """
        SELECT
            date_local,
            range_bucket,
            disp_bucket,
            close_pos_bucket,
            impulse_bucket
        FROM day_state_features
        WHERE orb_code = '2300'
            AND range_bucket IS NOT NULL
            AND disp_bucket IS NOT NULL
            AND close_pos_bucket IS NOT NULL
            AND impulse_bucket IS NOT NULL
    """

    df = con.execute(query).df()

    print(f"Total 2300 dates with state data: {len(df)}")
    print()

    # Test common patterns (same as 1800)
    test_states = [
        {
            'name': 'State A',
            'range_bucket': 'NORMAL',
            'disp_bucket': 'D_SMALL',
            'close_pos_bucket': 'HIGH',
            'impulse_bucket': 'MID'
        },
        {
            'name': 'State B',
            'range_bucket': 'NORMAL',
            'disp_bucket': 'D_SMALL',
            'close_pos_bucket': 'MID',
            'impulse_bucket': 'MID'
        },
        {
            'name': 'State C',
            'range_bucket': 'NORMAL',
            'disp_bucket': 'D_SMALL',
            'close_pos_bucket': 'MID',
            'impulse_bucket': 'LOW'
        }
    ]

    state_results = []

    for state in test_states:
        mask = (
            (df['range_bucket'] == state['range_bucket']) &
            (df['disp_bucket'] == state['disp_bucket']) &
            (df['close_pos_bucket'] == state['close_pos_bucket']) &
            (df['impulse_bucket'] == state['impulse_bucket'])
        )

        dates = df[mask]['date_local'].tolist()

        if len(dates) > 0:
            state_results.append({
                'state': state,
                'dates': dates,
                'n_dates': len(dates),
                'frequency': len(dates) / len(df) * 100
            })

            print(f"{state['name']}: {len(dates)} dates ({len(dates)/len(df)*100:.1f}%)")

    return state_results


def test_liquidity_reaction(con, date_local):
    """
    Test liquidity reaction on single date.
    SAME logic as 1800: invalidation + reaction + 5m reclaim entry.
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    # 2300 ORB: 23:00-23:05 same day
    # Test window: 22:45-00:00 (15min before + 60min after)
    test_start = datetime.combine(date_obj, datetime.min.time()).replace(hour=22, minute=45)
    test_end = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=0)

    bars_1m = con.execute("""
        SELECT
            ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local,
            open, high, low, close
        FROM bars_1m
        WHERE symbol = ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    bars_5m = con.execute("""
        SELECT
            ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local,
            open, high, low, close
        FROM bars_5m
        WHERE symbol = ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
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

    # Invalidation check (23:00-23:10)
    initial_bars = bars_1m[bars_1m['ts_local'].str.contains('23:0[0-9]')]
    if not initial_bars.empty:
        initial_low = initial_bars['low'].min()
        initial_high = initial_bars['high'].max()
        initial_close = initial_bars.iloc[-1]['close']
        range_initial = initial_high - initial_low
        close_position = (initial_close - initial_low) / range_initial if range_initial > 0 else 0.5
        down_move = orb_high - initial_low
        if close_position < 0.3 and down_move > 5.0:
            return None  # Invalidated

    # Get reaction low
    reaction_bars = bars_1m[bars_1m['ts_local'].str.contains('23:0[0-9]|23:1[0-4]')]
    reaction_low = reaction_bars['low'].min() if not reaction_bars.empty else orb_low

    # Entry trigger: 5m close above 5m range high
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
        return None  # No entry

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


def test_baseline_breakout(con, date_local):
    """Get baseline breakout result for same date."""
    result = con.execute("""
        SELECT outcome, r_multiple
        FROM orb_trades_1m_exec_nofilters
        WHERE orb = '2300'
            AND date_local = ?
            AND close_confirmations = 1
            AND rr = 1.5
        LIMIT 1
    """, [date_local]).fetchone()

    if result is None:
        return None

    outcome, r_mult = result
    return {
        'date': str(date_local).split()[0],
        'outcome': outcome,
        'r_multiple': r_mult
    }


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*80)
    print("PHASE 2 — PROPER TEST: 2300 ORB")
    print("="*80)
    print()
    print("Using SAME framework as 1800:")
    print("1. State filtering (pre-ORB)")
    print("2. Liquidity reaction patterns")
    print("3. <50% selectivity requirement")
    print("4. Date-matched comparison")
    print()

    # Get states
    state_results = get_state_dates(con)
    print()

    if len(state_results) == 0:
        print("[NO STATES FOUND] Cannot proceed")
        con.close()
        return

    # Test each state
    for state_info in state_results:
        print("="*80)
        print(f"TESTING: {state_info['state']['name']}")
        print("="*80)
        print()
        print(f"Dates: {state_info['n_dates']} ({state_info['frequency']:.1f}%)")
        print()

        # Test reaction
        results_reaction = []
        results_baseline = []

        for date in state_info['dates']:
            result_r = test_liquidity_reaction(con, date)
            if result_r:
                results_reaction.append(result_r)

            result_b = test_baseline_breakout(con, date)
            if result_b:
                results_baseline.append(result_b)

        # Check selectivity
        selectivity = len(results_reaction) / state_info['n_dates'] * 100 if state_info['n_dates'] > 0 else 0

        print(f"Reaction entries: {len(results_reaction)}/{state_info['n_dates']} ({selectivity:.1f}%)")
        print()

        if selectivity >= 50:
            print(f"[FAILED] Selectivity too high ({selectivity:.1f}% >= 50%)")
            print("VERDICT: NO EDGE (not selective enough)")
            print()
            continue

        if len(results_reaction) == 0:
            print("[FAILED] No reaction trades")
            print("VERDICT: NO EDGE")
            print()
            continue

        # Results
        df_reaction = pd.DataFrame(results_reaction)
        df_baseline = pd.DataFrame(results_baseline)

        avg_r_reaction = df_reaction['r_multiple'].mean()
        avg_r_baseline = df_baseline['r_multiple'].mean() if len(df_baseline) > 0 else 0

        delta = avg_r_reaction - avg_r_baseline

        print(f"Reaction avg R: {avg_r_reaction:+.3f}R")
        print(f"Baseline avg R: {avg_r_baseline:+.3f}R (same dates)")
        print(f"Delta: {delta:+.3f}R")
        print()

        # Verdict
        if delta > 0.10 and len(results_reaction) >= 15:
            print(f"[EDGE FOUND] Delta {delta:+.3f}R, {len(results_reaction)} trades")
        elif delta > 0:
            print(f"[WEAK] Delta {delta:+.3f}R (too small or insufficient sample)")
        else:
            print(f"[NO EDGE] Delta {delta:+.3f}R (negative)")

        print()

    con.close()


if __name__ == '__main__':
    main()
