"""
Automated replay analysis for 0030 strongest state.

Programmatically analyzes all 11 dates using execution hypothesis rules.
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Dates to analyze
DATES = [
    "20260109",
    "20251231",
    "20250919",
    "20250903",
    "20250828",
    "20250805",
    "20250724",
    "20250722",
    "20250717",
    "20250313",
    "20250225"
]

def analyze_date(date_str):
    """Analyze single date using execution hypothesis."""

    # Load data
    try:
        bars_1m = pd.read_csv(f'replay_0030_{date_str}_1m.csv')
        bars_5m = pd.read_csv(f'replay_0030_{date_str}_5m.csv')
    except FileNotFoundError:
        return None

    result = {
        'date': date_str,
        'invalidation_check': 'NO',
        'reaction_pattern': 'NONE',
        'entry_triggered': 'NO',
        'entry_price': None,
        'stop_price': None,
        'outcome_60m': None,
        'r_multiple': None,
        'notes': ''
    }

    # Get ORB boundaries (00:30-00:35 bars)
    orb_bars = bars_5m[bars_5m['ts_local'].str.contains('00:30|00:35')]
    if orb_bars.empty:
        result['notes'] = 'No ORB data'
        return result

    orb_high = orb_bars['high'].max()
    orb_low = orb_bars['low'].min()
    orb_size = orb_high - orb_low

    # STEP 1: INVALIDATION CHECK (00:30-00:40)
    # Check first 10 minutes after ORB start for strong DOWN drive
    initial_bars_1m = bars_1m[bars_1m['ts_local'].str.contains('00:30|00:31|00:32|00:33|00:34|00:35|00:36|00:37|00:38|00:39')]

    if not initial_bars_1m.empty:
        initial_low = initial_bars_1m['low'].min()
        initial_high = initial_bars_1m['high'].max()
        initial_close = initial_bars_1m.iloc[-1]['close']

        # Strong DOWN drive = close near low AND moved down significantly
        range_initial = initial_high - initial_low
        close_position = (initial_close - initial_low) / range_initial if range_initial > 0 else 0.5

        down_move = orb_high - initial_low

        # Invalidation: close in bottom 30% AND down move > 50 ticks
        if close_position < 0.3 and down_move > 5.0:
            result['invalidation_check'] = 'YES'
            result['notes'] = f'Invalidated: DOWN {down_move:.1f} ticks, close at {close_position*100:.0f}%'
            return result

    # STEP 2: REACTION PATTERN ANALYSIS (00:30-00:45)
    reaction_bars_1m = bars_1m[bars_1m['ts_local'].str.contains('00:3[0-9]|00:4[0-4]')]

    if not reaction_bars_1m.empty:
        # Calculate wick ratios
        reaction_bars_1m = reaction_bars_1m.copy()
        reaction_bars_1m['body'] = abs(reaction_bars_1m['close'] - reaction_bars_1m['open'])
        reaction_bars_1m['upper_wick'] = reaction_bars_1m['high'] - reaction_bars_1m[['open', 'close']].max(axis=1)
        reaction_bars_1m['lower_wick'] = reaction_bars_1m[['open', 'close']].min(axis=1) - reaction_bars_1m['low']
        reaction_bars_1m['total_wick'] = reaction_bars_1m['upper_wick'] + reaction_bars_1m['lower_wick']
        reaction_bars_1m['bar_range'] = reaction_bars_1m['high'] - reaction_bars_1m['low']
        reaction_bars_1m['wick_pct'] = reaction_bars_1m['total_wick'] / reaction_bars_1m['bar_range']

        avg_wick_pct = reaction_bars_1m['wick_pct'].mean()
        reaction_high = reaction_bars_1m['high'].max()
        reaction_low = reaction_bars_1m['low'].min()
        reaction_range = reaction_high - reaction_low

        # Pattern A: Absorption/Stall (high wicks, compression)
        if avg_wick_pct > 0.6:
            result['reaction_pattern'] = 'A'
            result['notes'] += f'Absorption: {avg_wick_pct*100:.0f}% avg wicks. '
        # Pattern B: Fake Downside (tests ORB low, reclaims quickly)
        elif reaction_low <= orb_low + 1.0 and reaction_high >= orb_high - 2.0:
            result['reaction_pattern'] = 'B'
            result['notes'] += f'Fake DN: tested {orb_low:.2f}, reclaimed. '
        # Pattern C: Delayed Lift (chop then expansion)
        else:
            # Check if later bars show expansion
            late_bars = bars_1m[bars_1m['ts_local'].str.contains('00:4[5-9]|00:5[0-4]')]
            if not late_bars.empty:
                late_high = late_bars['high'].max()
                if late_high > reaction_high + 3.0:
                    result['reaction_pattern'] = 'C'
                    result['notes'] += f'Delayed lift: expansion at {late_high:.2f}. '

    # STEP 3: ENTRY TRIGGER (5m close above 5m range high during reaction)
    # Define "5m range high" as the highest 5m bar during pre-ORB + ORB window
    pre_orb_5m = bars_5m[bars_5m['ts_local'].str.contains('00:1[5-9]|00:2[0-9]|00:3[0-4]')]
    if not pre_orb_5m.empty:
        range_high_5m = pre_orb_5m['high'].max()
    else:
        range_high_5m = orb_high

    # Check 00:40-00:50 for 5m close above range_high_5m
    entry_window_5m = bars_5m[bars_5m['ts_local'].str.contains('00:40|00:45|00:50')]

    entry_price = None
    entry_bar_time = None

    for idx, bar in entry_window_5m.iterrows():
        if bar['close'] > range_high_5m:
            entry_price = bar['close']
            entry_bar_time = bar['ts_local']
            result['entry_triggered'] = 'YES'
            result['entry_price'] = entry_price
            result['notes'] += f'Entry at {entry_price:.2f} ({entry_bar_time}). '
            break

    if result['entry_triggered'] == 'NO':
        result['notes'] += f'No entry: never closed above {range_high_5m:.2f}. '
        return result

    # STEP 4: STOP PLACEMENT (structural low)
    # Use reaction window low as structural stop
    if not reaction_bars_1m.empty:
        stop_price = reaction_low - 0.5  # 5 ticks below reaction low
        result['stop_price'] = stop_price
    else:
        stop_price = orb_low - 1.0
        result['stop_price'] = stop_price

    # STEP 5: OUTCOME ANALYSIS (60 minutes from entry)
    # Extract entry bar time
    entry_time_parts = entry_bar_time.split()[1].split(':')
    entry_hour = int(entry_time_parts[0])
    entry_min = int(entry_time_parts[1])

    # 60 minutes from entry
    exit_hour = entry_hour + 1
    if entry_min >= 30:
        exit_hour += 1
        exit_min = entry_min - 30
    else:
        exit_min = entry_min + 30

    # Get bars from entry to exit window
    outcome_bars_1m = bars_1m[bars_1m['ts_local'].str.contains(f'{entry_hour:02d}:{entry_min:02d}')]

    # Simplified: check next 60 minutes of data
    entry_idx = None
    for idx, bar in bars_1m.iterrows():
        if entry_bar_time.split()[1][:5] in bar['ts_local']:
            entry_idx = idx
            break

    if entry_idx is not None:
        # Get next 60 bars (60 minutes)
        outcome_bars = bars_1m.iloc[entry_idx:entry_idx+60]

        if not outcome_bars.empty:
            max_profit = outcome_bars['high'].max() - entry_price
            max_loss = entry_price - outcome_bars['low'].min()

            # Check if stop hit
            stop_hit = (outcome_bars['low'].min() <= stop_price)

            # Target: +20-30 ticks = +2.0-3.0 price points
            target_hit = (max_profit >= 2.5)

            # Calculate R
            risk = entry_price - stop_price
            if risk <= 0:
                risk = 1.0  # Default if stop calculation failed

            if stop_hit and target_hit:
                # Worst case: assume stop hit first
                result['outcome_60m'] = 'LOSS'
                result['r_multiple'] = -1.0
                result['notes'] += f'Both hit (worst-case=LOSS). '
            elif stop_hit:
                result['outcome_60m'] = 'LOSS'
                actual_loss = max_loss
                result['r_multiple'] = -actual_loss / risk
                result['notes'] += f'Stop hit: -{actual_loss:.1f} ticks. '
            elif target_hit:
                result['outcome_60m'] = 'WIN'
                result['r_multiple'] = max_profit / risk
                result['notes'] += f'Target hit: +{max_profit:.1f} ticks. '
            else:
                # Timeout: exit at close of 60th bar
                exit_price = outcome_bars.iloc[-1]['close']
                pnl = exit_price - entry_price
                result['outcome_60m'] = 'TIMEOUT'
                result['r_multiple'] = pnl / risk
                result['notes'] += f'Timeout: {pnl:+.1f} ticks. '
        else:
            result['notes'] += 'Insufficient bars for outcome. '

    return result


def main():
    print("="*100)
    print("AUTOMATED REPLAY ANALYSIS - 0030 STRONGEST STATE")
    print("="*100)
    print()
    print("State: NORMAL + D_MED + HIGH close + HIGH impulse")
    print("Expected: 70% UP-favored, +44.5 tick median tail skew")
    print()

    results = []

    for date_str in DATES:
        print(f"Analyzing {date_str}...", end=" ")
        result = analyze_date(date_str)

        if result is not None:
            results.append(result)
            print(f"[{result['reaction_pattern']}] Entry: {result['entry_triggered']} | Outcome: {result['outcome_60m']}")
        else:
            print("[SKIP]")

    print()
    print("="*100)
    print("INDIVIDUAL RESULTS")
    print("="*100)
    print()

    df = pd.DataFrame(results)

    # Format output
    print(f"{'Date':<12} {'Invalid':<8} {'Pattern':<8} {'Entry':<8} {'Price':>9} {'Stop':>9} {'Outcome':<8} {'R':>7}")
    print("-"*100)

    for _, row in df.iterrows():
        entry_str = f"{row['entry_price']:.2f}" if row['entry_price'] else "-"
        stop_str = f"{row['stop_price']:.2f}" if row['stop_price'] else "-"
        r_str = f"{row['r_multiple']:+.2f}R" if row['r_multiple'] is not None else "-"

        print(f"{row['date']:<12} {row['invalidation_check']:<8} {row['reaction_pattern']:<8} {row['entry_triggered']:<8} {entry_str:>9} {stop_str:>9} {row['outcome_60m'] or '-':<8} {r_str:>7}")

    print()
    print("="*100)
    print("SUMMARY STATISTICS")
    print("="*100)
    print()

    total_dates = len(df)
    invalidated = len(df[df['invalidation_check'] == 'YES'])
    valid_dates = total_dates - invalidated

    print(f"Total dates analyzed:     {total_dates}")
    print(f"Invalidated (no trade):   {invalidated} ({invalidated/total_dates*100:.1f}%)")
    print(f"Valid for analysis:       {valid_dates} ({valid_dates/total_dates*100:.1f}%)")
    print()

    # Pattern analysis
    pattern_counts = df['reaction_pattern'].value_counts()
    print("Reaction patterns observed:")
    for pattern, count in pattern_counts.items():
        print(f"  {pattern}: {count} ({count/total_dates*100:.1f}%)")
    print()

    # Entry analysis
    entries = df[df['entry_triggered'] == 'YES']
    entry_rate = len(entries) / valid_dates * 100 if valid_dates > 0 else 0

    print(f"Entry triggers:           {len(entries)}/{valid_dates} ({entry_rate:.1f}%)")
    print()

    if len(entries) > 0:
        # Outcome analysis
        outcomes = entries['outcome_60m'].value_counts()
        wins = outcomes.get('WIN', 0)
        losses = outcomes.get('LOSS', 0)
        timeouts = outcomes.get('TIMEOUT', 0)

        win_rate = wins / len(entries) * 100 if len(entries) > 0 else 0

        print("Trade outcomes:")
        print(f"  WIN:     {wins} ({wins/len(entries)*100:.1f}%)")
        print(f"  LOSS:    {losses} ({losses/len(entries)*100:.1f}%)")
        print(f"  TIMEOUT: {timeouts} ({timeouts/len(entries)*100:.1f}%)")
        print()

        # R-multiple analysis
        r_values = entries[entries['r_multiple'].notna()]['r_multiple']

        if len(r_values) > 0:
            avg_r = r_values.mean()
            total_r = r_values.sum()

            print(f"R-multiple statistics:")
            print(f"  Average R:  {avg_r:+.3f}R")
            print(f"  Total R:    {total_r:+.2f}R")
            print(f"  Best trade: {r_values.max():+.2f}R")
            print(f"  Worst trade: {r_values.min():+.2f}R")
            print()

            # Expectancy
            win_trades = entries[entries['outcome_60m'] == 'WIN']['r_multiple']
            loss_trades = entries[entries['outcome_60m'] == 'LOSS']['r_multiple']

            if len(win_trades) > 0 and len(loss_trades) > 0:
                avg_win = win_trades.mean()
                avg_loss = loss_trades.mean()

                expectancy = (win_rate/100 * avg_win) + ((100-win_rate)/100 * avg_loss)

                print(f"Expectancy analysis:")
                print(f"  Win rate:   {win_rate:.1f}%")
                print(f"  Avg win:    {avg_win:+.2f}R")
                print(f"  Avg loss:   {avg_loss:+.2f}R")
                print(f"  Expectancy: {expectancy:+.3f}R per trade")
                print()

    # DECISION
    print("="*100)
    print("DECISION CRITERIA")
    print("="*100)
    print()

    observable_patterns = len(df[df['reaction_pattern'] != 'NONE'])
    pattern_pct = observable_patterns / total_dates * 100

    thresholds = {
        'Observable patterns': (observable_patterns, total_dates, 60.0, pattern_pct),
        'Entry triggers': (len(entries), valid_dates, 45.0, entry_rate),
        'Win rate': (wins, len(entries) if len(entries) > 0 else 1, 50.0, win_rate if len(entries) > 0 else 0),
        'Avg R-multiple': (avg_r if len(entries) > 0 else 0, None, 0.15, None)
    }

    print(f"{'Criterion':<20} {'Actual':<20} {'Threshold':<15} {'Status':<10}")
    print("-"*100)

    all_pass = True

    for criterion, (actual, total, threshold, pct) in thresholds.items():
        if criterion == 'Avg R-multiple':
            actual_str = f"{actual:+.3f}R"
            threshold_str = f"+0.15R"
            status = "PASS" if actual >= threshold else "FAIL"
        else:
            if total is not None:
                actual_str = f"{actual}/{total} ({pct:.1f}%)"
            else:
                actual_str = f"{actual}"
            threshold_str = f">{threshold:.0f}%"
            status = "PASS" if pct >= threshold else "FAIL"

        print(f"{criterion:<20} {actual_str:<20} {threshold_str:<15} {status:<10}")

        if status == "FAIL":
            all_pass = False

    print()
    print("="*100)
    print("FINAL VERDICT")
    print("="*100)
    print()

    if all_pass:
        print("[PASS] ALL THRESHOLDS MET")
        print()
        print("RECOMMENDATION: Code full backtest with hard-coded rules")
        print()
        print("Next steps:")
        print("  1. Build backtest_0030_liquidity_reaction.py")
        print("  2. Test execution hypothesis on full 30-date sample")
        print("  3. Measure if positive expectancy holds")
    else:
        print("[FAIL] THRESHOLDS NOT MET")
        print()
        print("RECOMMENDATION: Kill this state, test next option")
        print()
        print("Next options:")
        print("  1. Test 2300 TIGHT + D_SMALL + MID impulse (63.6% UP, +30 tick skew)")
        print("  2. Test 1100 WIDE + D_MED (different profile)")
        print("  3. Abandon edge state approach entirely")

    print()

    # Save results
    df.to_csv('replay_0030_automated_results.csv', index=False)
    print("Results saved to: replay_0030_automated_results.csv")
    print()


if __name__ == '__main__':
    main()
