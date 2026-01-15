"""
Session Correlation Analysis

Finds edges based on relationships between sessions:
- If 09:00 breaks UP, does 10:00 also break UP?
- If 18:00 wins, does 23:00 win?
- Session momentum vs reversal patterns
- Conditional win rates (trade X only if Y happened)
"""

import duckdb
import pandas as pd
from itertools import combinations

DB_PATH = "gold.db"

def analyze_correlations():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*100)
    print("SESSION CORRELATION & PATTERN ANALYSIS")
    print("="*100)
    print()

    # ========================================================================
    # 1. GET ALL ORB BREAKS FROM DAILY FEATURES
    # ========================================================================
    print("Loading ORB break data from daily_features_v2...")

    df_orbs = con.execute("""
        SELECT
            date_local,
            orb_0900_break_dir as d_0900,
            orb_1000_break_dir as d_1000,
            orb_1100_break_dir as d_1100,
            orb_1800_break_dir as d_1800,
            orb_2300_break_dir as d_2300,
            orb_0030_break_dir as d_0030
        FROM daily_features_v2
        WHERE date_local >= '2023-01-01'
        ORDER BY date_local
    """).fetchdf()

    print(f"Loaded {len(df_orbs)} days of ORB data")
    print()

    # ========================================================================
    # 2. SAME-DAY DIRECTIONAL CORRELATIONS
    # ========================================================================
    print("1. SAME-DAY DIRECTIONAL CORRELATIONS")
    print("-"*100)
    print("If session X breaks in a direction, what's the probability session Y breaks same direction?")
    print()

    sessions = ['0900', '1000', '1100', '1800', '2300', '0030']

    for sess1, sess2 in combinations(sessions, 2):
        col1 = f'd_{sess1}'
        col2 = f'd_{sess2}'

        # Filter for days where both sessions have breaks
        valid = df_orbs[(df_orbs[col1].notna()) & (df_orbs[col2].notna())].copy()

        if len(valid) == 0:
            continue

        # Count same direction
        same_dir = (valid[col1] == valid[col2]).sum()
        total = len(valid)
        pct_same = same_dir / total * 100

        # Count UP->UP and DOWN->DOWN
        up_up = ((valid[col1] == 'UP') & (valid[col2] == 'UP')).sum()
        down_down = ((valid[col1] == 'DOWN') & (valid[col2] == 'DOWN')).sum()

        up_total = (valid[col1] == 'UP').sum()
        down_total = (valid[col1] == 'DOWN').sum()

        up_follow = (up_up / up_total * 100) if up_total > 0 else 0
        down_follow = (down_down / down_total * 100) if down_total > 0 else 0

        print(f"{sess1} → {sess2}:")
        print(f"  Same direction: {same_dir}/{total} ({pct_same:.1f}%)")
        print(f"  UP follows UP: {up_up}/{up_total} ({up_follow:.1f}%)")
        print(f"  DOWN follows DOWN: {down_down}/{down_total} ({down_follow:.1f}%)")

        # Highlight strong correlations
        if pct_same > 55:
            print(f"  >>> MOMENTUM PATTERN (>{55}% same direction)")
        elif pct_same < 45:
            print(f"  >>> REVERSAL PATTERN (<{45}% same direction)")
        print()

    # ========================================================================
    # 3. CONDITIONAL WIN RATES (USING BEST VARIANTS)
    # ========================================================================
    print("2. CONDITIONAL WIN RATES BY PREVIOUS SESSION")
    print("-"*100)
    print("How does your win rate change based on what happened in the previous session?")
    print()

    # Get trade results from best 1m variant for each session
    df_trades = con.execute("""
        SELECT
            date_local,
            orb,
            direction,
            outcome,
            r_multiple
        FROM orb_trades_1m_exec
        WHERE outcome IN ('WIN', 'LOSS')
    """).fetchdf()

    # Merge with ORB break directions
    df_merged = df_trades.merge(df_orbs, on='date_local', how='left')

    # Analyze each session
    for sess in sessions:
        sess_trades = df_merged[df_merged['orb'] == sess].copy()

        if len(sess_trades) == 0:
            continue

        print(f"\n{sess} ORB - Conditional Analysis:")
        print("-"*60)

        # Find previous session (chronologically earlier on same day)
        sess_idx = sessions.index(sess)
        if sess_idx == 0:
            prev_sessions = []
        else:
            prev_sessions = sessions[:sess_idx]

        for prev_sess in prev_sessions:
            prev_col = f'd_{prev_sess}'

            # Win rate when prev session broke UP
            up_trades = sess_trades[sess_trades[prev_col] == 'UP']
            if len(up_trades) > 0:
                up_wr = (up_trades['outcome'] == 'WIN').mean()
                up_r = up_trades['r_multiple'].sum()
                print(f"  After {prev_sess} UP: WR={up_wr:.1%}, Total R={up_r:+.1f} ({len(up_trades)} trades)")

            # Win rate when prev session broke DOWN
            down_trades = sess_trades[sess_trades[prev_col] == 'DOWN']
            if len(down_trades) > 0:
                down_wr = (down_trades['outcome'] == 'WIN').mean()
                down_r = down_trades['r_multiple'].sum()
                print(f"  After {prev_sess} DOWN: WR={down_wr:.1%}, Total R={down_r:+.1f} ({len(down_trades)} trades)")

            # Overall for comparison
            overall_wr = (sess_trades['outcome'] == 'WIN').mean()
            overall_r = sess_trades['r_multiple'].sum()

            # Highlight significant differences
            if len(up_trades) > 20 and len(down_trades) > 20:
                if up_r > down_r + 20:
                    print(f"    >>> EDGE: Trade {sess} ONLY after {prev_sess} breaks UP (+{up_r - down_r:.0f}R)")
                elif down_r > up_r + 20:
                    print(f"    >>> EDGE: Trade {sess} ONLY after {prev_sess} breaks DOWN (+{down_r - up_r:.0f}R)")

    # ========================================================================
    # 4. SESSION CLUSTER ANALYSIS
    # ========================================================================
    print("\n3. SESSION CLUSTER PERFORMANCE")
    print("-"*100)
    print("Which session combinations perform best together?")
    print()

    # Asia cluster (09:00, 10:00, 11:00)
    asia_all_up = ((df_orbs['d_0900'] == 'UP') & (df_orbs['d_1000'] == 'UP') & (df_orbs['d_1100'] == 'UP')).sum()
    asia_all_down = ((df_orbs['d_0900'] == 'DOWN') & (df_orbs['d_1000'] == 'DOWN') & (df_orbs['d_1100'] == 'DOWN')).sum()
    asia_total = len(df_orbs[df_orbs['d_0900'].notna() & df_orbs['d_1000'].notna() & df_orbs['d_1100'].notna()])

    print(f"ASIA SESSION (09:00, 10:00, 11:00):")
    print(f"  All break UP: {asia_all_up}/{asia_total} ({asia_all_up/asia_total*100:.1f}%)")
    print(f"  All break DOWN: {asia_all_down}/{asia_total} ({asia_all_down/asia_total*100:.1f}%)")
    print(f"  Trend days (all same): {(asia_all_up + asia_all_down)}/{asia_total} ({(asia_all_up + asia_all_down)/asia_total*100:.1f}%)")
    print()

    # Evening cluster (18:00, 23:00, 00:30)
    eve_all_up = ((df_orbs['d_1800'] == 'UP') & (df_orbs['d_2300'] == 'UP') & (df_orbs['d_0030'] == 'UP')).sum()
    eve_all_down = ((df_orbs['d_1800'] == 'DOWN') & (df_orbs['d_2300'] == 'DOWN') & (df_orbs['d_0030'] == 'DOWN')).sum()
    eve_total = len(df_orbs[df_orbs['d_1800'].notna() & df_orbs['d_2300'].notna() & df_orbs['d_0030'].notna()])

    print(f"EVENING SESSION (18:00, 23:00, 00:30):")
    print(f"  All break UP: {eve_all_up}/{eve_total} ({eve_all_up/eve_total*100:.1f}%)")
    print(f"  All break DOWN: {eve_all_down}/{eve_total} ({eve_all_down/eve_total*100:.1f}%)")
    print(f"  Trend days (all same): {(eve_all_up + eve_all_down)}/{eve_total} ({(eve_all_up + eve_all_down)/eve_total*100:.1f}%)")
    print()

    # ========================================================================
    # 5. EXPORT CORRELATION MATRIX
    # ========================================================================
    print("4. EXPORTING CORRELATION MATRIX")
    print("-"*100)

    # Create numeric encoding for correlation
    orb_numeric = df_orbs.copy()
    for col in orb_numeric.columns:
        if col.startswith('d_'):
            orb_numeric[col] = orb_numeric[col].map({'UP': 1, 'DOWN': -1, 'NONE': 0})

    corr_matrix = orb_numeric[[f'd_{s}' for s in sessions]].corr()
    corr_matrix.columns = sessions
    corr_matrix.index = sessions

    corr_matrix.to_csv('session_correlations.csv')
    print("Correlation matrix exported to: session_correlations.csv")
    print()
    print(corr_matrix.round(2))
    print()

    print("="*100)
    print("CORRELATION ANALYSIS COMPLETE")
    print("="*100)
    print()
    print("Look for:")
    print("1. High correlation (>0.3): Sessions that trend together")
    print("2. Negative correlation (<-0.2): Sessions that reverse each other")
    print("3. Conditional edges: Only trade session X after session Y breaks in direction Z")

    con.close()

if __name__ == "__main__":
    analyze_correlations()
