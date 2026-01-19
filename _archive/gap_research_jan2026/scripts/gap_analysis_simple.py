"""
Simple Gap Analysis - Quick Research for MGC Futures

Focus: 60+ minute time gaps with immediate continuation
"""

import duckdb
import pandas as pd
import numpy as np

print("Gap Analysis - MGC Futures")
print("="*60)

# Connect with read-only mode to avoid lock
conn = duckdb.connect(r"C:\Users\sydne\OneDrive\myprojectx\gold.db", read_only=True)

print("\n1. Loading 1-minute bars...")
df = conn.execute("""
    SELECT ts_utc, open, high, low, close
    FROM bars_1m
    WHERE symbol = 'MGC'
        AND ts_utc >= '2024-01-01'
    ORDER BY ts_utc
""").fetchdf()

print(f"   Loaded {len(df):,} bars from {df['ts_utc'].min()} to {df['ts_utc'].max()}")

print("\n2. Detecting gaps (60+ minute breaks)...")
df['time_diff_min'] = pd.to_datetime(df['ts_utc']).diff().dt.total_seconds() / 60
df['prev_close'] = df['close'].shift(1)

gaps = df[df['time_diff_min'] > 60].copy()
gaps['gap_size'] = gaps['open'] - gaps['prev_close']
gaps['gap_dir'] = np.where(gaps['gap_size'] > 0, 1, -1)  # 1=long, -1=short

print(f"   Found {len(gaps)} gaps")
print(f"   UP: {(gaps['gap_dir'] == 1).sum()} | DOWN: {(gaps['gap_dir'] == -1).sum()}")
print(f"   Avg gap: {gaps['gap_size'].abs().mean():.3f}")

if len(gaps) < 30:
    print(f"\n❌ Insufficient data: only {len(gaps)} gaps (need 30+)")
    conn.close()
    exit(0)

print("\n3. Testing gap continuation (immediate entry, gap midpoint stop, 2R target)...")

results = []

for idx, gap_row in gaps.iterrows():
    # Entry setup
    entry_time = gap_row['ts_utc']
    entry_price = gap_row['open']
    direction = gap_row['gap_dir']

    # Stop at gap midpoint
    stop_price = (gap_row['prev_close'] + gap_row['open']) / 2
    stop_dist = abs(entry_price - stop_price)

    if stop_dist == 0:
        continue

    # Target at 2R
    target_price = entry_price + direction * stop_dist * 2.0

    # Get next 1000 bars (enough for most trades)
    future = df[df['ts_utc'] > entry_time].head(1000)

    if len(future) == 0:
        continue

    # Check for stop/target hit
    exit_time = None
    exit_price = None
    pnl_r = None

    for fidx, fbar in future.iterrows():
        if direction == 1:  # Long
            if fbar['low'] <= stop_price:
                exit_time = fbar['ts_utc']
                exit_price = stop_price
                pnl_r = -1.0
                break
            if fbar['high'] >= target_price:
                exit_time = fbar['ts_utc']
                exit_price = target_price
                pnl_r = 2.0
                break
        else:  # Short
            if fbar['high'] >= stop_price:
                exit_time = fbar['ts_utc']
                exit_price = stop_price
                pnl_r = -1.0
                break
            if fbar['low'] <= target_price:
                exit_time = fbar['ts_utc']
                exit_price = target_price
                pnl_r = 2.0
                break

    # If no exit, close at last bar
    if exit_time is None:
        exit_time = future.iloc[-1]['ts_utc']
        exit_price = future.iloc[-1]['close']
        pnl_r = (exit_price - entry_price) / stop_dist * direction

    results.append({
        'entry_time': entry_time,
        'entry_price': entry_price,
        'exit_time': exit_time,
        'exit_price': exit_price,
        'pnl_r': pnl_r,
        'direction': 'LONG' if direction == 1 else 'SHORT',
        'gap_size': gap_row['gap_size']
    })

trades = pd.DataFrame(results)

print(f"\n4. Results:")
print(f"   Total trades: {len(trades)}")
print(f"   Wins: {(trades['pnl_r'] > 0).sum()} ({(trades['pnl_r'] > 0).sum()/len(trades):.1%})")
print(f"   Losses: {(trades['pnl_r'] < 0).sum()} ({(trades['pnl_r'] < 0).sum()/len(trades):.1%})")
print(f"   Average R: {trades['pnl_r'].mean():.3f}")
print(f"   Median R: {trades['pnl_r'].median():.3f}")
print(f"   Total R: {trades['pnl_r'].sum():.2f}")

# IS/OOS split
trades['entry_date'] = pd.to_datetime(trades['entry_time']).dt.date
split_date = sorted(trades['entry_date'].unique())[int(len(trades['entry_date'].unique()) * 0.7)]

is_trades = trades[trades['entry_date'] < split_date]
oos_trades = trades[trades['entry_date'] >= split_date]

print(f"\n5. In-Sample / Out-of-Sample (split: {split_date}):")
print(f"\n   IN-SAMPLE ({len(is_trades)} trades):")
print(f"     Win rate: {(is_trades['pnl_r'] > 0).sum()/len(is_trades):.1%}")
print(f"     Avg R: {is_trades['pnl_r'].mean():.3f}")
print(f"     Total R: {is_trades['pnl_r'].sum():.2f}")

print(f"\n   OUT-OF-SAMPLE ({len(oos_trades)} trades):")
print(f"     Win rate: {(oos_trades['pnl_r'] > 0).sum()/len(oos_trades):.1%}")
print(f"     Avg R: {oos_trades['pnl_r'].mean():.3f}")
print(f"     Total R: {oos_trades['pnl_r'].sum():.2f}")

# Verdict
print(f"\n6. VERDICT:")
if is_trades['pnl_r'].mean() > 0 and oos_trades['pnl_r'].mean() > 0:
    print("   ✅ EDGE FOUND: Both IS and OOS show positive expectancy")
    print(f"   Strategy: 60min gap, immediate entry, midpoint stop, 2R target")
else:
    print("   ❌ NO EDGE: Strategy failed IS/OOS validation")
    if is_trades['pnl_r'].mean() <= 0:
        print("      IS expectancy is negative or zero")
    if oos_trades['pnl_r'].mean() <= 0:
        print("      OOS expectancy is negative or zero")

# Save
trades.to_csv(r"C:\Users\sydne\OneDrive\myprojectx\gap_analysis_trades.csv", index=False)
print(f"\n7. Saved trades to: gap_analysis_trades.csv")

conn.close()
print("\n" + "="*60)
print("Analysis complete")
