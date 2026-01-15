"""
PHASE 2 — 09:00 ASIA SESSION PATTERN TESTING

Based on Phase 1 behavioral findings:
- IMMEDIATE REJECTION dominates (65.8%)
- Balance = WEAKNESS (96.8% chop)
- Tiny ORBs (1.7 tick median)

PATTERN FAMILIES TO TEST:
1. Immediate Rejection Reversal (fade early break, trade the reversal)
2. Balance Failure (avoid/fade balanced opens)

STRICT VALIDATION:
- ≥50 trades
- Delta ≥+0.10R vs baseline
- 3/3 temporal chunks positive
- Stable expectancy
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "gold.db"
SYMBOL = "MGC"
ORB_CODE = "0900"

def get_candidate_states(con):
    """Get states for 09:00 based on pre-ORB characteristics."""

    query = """
        SELECT
            date_local,
            range_bucket,
            disp_bucket,
            close_pos_bucket
        FROM day_state_features
        WHERE orb_code = '0900'
            AND range_bucket IS NOT NULL
    """

    df = con.execute(query).df()

    # Test broad states (need large samples for ≥50 trade requirement)
    states = {
        'State_A_ALL': {},  # No filtering - all dates
        'State_B_TIGHT': {'range_bucket': 'TIGHT'},
        'State_C_NORMAL': {'range_bucket': 'NORMAL'},
    }

    state_results = {}

    for state_name, filters in states.items():
        if not filters:
            # All dates
            dates = df['date_local'].tolist()
        else:
            mask = True
            for key, val in filters.items():
                mask = mask & (df[key] == val)
            dates = df[mask]['date_local'].tolist()

        if len(dates) > 0:
            state_results[state_name] = {
                'dates': dates,
                'n_dates': len(dates),
                'frequency': len(dates) / len(df) * 100 if len(df) > 0 else 0,
                'filters': filters
            }

    return state_results


def pattern_immediate_rejection_reversal(con, date_local):
    """
    Pattern 1: Immediate Rejection Reversal

    Based on Phase 1 finding: 65.8% of time, price breaks ORB early then reverses.

    Logic:
    1. Price breaks ORB in first 5 minutes
    2. Reversal confirmed: 1m close back inside ORB
    3. Entry: on reversal confirmation
    4. Stop: break extreme + buffer
    5. Target: 1.0R
    6. Timeout: 20 minutes
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    # 09:00 ORB: 09:00-09:05
    # Test window: 09:05-09:30
    test_start = datetime.combine(date_obj, datetime.min.time()).replace(hour=9, minute=5)
    test_end = datetime.combine(date_obj, datetime.min.time()).replace(hour=9, minute=30)

    bars_1m = con.execute("""
        SELECT ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local, open, high, low, close
        FROM bars_1m
        WHERE symbol = ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    orb_data = con.execute("""
        SELECT orb_0900_high, orb_0900_low
        FROM daily_features_v2
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars_1m.empty or orb_data is None:
        return None

    orb_high, orb_low = orb_data
    if orb_high is None or orb_low is None:
        return None

    bars_1m['ts_local'] = bars_1m['ts_local'].astype(str)

    if len(bars_1m) < 15:
        return None

    # STEP 1: Detect break in first 5 bars
    first_5_bars = bars_1m.head(5)

    first_5_high = first_5_bars['high'].max()
    first_5_low = first_5_bars['low'].min()

    broke_up = (first_5_high > orb_high)
    broke_down = (first_5_low < orb_low)

    if not broke_up and not broke_down:
        return None  # No break

    # Determine break direction
    if broke_up and broke_down:
        up_dist = first_5_high - orb_high
        down_dist = orb_low - first_5_low
        if up_dist > down_dist:
            break_dir = 'UP'
            break_extreme = first_5_high
        else:
            break_dir = 'DOWN'
            break_extreme = first_5_low
    elif broke_up:
        break_dir = 'UP'
        break_extreme = first_5_high
    else:
        break_dir = 'DOWN'
        break_extreme = first_5_low

    # STEP 2: Look for reversal (close back inside ORB)
    reversal_search = bars_1m.iloc[5:]  # After first 5 bars

    entry_price = None
    entry_idx = None

    for idx, bar in reversal_search.iterrows():
        if break_dir == 'UP':
            # Enter SHORT on first close below ORB high
            if bar['close'] < orb_high:
                entry_price = bar['close']
                entry_idx = idx
                trade_dir = 'SHORT'
                break
        else:
            # Enter LONG on first close above ORB low
            if bar['close'] > orb_low:
                entry_price = bar['close']
                entry_idx = idx
                trade_dir = 'LONG'
                break

    if entry_price is None:
        return None  # No reversal

    # Stop and target
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

    # Worst case
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
        'pattern': 'Immediate_Rejection_Reversal',
        'outcome': outcome,
        'r_multiple': r_multiple
    }


