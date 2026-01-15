"""
Analyze 18:00 ORB Results Across Different Buffer Values

Shows how buffer impacts:
- Total R
- Win rate
- Trade count
- Average stop size
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def analyze():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*100)
    print("18:00 ORB BUFFER ANALYSIS")
    print("="*100)
    print("Config: RR=2.0, confirm=1, half-SL")
    print("="*100)
    print()

    # Query all buffer variations for 18:00 ORB
    results = con.execute("""
        SELECT
            buffer_ticks,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
            COUNT(*) FILTER (WHERE outcome = 'LOSS') as losses,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
            SUM(r_multiple) as total_r,
            AVG(r_multiple) as avg_r,
            AVG(stop_ticks) as avg_stop,
            AVG(CASE WHEN outcome IN ('WIN','LOSS') THEN mae_r END) as avg_mae_r,
            AVG(CASE WHEN outcome IN ('WIN','LOSS') THEN mfe_r END) as avg_mfe_r
        FROM orb_trades_5m_exec
        WHERE orb = '1800'
          AND rr = 2.0
          AND close_confirmations = 1
          AND sl_mode = 'half'
        GROUP BY buffer_ticks
        ORDER BY buffer_ticks
    """).fetchdf()

    if len(results) == 0:
        print("No results found. Run test_1800_buffer_sweep.py first.")
        con.close()
        return

    print(f"Found {len(results)} buffer configurations:")
    print("-"*100)
    print()

    # Display results
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.float_format', '{:.2f}'.format)

    print(results[['buffer_ticks', 'trades', 'wins', 'losses', 'win_rate', 'total_r', 'avg_r', 'avg_stop']].to_string(index=False))
    print()

    # Find best config
    best_idx = results['total_r'].idxmax()
    best_buffer = results.loc[best_idx, 'buffer_ticks']
    best_r = results.loc[best_idx, 'total_r']
    best_wr = results.loc[best_idx, 'win_rate']
    best_trades = results.loc[best_idx, 'trades']
    best_stop = results.loc[best_idx, 'avg_stop']

    baseline_idx = results[results['buffer_ticks'] == 0.0].index
    if len(baseline_idx) > 0:
        baseline_r = results.loc[baseline_idx[0], 'total_r']
        baseline_wr = results.loc[baseline_idx[0], 'win_rate']
        baseline_trades = results.loc[baseline_idx[0], 'trades']
        baseline_stop = results.loc[baseline_idx[0], 'avg_stop']
    else:
        baseline_r = None
        baseline_wr = None
        baseline_trades = None
        baseline_stop = None

    print("-"*100)
    print("ANALYSIS")
    print("-"*100)
    print()

    if baseline_r is not None:
        print(f"BASELINE (buffer=0):")
        print(f"  Total R: {baseline_r:+.1f}R | Trades: {baseline_trades} | Win Rate: {baseline_wr:.1%} | Avg Stop: {baseline_stop:.1f} ticks")
        print()

    print(f"BEST BUFFER (buffer={best_buffer:.0f}):")
    print(f"  Total R: {best_r:+.1f}R | Trades: {best_trades} | Win Rate: {best_wr:.1%} | Avg Stop: {best_stop:.1f} ticks")
    print()

    if baseline_r is not None:
        r_diff = best_r - baseline_r
        wr_diff = (best_wr - baseline_wr) * 100
        trade_diff = best_trades - baseline_trades
        stop_diff = best_stop - baseline_stop

        print(f"IMPROVEMENT vs BASELINE:")
        print(f"  R Change: {r_diff:+.1f}R")
        print(f"  Win Rate Change: {wr_diff:+.1f} percentage points")
        print(f"  Trade Change: {trade_diff:+d}")
        print(f"  Avg Stop Change: {stop_diff:+.1f} ticks")
        print()

        if r_diff > 5:
            print(f">>> BUFFER HELPS: Use buffer={best_buffer:.0f} for +{r_diff:.0f}R improvement")
        elif r_diff < -5:
            print(f">>> BUFFER HURTS: Stick with buffer=0 (baseline is better)")
        else:
            print(f">>> NEUTRAL: Buffer doesn't significantly impact performance")
            print(f"    Use buffer=0 for simplicity")

    print()
    print("-"*100)
    print("BUFFER IMPACT SUMMARY")
    print("-"*100)

    # Show how buffer affects stop size and win rate
    print()
    print("Buffer vs Performance:")
    for idx, row in results.iterrows():
        buf = row['buffer_ticks']
        r = row['total_r']
        wr = row['win_rate']
        stop = row['avg_stop']
        print(f"  buffer={buf:>4.0f} -> Stop: {stop:5.1f} ticks | WR: {wr:5.1%} | R: {r:+7.1f}R")

    print()
    print("="*100)

    con.close()

if __name__ == "__main__":
    analyze()
