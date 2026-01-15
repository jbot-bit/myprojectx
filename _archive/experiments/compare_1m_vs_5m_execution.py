"""
Compare 1-Minute vs 5-Minute Execution

Analyzes which execution timeframe (1m vs 5m) produces better results
for ORB breakout strategies.
"""

import duckdb

DB_PATH = "gold.db"

def compare_1m_vs_5m():
    print("="*100)
    print("1-MINUTE VS 5-MINUTE EXECUTION COMPARISON")
    print("="*100)
    print()

    con = duckdb.connect(DB_PATH)

    # Check what's in each table
    print("1. TABLE SUMMARY")
    print("-" * 100)

    # 1m execution
    m1_summary = con.execute("""
        SELECT
            COUNT(DISTINCT CONCAT(orb, '-', close_confirmations, '-', rr, '-', sl_mode, '-', buffer_ticks)) as configs,
            COUNT(*) as total_rows,
            SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as trades,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
            ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) /
                  NULLIF(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END), 0), 1) as win_rate,
            ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r,
            ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE NULL END), 3) as avg_r
        FROM orb_trades_1m_exec
    """).fetchone()

    # 5m execution
    m5_summary = con.execute("""
        SELECT
            COUNT(DISTINCT CONCAT(orb, '-', close_confirmations, '-', rr, '-', sl_mode, '-', buffer_ticks)) as configs,
            COUNT(*) as total_rows,
            SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as trades,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
            ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) /
                  NULLIF(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END), 0), 1) as win_rate,
            ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r,
            ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE NULL END), 3) as avg_r
        FROM orb_trades_5m_exec
    """).fetchone()

    print("1-Minute Execution (orb_trades_1m_exec):")
    print(f"  Configs: {m1_summary[0]}")
    print(f"  Total rows: {m1_summary[1]:,}")
    print(f"  Actual trades: {m1_summary[2]:,}")
    print(f"  Wins: {m1_summary[3]:,}")
    print(f"  Losses: {m1_summary[4]:,}")
    print(f"  Win rate: {m1_summary[5]}%")
    print(f"  Total R: {m1_summary[6]:+.1f}R")
    print(f"  Average R: {m1_summary[7]:+.3f}R")
    print()

    print("5-Minute Execution (orb_trades_5m_exec):")
    print(f"  Configs: {m5_summary[0]}")
    print(f"  Total rows: {m5_summary[1]:,}")
    print(f"  Actual trades: {m5_summary[2]:,}")
    print(f"  Wins: {m5_summary[3]:,}")
    print(f"  Losses: {m5_summary[4]:,}")
    print(f"  Win rate: {m5_summary[5]}%")
    print(f"  Total R: {m5_summary[6]:+.1f}R")
    print(f"  Average R: {m5_summary[7]:+.3f}R")
    print()

    # Determine winner
    print("-" * 100)
    if m1_summary[6] > m5_summary[6]:
        diff = m1_summary[6] - m5_summary[6]
        print(f"WINNER: 1-Minute execution by {diff:+.1f}R")
    elif m5_summary[6] > m1_summary[6]:
        diff = m5_summary[6] - m1_summary[6]
        print(f"WINNER: 5-Minute execution by {diff:+.1f}R")
    else:
        print("TIE: Both timeframes have identical performance")
    print()

    # ============================================================================
    # 2. BEST CONFIGS FROM EACH TIMEFRAME
    # ============================================================================
    print()
    print("2. TOP 10 CONFIGS - 1-MINUTE EXECUTION")
    print("-" * 100)

    m1_best = con.execute("""
        SELECT
            orb,
            close_confirmations as cc,
            rr,
            sl_mode,
            buffer_ticks as buffer,
            SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as trades,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) /
                  NULLIF(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END), 0), 1) as wr,
            ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r,
            ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE NULL END), 3) as avg_r
        FROM orb_trades_1m_exec
        GROUP BY orb, close_confirmations, rr, sl_mode, buffer_ticks
        ORDER BY total_r DESC
        LIMIT 10
    """).df()

    print(m1_best.to_string(index=False))
    print()

    print()
    print("3. TOP 10 CONFIGS - 5-MINUTE EXECUTION")
    print("-" * 100)

    m5_best = con.execute("""
        SELECT
            orb,
            close_confirmations as cc,
            rr,
            sl_mode,
            buffer_ticks as buffer,
            SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as trades,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            ROUND(100.0 * SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) /
                  NULLIF(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END), 0), 1) as wr,
            ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r,
            ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE NULL END), 3) as avg_r
        FROM orb_trades_5m_exec
        GROUP BY orb, close_confirmations, rr, sl_mode, buffer_ticks
        ORDER BY total_r DESC
        LIMIT 10
    """).df()

    print(m5_best.to_string(index=False))
    print()

    # ============================================================================
    # 4. NOFILTERS COMPARISON
    # ============================================================================
    print()
    print("4. NOFILTERS COMPARISON (Testing without MAX_STOP/ASIA_TP_CAP)")
    print("-" * 100)

    # Check if nofilters tables have data
    m1_nf_count = con.execute("SELECT COUNT(*) FROM orb_trades_1m_exec_nofilters").fetchone()[0]
    m5_nf_count = con.execute("SELECT COUNT(*) FROM orb_trades_5m_exec_nofilters").fetchone()[0]

    if m1_nf_count > 0:
        m1_nf_summary = con.execute("""
            SELECT
                SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as trades,
                ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r
            FROM orb_trades_1m_exec_nofilters
        """).fetchone()
        print(f"1-Minute (no filters): {m1_nf_summary[0]:,} trades | {m1_nf_summary[1]:+.1f}R")
    else:
        print("1-Minute (no filters): No data")

    if m5_nf_count > 0:
        m5_nf_summary = con.execute("""
            SELECT
                SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 1 ELSE 0 END) as trades,
                ROUND(SUM(CASE WHEN outcome IN ('WIN', 'LOSS') THEN r_multiple ELSE 0 END), 1) as total_r
            FROM orb_trades_5m_exec_nofilters
        """).fetchone()
        print(f"5-Minute (no filters): {m5_nf_summary[0]:,} trades | {m5_nf_summary[1]:+.1f}R")
    else:
        print("5-Minute (no filters): No data")
    print()

    con.close()

    # ============================================================================
    # 5. SUMMARY & RECOMMENDATIONS
    # ============================================================================
    print()
    print("="*100)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*100)
    print()

    if m1_summary[6] > m5_summary[6]:
        print("1-MINUTE EXECUTION IS BETTER")
        print(f"  - {m1_summary[6]:+.1f}R vs {m5_summary[6]:+.1f}R (difference: {m1_summary[6] - m5_summary[6]:+.1f}R)")
        print(f"  - More precise entry timing on 1-minute closes")
        print(f"  - Potentially faster entries after ORB break")
        print()
        print("RECOMMENDATION: Use 1-minute execution for live trading")
    elif m5_summary[6] > m1_summary[6]:
        print("5-MINUTE EXECUTION IS BETTER")
        print(f"  - {m5_summary[6]:+.1f}R vs {m1_summary[6]:+.1f}R (difference: {m5_summary[6] - m1_summary[6]:+.1f}R)")
        print(f"  - More confirmation before entry (5-minute closes)")
        print(f"  - Fewer false breakouts")
        print()
        print("RECOMMENDATION: Use 5-minute execution for live trading")
    else:
        print("BOTH TIMEFRAMES PERFORM IDENTICALLY")
        print(f"  - Both: {m1_summary[6]:+.1f}R")
        print()
        print("RECOMMENDATION: Use either (slight preference for 5m for simplicity)")

    print()
    print("IMPORTANT NOTES:")
    print("  - Both timeframes may still be negative overall")
    print("  - Comparison is based on historical backtest with filters")
    print("  - Live execution may differ due to slippage, latency, etc.")
    print("  - Consider robustness test results (unfiltered) before trading")
    print()
    print("="*100)

if __name__ == "__main__":
    compare_1m_vs_5m()