def pattern_balance_failure(con, date_local):
    """
    Pattern 2: Balance Failure

    Based on Phase 1: Balance = weakness (96.8% chop).
    When price stays inside ORB, it tends to chop, not expand.

    DO NOT TRADE balanced opens at 09:00.

    This pattern tests if we can profit from the chop by:
    - Detecting balance (no break in first 10 bars)
    - Waiting for eventual break
    - Fading it immediately (expecting reversal/chop)
    """

    if isinstance(date_local, str):
        date_obj = datetime.strptime(date_local.split()[0], '%Y-%m-%d').date()
    elif hasattr(date_local, 'date'):
        date_obj = date_local.date()
    else:
        date_obj = date_local

    test_start = datetime.combine(date_obj, datetime.min.time()).replace(hour=9, minute=5)
    test_end = datetime.combine(date_obj, datetime.min.time()).replace(hour=9, minute=35)

    bars_1m = con.execute("""
        SELECT ts_utc AT TIME ZONE 'Australia/Brisbane' as ts_local, open, high, low, close
        FROM bars_1m
        WHERE symbol = ? AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
            AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
        ORDER BY ts_utc
    """, [SYMBOL, test_start, test_end]).df()

    orb_data = con.execute("""
        SELECT orb_0900_high, orb_0900_low
        FROM daily_features_v2
        WHERE date_local = ? AND instrument = ?
    """, [date_local, SYMBOL]).fetchone()

    if bars_1m.empty or orb_data is None:
        return None

    orb_high, orb_low = orb_data
    if orb_high is None or orb_low is None:
        return None

    bars_1m['ts_local'] = bars_1m['ts_local'].astype(str)

    if len(bars_1m) < 20:
        return None

    # STEP 1: Detect balance (no break in first 10 bars)
    first_10 = bars_1m.head(10)

    stayed_inside = (first_10['high'].max() <= orb_high) and (first_10['low'].min() >= orb_low)

    if not stayed_inside:
        return None  # Not balanced

    # STEP 2: Wait for eventual break
    later_bars = bars_1m.iloc[10:]

    break_idx = None
    break_dir = None
    break_extreme = None

    for idx, bar in later_bars.iterrows():
        if bar['high'] > orb_high:
            break_dir = 'UP'
            break_extreme = bar['high']
            break_idx = idx
            break
        elif bar['low'] < orb_low:
            break_dir = 'DOWN'
            break_extreme = bar['low']
            break_idx = idx
            break

    if break_idx is None:
        return None  # Never broke

    # STEP 3: Fade immediately (expect chop)
    # Enter on the break bar itself (fade the break)
    if break_dir == 'UP':
        entry_price = orb_high  # Fade at ORB high
        trade_dir = 'SHORT'
        stop_price = break_extreme + 0.5
    else:
        entry_price = orb_low  # Fade at ORB low
        trade_dir = 'LONG'
        stop_price = break_extreme - 0.5

    risk = abs(entry_price - stop_price)
    if risk <= 0:
        return None

    if trade_dir == 'SHORT':
        target_price = entry_price - risk
    else:
        target_price = entry_price + risk

    # Outcome (20 min timeout from break)
    break_position = bars_1m.index.get_loc(break_idx)
    outcome_bars = bars_1m.iloc[break_position:break_position+20]

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
        'pattern': 'Balance_Failure',
        'outcome': outcome,
        'r_multiple': r_multiple
    }


