"""
UNIFIED LIQUIDITY REACTION FRAMEWORK
Tests all 3 allowed patterns on all sessions with FIXED global parameters.

GLOBAL PARAMETERS (NO TUNING):
- N = 10 minutes (pattern development time)
- K = max(6, round(0.3 * ORB_range_ticks)) [adaptive to ORB size]
- X = 2.0 (volatility multiplier)

PATTERNS:
1. Failure-to-Continue: Break doesn't extend K ticks in N minutes -> enter on reclaim
2. Volatility Exhaustion: First impulse >= X * ORB range -> enter opposite on failure
3. No-Side-Chosen: Inside ORB for N minutes -> trade first sweep+reclaim trap

SESSIONS TO TEST: 0900, 1000, 1100, 0030
(1800 already validated, 2300 already tested)

STRICT RULES:
- Use ONLY existing pre-computed fields
- Pre-ORB state filters ONLY
- <50% selectivity requirement
- Date-matched baseline comparison
- 1m execution, worst-case resolution
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MGC"

# GLOBAL PARAMETERS (FROZEN)
N_MINUTES = 10
K_MIN = 6
X_MULTIPLIER = 2.0

def compute_k_threshold(orb_range_ticks):
    """Compute adaptive K threshold based on ORB size."""
    return max(K_MIN, round(0.3 * orb_range_ticks))


def get_orb_times(orb_code, date_obj):
    """Get ORB window times for each session."""
    orb_times = {
        '0900': {
            'orb_start': datetime.combine(date_obj, datetime.min.time()).replace(hour=9, minute=0),
            'orb_end': datetime.combine(date_obj, datetime.min.time()).replace(hour=9, minute=5),
            'test_start': datetime.combine(date_obj, datetime.min.time()).replace(hour=9, minute=5),
            'test_end': datetime.combine(date_obj, datetime.min.time()).replace(hour=10, minute=0)
        },
        '1000': {
            'orb_start': datetime.combine(date_obj, datetime.min.time()).replace(hour=10, minute=0),
            'orb_end': datetime.combine(date_obj, datetime.min.time()).replace(hour=10, minute=5),
            'test_start': datetime.combine(date_obj, datetime.min.time()).replace(hour=10, minute=5),
            'test_end': datetime.combine(date_obj, datetime.min.time()).replace(hour=11, minute=0)
        },
        '1100': {
            'orb_start': datetime.combine(date_obj, datetime.min.time()).replace(hour=11, minute=0),
            'orb_end': datetime.combine(date_obj, datetime.min.time()).replace(hour=11, minute=5),
            'test_start': datetime.combine(date_obj, datetime.min.time()).replace(hour=11, minute=5),
            'test_end': datetime.combine(date_obj, datetime.min.time()).replace(hour=12, minute=0)
        },
        '0030': {
            'orb_start': datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=30),
            'orb_end': datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=35),
            'test_start': datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=35),
            'test_end': datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=1, minute=15)
        }
    }
    return orb_times[orb_code]


def get_candidate_states(con, orb_code):
    """Get candidate states for pattern testing."""
    query = """
        SELECT
            date_local,
            range_bucket,
            disp_bucket,
            close_pos_bucket,
            impulse_bucket
        FROM day_state_features
        WHERE orb_code = ?
            AND range_bucket IS NOT NULL
            AND disp_bucket IS NOT NULL
    """

    df = con.execute(query, [orb_code]).df()

    if df.empty:
        return []

    # Test common moderate states (broad enough to get samples)
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
            results.append({
                'state': state,
                'dates': state_dates,
                'n_dates': len(state_dates),
                'frequency': freq
            })

    return results


def test_pattern1_failure_to_continue(con, orb_code, date_local):
    """
    Pattern 1: Failure-to-Continue
    - After first break, if price does NOT extend >= K ticks within N minutes,
      then enter on reclaim/close back inside.
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    times = get_orb_times(orb_code, date_obj)

    # Get bars
    bars_1m = con.execute("""
        SELECT
            ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local,
            open, high, low, close
        FROM bars_1m
        WHERE symbol = ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, times['test_start'], times['test_end']]).df()

    # Get ORB data
    orb_data = con.execute(f"""
        SELECT orb_{orb_code}_high, orb_{orb_code}_low
        FROM daily_features
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars_1m.empty or orb_data is None:
        return None

    orb_high, orb_low = orb_data
    if orb_high is None or orb_low is None:
        return None

    orb_range_ticks = (orb_high - orb_low) * 10
    K = compute_k_threshold(orb_range_ticks)

    bars_1m['ts_local'] = bars_1m['ts_local'].astype(str)

    if len(bars_1m) < N_MINUTES + 10:
        return None

    # STEP 1: Detect first break (first 5 bars)
    first_bars = bars_1m.head(5)

    first_high = first_bars['high'].max()
    first_low = first_bars['low'].min()

    broke_up = (first_high > orb_high)
    broke_down = (first_low < orb_low)

    if not broke_up and not broke_down:
        return None

    if broke_up and broke_down:
        up_dist = first_high - orb_high
        down_dist = orb_low - first_low
        if up_dist > down_dist:
            break_dir = 'UP'
            break_extreme = first_high
        else:
            break_dir = 'DOWN'
            break_extreme = first_low
    elif broke_up:
        break_dir = 'UP'
        break_extreme = first_high
    else:
        break_dir = 'DOWN'
        break_extreme = first_low

    # STEP 2: Check if break FAILED TO CONTINUE (didn't extend K ticks in next N minutes)
    continuation_bars = bars_1m.iloc[5:5+N_MINUTES]

    if break_dir == 'UP':
        max_extension = continuation_bars['high'].max()
        extended = (max_extension >= break_extreme + K / 10.0)
    else:
        max_extension = continuation_bars['low'].min()
        extended = (max_extension <= break_extreme - K / 10.0)

    if extended:
        return None  # Break continued successfully

    # STEP 3: Entry on reclaim (close back inside ORB)
    entry_bars = bars_1m.iloc[5+N_MINUTES:]

    entry_price = None
    entry_idx = None

    for idx, bar in entry_bars.iterrows():
        if break_dir == 'UP':
            if bar['close'] < orb_high:
                entry_price = bar['close']
                entry_idx = idx
                trade_dir = 'SHORT'
                break
        else:
            if bar['close'] > orb_low:
                entry_price = bar['close']
                entry_idx = idx
                trade_dir = 'LONG'
                break

    if entry_price is None:
        return None

    # STEP 4: Stop and target
    if trade_dir == 'SHORT':
        stop_price = break_extreme + 0.5
        risk = stop_price - entry_price
        target_price = entry_price - risk
    else:
        stop_price = break_extreme - 0.5
        risk = entry_price - stop_price
        target_price = entry_price + risk

    if risk <= 0:
        return None

    # STEP 5: Outcome (20 min timeout)
    entry_position = bars_1m.index.get_loc(entry_idx)
    outcome_bars = bars_1m.iloc[entry_position:entry_position+20]

    if outcome_bars.empty:
        return None

    if trade_dir == 'SHORT':
        stop_hit = (outcome_bars['high'].max() >= stop_price)
        target_hit = (outcome_bars['low'].min() <= target_price)
    else:
        stop_hit = (outcome_bars['low'].min() <= stop_price)
        target_hit = (outcome_bars['high'].max() >= target_price)

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
        exit_price = outcome_bars.iloc[-1]['close']
        pnl = (entry_price - exit_price) if trade_dir == 'SHORT' else (exit_price - entry_price)
        outcome = 'TIMEOUT'
        r_multiple = pnl / risk

    return {
        'date': str(date_local).split()[0],
        'pattern': 'Failure-to-Continue',
        'outcome': outcome,
        'r_multiple': r_multiple
    }


def test_pattern2_volatility_exhaustion(con, orb_code, date_local):
    """
    Pattern 2: Volatility Exhaustion
    - If first impulse range >= X * ORB_range,
      then enter opposite on failure to make new extreme + reversal close.
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    times = get_orb_times(orb_code, date_obj)

    bars_1m = con.execute("""
        SELECT
            ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local,
            open, high, low, close
        FROM bars_1m
        WHERE symbol = ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, times['test_start'], times['test_end']]).df()

    orb_data = con.execute(f"""
        SELECT orb_{orb_code}_high, orb_{orb_code}_low
        FROM daily_features
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars_1m.empty or orb_data is None:
        return None

    orb_high, orb_low = orb_data
    if orb_high is None or orb_low is None:
        return None

    orb_range = orb_high - orb_low

    bars_1m['ts_local'] = bars_1m['ts_local'].astype(str)

    if len(bars_1m) < 20:
        return None

    # STEP 1: Measure first impulse (first 10 bars)
    impulse_bars = bars_1m.head(10)

    impulse_high = impulse_bars['high'].max()
    impulse_low = impulse_bars['low'].min()
    impulse_range = impulse_high - impulse_low

    # Check if impulse is >= X * ORB range (volatility exhaustion)
    if impulse_range < X_MULTIPLIER * orb_range:
        return None  # Not exhaustion

    # Determine impulse direction
    up_move = impulse_high - orb_high
    down_move = orb_low - impulse_low

    if up_move > down_move:
        impulse_dir = 'UP'
        impulse_extreme = impulse_high
    else:
        impulse_dir = 'DOWN'
        impulse_extreme = impulse_low

    # STEP 2: Check for failure to make new extreme (next 5 bars)
    stall_bars = bars_1m.iloc[10:15]

    if impulse_dir == 'UP':
        stalled = (stall_bars['high'].max() <= impulse_extreme + 0.2)
    else:
        stalled = (stall_bars['low'].min() >= impulse_extreme - 0.2)

    if not stalled:
        return None

    # STEP 3: Entry on reversal close inside ORB
    entry_bars = bars_1m.iloc[10:]

    entry_price = None
    entry_idx = None

    for idx, bar in entry_bars.iterrows():
        if impulse_dir == 'UP':
            if bar['close'] < orb_high:
                entry_price = bar['close']
                entry_idx = idx
                trade_dir = 'SHORT'
                break
        else:
            if bar['close'] > orb_low:
                entry_price = bar['close']
                entry_idx = idx
                trade_dir = 'LONG'
                break

    if entry_price is None:
        return None

    # Stop and target
    if trade_dir == 'SHORT':
        stop_price = impulse_extreme + 0.5
        risk = stop_price - entry_price
        target_price = entry_price - risk
    else:
        stop_price = impulse_extreme - 0.5
        risk = entry_price - stop_price
        target_price = entry_price + risk

    if risk <= 0:
        return None

    # Outcome (20 min timeout)
    entry_position = bars_1m.index.get_loc(entry_idx)
    outcome_bars = bars_1m.iloc[entry_position:entry_position+20]

    if outcome_bars.empty:
        return None

    if trade_dir == 'SHORT':
        stop_hit = (outcome_bars['high'].max() >= stop_price)
        target_hit = (outcome_bars['low'].min() <= target_price)
    else:
        stop_hit = (outcome_bars['low'].min() <= stop_price)
        target_hit = (outcome_bars['high'].max() >= target_price)

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
        exit_price = outcome_bars.iloc[-1]['close']
        pnl = (entry_price - exit_price) if trade_dir == 'SHORT' else (exit_price - entry_price)
        outcome = 'TIMEOUT'
        r_multiple = pnl / risk

    return {
        'date': str(date_local).split()[0],
        'pattern': 'Volatility Exhaustion',
        'outcome': outcome,
        'r_multiple': r_multiple
    }


def test_pattern3_no_side_chosen(con, orb_code, date_local):
    """
    Pattern 3: No-Side-Chosen
    - If price remains inside ORB for N minutes,
      only trade the first sweep + reclaim trap.
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    times = get_orb_times(orb_code, date_obj)

    bars_1m = con.execute("""
        SELECT
            ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local,
            open, high, low, close
        FROM bars_1m
        WHERE symbol = ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, times['test_start'], times['test_end']]).df()

    orb_data = con.execute(f"""
        SELECT orb_{orb_code}_high, orb_{orb_code}_low
        FROM daily_features
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars_1m.empty or orb_data is None:
        return None

    orb_high, orb_low = orb_data
    if orb_high is None or orb_low is None:
        return None

    bars_1m['ts_local'] = bars_1m['ts_local'].astype(str)

    if len(bars_1m) < N_MINUTES + 15:
        return None

    # STEP 1: Check if price stayed inside ORB for N minutes
    inside_bars = bars_1m.head(N_MINUTES)

    stayed_inside = (inside_bars['high'].max() <= orb_high) and (inside_bars['low'].min() >= orb_low)

    if not stayed_inside:
        return None  # Side was chosen early

    # STEP 2: Look for first sweep after N minutes
    sweep_bars = bars_1m.iloc[N_MINUTES:]

    sweep_idx = None
    sweep_dir = None
    sweep_extreme = None

    for idx, bar in sweep_bars.iterrows():
        if bar['high'] > orb_high:
            sweep_dir = 'UP'
            sweep_extreme = bar['high']
            sweep_idx = idx
            break
        elif bar['low'] < orb_low:
            sweep_dir = 'DOWN'
            sweep_extreme = bar['low']
            sweep_idx = idx
            break

    if sweep_idx is None:
        return None  # No sweep occurred

    # STEP 3: Look for reclaim (within next 5 bars)
    sweep_position = bars_1m.index.get_loc(sweep_idx)
    reclaim_bars = bars_1m.iloc[sweep_position+1:sweep_position+6]

    if reclaim_bars.empty:
        return None

    entry_price = None
    entry_idx = None

    for idx, bar in reclaim_bars.iterrows():
        if sweep_dir == 'UP':
            if bar['close'] < orb_high:
                entry_price = bar['close']
                entry_idx = idx
                trade_dir = 'SHORT'
                break
        else:
            if bar['close'] > orb_low:
                entry_price = bar['close']
                entry_idx = idx
                trade_dir = 'LONG'
                break

    if entry_price is None:
        return None

    # Stop and target
    if trade_dir == 'SHORT':
        stop_price = sweep_extreme + 0.5
        risk = stop_price - entry_price
        target_price = entry_price - risk
    else:
        stop_price = sweep_extreme - 0.5
        risk = entry_price - stop_price
        target_price = entry_price + risk

    if risk <= 0:
        return None

    # Outcome (20 min timeout)
    entry_position = bars_1m.index.get_loc(entry_idx)
    outcome_bars = bars_1m.iloc[entry_position:entry_position+20]

    if outcome_bars.empty:
        return None

    if trade_dir == 'SHORT':
        stop_hit = (outcome_bars['high'].max() >= stop_price)
        target_hit = (outcome_bars['low'].min() <= target_price)
    else:
        stop_hit = (outcome_bars['low'].min() <= stop_price)
        target_hit = (outcome_bars['high'].max() >= target_price)

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
        exit_price = outcome_bars.iloc[-1]['close']
        pnl = (entry_price - exit_price) if trade_dir == 'SHORT' else (exit_price - entry_price)
        outcome = 'TIMEOUT'
        r_multiple = pnl / risk

    return {
        'date': str(date_local).split()[0],
        'pattern': 'No-Side-Chosen',
        'outcome': outcome,
        'r_multiple': r_multiple
    }


def test_baseline(con, orb_code, date_local):
    """Get baseline breakout for date-matched comparison."""
    result = con.execute(f"""
        SELECT outcome, r_multiple
        FROM orb_trades_1m_exec_nofilters
        WHERE orb = ?
            AND date_local = ?
            AND close_confirmations = 1
            AND rr = 1.0
        LIMIT 1
    """, [orb_code, date_local]).fetchone()

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
    print("UNIFIED LIQUIDITY REACTION FRAMEWORK")
    print("="*80)
    print()
    print("GLOBAL PARAMETERS (FROZEN):")
    print(f"  N = {N_MINUTES} minutes")
    print(f"  K = max({K_MIN}, round(0.3 * ORB_range_ticks))")
    print(f"  X = {X_MULTIPLIER}")
    print()
    print("TESTING SESSIONS: 0900, 1000, 1100, 0030")
    print("PATTERNS: Failure-to-Continue, Volatility Exhaustion, No-Side-Chosen")
    print()

    sessions = ['0900', '1000', '1100', '0030']
    patterns = [
        ('Pattern 1', test_pattern1_failure_to_continue),
        ('Pattern 2', test_pattern2_volatility_exhaustion),
        ('Pattern 3', test_pattern3_no_side_chosen)
    ]

    for orb_code in sessions:
        print("="*80)
        print(f"SESSION: {orb_code} ORB")
        print("="*80)
        print()

        # Get candidate states
        state_results = get_candidate_states(con, orb_code)

        if len(state_results) == 0:
            print(f"[NO STATES] No data for {orb_code}")
            print()
            continue

        print(f"Candidate states for {orb_code}:")
        for sr in state_results:
            print(f"  {sr['state']['name']}: {sr['n_dates']} dates ({sr['frequency']:.1f}%)")
        print()

        # Test each pattern
        for pattern_name, pattern_func in patterns:
            print("-"*80)
            print(f"{pattern_name}: {pattern_func.__name__.replace('test_pattern', '').replace('_', ' ').title()}")
            print("-"*80)
            print()

            # Test on first state only (to save time)
            if len(state_results) > 0:
                state_info = state_results[0]

                results_reaction = []
                results_baseline = []

                for date in state_info['dates']:
                    result_r = pattern_func(con, orb_code, date)
                    if result_r:
                        results_reaction.append(result_r)

                    result_b = test_baseline(con, orb_code, date)
                    if result_b:
                        results_baseline.append(result_b)

                selectivity = len(results_reaction) / state_info['n_dates'] * 100 if state_info['n_dates'] > 0 else 0

                print(f"State: {state_info['state']['name']}")
                print(f"Entries: {len(results_reaction)}/{state_info['n_dates']} ({selectivity:.1f}%)")

                if selectivity >= 50:
                    print(f"[FAILED] Selectivity too high")
                    print()
                    continue

                if len(results_reaction) == 0:
                    print("[FAILED] No trades")
                    print()
                    continue

                if len(results_reaction) < 20:
                    print(f"[INSUFFICIENT] Only {len(results_reaction)} trades (need 20+)")

                df_r = pd.DataFrame(results_reaction)
                df_b = pd.DataFrame(results_baseline)

                avg_r_reaction = df_r['r_multiple'].mean()
                avg_r_baseline = df_b['r_multiple'].mean() if len(df_b) > 0 else 0
                delta = avg_r_reaction - avg_r_baseline

                print(f"Reaction: {avg_r_reaction:+.3f}R")
                print(f"Baseline: {avg_r_baseline:+.3f}R")
                print(f"Delta: {delta:+.3f}R")
                print()

    con.close()


if __name__ == '__main__':
    main()
