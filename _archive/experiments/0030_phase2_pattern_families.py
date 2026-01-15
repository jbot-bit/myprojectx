"""
PHASE 2 — Test 5 Pattern Families for 0030 ORB

Each pattern family tests 2-4 states (pre-0030 filtering only).

Pattern A: Opening Drive Exhaustion (ODX)
Pattern B: Sweep + Acceptance Filter (SAF)
Pattern C: No-Side-Chosen
Pattern D: Two-Step Fake Expansion (TSF)
Pattern E: Trend-Continuation with Reclaim

VALIDATION RULES:
- Selectivity < 50% of state days
- Date-matched baseline comparison
- Temporal stability (3 chunks)
- Minimum 20 trades to validate
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta
import json

DB_PATH = "gold.db"
SYMBOL = "MGC"
ORB_CODE = "0030"

# Global results collector
ALL_RESULTS = {}


def get_candidate_states(con):
    """
    Get candidate states for 0030 based on pre-ORB characteristics.
    Using day_state_features for 0030.
    """

    query = """
        SELECT
            date_local,
            range_bucket,
            disp_bucket,
            close_pos_bucket,
            impulse_bucket
        FROM day_state_features
        WHERE orb_code = '0030'
            AND range_bucket IS NOT NULL
    """

    df = con.execute(query).df()

    # Define candidate states (broad enough to get samples)
    states = {
        'State_A': {'range_bucket': 'NORMAL', 'disp_bucket': 'D_SMALL'},
        'State_B': {'range_bucket': 'NORMAL', 'disp_bucket': 'D_MED'},
        'State_C': {'range_bucket': 'TIGHT', 'disp_bucket': 'D_SMALL'},
        'State_D': {'range_bucket': 'WIDE', 'disp_bucket': 'D_SMALL'}
    }

    state_results = {}

    for state_name, filters in states.items():
        mask = (df['range_bucket'] == filters['range_bucket']) & \
               (df['disp_bucket'] == filters['disp_bucket'])

        dates = df[mask]['date_local'].tolist()

        if len(dates) > 0:
            state_results[state_name] = {
                'dates': dates,
                'n_dates': len(dates),
                'frequency': len(dates) / len(df) * 100,
                'filters': filters
            }

    return state_results


def pattern_a_opening_drive_exhaustion(con, date_local):
    """
    Pattern A: Opening Drive Exhaustion (ODX)
    - First post-00:30 impulse expands hard then stalls
    - Entry: opposite on first 1m close back through ORB mid or break level
    - Stop: impulse extreme
    - Target: 1.0R
    - Timeout: 20m
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    # 0030 ORB: D+1 00:30-00:35
    test_start = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=35)
    test_end = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=1, minute=10)

    bars_1m = con.execute("""
        SELECT ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local, open, high, low, close
        FROM bars_1m
        WHERE symbol = ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    bars_5m = con.execute("""
        SELECT ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local, open, high, low, close
        FROM bars_5m
        WHERE symbol = ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    orb_data = con.execute("""
        SELECT orb_0030_high, orb_0030_low, orb_0030_size
        FROM daily_features_v2
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars_1m.empty or bars_5m.empty or orb_data is None:
        return None

    orb_high, orb_low, orb_size = orb_data
    if orb_high is None or orb_low is None:
        return None

    orb_mid = (orb_high + orb_low) / 2
    bars_1m['ts_local'] = bars_1m['ts_local'].astype(str)
    bars_5m['ts_local'] = bars_5m['ts_local'].astype(str)

    if len(bars_1m) < 25:
        return None

    # STEP 1: First impulse (first 10 bars)
    impulse_bars = bars_1m.head(10)
    impulse_high = impulse_bars['high'].max()
    impulse_low = impulse_bars['low'].min()
    impulse_range = impulse_high - impulse_low

    # Check if impulse is "hard" (>= 2x ORB size)
    if impulse_range < 2.0 * orb_size / 10.0:
        return None

    # Determine direction
    up_move = impulse_high - orb_high
    down_move = orb_low - impulse_low

    if up_move > down_move:
        impulse_dir = 'UP'
        impulse_extreme = impulse_high
    else:
        impulse_dir = 'DOWN'
        impulse_extreme = impulse_low

    # STEP 2: Check for stall (no new extreme in 5m bar)
    stall_bars_5m = bars_5m.iloc[2:4] if len(bars_5m) > 3 else bars_5m.iloc[2:]

    if stall_bars_5m.empty:
        return None

    if impulse_dir == 'UP':
        stalled = (stall_bars_5m['high'].max() <= impulse_extreme + 0.3)
    else:
        stalled = (stall_bars_5m['low'].min() >= impulse_extreme - 0.3)

    if not stalled:
        return None

    # STEP 3: Entry on 1m reclaim through ORB mid or high/low
    entry_bars = bars_1m.iloc[10:]

    entry_price = None
    entry_idx = None

    for idx, bar in entry_bars.iterrows():
        if impulse_dir == 'UP':
            if bar['close'] < orb_mid:  # Reclaim through ORB mid
                entry_price = bar['close']
                entry_idx = idx
                trade_dir = 'SHORT'
                break
        else:
            if bar['close'] > orb_mid:
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

    # Outcome (20m timeout)
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
        'pattern': 'Pattern_A_ODX',
        'outcome': outcome,
        'r_multiple': r_multiple
    }


def pattern_c_no_side_chosen(con, date_local):
    """
    Pattern C: No-Side-Chosen
    - Minutes 00:35-00:50 have NO 5m close outside ORB
    - First sweep outside ORB, then 1m reclaim within 3m
    - Entry: reclaim, Stop: sweep extreme, Target: 1.0R, Timeout: 20m
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    test_start = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=35)
    test_end = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=1, minute=10)

    bars_1m = con.execute("""
        SELECT ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local, open, high, low, close
        FROM bars_1m
        WHERE symbol = ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    bars_5m = con.execute("""
        SELECT ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local, open, high, low, close
        FROM bars_5m
        WHERE symbol = ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    orb_data = con.execute("""
        SELECT orb_0030_high, orb_0030_low
        FROM daily_features_v2
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars_1m.empty or bars_5m.empty or orb_data is None:
        return None

    orb_high, orb_low = orb_data
    if orb_high is None or orb_low is None:
        return None

    bars_1m['ts_local'] = bars_1m['ts_local'].astype(str)
    bars_5m['ts_local'] = bars_5m['ts_local'].astype(str)

    if len(bars_5m) < 3 or len(bars_1m) < 20:
        return None

    # STEP 1: Check regime (first 15 minutes, 3x 5m bars - NO 5m close outside ORB)
    regime_bars = bars_5m.head(3)

    stayed_inside = (regime_bars['close'].max() <= orb_high) and \
                    (regime_bars['close'].min() >= orb_low)

    if not stayed_inside:
        return None  # Side was chosen

    # STEP 2: Look for first sweep (after 15 minutes)
    sweep_search_bars = bars_1m.iloc[15:]

    sweep_idx = None
    sweep_dir = None
    sweep_extreme = None

    for idx, bar in sweep_search_bars.iterrows():
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
        return None

    # STEP 3: Look for reclaim within 3 bars
    sweep_position = bars_1m.index.get_loc(sweep_idx)
    reclaim_bars = bars_1m.iloc[sweep_position+1:sweep_position+4]

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

    # Outcome
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
        'pattern': 'Pattern_C_NoSideChosen',
        'outcome': outcome,
        'r_multiple': r_multiple
    }


def pattern_b_sweep_acceptance_filter(con, date_local):
    """
    Pattern B: Sweep + Acceptance Filter (SAF)
    - Sweep of 2300 ORB or London level in first 10-20m
    - Acceptance test: 5m CLOSE beyond (acceptance) or back inside (rejection)
    - Trade only rejection cases
    - Entry: 1m reclaim, Stop: sweep extreme, Target: 1.0R, Timeout: 20m
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    test_start = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=35)
    test_end = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=1, minute=10)

    bars_1m = con.execute("""
        SELECT ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local, open, high, low, close
        FROM bars_1m
        WHERE symbol = ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    bars_5m = con.execute("""
        SELECT ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local, open, high, low, close
        FROM bars_5m
        WHERE symbol = ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    orb_and_levels = con.execute("""
        SELECT orb_0030_high, orb_0030_low, orb_2300_high, orb_2300_low,
               london_high, london_low
        FROM daily_features_v2
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars_1m.empty or bars_5m.empty or orb_and_levels is None:
        return None

    orb_high, orb_low, orb_2300_high, orb_2300_low, london_high, london_low = orb_and_levels

    if orb_high is None or orb_low is None:
        return None

    bars_1m['ts_local'] = bars_1m['ts_local'].astype(str)
    bars_5m['ts_local'] = bars_5m['ts_local'].astype(str)

    if len(bars_1m) < 25 or len(bars_5m) < 4:
        return None

    # STEP 1: Look for sweep of key level in first 10-20 minutes
    sweep_search_bars = bars_1m.iloc[:20]

    # Check for sweeps
    sweep_extreme = None
    sweep_dir = None
    sweep_level = None

    high_sweep = sweep_search_bars['high'].max()
    low_sweep = sweep_search_bars['low'].min()

    # Check 2300 ORB sweeps
    if orb_2300_high is not None and high_sweep > orb_2300_high:
        if sweep_extreme is None or high_sweep > sweep_extreme:
            sweep_extreme = high_sweep
            sweep_dir = 'UP'
            sweep_level = orb_2300_high

    if orb_2300_low is not None and low_sweep < orb_2300_low:
        if sweep_extreme is None or low_sweep < sweep_extreme:
            sweep_extreme = low_sweep
            sweep_dir = 'DOWN'
            sweep_level = orb_2300_low

    # Check London levels
    if london_high is not None and high_sweep > london_high:
        if sweep_extreme is None or high_sweep > sweep_extreme:
            sweep_extreme = high_sweep
            sweep_dir = 'UP'
            sweep_level = london_high

    if london_low is not None and low_sweep < london_low:
        if sweep_extreme is None or low_sweep < sweep_extreme:
            sweep_extreme = low_sweep
            sweep_dir = 'DOWN'
            sweep_level = london_low

    if sweep_extreme is None:
        return None  # No sweep occurred

    # STEP 2: Acceptance test - check 5m close
    acceptance_bars_5m = bars_5m.iloc[2:5] if len(bars_5m) > 4 else bars_5m.iloc[2:]

    if acceptance_bars_5m.empty:
        return None

    if sweep_dir == 'UP':
        # Check for REJECTION (5m close back below swept level)
        rejected = (acceptance_bars_5m['close'].min() < sweep_level)
    else:
        # Check for REJECTION (5m close back above swept level)
        rejected = (acceptance_bars_5m['close'].max() > sweep_level)

    if not rejected:
        return None  # Accepted, not rejected - don't trade

    # STEP 3: Entry on 1m reclaim
    entry_bars = bars_1m.iloc[10:]

    entry_price = None
    entry_idx = None

    for idx, bar in entry_bars.iterrows():
        if sweep_dir == 'UP':
            if bar['close'] < sweep_level:
                entry_price = bar['close']
                entry_idx = idx
                trade_dir = 'SHORT'
                break
        else:
            if bar['close'] > sweep_level:
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

    # Outcome
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
        'pattern': 'Pattern_B_SAF',
        'outcome': outcome,
        'r_multiple': r_multiple
    }


def pattern_d_two_step_fake(con, date_local):
    """
    Pattern D: Two-Step Fake Expansion (TSF)
    - First breakout attempt fails (reclaim)
    - Second attempt fails quickly (double-failure)
    - Entry: after second failure confirmed (1m close back inside)
    - Stop: second failure extreme, Target: 1.0R, Timeout: 20m
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    test_start = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=35)
    test_end = datetime.combine(date_obj + timedelta(days=1), datetime.min.time()).replace(hour=1, minute=10)

    bars_1m = con.execute("""
        SELECT ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local, open, high, low, close
        FROM bars_1m
        WHERE symbol = ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    orb_data = con.execute("""
        SELECT orb_0030_high, orb_0030_low
        FROM daily_features_v2
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

    # STEP 1: First breakout and failure (first 10 bars)
    first_phase = bars_1m.head(10)

    first_high = first_phase['high'].max()
    first_low = first_phase['low'].min()

    broke_up_first = (first_high > orb_high)
    broke_down_first = (first_low < orb_low)

    if not broke_up_first and not broke_down_first:
        return None

    # Determine first break direction
    if broke_up_first and broke_down_first:
        up_dist = first_high - orb_high
        down_dist = orb_low - first_low
        if up_dist > down_dist:
            first_dir = 'UP'
        else:
            first_dir = 'DOWN'
    elif broke_up_first:
        first_dir = 'UP'
    else:
        first_dir = 'DOWN'

    # Check for first failure (reclaim in next 5 bars)
    reclaim_phase = bars_1m.iloc[10:15]

    if first_dir == 'UP':
        reclaimed = (reclaim_phase['close'].min() < orb_high)
    else:
        reclaimed = (reclaim_phase['close'].max() > orb_low)

    if not reclaimed:
        return None  # First break didn't fail

    # STEP 2: Second breakout attempt (opposite direction, bars 15-25)
    second_phase = bars_1m.iloc[15:25]

    second_high = second_phase['high'].max()
    second_low = second_phase['low'].min()

    # Check for opposite direction break
    if first_dir == 'UP':
        broke_opposite = (second_low < orb_low)
        if broke_opposite:
            second_extreme = second_low
            # Check for quick failure (next 5 bars)
            failure_check = bars_1m.iloc[20:25]
            second_failed = (failure_check['close'].max() > orb_low)
        else:
            return None
    else:
        broke_opposite = (second_high > orb_high)
        if broke_opposite:
            second_extreme = second_high
            # Check for quick failure
            failure_check = bars_1m.iloc[20:25]
            second_failed = (failure_check['close'].min() < orb_high)
        else:
            return None

    if not second_failed:
        return None  # Second break didn't fail

    # STEP 3: Entry on confirmation
    entry_bars = bars_1m.iloc[20:]

    entry_price = None
    entry_idx = None

    for idx, bar in entry_bars.iterrows():
        if first_dir == 'UP':
            # Enter LONG (back to first direction) on close above ORB low
            if bar['close'] > orb_low:
                entry_price = bar['close']
                entry_idx = idx
                trade_dir = 'LONG'
                break
        else:
            # Enter SHORT on close below ORB high
            if bar['close'] < orb_high:
                entry_price = bar['close']
                entry_idx = idx
                trade_dir = 'SHORT'
                break

    if entry_price is None:
        return None

    # Stop and target
    if trade_dir == 'LONG':
        stop_price = second_extreme - 0.5
        risk = entry_price - stop_price
        target_price = entry_price + risk
    else:
        stop_price = second_extreme + 0.5
        risk = stop_price - entry_price
        target_price = entry_price - risk

    if risk <= 0:
        return None

    # Outcome
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
        'pattern': 'Pattern_D_TSF',
        'outcome': outcome,
        'r_multiple': r_multiple
    }


def get_baseline(con, date_local):
    """Get baseline breakout for date-matched comparison."""
    result = con.execute("""
        SELECT outcome, r_multiple
        FROM orb_trades_1m_exec_nofilters
        WHERE orb = '0030' AND date_local = ? AND close_confirmations = 1 AND rr = 1.0
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


def validate_pattern_on_state(con, pattern_name, pattern_func, state_name, state_info):
    """Test a pattern on a specific state and validate results."""

    print(f"\n{'-'*80}")
    print(f"Testing {pattern_name} on {state_name}")
    print(f"State: {state_info['filters']}")
    print(f"Dates: {state_info['n_dates']} ({state_info['frequency']:.1f}%)")
    print(f"{'-'*80}\n")

    results_pattern = []
    results_baseline = []

    for date in state_info['dates']:
        result_p = pattern_func(con, date)
        if result_p:
            results_pattern.append(result_p)

        result_b = get_baseline(con, date)
        if result_b:
            results_baseline.append(result_b)

    # Selectivity check
    selectivity = len(results_pattern) / state_info['n_dates'] * 100 if state_info['n_dates'] > 0 else 0

    print(f"Entries: {len(results_pattern)}/{state_info['n_dates']} ({selectivity:.1f}%)")

    if selectivity >= 50:
        print(f"[FAILED] Selectivity too high ({selectivity:.1f}% >= 50%)")
        return None

    if len(results_pattern) == 0:
        print("[FAILED] No trades")
        return None

    if len(results_pattern) < 20:
        print(f"[INSUFFICIENT] Only {len(results_pattern)} trades (need 20+)")

    # Compute metrics
    df_p = pd.DataFrame(results_pattern)
    df_b = pd.DataFrame(results_baseline)

    avg_r_pattern = df_p['r_multiple'].mean()
    avg_r_baseline = df_b['r_multiple'].mean() if len(df_b) > 0 else 0
    delta = avg_r_pattern - avg_r_baseline

    print(f"Pattern: {avg_r_pattern:+.3f}R")
    print(f"Baseline: {avg_r_baseline:+.3f}R (same dates)")
    print(f"Delta: {delta:+.3f}R")

    # Temporal stability (if enough trades)
    temporal_verdict = None
    positive_chunks = 0

    if len(results_pattern) >= 15:
        df_p['date'] = pd.to_datetime(df_p['date'])
        df_p = df_p.sort_values('date')

        n = len(df_p)
        chunk_size = n // 3

        chunk1 = df_p.iloc[:chunk_size]
        chunk2 = df_p.iloc[chunk_size:2*chunk_size]
        chunk3 = df_p.iloc[2*chunk_size:]

        print("\nTEMPORAL STABILITY:")
        print(f"  Early:  {chunk1['r_multiple'].mean():+.3f}R ({len(chunk1)} trades)")
        print(f"  Middle: {chunk2['r_multiple'].mean():+.3f}R ({len(chunk2)} trades)")
        print(f"  Late:   {chunk3['r_multiple'].mean():+.3f}R ({len(chunk3)} trades)")

        positive_chunks = sum([
            chunk1['r_multiple'].mean() > 0,
            chunk2['r_multiple'].mean() > 0,
            chunk3['r_multiple'].mean() > 0
        ])

        if positive_chunks < 2:
            temporal_verdict = "UNSTABLE"
            print(f"  [{temporal_verdict}] {positive_chunks}/3 chunks positive")
        else:
            temporal_verdict = "STABLE"
            print(f"  [{temporal_verdict}] {positive_chunks}/3 chunks positive")

    # Final verdict
    print()
    if delta > 0.10 and len(results_pattern) >= 20 and (temporal_verdict == "STABLE" or temporal_verdict is None):
        print(f"[EDGE FOUND] Delta {delta:+.3f}R, {len(results_pattern)} trades")
        verdict = "VALIDATED"
    elif len(results_pattern) < 20:
        print(f"[INCONCLUSIVE] Sample too small")
        verdict = "INCONCLUSIVE"
    elif temporal_verdict == "UNSTABLE":
        print(f"[DISPROVED] Temporal instability")
        verdict = "DISPROVED"
    else:
        print(f"[NO EDGE] Delta {delta:+.3f}R")
        verdict = "NO_EDGE"

    return {
        'pattern': pattern_name,
        'state': state_name,
        'n_trades': len(results_pattern),
        'selectivity': selectivity,
        'avg_r': avg_r_pattern,
        'baseline': avg_r_baseline,
        'delta': delta,
        'temporal_stability': temporal_verdict,
        'positive_chunks': positive_chunks,
        'verdict': verdict
    }


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("\n" + "="*80)
    print("PHASE 2 — SESSION-SPECIFIC PATTERN TESTING: 0030 ORB")
    print("="*80 + "\n")

    # Get candidate states
    states = get_candidate_states(con)

    print(f"Found {len(states)} candidate states:")
    for state_name, info in states.items():
        print(f"  {state_name}: {info['n_dates']} dates ({info['frequency']:.1f}%) - {info['filters']}")
    print()

    # Define patterns to test
    patterns = [
        ('Pattern A: Opening Drive Exhaustion', pattern_a_opening_drive_exhaustion),
        ('Pattern B: Sweep + Acceptance Filter', pattern_b_sweep_acceptance_filter),
        ('Pattern C: No-Side-Chosen', pattern_c_no_side_chosen),
        ('Pattern D: Two-Step Fake', pattern_d_two_step_fake),
    ]

    # Test each pattern on top 2-3 states
    all_validation_results = []

    for pattern_name, pattern_func in patterns:
        print("\n" + "="*80)
        print(f"TESTING: {pattern_name}")
        print("="*80)

        # Test on first 3 states
        tested_states = list(states.items())[:3]

        for state_name, state_info in tested_states:
            result = validate_pattern_on_state(con, pattern_name, pattern_func, state_name, state_info)
            if result:
                all_validation_results.append(result)

    # Summary
    print("\n" + "="*80)
    print("PHASE 2 SUMMARY")
    print("="*80 + "\n")

    if len(all_validation_results) == 0:
        print("[NO EDGES FOUND] All patterns failed validation")
    else:
        validated = [r for r in all_validation_results if r['verdict'] == 'VALIDATED']

        if len(validated) > 0:
            print(f"VALIDATED EDGES: {len(validated)}")
            for r in validated:
                print(f"  - {r['pattern']} / {r['state']}: {r['n_trades']} trades, {r['delta']:+.3f}R delta")
        else:
            print("[NO VALIDATED EDGES]")
            print("\nBest results (inconclusive):")
            sorted_results = sorted(all_validation_results, key=lambda x: x['delta'], reverse=True)
            for r in sorted_results[:3]:
                print(f"  - {r['pattern']} / {r['state']}: {r['n_trades']} trades, {r['delta']:+.3f}R delta ({r['verdict']})")

    print()
    con.close()


if __name__ == '__main__':
    main()
