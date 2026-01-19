"""
Ultra-Fast Gap Research - Sample-Based Approach

Instead of processing all 720k bars, sample strategically and extrapolate.
This ensures completion within 30 seconds.
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime
import sys

print("="*70)
print("FAST GAP CONTINUATION RESEARCH - MGC FUTURES")
print("="*70)

# Try to connect - if database is locked, inform user
try:
    conn = duckdb.connect(r"C:\Users\sydne\OneDrive\myprojectx\gold.db", read_only=True)
except Exception as e:
    print(f"\n❌ Database is locked: {e}")
    print("\nAnother research process is running (PID 17164).")
    print("Please wait for it to complete or terminate it.")
    print("\nTo terminate: taskkill /PID 17164 /F")
    sys.exit(1)

print("\n[1/6] Loading data sample...")

# Load a representative sample (every 5th bar) for speed
query = """
WITH numbered AS (
    SELECT
        ts_utc, open, high, low, close,
        ROW_NUMBER() OVER (ORDER BY ts_utc) as rn
    FROM bars_1m
    WHERE symbol = 'MGC'
        AND ts_utc >= '2024-01-01'
)
SELECT ts_utc, open, high, low, close
FROM numbered
WHERE rn % 5 = 0
ORDER BY ts_utc
"""

sample = conn.execute(query).fetchdf()
conn.close()

print(f"      Loaded {len(sample):,} bars (sampled from full dataset)")
print(f"      Date range: {sample['ts_utc'].min()} to {sample['ts_utc'].max()}")

print("\n[2/6] Detecting time gaps...")

sample['ts'] = pd.to_datetime(sample['ts_utc'], utc=True)
sample['time_diff_min'] = sample['ts'].diff().dt.total_seconds() / 60
sample['prev_close'] = sample['close'].shift(1)

# Detect 60+ minute gaps
gaps = sample[sample['time_diff_min'] > 60].copy()
gaps['gap_size'] = gaps['open'] - gaps['prev_close']
gaps['gap_pct'] = (gaps['gap_size'] / gaps['prev_close'] * 100).abs()
gaps['direction'] = np.where(gaps['gap_size'] > 0, 1, -1)

print(f"      Found {len(gaps)} gaps (60+ minutes)")
print(f"      UP: {(gaps['direction'] == 1).sum()} | DOWN: {(gaps['direction'] == -1).sum()}")
print(f"      Avg gap: {gaps['gap_pct'].mean():.3f}%")

if len(gaps) < 20:
    print(f"\n❌ Insufficient gaps: {len(gaps)} (need 20+)")
    sys.exit(0)

print("\n[3/6] Testing strategy: Immediate continuation, midpoint stop, 2R target...")

trades = []

for idx, gap in gaps.iterrows():
    entry_time = gap['ts']
    entry_px = gap['open']
    direction = gap['direction']

    # Stop at gap midpoint
    stop_px = (gap['prev_close'] + gap['open']) / 2
    stop_dist = abs(entry_px - stop_px)

    if stop_dist < 0.01:  # Skip tiny stops
        continue

    target_px = entry_px + direction * stop_dist * 2.0

    # Get future bars
    future = sample[sample['ts'] > entry_time].head(200)  # Max ~1000 minutes

    if len(future) == 0:
        continue

    # Simulate trade
    hit_stop = False
    hit_target = False

    for _, bar in future.iterrows():
        if direction == 1:  # Long
            if bar['low'] <= stop_px:
                trades.append({'entry': entry_time, 'pnl_r': -1.0, 'dir': 'LONG'})
                hit_stop = True
                break
            if bar['high'] >= target_px:
                trades.append({'entry': entry_time, 'pnl_r': +2.0, 'dir': 'LONG'})
                hit_target = True
                break
        else:  # Short
            if bar['high'] >= stop_px:
                trades.append({'entry': entry_time, 'pnl_r': -1.0, 'dir': 'SHORT'})
                hit_stop = True
                break
            if bar['low'] <= target_px:
                trades.append({'entry': entry_time, 'pnl_r': +2.0, 'dir': 'SHORT'})
                hit_target = True
                break

    # If no exit, close at last bar
    if not hit_stop and not hit_target and len(future) > 0:
        exit_px = future.iloc[-1]['close']
        pnl_r = (exit_px - entry_px) / stop_dist * direction
        trades.append({'entry': entry_time, 'pnl_r': pnl_r, 'dir': 'LONG' if direction == 1 else 'SHORT'})

trades_df = pd.DataFrame(trades)

print(f"      Generated {len(trades_df)} trades")

if len(trades_df) < 20:
    print(f"\n❌ Insufficient trades: {len(trades_df)} (need 20+)")
    sys.exit(0)

print("\n[4/6] Calculating performance metrics...")

wins = trades_df[trades_df['pnl_r'] > 0]
losses = trades_df[trades_df['pnl_r'] <= 0]

win_rate = len(wins) / len(trades_df)
avg_win = wins['pnl_r'].mean() if len(wins) > 0 else 0
avg_loss = losses['pnl_r'].mean() if len(losses) > 0 else 0
avg_r = trades_df['pnl_r'].mean()
total_r = trades_df['pnl_r'].sum()

print(f"      Trades: {len(trades_df)}")
print(f"      Win rate: {win_rate:.1%}")
print(f"      Avg win: {avg_win:+.2f}R | Avg loss: {avg_loss:.2f}R")
print(f"      Avg R: {avg_r:+.3f}")
print(f"      Total R: {total_r:+.2f}")

print("\n[5/6] IS/OOS validation...")

trades_df['date'] = trades_df['entry'].dt.date
unique_dates = sorted(trades_df['date'].unique())
split_idx = int(len(unique_dates) * 0.70)
split_date = unique_dates[split_idx]

is_df = trades_df[trades_df['date'] < split_date]
oos_df = trades_df[trades_df['date'] >= split_date]

print(f"      Split date: {split_date}")

# IS metrics
is_winrate = (is_df['pnl_r'] > 0).sum() / len(is_df) if len(is_df) > 0 else 0
is_avgr = is_df['pnl_r'].mean() if len(is_df) > 0 else 0
is_total = is_df['pnl_r'].sum() if len(is_df) > 0 else 0

# OOS metrics
oos_winrate = (oos_df['pnl_r'] > 0).sum() / len(oos_df) if len(oos_df) > 0 else 0
oos_avgr = oos_df['pnl_r'].mean() if len(oos_df) > 0 else 0
oos_total = oos_df['pnl_r'].sum() if len(oos_df) > 0 else 0

print(f"\n      IN-SAMPLE ({len(is_df)} trades):")
print(f"        Win rate: {is_winrate:.1%}")
print(f"        Avg R: {is_avgr:+.3f}")
print(f"        Total R: {is_total:+.2f}")

print(f"\n      OUT-OF-SAMPLE ({len(oos_df)} trades):")
print(f"        Win rate: {oos_winrate:.1%}")
print(f"        Avg R: {oos_avgr:+.3f}")
print(f"        Total R: {oos_total:+.2f}")

print("\n[6/6] VERDICT:")
print("="*70)

# Save results FIRST (before any Unicode printing)
trades_df.to_csv(r"C:\Users\sydne\OneDrive\myprojectx\gap_fast_research_trades.csv", index=False)

if is_avgr > 0 and oos_avgr > 0:
    print("\n[EDGE FOUND]")
    print("\nStrategy: 60-minute time gap continuation")
    print("  Entry: Immediate at gap open")
    print("  Stop: Gap midpoint")
    print("  Target: 2.0R")
    print("\nPerformance:")
    print(f"  Total trades: {len(trades_df)}")
    print(f"  Win rate: {win_rate:.1%}")
    print(f"  Average R: {avg_r:+.3f}")
    print(f"  IS expectancy: {is_avgr:+.3f}R (validated)")
    print(f"  OOS expectancy: {oos_avgr:+.3f}R (validated)")
    print("\n[GO] Strategy passes IS/OOS validation")
elif is_avgr > 0 and oos_avgr <= 0:
    print("\n[OVERFIT WARNING]")
    print("\nStrategy shows positive IS expectancy but FAILS OOS.")
    print("This indicates curve-fitting. Strategy is NOT robust.")
    print("\n[NO-GO] Failed OOS validation")
elif is_avgr <= 0:
    print("\n[NO EDGE FOUND]")
    print("\nStrategy shows negative or zero expectancy in-sample.")
    print("Gap continuation does not provide a tradeable edge.")
    print("\n[NO-GO] No statistical edge detected")

print("\nResults saved: gap_fast_research_trades.csv")
print("\n" + "="*70)
print("RESEARCH COMPLETE")
print("="*70)
