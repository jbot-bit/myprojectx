"""
PHASE 1 — SESSION REALITY CHECK

For each ORB session, describe dominant liquidity behavior.
Determine if structurally suitable for reaction trading.

STRICT RULES:
- Use ONLY existing pre-computed fields
- No derivations or recomputations
- Attempt to DISPROVE suitability first
- Report failures honestly

DATA SOURCES (locked):
- daily_features (for ORB data)
- bars_1m (for intrabar behavior)
- orb_trades_1m_exec_nofilters (for baseline breakout reference)
"""

import duckdb
import pandas as pd
import numpy as np

DB_PATH = "gold.db"

ORBS = ['0900', '1000', '1100', '1800', '2300', '0030']

def analyze_orb_session(con, orb_code):
    """
    Describe dominant liquidity behavior for this ORB.
    Use ONLY existing fields.
    """

    print("="*80)
    print(f"SESSION: {orb_code} ORB")
    print("="*80)
    print()

    # 1. Get ORB baseline stats (from existing backtest)
    baseline = con.execute("""
        SELECT
            orb,
            COUNT(*) as n_trades,
            AVG(r_multiple) as avg_r,
            SUM(r_multiple) as total_r,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
        FROM orb_trades_1m_exec_nofilters
        WHERE orb = ?
            AND close_confirmations = 1
        GROUP BY orb
    """, [orb_code]).fetchone()

    if baseline is None:
        print(f"[ERROR] No baseline data for {orb_code}")
        return None

    orb, n_trades, avg_r, total_r, win_rate = baseline

    print(f"BASELINE BREAKOUT PERFORMANCE:")
    print(f"  Trades: {n_trades}")
    print(f"  Avg R: {avg_r:+.3f}R")
    print(f"  Total R: {total_r:+.1f}R")
    print(f"  Win Rate: {win_rate:.1f}%")
    print()

    # 2. Get ORB size distribution (measures volatility/range)
    orb_sizes = con.execute(f"""
        SELECT
            orb_{orb_code}_size as orb_size
        FROM daily_features
        WHERE orb_{orb_code}_size IS NOT NULL
    """).df()

    if orb_sizes.empty:
        print(f"[ERROR] No ORB size data")
        return None

    median_orb_size = orb_sizes['orb_size'].median()
    mean_orb_size = orb_sizes['orb_size'].mean()
    std_orb_size = orb_sizes['orb_size'].std()

    print(f"ORB SIZE CHARACTERISTICS:")
    print(f"  Median: {median_orb_size:.1f} ticks")
    print(f"  Mean: {mean_orb_size:.1f} ticks")
    print(f"  Std Dev: {std_orb_size:.1f} ticks")
    print(f"  CV: {(std_orb_size/mean_orb_size)*100:.1f}% (volatility)")
    print()

    # 3. Breakout direction bias (UP vs DOWN wins)
    breakout_direction = con.execute("""
        SELECT
            direction,
            COUNT(*) as n,
            AVG(r_multiple) as avg_r,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
        FROM orb_trades_1m_exec_nofilters
        WHERE orb = ?
            AND close_confirmations = 1
        GROUP BY direction
    """, [orb_code]).fetchall()

    print(f"DIRECTIONAL BIAS (BREAKOUT):")
    for row in breakout_direction:
        direction, n, avg_r_dir, wr_dir = row
        print(f"  {direction}: {n} trades, {avg_r_dir:+.3f}R avg, {wr_dir:.1f}% WR")
    print()

    # 4. ORB break rate (how often does price break out?)
    break_rate = con.execute(f"""
        SELECT
            orb_{orb_code}_break_dir as break_dir,
            COUNT(*) as n
        FROM daily_features
        WHERE orb_{orb_code}_break_dir IS NOT NULL
        GROUP BY orb_{orb_code}_break_dir
    """).fetchall()

    total_days = sum(row[1] for row in break_rate)

    print(f"ORB BREAK FREQUENCY:")
    for row in break_rate:
        break_dir, n = row
        pct = (n / total_days * 100) if total_days > 0 else 0
        print(f"  {break_dir}: {n} days ({pct:.1f}%)")
    print()

    # 5. LIQUIDITY ASSESSMENT
    print("LIQUIDITY BEHAVIOR ASSESSMENT:")
    print("-"*80)

    # Strong breakout = NOT suitable for reaction
    # Weak/negative breakout = potentially suitable for reaction

    if avg_r > 0.05:
        liquidity_verdict = "STRONG DIRECTIONAL (breakout works)"
        reaction_suitable = "UNLIKELY - Price follows through on breaks"
    elif avg_r > -0.05:
        liquidity_verdict = "NEUTRAL/MIXED (breakout marginal)"
        reaction_suitable = "POSSIBLE - No clear directional bias"
    else:
        liquidity_verdict = "WEAK/CHOPPY (breakout fails)"
        reaction_suitable = "LIKELY - Breakouts frequently fail (reaction opportunity)"

    print(f"  Pattern: {liquidity_verdict}")
    print(f"  Reaction Suitability: {reaction_suitable}")
    print()

    # 6. VERDICT
    print("="*80)
    print("VERDICT")
    print("="*80)
    print()

    if avg_r > 0.05:
        print(f"[NOT SUITABLE] {orb_code} ORB shows strong directional breakout edge")
        print(f"Baseline breakout: {avg_r:+.3f}R avg")
        print(f"Liquidity follows through - reaction trading NOT appropriate")
        print()
        print("RECOMMENDATION: Trade baseline breakout, skip reaction testing")
        suitable = False
    elif avg_r > -0.05:
        print(f"[MARGINAL] {orb_code} ORB shows weak/neutral breakout")
        print(f"Baseline breakout: {avg_r:+.3f}R avg")
        print(f"Liquidity is mixed - reaction trading MAY work")
        print()
        print("RECOMMENDATION: Test reaction approach cautiously")
        suitable = True
    else:
        print(f"[SUITABLE] {orb_code} ORB shows failing breakouts")
        print(f"Baseline breakout: {avg_r:+.3f}R avg (negative)")
        print(f"Liquidity fails after breaks - strong reaction candidate")
        print()
        print("RECOMMENDATION: Test reaction approach (failures = opportunity)")
        suitable = True

    print()

    return {
        'orb_code': orb_code,
        'baseline_avg_r': avg_r,
        'baseline_total_r': total_r,
        'baseline_wr': win_rate,
        'n_trades': n_trades,
        'median_orb_size': median_orb_size,
        'liquidity_verdict': liquidity_verdict,
        'reaction_suitable': suitable
    }


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print()
    print("="*80)
    print("PHASE 1 — SESSION REALITY CHECK")
    print("="*80)
    print()
    print("Testing all 6 ORB sessions for liquidity behavior")
    print("Goal: DISPROVE suitability for reaction trading")
    print()

    results = []

    for orb_code in ORBS:
        result = analyze_orb_session(con, orb_code)
        if result:
            results.append(result)

    # Summary table
    print()
    print("="*80)
    print("SUMMARY: ALL 6 ORB SESSIONS")
    print("="*80)
    print()

    df = pd.DataFrame(results)

    print(f"{'ORB':<6} {'Baseline R':<12} {'ORB Size':<12} {'Suitable?':<12} {'Verdict':<30}")
    print("-"*80)

    for _, row in df.iterrows():
        suitable_str = "YES" if row['reaction_suitable'] else "NO"
        print(f"{row['orb_code']:<6} {row['baseline_avg_r']:+.3f}R      {row['median_orb_size']:.1f} ticks   {suitable_str:<12} {row['liquidity_verdict']:<30}")

    print()
    print("="*80)
    print("SESSIONS TO TEST WITH REACTION APPROACH:")
    print("="*80)
    print()

    suitable_sessions = df[df['reaction_suitable'] == True]

    if len(suitable_sessions) == 0:
        print("[NONE] All sessions show strong directional breakout edges")
        print("Reaction trading NOT appropriate for any session")
        print()
        print("RECOMMENDATION: Trade baseline breakouts only")
    else:
        print(f"Total suitable: {len(suitable_sessions)}/6")
        print()
        for _, row in suitable_sessions.iterrows():
            print(f"  {row['orb_code']}: {row['liquidity_verdict']}")
        print()
        print("NEXT PHASE: Test reaction approach on suitable sessions ONLY")

    print()

    # Save results
    df.to_csv('session_reality_check_results.csv', index=False)
    print("Results saved to: session_reality_check_results.csv")
    print()

    con.close()


if __name__ == '__main__':
    main()
