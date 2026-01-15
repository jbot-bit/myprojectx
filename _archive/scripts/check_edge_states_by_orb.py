"""Check which edge states were found for each ORB."""
import pandas as pd

df = pd.read_csv('edge_states_discovered.csv', dtype={'orb_code': str})

print("="*80)
print("EDGE STATES BY ORB")
print("="*80)
print()

# Group by ORB and show best sessions first
for orb in ['1000', '1800', '1100', '0900', '2300', '0030']:
    states = df[df['orb_code'] == orb].sort_values('median_tail_skew_60m', key=abs, ascending=False)

    if len(states) > 0:
        print(f"{orb} ORB: {len(states)} edge states found")
        print("-"*80)

        for _, s in states.iterrows():
            direction = "UP" if s['sign_skew_60m'] > 50 else "DN"
            print(f"  {s['state_label']}")
            print(f"    Sample: {s['n_days']} days ({s['frequency_pct']:.1f}%)")
            print(f"    Direction: {direction}-favored ({s['sign_skew_60m']:.1f}%)")
            print(f"    Tail skew: {s['median_tail_skew_60m']:+.1f} ticks")
            print()
    else:
        print(f"{orb} ORB: No edge states found")
        print()

print()
print("="*80)
print("ORB BREAKOUT PERFORMANCE (for reference)")
print("="*80)
print()
print("BEST:")
print("  1000: +0.094R avg (breakout backtest)")
print("  1800: +0.062R avg (breakout backtest)")
print("  1100: +0.006R avg (breakout backtest)")
print()
print("WORST:")
print("  0030: -0.396R avg (breakout backtest) <- WE JUST TESTED THIS")
print("  2300: -0.360R avg (breakout backtest)")
print()
