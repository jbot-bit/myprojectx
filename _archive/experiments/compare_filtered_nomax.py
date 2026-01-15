"""
Phase 3: Compare Filtered vs No-Max Results

Apples-to-apples comparison of same configs with and without MAX_STOP/ASIA_TP_CAP filters.

Shows:
- How many trades were filtered out
- R-multiple impact (positive = filters hurt, negative = filters help)
- Average stop size change
- Win rate changes

Helps determine: Should we keep the filters or remove them?
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def compare_results():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*100)
    print("PHASE 3: COMPARE FILTERED VS NO-MAX RESULTS")
    print("="*100)
    print()

    # Get common configs (exist in both tables)
    common_configs = con.execute("""
        WITH filtered_configs AS (
            SELECT DISTINCT orb, close_confirmations, rr, sl_mode, buffer_ticks
            FROM orb_trades_5m_exec
        ),
        nomax_configs AS (
            SELECT DISTINCT orb, close_confirmations, rr, sl_mode, buffer_ticks
            FROM orb_trades_5m_exec_nomax
        )
        SELECT f.*
        FROM filtered_configs f
        INNER JOIN nomax_configs n
            ON f.orb = n.orb
            AND f.close_confirmations = n.close_confirmations
            AND f.rr = n.rr
            AND f.sl_mode = n.sl_mode
            AND f.buffer_ticks = n.buffer_ticks
    """).fetchdf()

    print(f"Found {len(common_configs)} common configurations in both tables")
    print()

    # Compare overall stats
    print("OVERALL COMPARISON")
    print("-"*100)

    overall_filtered = con.execute("""
        SELECT
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) FILTER (WHERE outcome IN ('WIN','LOSS')) as win_rate,
            SUM(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) as total_r,
            AVG(stop_ticks) FILTER (WHERE outcome IN ('WIN','LOSS')) as avg_stop
        FROM orb_trades_5m_exec
        WHERE outcome IN ('WIN','LOSS')
    """).fetchone()

    overall_nomax = con.execute("""
        SELECT
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) FILTER (WHERE outcome IN ('WIN','LOSS')) as win_rate,
            SUM(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) as total_r,
            AVG(stop_ticks) FILTER (WHERE outcome IN ('WIN','LOSS')) as avg_stop
        FROM orb_trades_5m_exec_nomax
        WHERE outcome IN ('WIN','LOSS')
    """).fetchone()

    df_overall = pd.DataFrame([
        {
            'version': 'WITH Filters (MAX_STOP=100, ASIA_TP_CAP=150)',
            'trades': overall_filtered[0],
            'win_rate': overall_filtered[1] * 100,
            'total_r': overall_filtered[2],
            'avg_r': overall_filtered[2] / overall_filtered[0] if overall_filtered[0] > 0 else 0,
            'avg_stop': overall_filtered[3]
        },
        {
            'version': 'NO MAX (No Filters)',
            'trades': overall_nomax[0],
            'win_rate': overall_nomax[1] * 100,
            'total_r': overall_nomax[2],
            'avg_r': overall_nomax[2] / overall_nomax[0] if overall_nomax[0] > 0 else 0,
            'avg_stop': overall_nomax[3]
        }
    ])

    print(df_overall.to_string(index=False))
    print()

    trades_filtered_out = overall_nomax[0] - overall_filtered[0]
    r_difference = overall_nomax[2] - overall_filtered[2]

    print(f"Trades filtered out: {trades_filtered_out:,} ({trades_filtered_out/overall_nomax[0]*100:.1f}% of no-max)")
    print(f"R-multiple difference: {r_difference:+.1f}R")
    print()

    if r_difference > 0:
        print("[INSIGHT] Filters HURT performance (removed {:.1f}R)".format(abs(r_difference)))
        print("          Consider REMOVING filters")
    elif r_difference < 0:
        print("[INSIGHT] Filters HELP performance (saved {:.1f}R)".format(abs(r_difference)))
        print("          Consider KEEPING filters")
    else:
        print("[INSIGHT] Filters have NEUTRAL impact")

    print()
    print()

    # Compare by session
    print("SESSION-BY-SESSION COMPARISON")
    print("-"*100)

    sessions = ['0900', '1000', '1100', '1800', '2300', '0030']

    session_comparison = []

    for session in sessions:
        filtered = con.execute("""
            SELECT
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) FILTER (WHERE outcome IN ('WIN','LOSS')) as win_rate,
                SUM(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) as total_r
            FROM orb_trades_5m_exec
            WHERE orb = ? AND outcome IN ('WIN','LOSS')
        """, [session]).fetchone()

        nomax = con.execute("""
            SELECT
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
                AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) FILTER (WHERE outcome IN ('WIN','LOSS')) as win_rate,
                SUM(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) as total_r
            FROM orb_trades_5m_exec_nomax
            WHERE orb = ? AND outcome IN ('WIN','LOSS')
        """, [session]).fetchone()

        if filtered[0] > 0 or nomax[0] > 0:
            session_comparison.append({
                'session': session,
                'trades_filtered': filtered[0],
                'trades_nomax': nomax[0],
                'trades_removed': nomax[0] - filtered[0],
                'wr_filtered': filtered[1] * 100 if filtered[1] else 0,
                'wr_nomax': nomax[1] * 100 if nomax[1] else 0,
                'r_filtered': filtered[2] if filtered[2] else 0,
                'r_nomax': nomax[2] if nomax[2] else 0,
                'r_diff': (nomax[2] if nomax[2] else 0) - (filtered[2] if filtered[2] else 0)
            })

    df_session = pd.DataFrame(session_comparison)

    # Format for display
    df_display = df_session.copy()
    df_display['trades_filtered'] = df_display['trades_filtered'].astype(int)
    df_display['trades_nomax'] = df_display['trades_nomax'].astype(int)
    df_display['trades_removed'] = df_display['trades_removed'].astype(int)

    print(df_display.to_string(index=False))
    print()

    # Interpretation
    print("="*100)
    print("INTERPRETATION")
    print("="*100)
    print()

    sessions_hurt = df_session[df_session['r_diff'] > 5]
    sessions_helped = df_session[df_session['r_diff'] < -5]
    sessions_neutral = df_session[(df_session['r_diff'] >= -5) & (df_session['r_diff'] <= 5)]

    if len(sessions_hurt) > 0:
        print("SESSIONS WHERE FILTERS HURT (lost >5R):")
        for _, row in sessions_hurt.iterrows():
            print(f"  {row['session']}: Lost {row['r_diff']:.1f}R by filtering out {row['trades_removed']} trades")
        print()

    if len(sessions_helped) > 0:
        print("SESSIONS WHERE FILTERS HELP (saved >5R):")
        for _, row in sessions_helped.iterrows():
            print(f"  {row['session']}: Saved {abs(row['r_diff']):.1f}R by filtering out {row['trades_removed']} trades")
        print()

    if len(sessions_neutral) > 0:
        print("SESSIONS WHERE FILTERS NEUTRAL (-5R to +5R):")
        for _, row in sessions_neutral.iterrows():
            print(f"  {row['session']}: {row['r_diff']:+.1f}R difference")
        print()

    # Recommendation
    print("="*100)
    print("RECOMMENDATION")
    print("="*100)
    print()

    if r_difference > 20:
        print("STRONG RECOMMENDATION: REMOVE FILTERS")
        print(f"  Filters cost you {r_difference:.1f}R across all sessions")
        print("  The MAX_STOP=100 and ASIA_TP_CAP=150 filters are hurting performance")
    elif r_difference < -20:
        print("STRONG RECOMMENDATION: KEEP FILTERS")
        print(f"  Filters saved you {abs(r_difference):.1f}R across all sessions")
        print("  The MAX_STOP=100 and ASIA_TP_CAP=150 filters are protecting you from bad trades")
    else:
        print("MODERATE RECOMMENDATION: Filters have minimal impact")
        print(f"  Net difference: {r_difference:+.1f}R")
        print("  Consider session-specific filter rules instead of blanket approach")

    print()
    print("="*100)

    con.close()

if __name__ == "__main__":
    compare_results()