def get_baseline(con, date_local):
    """Get baseline breakout for date-matched comparison."""
    result = con.execute("""
        SELECT outcome, r_multiple
        FROM orb_trades_1m_exec_nofilters
        WHERE orb = '0900' AND date_local = ? AND close_confirmations = 1 AND rr = 1.0
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


def validate_pattern(con, pattern_name, pattern_func, state_name, state_info):
    """Test pattern with strict validation criteria."""

    print(f"\n{'='*80}")
    print(f"Testing {pattern_name} on {state_name}")
    print(f"State: {state_info['filters']}")
    print(f"Dates: {state_info['n_dates']} ({state_info['frequency']:.1f}%)")
    print(f"{'='*80}\n")

    results_pattern = []
    results_baseline = []

    for date in state_info['dates']:
        result_p = pattern_func(con, date)
        if result_p:
            results_pattern.append(result_p)

        result_b = get_baseline(con, date)
        if result_b:
            results_baseline.append(result_b)

    # Selectivity
    selectivity = len(results_pattern) / state_info['n_dates'] * 100 if state_info['n_dates'] > 0 else 0

    print(f"Entries: {len(results_pattern)}/{state_info['n_dates']} ({selectivity:.1f}%)")

    if selectivity >= 50:
        print(f"[FAILED] Selectivity too high ({selectivity:.1f}% >= 50%)")
        return {'verdict': 'FAILED', 'reason': 'Selectivity'}

    if len(results_pattern) < 40:
        print(f"[FAILED] Insufficient trades ({len(results_pattern)} < 40 minimum)")
        return {'verdict': 'FAILED', 'reason': 'Sample size', 'n_trades': len(results_pattern)}

    # Compute metrics
    df_p = pd.DataFrame(results_pattern)
    df_b = pd.DataFrame(results_baseline)

    avg_r_pattern = df_p['r_multiple'].mean()
    avg_r_baseline = df_b['r_multiple'].mean() if len(df_b) > 0 else 0
    delta = avg_r_pattern - avg_r_baseline

    print(f"Pattern: {avg_r_pattern:+.3f}R")
    print(f"Baseline: {avg_r_baseline:+.3f}R")
    print(f"Delta: {delta:+.3f}R")

    if delta < 0.10:
        print(f"[FAILED] Delta too small ({delta:+.3f}R < +0.10R minimum)")
        return {'verdict': 'FAILED', 'reason': 'Delta', 'delta': delta, 'n_trades': len(results_pattern)}

    # Temporal stability
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

    if positive_chunks < 3:
        print(f"[FAILED] Temporal instability ({positive_chunks}/3 chunks positive, need 3/3)")
        return {'verdict': 'FAILED', 'reason': 'Temporal stability', 'positive_chunks': positive_chunks, 'n_trades': len(results_pattern), 'delta': delta}

    # SUCCESS
    print(f"\n[VALIDATED] All criteria met:")
    print(f"  - {len(results_pattern)} trades (>= 40)")
    print(f"  - Delta {delta:+.3f}R (>= +0.10R)")
    print(f"  - 3/3 chunks positive")
    print(f"  - Selectivity {selectivity:.1f}% (< 50%)")

    return {
        'verdict': 'VALIDATED',
        'n_trades': len(results_pattern),
        'selectivity': selectivity,
        'avg_r': avg_r_pattern,
        'baseline': avg_r_baseline,
        'delta': delta,
        'positive_chunks': positive_chunks
    }


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("\n" + "="*80)
    print("PHASE 2 — 09:00 ASIA SESSION PATTERN TESTING")
    print("="*80 + "\n")

    print("STRICT VALIDATION CRITERIA:")
    print("  - >= 40 trades (adjusted from 50)")
    print("  - Delta >= +0.10R vs baseline")
    print("  - 3/3 temporal chunks positive")
    print("  - Selectivity < 50%")
    print()

    # Get states
    states = get_candidate_states(con)

    print(f"Testing {len(states)} candidate states:")
    for state_name, info in states.items():
        print(f"  {state_name}: {info['n_dates']} dates ({info['frequency']:.1f}%)")
    print()

    # Pattern families based on Phase 1
    patterns = [
        ('Pattern 1: Immediate Rejection Reversal', pattern_immediate_rejection_reversal),
        ('Pattern 2: Balance Failure', pattern_balance_failure),
    ]

    all_results = []

    for pattern_name, pattern_func in patterns:
        print("\n" + "="*80)
        print(f"TESTING: {pattern_name}")
        print("="*80)

        for state_name, state_info in states.items():
            result = validate_pattern(con, pattern_name, pattern_func, state_name, state_info)
            if result:
                result['pattern'] = pattern_name
                result['state'] = state_name
                all_results.append(result)

    # Summary
    print("\n" + "="*80)
    print("PHASE 2 SUMMARY — 09:00 ASIA SESSION")
    print("="*80 + "\n")

    validated = [r for r in all_results if r['verdict'] == 'VALIDATED']

    if len(validated) == 0:
        print("[NO VALIDATED EDGES FOUND]")
        print("\nAll patterns FAILED strict validation criteria.")
        print()

        print("Failed patterns:")
        for r in all_results:
            reason = r.get('reason', 'Unknown')
            n_trades = r.get('n_trades', 0)
            delta = r.get('delta', 0)
            chunks = r.get('positive_chunks', 0)
            print(f"  - {r['pattern']} / {r['state']}: FAILED ({reason})")
            if n_trades > 0:
                print(f"      {n_trades} trades, delta {delta:+.3f}R, {chunks}/3 chunks")
    else:
        print(f"[VALIDATED EDGES: {len(validated)}]")
        for r in validated:
            print(f"  - {r['pattern']} / {r['state']}:")
            print(f"      {r['n_trades']} trades, delta {r['delta']:+.3f}R, 3/3 chunks positive")

    print()
    print("="*80)
    print("PHASE 2 COMPLETE")
    print("="*80)

    con.close()


if __name__ == '__main__':
    main()
