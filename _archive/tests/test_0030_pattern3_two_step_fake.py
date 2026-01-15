"""
0030 ORB - PATTERN 3: Two-Step Fake

State (pre-0030 only): any state with ORB size >= 3.0 ticks (not TIGHT)
Liquidity event:
  1. First break of ORB (either direction)
  2. Price reverses, breaks opposite boundary
  3. Second break fails (doesn't extend significantly)
Entry: on reversal after second break fails (back toward first break direction)
Stop: extreme of second break + buffer
Target: 1.0R
Timeout: 30 minutes

STRICT RULES:
- Use ONLY existing pre-computed fields (day_state_features)
- Pre-ORB state filters ONLY
- <50% selectivity requirement
- Date-matched baseline comparison
- 1m execution, worst-case resolution
- Report failures honestly
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MGC"
ORB_CODE = "0030"

def get_candidate_states(con):
    """
    Find 0030 states with:
    - ORB size >= 3.0 ticks (NORMAL or WIDE, not TIGHT)
    - Any displacement/close position

    Using ONLY existing day_state_features fields.
    """

    query = """
        SELECT
            date_local,
            range_bucket,
            disp_bucket,
            close_pos_bucket
        FROM day_state_features
        WHERE orb_code = '0030'
            AND range_bucket IS NOT NULL
            AND range_bucket IN ('NORMAL', 'WIDE')
    """

    df = con.execute(query).df()

    print(f"Total 0030 dates with NORMAL/WIDE range: {len(df)}")
    print()

    # Test broader states (any D/CP combo with decent range)
    candidate_states = [
        {
            'name': 'State A: NORMAL + D_SMALL',
            'range_bucket': 'NORMAL',
            'disp_bucket': 'D_SMALL'
        },
        {
            'name': 'State B: NORMAL + D_MED',
            'range_bucket': 'NORMAL',
            'disp_bucket': 'D_MED'
        },
        {
            'name': 'State C: WIDE + D_SMALL',
            'range_bucket': 'WIDE',
            'disp_bucket': 'D_SMALL'
        }
    ]

    results = []

    for state in candidate_states:
        mask = (
            (df['range_bucket'] == state['range_bucket']) &
            (df['disp_bucket'] == state['disp_bucket'])
        )

        state_dates = df[mask]['date_local'].tolist()

        if len(state_dates) > 0:
            freq = len(state_dates) / len(df) * 100
            print(f"{state['name']}: {len(state_dates)} dates ({freq:.1f}%)")

            results.append({
                'state': state,
                'dates': state_dates,
                'n_dates': len(state_dates),
                'frequency': freq
            })

    print()
    return results


def test_two_step_fake(con, date_local):
    """
    Test Pattern 3: Two-Step Fake

    1. First break: detect initial ORB break in first 15 bars
    2. Reversal: price reverses and breaks opposite boundary
    3. Second break fails: doesn't extend beyond first break + some threshold
    4. Entry: on reversal back toward first break direction
    5. Stop: extreme of second break + buffer
    6. Target: 1.0R
    7. Timeout: 30 minutes
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    # 0030 ORB: D+1 00:30-00:35
    # Test window: D+1 00:35-01:15 (40 min post-ORB)
    test_start = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=35)
    test_end = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=1, minute=15)

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

    orb_data = con.execute("""
        SELECT orb_0030_high, orb_0030_low
        FROM daily_features
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars_1m.empty or orb_data is None:
        return None

    orb_high, orb_low = orb_data
    if orb_high is None or orb_low is None:
        return None

    bars_1m['ts_local'] = bars_1m['ts_local'].astype(str)

    if len(bars_1m) < 30:
        return None

    # STEP 1: Detect first break (first 15 bars)
    first_break_bars = bars_1m.head(15)

    first_break_high = first_break_bars['high'].max()
    first_break_low = first_break_bars['low'].min()

    broke_up_first = (first_break_high > orb_high)
    broke_down_first = (first_break_low < orb_low)

    if not broke_up_first and not broke_down_first:
        return None  # No first break

    if broke_up_first and broke_down_first:
        # Determine which was more significant
        up_distance = first_break_high - orb_high
        down_distance = orb_low - first_break_low
        if up_distance > down_distance:
            first_break_dir = 'UP'
            first_break_extreme = first_break_high
        else:
            first_break_dir = 'DOWN'
            first_break_extreme = first_break_low
    elif broke_up_first:
        first_break_dir = 'UP'
        first_break_extreme = first_break_high
    else:
        first_break_dir = 'DOWN'
        first_break_extreme = first_break_low

    # STEP 2: Look for reversal and second break (bars 15-30)
    second_phase_bars = bars_1m.iloc[15:30]

    if second_phase_bars.empty:
        return None

    second_phase_high = second_phase_bars['high'].max()
    second_phase_low = second_phase_bars['low'].min()

    # Check if price broke OPPOSITE boundary
    if first_break_dir == 'UP':
        # First broke UP, check if it reversed and broke DOWN
        broke_opposite = (second_phase_low < orb_low)
        if broke_opposite:
            second_break_extreme = second_phase_low
            # Check if second break failed (didn't extend past first break significantly)
            failed = (second_break_extreme > first_break_extreme - 3.0)
        else:
            return None
    else:
        # First broke DOWN, check if it reversed and broke UP
        broke_opposite = (second_phase_high > orb_high)
        if broke_opposite:
            second_break_extreme = second_phase_high
            # Check if second break failed (didn't extend past first break significantly)
            failed = (second_break_extreme < first_break_extreme + 3.0)
        else:
            return None

    if not failed:
        return None  # Second break succeeded (not a fake)

    # STEP 3: Entry on reversal back toward first break direction
    # Look for entry after bar 20
    entry_search_bars = bars_1m.iloc[20:]

    entry_price = None
    entry_idx = None

    for idx, bar in entry_search_bars.iterrows():
        if first_break_dir == 'UP':
            # Enter LONG (back toward UP direction) on close above ORB low
            if bar['close'] > orb_low:
                entry_price = bar['close']
                entry_idx = idx
                trade_direction = 'LONG'
                break
        else:
            # Enter SHORT (back toward DOWN direction) on close below ORB high
            if bar['close'] < orb_high:
                entry_price = bar['close']
                entry_idx = idx
                trade_direction = 'SHORT'
                break

    if entry_price is None:
        return None  # No entry triggered

    # STEP 4: Stop and target
    if trade_direction == 'LONG':
        stop_price = second_break_extreme - 0.5  # Second break low - buffer
        risk = entry_price - stop_price
        target_price = entry_price + risk  # 1.0R
    else:
        stop_price = second_break_extreme + 0.5  # Second break high + buffer
        risk = stop_price - entry_price
        target_price = entry_price - risk  # 1.0R

    if risk <= 0:
        return None

    # STEP 5: Outcome (30 minute timeout)
    entry_position = bars_1m.index.get_loc(entry_idx)
    outcome_bars = bars_1m.iloc[entry_position:entry_position+30]

    if outcome_bars.empty:
        return None

    if trade_direction == 'SHORT':
        stop_hit = (outcome_bars['high'].max() >= stop_price)
        target_hit = (outcome_bars['low'].min() <= target_price)
    else:
        stop_hit = (outcome_bars['low'].min() <= stop_price)
        target_hit = (outcome_bars['high'].max() >= target_price)

    # Worst case: both hit = LOSS
    if stop_hit and target_hit:
        outcome = 'LOSS'
        r_multiple = -1.0
    elif stop_hit:
        outcome = 'LOSS'
        r_multiple = -1.0
    elif target_hit:
        outcome = 'WIN'
        r_multiple = 1.0
    else:
        # Timeout: exit at close
        exit_price = outcome_bars.iloc[-1]['close']
        if trade_direction == 'SHORT':
            pnl = entry_price - exit_price
        else:
            pnl = exit_price - entry_price
        outcome = 'TIMEOUT'
        r_multiple = pnl / risk

    return {
        'date': str(date_local).split()[0],
        'first_break': first_break_dir,
        'trade_dir': trade_direction,
        'outcome': outcome,
        'r_multiple': r_multiple
    }


def test_baseline(con, date_local):
    """Get baseline breakout on same date."""
    result = con.execute("""
        SELECT outcome, r_multiple
        FROM orb_trades_1m_exec_nofilters
        WHERE orb = '0030'
            AND date_local = ?
            AND close_confirmations = 1
            AND rr = 1.0
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
    print("0030 ORB - PATTERN 3: Two-Step Fake")
    print("="*80)
    print()

    # Get candidate states
    state_results = get_candidate_states(con)

    if len(state_results) == 0:
        print("[NO STATES] Cannot proceed")
        con.close()
        return

    # Test each state
    for state_info in state_results[:3]:  # Max 3 states
        print("="*80)
        print(f"TESTING: {state_info['state']['name']}")
        print("="*80)
        print()
        print(f"Dates: {state_info['n_dates']} ({state_info['frequency']:.1f}%)")
        print()

        results_reaction = []
        results_baseline = []

        for date in state_info['dates']:
            result_r = test_two_step_fake(con, date)
            if result_r:
                results_reaction.append(result_r)

            result_b = test_baseline(con, date)
            if result_b:
                results_baseline.append(result_b)

        # Check selectivity
        selectivity = len(results_reaction) / state_info['n_dates'] * 100 if state_info['n_dates'] > 0 else 0

        print(f"Reaction entries: {len(results_reaction)}/{state_info['n_dates']} ({selectivity:.1f}%)")
        print()

        if selectivity >= 50:
            print(f"[FAILED] Selectivity too high ({selectivity:.1f}% >= 50%)")
            print()
            continue

        if len(results_reaction) == 0:
            print("[FAILED] No reaction trades")
            print()
            continue

        if len(results_reaction) < 20:
            print(f"[INSUFFICIENT] Only {len(results_reaction)} trades (need 20+)")
            print()

        # Results
        df_r = pd.DataFrame(results_reaction)
        df_b = pd.DataFrame(results_baseline)

        avg_r_reaction = df_r['r_multiple'].mean()
        avg_r_baseline = df_b['r_multiple'].mean() if len(df_b) > 0 else 0
        delta = avg_r_reaction - avg_r_baseline

        print(f"Reaction avg R: {avg_r_reaction:+.3f}R ({len(results_reaction)} trades)")
        print(f"Baseline avg R: {avg_r_baseline:+.3f}R (same dates)")
        print(f"Delta: {delta:+.3f}R")
        print()

        # Temporal stability if sample adequate
        if len(results_reaction) >= 15:
            df_r['date'] = pd.to_datetime(df_r['date'])
            df_r = df_r.sort_values('date')

            n = len(df_r)
            chunk_size = n // 3

            chunk1 = df_r.iloc[:chunk_size]
            chunk2 = df_r.iloc[chunk_size:2*chunk_size]
            chunk3 = df_r.iloc[2*chunk_size:]

            print("TEMPORAL STABILITY:")
            print(f"  Early:  {chunk1['r_multiple'].mean():+.3f}R ({len(chunk1)} trades)")
            print(f"  Middle: {chunk2['r_multiple'].mean():+.3f}R ({len(chunk2)} trades)")
            print(f"  Late:   {chunk3['r_multiple'].mean():+.3f}R ({len(chunk3)} trades)")
            print()

            positive_chunks = sum([
                chunk1['r_multiple'].mean() > 0,
                chunk2['r_multiple'].mean() > 0,
                chunk3['r_multiple'].mean() > 0
            ])

            if positive_chunks < 2:
                print(f"[DISPROVED] Temporal instability ({positive_chunks}/3 positive)")
            else:
                print(f"[STABLE] {positive_chunks}/3 chunks positive")

            print()

        # Verdict
        if delta > 0.10 and len(results_reaction) >= 20:
            print(f"[EDGE FOUND] Delta {delta:+.3f}R, {len(results_reaction)} trades")
        elif len(results_reaction) < 20:
            print(f"[INCONCLUSIVE] Sample too small")
        else:
            print(f"[NO EDGE] Delta {delta:+.3f}R")

        print()

    con.close()


if __name__ == '__main__':
    main()
