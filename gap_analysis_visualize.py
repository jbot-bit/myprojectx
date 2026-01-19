"""
Gap Continuation - Generate Summary Statistics and Trade List

Creates detailed trade-by-trade breakdown and summary statistics.
"""

import pandas as pd
import numpy as np

print("="*70)
print("GAP CONTINUATION - DETAILED ANALYSIS")
print("="*70)

# Load trades
trades = pd.read_csv(r"C:\Users\sydne\OneDrive\myprojectx\gap_fast_research_trades.csv")
trades['entry'] = pd.to_datetime(trades['entry'])
trades['date'] = trades['entry'].dt.date

print(f"\nLoaded {len(trades)} trades")

# Calculate cumulative returns
trades = trades.sort_values('entry').reset_index(drop=True)
trades['cumulative_r'] = trades['pnl_r'].cumsum()
trades['trade_num'] = range(1, len(trades) + 1)

# Calculate running drawdown
running_max = trades['cumulative_r'].cummax()
trades['drawdown_r'] = running_max - trades['cumulative_r']

# IS/OOS split
split_date = pd.to_datetime('2025-06-15').date()
trades['period'] = trades['date'].apply(lambda x: 'IS' if x < split_date else 'OOS')

# Summary statistics
print("\n" + "="*70)
print("SUMMARY STATISTICS")
print("="*70)

for period in ['IS', 'OOS', 'FULL']:
    if period == 'FULL':
        subset = trades
    else:
        subset = trades[trades['period'] == period]

    if len(subset) == 0:
        continue

    wins = subset[subset['pnl_r'] > 0]
    losses = subset[subset['pnl_r'] <= 0]

    print(f"\n{period} SAMPLE:")
    print(f"  Trades: {len(subset)}")
    print(f"  Date range: {subset['date'].min()} to {subset['date'].max()}")
    print(f"  Wins: {len(wins)} ({len(wins)/len(subset):.1%})")
    print(f"  Losses: {len(losses)} ({len(losses)/len(subset):.1%})")
    print(f"  Avg win: {wins['pnl_r'].mean():.3f}R" if len(wins) > 0 else "  Avg win: N/A")
    print(f"  Avg loss: {losses['pnl_r'].mean():.3f}R" if len(losses) > 0 else "  Avg loss: N/A")
    print(f"  Avg R: {subset['pnl_r'].mean():.3f}R")
    print(f"  Median R: {subset['pnl_r'].median():.3f}R")
    print(f"  Std Dev: {subset['pnl_r'].std():.3f}R")
    print(f"  Total R: {subset['pnl_r'].sum():.2f}R")
    print(f"  Max drawdown: {subset['drawdown_r'].max():.2f}R")

    # Streak analysis
    win_streaks = []
    loss_streaks = []
    current_streak = 0
    current_type = None

    for pnl in subset['pnl_r']:
        if pnl > 0:
            if current_type == 'win':
                current_streak += 1
            else:
                if current_type == 'loss' and current_streak > 0:
                    loss_streaks.append(current_streak)
                current_streak = 1
                current_type = 'win'
        else:
            if current_type == 'loss':
                current_streak += 1
            else:
                if current_type == 'win' and current_streak > 0:
                    win_streaks.append(current_streak)
                current_streak = 1
                current_type = 'loss'

    if current_type == 'win':
        win_streaks.append(current_streak)
    elif current_type == 'loss':
        loss_streaks.append(current_streak)

    if win_streaks:
        print(f"  Max win streak: {max(win_streaks)}")
    if loss_streaks:
        print(f"  Max loss streak: {max(loss_streaks)}")

# Best and worst trades
print("\n" + "="*70)
print("EXTREME TRADES")
print("="*70)

