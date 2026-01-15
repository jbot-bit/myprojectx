"""
Compare Filtered vs No-Filters Results

Shows how removing MAX_STOP_TICKS and ASIA_TP_CAP filters affects performance.
Highlights which sessions benefit from removing filters.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def compare_results():
    con = duckdb.connect(DB_PATH)

    print("="*100)
    print("FILTERED VS NO-FILTERS COMPARISON")
    print("="*100)
    print()

    # Check if nofilters tables exist
    tables = con.execute("SHOW TABLES").fetchdf()
    has_nofilters = any('nofilters' in str(t) for t in tables.values)

    if not has_nofilters:
        print("No-filters tables not found yet. Run the no-filters variants first:")
        print("  python run_nofilters_variants.py")
        con.close()
        return

    # ========================================================================
    # 1. OVERALL COMPARISON (ALL SESSIONS COMBINED)
    # ========================================================================
    print("1. OVERALL COMPARISON (All Sessions Combined)")
    print("-"*100)

    # 1m comparison
    print("\n1m Midstop - Filtered vs No-Filters:")
    print("-"*100)

    df_1m_compare = con.execute("""
        WITH filtered AS (
            SELECT
                rr,
                close_confirmations as confirm,
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
                SUM(r_multiple) as total_r,
                AVG(r_multiple) as avg_r
            FROM orb_trades_1m_exec
            GROUP BY rr, close_confirmations
        ),
        nofilters AS (
            SELECT
                rr,
                close_confirmations as confirm,
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
                SUM(r_multiple) as total_r,
                AVG(r_multiple) as avg_r
            FROM orb_trades_1m_exec_nofilters
            GROUP BY rr, close_confirmations
        )
        SELECT
            COALESCE(f.rr, n.rr) as rr,
            COALESCE(f.confirm, n.confirm) as confirm,
            f.trades as trades_filtered,
            n.trades as trades_nofilters,
            f.win_rate as wr_filtered,
            n.win_rate as wr_nofilters,
            f.total_r as total_r_filtered,
            n.total_r as total_r_nofilters,
            n.total_r - f.total_r as r_improvement
        FROM filtered f
        FULL OUTER JOIN nofilters n ON f.rr = n.rr AND f.confirm = n.confirm
        ORDER BY ABS(n.total_r - f.total_r) DESC
    """).fetchdf()

    if len(df_1m_compare) > 0:
        print(df_1m_compare.to_string(index=False))

        total_improvement = df_1m_compare['r_improvement'].sum()
        print(f"\n  >> Total R Improvement (removing filters): {total_improvement:+.1f}")
    print()

    # 5m half-SL comparison
    print("\n5m Half-SL - Filtered vs No-Filters (Top 10 Improvements):")
    print("-"*100)

    df_5m_compare = con.execute("""
        WITH filtered AS (
            SELECT
                sl_mode,
                buffer_ticks,
                rr,
                close_confirmations as confirm,
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                SUM(r_multiple) as total_r
            FROM orb_trades_5m_exec
            WHERE sl_mode IS NOT NULL AND sl_mode != ''
            GROUP BY sl_mode, buffer_ticks, rr, close_confirmations
        ),
        nofilters AS (
            SELECT
                sl_mode,
                buffer_ticks,
                rr,
                close_confirmations as confirm,
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                SUM(r_multiple) as total_r
            FROM orb_trades_5m_exec_nofilters
            WHERE sl_mode IS NOT NULL AND sl_mode != ''
            GROUP BY sl_mode, buffer_ticks, rr, close_confirmations
        )
        SELECT
            COALESCE(f.sl_mode, n.sl_mode) as sl_mode,
            COALESCE(f.buffer_ticks, n.buffer_ticks) as buffer,
            COALESCE(f.rr, n.rr) as rr,
            COALESCE(f.confirm, n.confirm) as confirm,
            f.trades as trades_filtered,
            n.trades as trades_nofilters,
            f.total_r as total_r_filtered,
            n.total_r as total_r_nofilters,
            n.total_r - f.total_r as r_improvement
        FROM filtered f
        FULL OUTER JOIN nofilters n
            ON f.sl_mode = n.sl_mode
            AND f.buffer_ticks = n.buffer_ticks
            AND f.rr = n.rr
            AND f.confirm = n.confirm
        ORDER BY ABS(n.total_r - f.total_r) DESC
        LIMIT 10
    """).fetchdf()

    if len(df_5m_compare) > 0:
        print(df_5m_compare.to_string(index=False))
    print()

    # ========================================================================
    # 2. SESSION-SPECIFIC COMPARISON
    # ========================================================================
    print("2. SESSION-SPECIFIC IMPACT (Filtered vs No-Filters)")
    print("-"*100)

    for orb in ['0900', '1000', '1100', '1800', '2300', '0030']:
        print(f"\n{orb} ORB - Impact of Removing Filters:")
        print("-"*60)

        # 1m session comparison
        df_session = con.execute(f"""
            WITH filtered AS (
                SELECT
                    rr,
                    close_confirmations as confirm,
                    COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                    SUM(r_multiple) as total_r
                FROM orb_trades_1m_exec
                WHERE orb = '{orb}'
                GROUP BY rr, close_confirmations
            ),
            nofilters AS (
                SELECT
                    rr,
                    close_confirmations as confirm,
                    COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                    SUM(r_multiple) as total_r
                FROM orb_trades_1m_exec_nofilters
                WHERE orb = '{orb}'
                GROUP BY rr, close_confirmations
            )
            SELECT
                COALESCE(f.rr, n.rr) as rr,
                COALESCE(f.confirm, n.confirm) as confirm,
                f.trades as trades_filt,
                n.trades as trades_nofilt,
                f.total_r as r_filt,
                n.total_r as r_nofilt,
                n.total_r - f.total_r as improvement
            FROM filtered f
            FULL OUTER JOIN nofilters n ON f.rr = n.rr AND f.confirm = n.confirm
            ORDER BY improvement DESC
            LIMIT 5
        """).fetchdf()

        if len(df_session) > 0:
            print(df_session.to_string(index=False))

            # Calculate session-level impact
            trades_added = (df_session['trades_nofilt'] - df_session['trades_filt']).sum()
            r_improvement = df_session['improvement'].sum()

            print(f"\n  {orb} Impact: +{trades_added:.0f} trades, {r_improvement:+.1f}R improvement")
        else:
            print(f"  No data for {orb}")

    print()
    print("="*100)
    print("ANALYSIS COMPLETE")
    print("="*100)
    print()
    print("Key Insights:")
    print("- Sessions with large positive improvements: filters were too restrictive")
    print("- Sessions with negative improvements: filters were protecting from bad trades")
    print("- Focus on sessions where removing filters adds significant R")

    con.close()

if __name__ == "__main__":
    compare_results()
