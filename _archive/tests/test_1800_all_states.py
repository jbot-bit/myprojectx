"""
Test all 3 discovered 1800 ORB states with date-matched comparison.

State #1: NORMAL + D_SMALL + HIGH + MID (28 days, 71.4% UP, +3.2 ticks) - TESTED: +0.480R
State #2: NORMAL + D_SMALL + MID + MID (33 days, 60.6% UP, +2.8 ticks) - TESTING NOW
State #3: NORMAL + D_SMALL + MID + LOW (47 days, 55.3% UP, +2.3 ticks) - TESTING NOW
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
        'impulse_bucket': 'MID',
        'expected_days': 28,
        'expected_skew': 71.4,
        'expected_tail': 3.2
    },
    {
        'name': 'State #2',
        'range_bucket': 'NORMAL',
        'disp_bucket': 'D_SMALL',
        'close_pos_bucket': 'MID',
        'impulse_bucket': 'MID',
        'expected_days': 33,
        'expected_skew': 60.6,
        'expected_tail': 2.8
    },
    {
        'name': 'State #3',
        'range_bucket': 'NORMAL',
        'disp_bucket': 'D_SMALL',
        'close_pos_bucket': 'MID',
        'impulse_bucket': 'LOW',
        'expected_days': 47,
        'expected_skew': 55.3,
        'expected_tail': 2.3
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
    """Test liquidity reaction approach on single date."""

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
        'entry_triggered': 'NO',
        'entry_price': None,
        'stop_price': None,
        'outcome': None,
        'r_multiple': None
    }

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
            return result

    # Reaction pattern
    reaction_bars = bars_1m[bars_1m['ts_local'].str.contains('18:0[0-9]|18:1[0-4]')]

    if not reaction_bars.empty:
        reaction_low = reaction_bars['low'].min()
    else:
        reaction_low = orb_low

    # Entry trigger
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

    # Stop
    stop_price = reaction_low - 0.5
    result['stop_price'] = stop_price

    # Outcome
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

    result = con.execute("""
        SELECT
            orb,
            date_local,
            outcome,
            r_multiple
        FROM orb_trades_1m_exec_nofilters
        WHERE orb = '1800'
            AND date_local = ?
            AND close_confirmations = 1
            AND rr = 1.5
        LIMIT 1
    """, [date_local]).fetchone()

    if result is None:
        return None

    orb, date, outcome, r_mult = result

    return {
        'date': str(date),
        'outcome': outcome,
        'r_multiple': r_mult
    }


def test_state(con, state):
    """Test single state with date-matched comparison."""

    print("="*80)
    print(f"TESTING: {state['name']}")
    print("="*80)
    print()
    print(f"State: {state['range_bucket']} + {state['disp_bucket']} + {state['close_pos_bucket']} + {state['impulse_bucket']}")
    print(f"Expected: {state['expected_days']} days, {state['expected_skew']:.1f}% UP, {state['expected_tail']:+.1f} tick skew")
    print()

    # Get dates
    state_dates = get_state_dates(con, state)
    print(f"Actual dates found: {len(state_dates)}")

    if len(state_dates) == 0:
        print("[ERROR] No dates found")
        print()
        return None

    print()

    # Test both methods
    results_reaction = []
    results_baseline = []

    for date in state_dates:
        result_a = test_liquidity_reaction(con, date)
        if result_a:
            results_reaction.append(result_a)

        result_b = test_baseline_breakout(con, date)
        if result_b:
            results_baseline.append(result_b)

    # Analyze
    df_reaction = pd.DataFrame(results_reaction)
    entries_reaction = df_reaction[df_reaction['entry_triggered'] == 'YES']

    df_baseline = pd.DataFrame(results_baseline)

    # Reaction stats
    if len(entries_reaction) > 0:
        r_values = entries_reaction[entries_reaction['r_multiple'].notna()]['r_multiple']
        avg_r_reaction = r_values.mean()
        total_r_reaction = r_values.sum()
        wins_reaction = (entries_reaction['outcome'] == 'WIN').sum()
        losses_reaction = (entries_reaction['outcome'] == 'LOSS').sum()
        wr_reaction = wins_reaction / len(entries_reaction) * 100 if len(entries_reaction) > 0 else 0
    else:
        avg_r_reaction = 0.0
        total_r_reaction = 0.0
        wins_reaction = 0
        losses_reaction = 0
        wr_reaction = 0.0

    # Baseline stats
    if len(df_baseline) > 0:
        avg_r_baseline = df_baseline['r_multiple'].mean()
        total_r_baseline = df_baseline['r_multiple'].sum()
        wins_baseline = (df_baseline['outcome'] == 'WIN').sum()
        losses_baseline = (df_baseline['outcome'] == 'LOSS').sum()
        wr_baseline = wins_baseline / len(df_baseline) * 100
    else:
        avg_r_baseline = 0.0
        total_r_baseline = 0.0
        wins_baseline = 0
        losses_baseline = 0
        wr_baseline = 0.0

    # Print results
    print(f"LIQUIDITY REACTION:")
    print(f"  Entries: {len(entries_reaction)}/{len(df_reaction)} ({len(entries_reaction)/len(df_reaction)*100:.1f}%)")
    print(f"  Win rate: {wr_reaction:.1f}% ({wins_reaction}W-{losses_reaction}L)")
    print(f"  Avg R: {avg_r_reaction:+.3f}R")
    print(f"  Total R: {total_r_reaction:+.2f}R")
    print()

    print(f"BASELINE BREAKOUT (same dates):")
    print(f"  Trades: {len(df_baseline)}")
    print(f"  Win rate: {wr_baseline:.1f}% ({wins_baseline}W-{losses_baseline}L)")
    print(f"  Avg R: {avg_r_baseline:+.3f}R")
    print(f"  Total R: {total_r_baseline:+.2f}R")
    print()

    delta_r = avg_r_reaction - avg_r_baseline

    print(f"DELTA: {delta_r:+.3f}R (Reaction - Baseline)")
    print()

    # Verdict
    if delta_r > 0.10:
        verdict = "PASS - Reaction WINS"
    elif delta_r > 0.03:
        verdict = "MARGINAL - Slight edge"
    elif delta_r > -0.03:
        verdict = "NEUTRAL - Similar"
    else:
        verdict = "FAIL - Baseline better"

    print(f"VERDICT: {verdict}")
    print()

    return {
        'state_name': state['name'],
        'state_label': f"{state['range_bucket']}+{state['disp_bucket']}+{state['close_pos_bucket']}+{state['impulse_bucket']}",
        'n_dates': len(state_dates),
        'reaction_entries': len(entries_reaction),
        'reaction_wr': wr_reaction,
        'reaction_avg_r': avg_r_reaction,
        'reaction_total_r': total_r_reaction,
        'baseline_trades': len(df_baseline),
        'baseline_wr': wr_baseline,
        'baseline_avg_r': avg_r_baseline,
        'baseline_total_r': total_r_baseline,
        'delta_r': delta_r,
        'verdict': verdict
    }


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print()
    print("="*80)
    print("1800 ORB - TESTING ALL 3 DISCOVERED STATES")
    print("="*80)
    print()
    print("Comparing Liquidity Reaction vs Baseline Breakout (date-matched)")
    print()

    summary = []

    # Test State #1 (already tested, just for completeness)
    print("[State #1 already tested: +0.480R vs -0.018R, delta +0.498R]")
    summary.append({
        'state_name': 'State #1',
        'state_label': 'NORMAL+D_SMALL+HIGH+MID',
        'n_dates': 28,
        'reaction_entries': 15,
        'reaction_wr': 60.0,
        'reaction_avg_r': 0.480,
        'reaction_total_r': 7.21,
        'baseline_trades': 28,
        'baseline_wr': 39.3,
        'baseline_avg_r': -0.018,
        'baseline_total_r': -0.50,
        'delta_r': 0.498,
        'verdict': 'PASS - Reaction WINS'
    })
    print()

    # Test State #2
    result_2 = test_state(con, STATES[1])
    if result_2:
        summary.append(result_2)

    # Test State #3
    result_3 = test_state(con, STATES[2])
    if result_3:
        summary.append(result_3)

    # Summary table
    print()
    print("="*80)
    print("SUMMARY: ALL 3 STATES")
    print("="*80)
    print()

    df_summary = pd.DataFrame(summary)

    print(f"{'State':<15} {'Dates':<7} {'R Entries':<10} {'R Avg R':<10} {'B Avg R':<10} {'Delta':<10} {'Verdict':<20}")
    print("-"*80)

    for _, row in df_summary.iterrows():
        print(f"{row['state_name']:<15} {row['n_dates']:<7} {row['reaction_entries']:<10} {row['reaction_avg_r']:+.3f}R    {row['baseline_avg_r']:+.3f}R    {row['delta_r']:+.3f}R    {row['verdict']:<20}")

    print()
    print("="*80)
    print("COMBINED POTENTIAL")
    print("="*80)
    print()

    # Filter passing states
    passing = df_summary[df_summary['delta_r'] > 0.10]

    if len(passing) > 0:
        total_entries = passing['reaction_entries'].sum()
        total_r = passing['reaction_total_r'].sum()
        weighted_avg_r = total_r / total_entries if total_entries > 0 else 0

        print(f"Passing states: {len(passing)}")
        print(f"Total dates: {passing['n_dates'].sum()}")
        print(f"Total entries: {total_entries}")
        print(f"Combined total R: {total_r:+.2f}R")
        print(f"Weighted avg R: {weighted_avg_r:+.3f}R")
        print()

        print("RECOMMENDATION:")
        if len(passing) == 3:
            print("  Trade ALL 3 states with Liquidity Reaction approach")
        elif len(passing) == 2:
            print(f"  Trade {passing.iloc[0]['state_name']} and {passing.iloc[1]['state_name']} with Liquidity Reaction")
        else:
            print(f"  Trade {passing.iloc[0]['state_name']} only with Liquidity Reaction")

        print()
        print(f"Expected annual performance:")
        print(f"  ~{total_entries} trades/year (assuming ~{passing['n_dates'].sum()} state occurrences/year)")
        print(f"  {weighted_avg_r:+.3f}R avg × {total_entries} trades = {total_r:+.1f}R/year")
        print(f"  At 1R = $100: {total_r * 100:+.0f}$/year")
        print(f"  At 1R = $200: {total_r * 200:+.0f}$/year")

    else:
        print("No states passed threshold (delta > +0.10R)")
        print("RECOMMENDATION: Stick with State #1 only (+0.480R)")

    print()

    # Save summary
    df_summary.to_csv('1800_all_states_summary.csv', index=False)
    print("Summary saved to: 1800_all_states_summary.csv")
    print()

    con.close()


if __name__ == '__main__':
    main()