print("\nBEST 5 TRADES:")
best = trades.nlargest(5, 'pnl_r')[['trade_num', 'entry', 'dir', 'pnl_r']]
for _, row in best.iterrows():
    print(f"  Trade #{row['trade_num']:3d} | {row['entry'].strftime('%Y-%m-%d %H:%M')} | {row['dir']:5s} | {row['pnl_r']:+.3f}R")

print("\nWORST 5 TRADES:")
worst = trades.nsmallest(5, 'pnl_r')[['trade_num', 'entry', 'dir', 'pnl_r']]
for _, row in worst.iterrows():
    print(f"  Trade #{row['trade_num']:3d} | {row['entry'].strftime('%Y-%m-%d %H:%M')} | {row['dir']:5s} | {row['pnl_r']:+.3f}R")

# Direction comparison
print("\n" + "="*70)
print("DIRECTION ANALYSIS")
print("="*70)

for direction in ['LONG', 'SHORT']:
    subset = trades[trades['dir'] == direction]
    wins = len(subset[subset['pnl_r'] > 0])
    print(f"\n{direction}:")
    print(f"  Trades: {len(subset)}")
    print(f"  Wins: {wins} ({wins/len(subset):.1%})")
    print(f"  Avg R: {subset['pnl_r'].mean():.3f}R")
    print(f"  Total R: {subset['pnl_r'].sum():.2f}R")

# Day of week analysis
print("\n" + "="*70)
print("DAY OF WEEK ANALYSIS")
print("="*70)

trades['dow'] = pd.to_datetime(trades['entry']).dt.day_name()

dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
for dow in dow_order:
    subset = trades[trades['dow'] == dow]
    if len(subset) == 0:
        continue
    wins = len(subset[subset['pnl_r'] > 0])
    print(f"{dow:9s}: {len(subset):3d} trades | {wins:3d} wins ({wins/len(subset):.1%}) | {subset['pnl_r'].mean():+.3f}R avg | {subset['pnl_r'].sum():+.2f}R total")

# Save detailed trades
output = trades[['trade_num', 'entry', 'dir', 'pnl_r', 'cumulative_r', 'drawdown_r', 'period']].copy()
output.columns = ['Trade#', 'Entry Time', 'Direction', 'P&L (R)', 'Cumulative R', 'Drawdown (R)', 'Period']

output_path = r"C:\Users\sydne\OneDrive\myprojectx\gap_trades_detailed.csv"
output.to_csv(output_path, index=False)

print("\n" + "="*70)
print(f"Saved detailed trades to: gap_trades_detailed.csv")
print("="*70)

# Create equity curve data
equity = trades[['trade_num', 'entry', 'pnl_r', 'cumulative_r', 'drawdown_r']].copy()
equity_path = r"C:\Users\sydne\OneDrive\myprojectx\gap_equity_curve.csv"
equity.to_csv(equity_path, index=False)

print(f"Saved equity curve to: gap_equity_curve.csv")

# Summary for quick reference
summary = {
    'Total Trades': len(trades),
    'IS Trades': len(trades[trades['period'] == 'IS']),
    'OOS Trades': len(trades[trades['period'] == 'OOS']),
    'IS Win Rate': f"{(trades[trades['period'] == 'IS']['pnl_r'] > 0).sum() / len(trades[trades['period'] == 'IS']):.1%}",
    'OOS Win Rate': f"{(trades[trades['period'] == 'OOS']['pnl_r'] > 0).sum() / len(trades[trades['period'] == 'OOS']):.1%}",
    'IS Avg R': f"{trades[trades['period'] == 'IS']['pnl_r'].mean():.3f}",
    'OOS Avg R': f"{trades[trades['period'] == 'OOS']['pnl_r'].mean():.3f}",
    'Total R': f"{trades['pnl_r'].sum():.2f}",
    'Max Drawdown': f"{trades['drawdown_r'].max():.2f}R"
}

print("\n" + "="*70)
print("QUICK REFERENCE SUMMARY")
print("="*70)

for key, value in summary.items():
    print(f"{key:20s}: {value}")

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
