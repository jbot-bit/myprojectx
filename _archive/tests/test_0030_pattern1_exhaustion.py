"""
0030 ORB — PATTERN 1: Opening Drive Exhaustion Fade

State (pre-0030 only): high pre-ORB travel + ORB size not extreme
Liquidity event: first impulse after 00:30 extends then stalls (no new extreme for N minutes)
Entry: opposite direction on first 1m close back inside ORB OR after failure to make new extreme
Stop: extreme of impulse + small buffer
Target: 1.0R (fixed)
Timeout: 20 minutes

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
    - High pre-ORB travel (upper percentile)
    - ORB size not extreme (NORMAL or WIDE, not TIGHT)

    Using ONLY existing day_state_features fields.
    """

    query = """
        SELECT
            date_local,
            range_bucket,
            disp_bucket,
            close_pos_bucket,
            impulse_bucket,
            pre_orb_disp,
            pre_orb_range
        FROM day_state_features
        WHERE orb_code = '0030'
            AND range_bucket IS NOT NULL
            AND disp_bucket IS NOT NULL
    """

    df = con.execute(query).df()

    print(f"Total 0030 dates: {len(df)}")
    print()

    # Define "high pre-ORB travel" states
    # Test combinations with D_MED or D_LARGE (high displacement)
    candidate_states = [
        {
            'name': 'State A: NORMAL + D_MED',
            'range_bucket': 'NORMAL',
            'disp_bucket': 'D_MED'
        },
        {
            'name': 'State B: WIDE + D_MED',
            'range_bucket': 'WIDE',
            'disp_bucket': 'D_MED'
        },
        {
            'name': 'State C: NORMAL + D_LARGE',
            'range_bucket': 'NORMAL',
            'disp_bucket': 'D_LARGE'
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


def test_exhaustion_fade(con, date_local):
    """
    Test Pattern 1: Opening Drive Exhaustion Fade

    1. Detect first impulse after 00:30 (direction of initial move)
    2. Check if it stalls (no new extreme for 5+ minutes)
    3. Enter opposite direction on first close back inside ORB
    4. Stop: impulse extreme + 0.5
    5. Target: 1.0R
    6. Timeout: 20 minutes
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    # 0030 ORB: D+1 00:30-00:35
    # Test window: D+1 00:30-01:00 (30 min post-ORB)
    test_start = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=30)
    test_end = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=1, minute=0)

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

    # STEP 1: Detect first impulse (00:30-00:40, first 10 minutes)
    impulse_bars = bars_1m.head(10)  # First 10 bars after ORB

    if len(impulse_bars) < 5:
        return None

    # Determine impulse direction
    impulse_high = impulse_bars['high'].max()
    impulse_low = impulse_bars['low'].min()

    up_move = impulse_high - orb_high
    down_move = orb_low - impulse_low

    if up_move > down_move:
        impulse_direction = 'UP'
        impulse_extreme = impulse_high
    else:
        impulse_direction = 'DOWN'
        impulse_extreme = impulse_low

    # STEP 2: Check if stalls (no new extreme for 5+ minutes)
    # Look at next 5 bars after impulse
    if len(bars_1m) < 15:
        return None

    stall_bars = bars_1m.iloc[10:15]  # Minutes 10-15

    if impulse_direction == 'UP':
        stalled = (stall_bars['high'].max() <= impulse_extreme + 0.2)  # No new high
    else:
        stalled = (stall_bars['low'].min() >= impulse_extreme - 0.2)  # No new low

    if not stalled:
        return None  # Impulse continued, not exhaustion

    # STEP 3: Entry on first close back inside ORB
    entry_search_bars = bars_1m.iloc[10:]  # After impulse

    entry_price = None
    entry_idx = None

    for idx, bar in entry_search_bars.iterrows():
        if impulse_direction == 'UP':
            # Enter SHORT on first close below ORB high
            if bar['close'] < orb_high:
                entry_price = bar['close']
                entry_idx = idx
                trade_direction = 'SHORT'
                break
        else:
            # Enter LONG on first close above ORB low
            if bar['close'] > orb_low:
                entry_price = bar['close']
                entry_idx = idx
                trade_direction = 'LONG'
                break

    if entry_price is None:
        return None  # No entry triggered

    # STEP 4: Stop and target
    if trade_direction == 'SHORT':
        stop_price = impulse_extreme + 0.5  # Impulse high + buffer
        risk = stop_price - entry_price
        target_price = entry_price - risk  # 1.0R
    else:
        stop_price = impulse_extreme - 0.5  # Impulse low - buffer
        risk = entry_price - stop_price
        target_price = entry_price + risk  # 1.0R

    if risk <= 0:
        return None

    # STEP 5: Outcome (20 minute timeout)
    entry_position = bars_1m.index.get_loc(entry_idx)
    outcome_bars = bars_1m.iloc[entry_position:entry_position+20]

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
        'impulse_dir': impulse_direction,
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
    print("0030 ORB — PATTERN 1: Opening Drive Exhaustion Fade")
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
            result_r = test_exhaustion_fade(con, date)
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
