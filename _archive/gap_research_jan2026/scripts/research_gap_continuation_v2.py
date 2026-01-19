"""
Gap Continuation Strategy Research - MGC Futures (Optimized Version)

Fast execution with focus on most promising gap definitions.
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

# Configuration
DB_PATH = r"C:\Users\sydne\OneDrive\myprojectx\gold.db"
MIN_TRADES = 30
IS_OOS_SPLIT = 0.70

print("="*80)
print("GAP CONTINUATION STRATEGY RESEARCH - MGC FUTURES")
print("="*80)
print(f"\nConfiguration:")
print(f"  Database: {DB_PATH}")
print(f"  Min trades: {MIN_TRADES}")
print(f"  IS/OOS split: {IS_OOS_SPLIT:.0%}")
print()

# Load data
print("Loading data...")
conn = duckdb.connect(DB_PATH)

print("  Loading 1m bars...")
bars_1m = conn.execute("""
    SELECT ts_utc, open, high, low, close, volume
    FROM bars_1m
    WHERE symbol = 'MGC'
    ORDER BY ts_utc
""").fetchdf()
bars_1m['ts_utc'] = pd.to_datetime(bars_1m['ts_utc'], utc=True)
print(f"    Loaded {len(bars_1m):,} bars")

# Calculate IS/OOS split
all_dates = sorted(bars_1m['ts_utc'].dt.date.unique())
split_idx = int(len(all_dates) * IS_OOS_SPLIT)
is_split_date = all_dates[split_idx]

print(f"\n  IS/OOS split date: {is_split_date}")
print(f"    In-sample: {all_dates[0]} to {all_dates[split_idx-1]} ({split_idx} days)")
print(f"    Out-of-sample: {all_dates[split_idx]} to {all_dates[-1]} ({len(all_dates)-split_idx} days)")

# Detect time gaps (60+ minutes)
print(f"\n{'='*80}")
print("DETECTING TIME GAPS (60+ minutes)")
print('='*80)

bars_1m['time_diff_min'] = bars_1m['ts_utc'].diff().dt.total_seconds() / 60
bars_1m['prev_close'] = bars_1m['close'].shift(1)

gaps_60m = bars_1m[bars_1m['time_diff_min'] > 60].copy()
gaps_60m['gap_size'] = gaps_60m['open'] - gaps_60m['prev_close']
gaps_60m['gap_direction'] = np.where(gaps_60m['gap_size'] > 0, 'UP', 'DOWN')

print(f"\nFound {len(gaps_60m)} gaps (60+ minutes):")
print(f"  UP gaps: {(gaps_60m['gap_direction'] == 'UP').sum()}")
print(f"  DOWN gaps: {(gaps_60m['gap_direction'] == 'DOWN').sum()}")
print(f"  Avg gap size: {gaps_60m['gap_size'].abs().mean():.3f}")
print(f"  Median gap size: {gaps_60m['gap_size'].abs().median():.3f}")

if len(gaps_60m) < MIN_TRADES:
    print(f"\n❌ INSUFFICIENT DATA: Only {len(gaps_60m)} gaps found (minimum {MIN_TRADES} required)")
    sys.exit(0)

# Test immediate continuation strategies
print(f"\n{'='*80}")
print("TESTING IMMEDIATE CONTINUATION STRATEGIES")
print('='*80)

def test_strategy(gaps_df, stop_type, target_r, strategy_name):
    """Test a gap continuation strategy"""

    trades = []

    for idx, gap in gaps_df.iterrows():
        entry_time = gap['ts_utc']
        entry_price = gap['open']
        direction = 1 if gap['gap_direction'] == 'UP' else -1

        # Calculate stop
        if stop_type == 'gap_midpoint':
            stop_price = (gap['prev_close'] + gap['open']) / 2
        else:  # gap_origin
            stop_price = gap['prev_close']

        stop_distance = abs(entry_price - stop_price)
        if stop_distance == 0:
            continue

        target_price = entry_price + direction * stop_distance * target_r

        # Get future bars (max 1 day)
        future_bars = bars_1m[(bars_1m['ts_utc'] > entry_time) &
                              (bars_1m['ts_utc'] <= entry_time + pd.Timedelta(days=1))]

        if len(future_bars) == 0:
            continue

        # Simulate trade
        mae = 0
        mfe = 0
        exit_time = None
        exit_price = None
        pnl_r = None

        for _, bar in future_bars.iterrows():
            if direction == 1:  # Long
                mae = min(mae, (bar['low'] - entry_price) / stop_distance)
                mfe = max(mfe, (bar['high'] - entry_price) / stop_distance)

                if bar['low'] <= stop_price:
                    exit_time = bar['ts_utc']
                    exit_price = stop_price
                    pnl_r = -1.0
                    break

                if bar['high'] >= target_price:
                    exit_time = bar['ts_utc']
                    exit_price = target_price
                    pnl_r = target_r
                    break
            else:  # Short
                mae = min(mae, (entry_price - bar['high']) / stop_distance)
                mfe = max(mfe, (entry_price - bar['low']) / stop_distance)

                if bar['high'] >= stop_price:
                    exit_time = bar['ts_utc']
                    exit_price = stop_price
                    pnl_r = -1.0
                    break

                if bar['low'] <= target_price:
                    exit_time = bar['ts_utc']
                    exit_price = target_price
                    pnl_r = target_r
                    break

        # Close at end if no exit
        if exit_time is None:
            exit_time = future_bars.iloc[-1]['ts_utc']
            exit_price = future_bars.iloc[-1]['close']
            pnl_r = (exit_price - entry_price) / stop_distance * direction

        trades.append({
            'entry_time': entry_time,
            'entry_date': entry_time.date(),
            'entry_price': entry_price,
            'stop_price': stop_price,
            'target_price': target_price,
            'exit_time': exit_time,
            'exit_price': exit_price,
            'pnl_r': pnl_r,
            'mae_r': mae,
            'mfe_r': mfe,
            'gap_size': gap['gap_size'],
            'direction': gap['gap_direction']
        })

    if len(trades) == 0:
        return None

    trades_df = pd.DataFrame(trades)

    # Split IS/OOS
    is_trades = trades_df[trades_df['entry_date'] < is_split_date]
    oos_trades = trades_df[trades_df['entry_date'] >= is_split_date]

    def calc_metrics(df, label):
        if len(df) == 0:
            return None

        wins = df[df['pnl_r'] > 0]
        win_rate = len(wins) / len(df)
        avg_r = df['pnl_r'].mean()

        date_range_days = (df['entry_time'].max() - df['entry_time'].min()).days
        trades_per_year = len(df) / (date_range_days / 365.25) if date_range_days > 0 else 0

        cumsum = df['pnl_r'].cumsum()
        running_max = cumsum.cummax()
        drawdown = running_max - cumsum
        max_dd = drawdown.max()

        return {
            'label': label,
            'trades': len(df),
            'win_rate': win_rate,
            'avg_r': avg_r,
            'expectancy': avg_r,
            'trades_per_year': trades_per_year,
            'max_dd_r': max_dd,
            'mae_avg': df['mae_r'].mean(),
            'mfe_avg': df['mfe_r'].mean()
        }

    is_metrics = calc_metrics(is_trades, 'IS')
    oos_metrics = calc_metrics(oos_trades, 'OOS')
    full_metrics = calc_metrics(trades_df, 'FULL')

    return {
        'strategy': strategy_name,
        'is': is_metrics,
        'oos': oos_metrics,
        'full': full_metrics,
        'trades_df': trades_df
    }

# Test all combinations
results = []

for stop_type in ['gap_midpoint', 'gap_origin']:
    for target_r in [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]:
        strategy_name = f"time_60m_{stop_type}_{target_r}R"
        print(f"\nTesting: {strategy_name}")

        result = test_strategy(gaps_60m, stop_type, target_r, strategy_name)

        if result is None:
            print("  No trades generated")
            continue

        is_m = result['is']
        oos_m = result['oos']

        if is_m is None or oos_m is None:
            print("  Insufficient IS/OOS data")
            continue

        print(f"  IS:  {is_m['trades']} trades | {is_m['win_rate']:.1%} win | {is_m['avg_r']:+.3f}R avg | {is_m['expectancy']:+.3f} exp")
        print(f"  OOS: {oos_m['trades']} trades | {oos_m['win_rate']:.1%} win | {oos_m['avg_r']:+.3f}R avg | {oos_m['expectancy']:+.3f} exp")

        # Validation: both IS and OOS must be profitable
        if (is_m['trades'] >= MIN_TRADES and
            oos_m['trades'] >= MIN_TRADES * 0.5 and
            is_m['expectancy'] > 0 and
            oos_m['expectancy'] > 0):
            results.append(result)
            print("  ✅ VALIDATED")
        else:
            print("  ❌ Failed validation")

# Final results
print(f"\n{'='*80}")
print("FINAL RESULTS")
print('='*80)

if len(results) == 0:
    print("\n❌ NO EDGE FOUND")
    print("\nConclusion:")
    print("  No gap continuation strategy survived IS/OOS validation.")
    print("  All tested combinations failed to show consistent positive expectancy.")
    print("  Gap continuation (60+ minute gaps) does NOT provide a statistically valid edge on MGC futures.")
else:
    # Sort by OOS expectancy
    results.sort(key=lambda x: x['oos']['expectancy'], reverse=True)

    print(f"\n✅ FOUND {len(results)} VALIDATED STRATEGIES\n")

    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['strategy']}")
        print(f"   IN-SAMPLE:")
        print(f"     {r['is']['trades']} trades | {r['is']['win_rate']:.1%} win | {r['is']['avg_r']:+.3f}R avg")
        print(f"     Expectancy: {r['is']['expectancy']:+.3f} | MaxDD: {r['is']['max_dd_r']:.2f}R")
        print(f"     MAE: {r['is']['mae_avg']:.2f}R | MFE: {r['is']['mfe_avg']:.2f}R")
        print(f"   OUT-OF-SAMPLE:")
        print(f"     {r['oos']['trades']} trades | {r['oos']['win_rate']:.1%} win | {r['oos']['avg_r']:+.3f}R avg")
        print(f"     Expectancy: {r['oos']['expectancy']:+.3f} | MaxDD: {r['oos']['max_dd_r']:.2f}R")
        print(f"     MAE: {r['oos']['mae_avg']:.2f}R | MFE: {r['oos']['mfe_avg']:.2f}R")
        print(f"   FULL SAMPLE:")
        print(f"     Trades/Year: {r['full']['trades_per_year']:.1f}")

    # Save results
    print(f"\n{'='*80}")
    print("SAVING RESULTS")
    print('='*80)

    summary_data = []
    for r in results:
        summary_data.append({
            'strategy': r['strategy'],
            'is_trades': r['is']['trades'],
            'is_winrate': r['is']['win_rate'],
            'is_avgr': r['is']['avg_r'],
            'is_exp': r['is']['expectancy'],
            'oos_trades': r['oos']['trades'],
            'oos_winrate': r['oos']['win_rate'],
            'oos_avgr': r['oos']['avg_r'],
            'oos_exp': r['oos']['expectancy'],
            'trades_per_year': r['full']['trades_per_year'],
            'mae_avg': r['full']['mae_avg'],
            'mfe_avg': r['full']['mfe_avg']
        })

    summary_df = pd.DataFrame(summary_data)
    summary_path = r"C:\Users\sydne\OneDrive\myprojectx\gap_research_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"  Saved summary: {summary_path}")

    # Save top strategy trades
    top_trades_path = r"C:\Users\sydne\OneDrive\myprojectx\gap_research_top_trades.csv"
    results[0]['trades_df'].to_csv(top_trades_path, index=False)
    print(f"  Saved top strategy trades: {top_trades_path}")

print(f"\n{'='*80}")
print("RESEARCH COMPLETE")
print('='*80)

conn.close()
