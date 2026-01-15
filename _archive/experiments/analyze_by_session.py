"""
Session-Specific Variant Analysis

Breaks down backtest results by ORB time + variant to find specific edges.
Shows which variants work best for which sessions.
"""

import duckdb
import pandas as pd
from datetime import datetime

DB_PATH = "gold.db"

def analyze_by_session():
    con = duckdb.connect(DB_PATH)

    print("="*100)
    print("SESSION-SPECIFIC VARIANT ANALYSIS")
    print("="*100)
    print()

    # ========================================================================
    # 1. 1M MIDSTOP BY SESSION
    # ========================================================================
    print("1. 1M MIDSTOP BY SESSION")
    print("-"*100)

    df_1m_session = con.execute("""
        SELECT
            orb,
            rr,
            close_confirmations as confirm,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
            SUM(r_multiple) as total_r,
            AVG(r_multiple) as avg_r,
            AVG(mae_r) as avg_mae,
            AVG(mfe_r) as avg_mfe
        FROM orb_trades_1m_exec
        GROUP BY orb, rr, close_confirmations
        ORDER BY orb, total_r DESC
    """).fetchdf()

    if len(df_1m_session) > 0:
        # Show top 3 configs per session
        for orb in ['0900', '1000', '1100', '1800', '2300', '0030']:
            session_data = df_1m_session[df_1m_session['orb'] == orb]
            if len(session_data) > 0:
                print(f"\n{orb} ORB (1m midstop):")
                print(session_data.head(3).to_string(index=False))
                best = session_data.iloc[0]
                print(f"  >> BEST: RR={best['rr']}, Confirm={best['confirm']}, "
                      f"Win={best['win_rate']:.1%}, Trades={best['trades']:.0f}, Total R={best['total_r']:+.1f}")
    print()

    # ========================================================================
    # 2. 5M HALF-SL BY SESSION
    # ========================================================================
    print("2. 5M HALF-SL BY SESSION (with sl_mode and buffer)")
    print("-"*100)

    df_5m_session = con.execute("""
        SELECT
            orb,
            sl_mode,
            buffer_ticks,
            rr,
            close_confirmations as confirm,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
            SUM(r_multiple) as total_r,
            AVG(r_multiple) as avg_r
        FROM orb_trades_5m_exec
        WHERE sl_mode IS NOT NULL AND sl_mode != ''
        GROUP BY orb, sl_mode, buffer_ticks, rr, close_confirmations
        ORDER BY orb, total_r DESC
    """).fetchdf()

    if len(df_5m_session) > 0:
        # Show top 5 configs per session
        for orb in ['0900', '1000', '1100', '1800', '2300', '0030']:
            session_data = df_5m_session[df_5m_session['orb'] == orb]
            if len(session_data) > 0:
                print(f"\n{orb} ORB (5m half-SL):")
                print(session_data.head(5).to_string(index=False))
                best = session_data.iloc[0]
                print(f"  >> BEST: SL={best['sl_mode']}, Buffer={best['buffer_ticks']:.0f}, "
                      f"RR={best['rr']}, Confirm={best['confirm']}, "
                      f"Win={best['win_rate']:.1%}, Trades={best['trades']:.0f}, Total R={best['total_r']:+.1f}")
    print()

    # ========================================================================
    # 3. 5M EXEC BY SESSION (no sl_mode/buffer)
    # ========================================================================
    print("3. 5M EXEC BY SESSION (no half-SL)")
    print("-"*100)

    df_5m_exec_session = con.execute("""
        SELECT
            orb,
            rr,
            close_confirmations as confirm,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
            SUM(r_multiple) as total_r,
            AVG(r_multiple) as avg_r
        FROM orb_trades_5m_exec
        WHERE (sl_mode IS NULL OR sl_mode = '') AND (buffer_ticks IS NULL OR buffer_ticks = 0)
        GROUP BY orb, rr, close_confirmations
        ORDER BY orb, total_r DESC
    """).fetchdf()

    if len(df_5m_exec_session) > 0:
        # Show top 3 configs per session
        for orb in ['0900', '1000', '1100', '1800', '2300', '0030']:
            session_data = df_5m_exec_session[df_5m_exec_session['orb'] == orb]
            if len(session_data) > 0:
                print(f"\n{orb} ORB (5m exec):")
                print(session_data.head(3).to_string(index=False))
                best = session_data.iloc[0]
                print(f"  >> BEST: RR={best['rr']}, Confirm={best['confirm']}, "
                      f"Win={best['win_rate']:.1%}, Trades={best['trades']:.0f}, Total R={best['total_r']:+.1f}")
    print()

    # ========================================================================
    # 4. SUMMARY: BEST VARIANT PER SESSION
    # ========================================================================
    print("="*100)
    print("SUMMARY: BEST VARIANT PER SESSION (across all approaches)")
    print("="*100)
    print()

    # Combine all approaches and find best per session
    summary = []

    for orb in ['0900', '1000', '1100', '1800', '2300', '0030']:
        best_configs = []

        # 1m midstop
        if len(df_1m_session) > 0:
            orb_1m = df_1m_session[df_1m_session['orb'] == orb]
            if len(orb_1m) > 0:
                best_1m = orb_1m.iloc[0]
                best_configs.append({
                    'orb': orb,
                    'approach': '1m midstop',
                    'total_r': best_1m['total_r'],
                    'win_rate': best_1m['win_rate'],
                    'trades': best_1m['trades'],
                    'config': f"RR={best_1m['rr']}, Confirm={best_1m['confirm']}"
                })

        # 5m exec
        if len(df_5m_exec_session) > 0:
            orb_5m = df_5m_exec_session[df_5m_exec_session['orb'] == orb]
            if len(orb_5m) > 0:
                best_5m = orb_5m.iloc[0]
                best_configs.append({
                    'orb': orb,
                    'approach': '5m exec',
                    'total_r': best_5m['total_r'],
                    'win_rate': best_5m['win_rate'],
                    'trades': best_5m['trades'],
                    'config': f"RR={best_5m['rr']}, Confirm={best_5m['confirm']}"
                })

        # 5m half-SL
        if len(df_5m_session) > 0:
            orb_5m_half = df_5m_session[df_5m_session['orb'] == orb]
            if len(orb_5m_half) > 0:
                best_5m_half = orb_5m_half.iloc[0]
                best_configs.append({
                    'orb': orb,
                    'approach': '5m half-SL',
                    'total_r': best_5m_half['total_r'],
                    'win_rate': best_5m_half['win_rate'],
                    'trades': best_5m_half['trades'],
                    'config': f"SL={best_5m_half['sl_mode']}, Buf={best_5m_half['buffer_ticks']:.0f}, RR={best_5m_half['rr']}, Confirm={best_5m_half['confirm']}"
                })

        # Find winner for this session
        if best_configs:
            best_configs.sort(key=lambda x: x['total_r'], reverse=True)
            winner = best_configs[0]
            summary.append(winner)

            print(f"{orb} SESSION WINNER:")
            print(f"  Approach: {winner['approach']}")
            print(f"  Total R: {winner['total_r']:+.1f} | Win Rate: {winner['win_rate']:.1%} | Trades: {winner['trades']:.0f}")
            print(f"  Config: {winner['config']}")
            print()

    # ========================================================================
    # 5. EXPORT TO CSV
    # ========================================================================
    print("="*100)
    print("EXPORTING RESULTS")
    print("="*100)

    # Export full session breakdowns
    if len(df_1m_session) > 0:
        df_1m_session.to_csv('results_1m_by_session.csv', index=False)
        print("1m results by session: results_1m_by_session.csv")

    if len(df_5m_exec_session) > 0:
        df_5m_exec_session.to_csv('results_5m_exec_by_session.csv', index=False)
        print("5m exec results by session: results_5m_exec_by_session.csv")

    if len(df_5m_session) > 0:
        df_5m_session.to_csv('results_5m_halfsl_by_session.csv', index=False)
        print("5m half-SL results by session: results_5m_halfsl_by_session.csv")

    # Export summary
    if summary:
        df_summary = pd.DataFrame(summary)
        df_summary.to_csv('results_session_winners.csv', index=False)
        print("Session winners summary: results_session_winners.csv")

    print()
    print("="*100)
    print("ANALYSIS COMPLETE")
    print("="*100)

    con.close()

if __name__ == "__main__":
    analyze_by_session()
