"""
View Current Backtest Results

Quick viewer for your backtest data.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def view_results():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*100)
    print("YOUR CURRENT BACKTEST RESULTS")
    print("="*100)
    print()

    # Overall summary
    print("OVERALL SUMMARY (All Sessions)")
    print("-"*100)

    overall = con.execute("""
        SELECT
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
            COUNT(*) FILTER (WHERE outcome = 'LOSS') as losses,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
            SUM(r_multiple) as total_r,
            AVG(r_multiple) as avg_r
        FROM orb_trades_5m_exec
    """).fetchone()

    if overall:
        trades, wins, losses, wr, total_r, avg_r = overall
        print(f"Total Trades: {trades} ({wins}W / {losses}L)")
        print(f"Win Rate: {wr:.1%}")
        print(f"Total R: {total_r:+.1f}R")
        print(f"Average R per trade: {avg_r:+.2f}R")
    print()

    # By session
    print("RESULTS BY SESSION")
    print("-"*100)

    by_session = con.execute("""
        SELECT
            orb,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
            COUNT(*) FILTER (WHERE outcome = 'LOSS') as losses,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
            SUM(r_multiple) as total_r,
            AVG(r_multiple) as avg_r
        FROM orb_trades_5m_exec
        GROUP BY orb
        ORDER BY total_r DESC
    """).fetchdf()

    if len(by_session) > 0:
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(by_session.to_string(index=False))
    print()

    # Best configs per session
    print("BEST CONFIG PER SESSION")
    print("-"*100)

    best_configs = con.execute("""
        WITH ranked AS (
            SELECT
                orb,
                rr,
                close_confirmations as confirm,
                sl_mode,
                buffer_ticks,
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
                SUM(r_multiple) as total_r,
                ROW_NUMBER() OVER (PARTITION BY orb ORDER BY SUM(r_multiple) DESC) as rank
            FROM orb_trades_5m_exec
            GROUP BY orb, rr, close_confirmations, sl_mode, buffer_ticks
        )
        SELECT orb, rr, confirm, sl_mode, buffer_ticks, trades, win_rate, total_r
        FROM ranked
        WHERE rank = 1
        ORDER BY total_r DESC
    """).fetchdf()

    if len(best_configs) > 0:
        print(best_configs.to_string(index=False))
    print()

    # Recent trades
    print("RECENT TRADES (Last 10)")
    print("-"*100)

    recent = con.execute("""
        SELECT
            date_local,
            orb,
            direction,
            outcome,
            r_multiple,
            entry_price,
            stop_price,
            target_price
        FROM orb_trades_5m_exec
        ORDER BY date_local DESC
        LIMIT 10
    """).fetchdf()

    if len(recent) > 0:
        print(recent.to_string(index=False))
    print()

    print("="*100)
    print()
    print("To view detailed CSV exports:")
    print("  - results_session_winners.csv")
    print("  - results_1m_by_session.csv")
    print("  - results_5m_halfsl_by_session.csv")
    print()

    con.close()

if __name__ == "__main__":
    view_results()
