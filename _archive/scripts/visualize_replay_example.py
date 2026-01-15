"""
Visualize one example date for manual replay analysis.

This creates a text-based visualization of the price action
to help identify reaction patterns.
"""

import pandas as pd
from datetime import datetime

def visualize_bars(date_str):
    """Create text visualization of 1m and 5m bars."""

    # Load data
    bars_1m = pd.read_csv(f'replay_0030_{date_str}_1m.csv')
    bars_5m = pd.read_csv(f'replay_0030_{date_str}_5m.csv')

    print("="*100)
    print(f"MANUAL REPLAY VISUALIZATION - {date_str}")
    print("="*100)
    print()

    # Show 5m bars first (overview)
    print("5-MINUTE BARS (00:15-01:30)")
    print("-"*100)
    print(f"{'Time':<8} {'Open':>8} {'High':>8} {'Low':>8} {'Close':>8} {'Range':>6} {'Notes':<30}")
    print("-"*100)

    for idx, bar in bars_5m.iterrows():
        ts_local = bar['ts_local']
        time_str = ts_local.split()[1][:5]  # Extract HH:MM

        bar_range = bar['high'] - bar['low']

        # Determine bar character (up/down/neutral)
        if bar['close'] > bar['open']:
            bar_type = "UP"
            symbol = "^"
        elif bar['close'] < bar['open']:
            bar_type = "DN"
            symbol = "v"
        else:
            bar_type = "=="
            symbol = "-"

        # Mark ORB window
        notes = ""
        if '00:30' in time_str or '00:35' in time_str:
            notes = "*** ORB WINDOW ***"
        elif '00:40' in time_str or '00:45' in time_str:
            notes = "<- Reaction window"
        elif '00:50' in time_str or '00:55' in time_str or '01:00' in time_str:
            notes = "<- Post-ORB outcome"

        print(f"{time_str:<8} {bar['open']:>8.2f} {bar['high']:>8.2f} {bar['low']:>8.2f} {bar['close']:>8.2f} {bar_range:>6.2f} {symbol} {notes}")

    print()
    print()

    # Show 1m bars for critical window (00:30-00:50)
    print("1-MINUTE BARS (00:30-00:50 - Critical reaction window)")
    print("-"*100)
    print(f"{'Time':<8} {'Open':>8} {'High':>8} {'Low':>8} {'Close':>8} {'Range':>6} {'Wick':>6}")
    print("-"*100)

    for idx, bar in bars_1m.iterrows():
        ts_local = bar['ts_local']
        time_str = ts_local.split()[1][:5]  # Extract HH:MM

        # Only show 00:30-00:50
        if time_str < '00:30' or time_str >= '00:50':
            continue

        bar_range = bar['high'] - bar['low']

        # Calculate wick ratio
        body = abs(bar['close'] - bar['open'])
        upper_wick = bar['high'] - max(bar['open'], bar['close'])
        lower_wick = min(bar['open'], bar['close']) - bar['low']
        total_wick = upper_wick + lower_wick

        wick_pct = (total_wick / bar_range * 100) if bar_range > 0 else 0

        print(f"{time_str:<8} {bar['open']:>8.2f} {bar['high']:>8.2f} {bar['low']:>8.2f} {bar['close']:>8.2f} {bar_range:>6.2f} {wick_pct:>6.1f}%")

    print()
    print()

    # Summary statistics
    print("SUMMARY STATISTICS")
    print("-"*100)

    orb_bars = bars_5m[(bars_5m['ts_local'].str.contains('00:30')) | (bars_5m['ts_local'].str.contains('00:35'))]
    if not orb_bars.empty:
        orb_high = orb_bars['high'].max()
        orb_low = orb_bars['low'].min()
        orb_size = orb_high - orb_low
        print(f"ORB High:  {orb_high:.2f}")
        print(f"ORB Low:   {orb_low:.2f}")
        print(f"ORB Size:  {orb_size:.2f} ({orb_size * 10:.1f} ticks)")

    print()

    reaction_bars = bars_5m[bars_5m['ts_local'].str.contains('00:40|00:45')]
    if not reaction_bars.empty:
        reaction_high = reaction_bars['high'].max()
        reaction_low = reaction_bars['low'].min()
        reaction_close = reaction_bars['close'].iloc[-1]
        print(f"Reaction window (00:40-00:45):")
        print(f"  High:  {reaction_high:.2f}")
        print(f"  Low:   {reaction_low:.2f}")
        print(f"  Close: {reaction_close:.2f}")

    print()

    post_orb_bars = bars_5m[bars_5m['ts_local'].str.contains('00:50|00:55|01:00')]
    if not post_orb_bars.empty:
        post_high = post_orb_bars['high'].max()
        post_low = post_orb_bars['low'].min()
        print(f"Post-ORB outcome (00:50-01:00):")
        print(f"  Max High: {post_high:.2f}")
        print(f"  Min Low:  {post_low:.2f}")

        if not orb_bars.empty:
            up_move = post_high - orb_high
            dn_move = orb_low - post_low
            print(f"  Up from ORB high: {up_move:.2f} ({up_move * 10:.1f} ticks)")
            print(f"  Dn from ORB low:  {dn_move:.2f} ({dn_move * 10:.1f} ticks)")

    print()
    print("="*100)
    print("ANALYSIS QUESTIONS")
    print("="*100)
    print()
    print("1. INVALIDATION: Strong DOWN drive in first 5-10min? (YES/NO)")
    print("2. REACTION PATTERN: A=Absorption, B=Fake DN, C=Delayed Lift, NONE")
    print("3. ENTRY TRIGGER: Did 5m close ABOVE 5m range high? (YES/NO)")
    print("4. STOP: Where is structural low?")
    print("5. OUTCOME: WIN/LOSS/TIMEOUT (60min from entry)")
    print()

if __name__ == '__main__':
    # Example: Visualize most recent date
    date_str = "20260109"

    print()
    print("Visualizing most recent example: 2026-01-09")
    print()

    visualize_bars(date_str)

    print()
    print("To visualize other dates, modify date_str in the script:")
    print("  20251231, 20250919, 20250903, 20250828, 20250805,")
    print("  20250724, 20250722, 20250717, 20250313, 20250225")
    print()
