"""
PHASE 1 — Map 0030 NYC ORB Behavior

1. Summarize baseline breakout results at 0030
2. Identify liquidity magnets available in data
3. Propose session-specific hypotheses

Using ONLY existing tables: daily_features_v2, bars_1m, bars_5m
"""

import duckdb
import pandas as pd
import numpy as np

DB_PATH = "gold.db"
SYMBOL = "MGC"
ORB_CODE = "0030"

def analyze_baseline_breakout(con):
    """Summarize baseline 0030 breakout performance."""

    print("="*80)
    print("BASELINE 0030 BREAKOUT ANALYSIS")
    print("="*80)
    print()

    # Get all 0030 baseline trades
    baseline = con.execute("""
        SELECT
            COUNT(*) as n_trades,
            AVG(r_multiple) as avg_r,
            SUM(r_multiple) as total_r,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
            AVG(CASE WHEN outcome = 'WIN' THEN r_multiple END) as avg_win,
            AVG(CASE WHEN outcome = 'LOSS' THEN r_multiple END) as avg_loss
        FROM orb_trades_1m_exec_nofilters
        WHERE orb = '0030'
            AND close_confirmations = 1
            AND rr = 1.0
    """).fetchone()

    n_trades, avg_r, total_r, win_rate, avg_win, avg_loss = baseline

    print(f"Total trades: {n_trades}")
    print(f"Avg R: {avg_r:+.3f}R")
    print(f"Total R: {total_r:+.2f}R")
    print(f"Win rate: {win_rate:.1f}%")
    print(f"Avg win: {avg_win:+.3f}R")
    print(f"Avg loss: {avg_loss:+.3f}R")
    print()

    # ORB size distribution
    orb_sizes = con.execute("""
        SELECT
            orb_0030_size
        FROM daily_features_v2
        WHERE orb_0030_size IS NOT NULL
            AND instrument = 'MGC'
    """).df()

    if not orb_sizes.empty:
        print("ORB SIZE DISTRIBUTION:")
        print(f"  Min: {orb_sizes['orb_0030_size'].min():.1f} ticks")
        print(f"  Median: {orb_sizes['orb_0030_size'].median():.1f} ticks")
        print(f"  Mean: {orb_sizes['orb_0030_size'].mean():.1f} ticks")
        print(f"  Max: {orb_sizes['orb_0030_size'].max():.1f} ticks")

        # Percentiles
        p25 = orb_sizes['orb_0030_size'].quantile(0.25)
        p75 = orb_sizes['orb_0030_size'].quantile(0.75)
        print(f"  25th percentile: {p25:.1f} ticks")
        print(f"  75th percentile: {p75:.1f} ticks")
        print()

    return baseline


def check_available_liquidity_magnets(con):
    """Check what liquidity reference levels are available in daily_features_v2."""

    print("="*80)
    print("AVAILABLE LIQUIDITY MAGNETS (Pre-0030 Information)")
    print("="*80)
    print()

    # Get column list from daily_features_v2
    columns = con.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'daily_features_v2'
        ORDER BY column_name
    """).df()

    print("Session levels available:")
    session_levels = [col for col in columns['column_name'] if 'high' in col or 'low' in col]

    relevant_levels = []

    for level in session_levels:
        if any(x in level for x in ['asia', 'london', 'ny', 'prev', 'prior', '2300', '1800']):
            relevant_levels.append(level)

    if relevant_levels:
        for level in sorted(relevant_levels):
            print(f"  - {level}")
    else:
        print("  [Checking actual data...]")

        # Try to find what's actually available
        sample = con.execute("""
            SELECT *
            FROM daily_features_v2
            WHERE instrument = 'MGC'
            LIMIT 1
        """).df()

        # Find columns with 'high' or 'low'
        level_cols = [col for col in sample.columns if 'high' in col.lower() or 'low' in col.lower()]

        print("\n  Available level columns:")
        for col in sorted(level_cols):
            print(f"    - {col}")

    print()

    # Check if we have pre-session data
    pre_session_check = con.execute("""
        SELECT
            COUNT(*) as n_with_pre_asia,
            SUM(CASE WHEN pre_london_high IS NOT NULL THEN 1 ELSE 0 END) as n_with_pre_london,
            SUM(CASE WHEN pre_ny_high IS NOT NULL THEN 1 ELSE 0 END) as n_with_pre_ny
        FROM daily_features_v2
        WHERE instrument = 'MGC'
            AND pre_asia_high IS NOT NULL
    """).fetchone()

    print(f"Pre-session levels available:")
    print(f"  - Pre-Asia levels: {pre_session_check[0]} days")
    print(f"  - Pre-London levels: {pre_session_check[1]} days")
    print(f"  - Pre-NY levels: {pre_session_check[2]} days")

    print()

    return relevant_levels


def analyze_0030_timing_context(con):
    """Analyze what happens BEFORE 0030 (context available for state filtering)."""

    print("="*80)
    print("0030 TIMING CONTEXT (Pre-ORB Information)")
    print("="*80)
    print()

    print("Time sequence (Brisbane UTC+10):")
    print("  - Prior day: 09:00 -> 23:00 (full day trading)")
    print("  - 23:00-23:05: 2300 ORB (last session before NYC open)")
    print("  - 23:05-00:30: Gap period (85 minutes)")
    print("  - 00:30-00:35: 0030 ORB (NYC OPEN)")
    print()

    print("Available pre-0030 information:")
    print("  1. Prior day range, high, low, close")
    print("  2. Session stats: Asia (09:00-17:00), London (18:00-23:00)")
    print("  3. 2300 ORB levels (completed 85 minutes before)")
    print("  4. Gap period behavior (23:05-00:30)")
    print()

    # Check 2300 ORB completion vs 0030 ORB
    print("Key insight: 2300 ORB closes 85 minutes BEFORE 0030 ORB")
    print("  - Can use 2300 ORB levels as reference")
    print("  - Can measure gap period travel (23:05-00:30)")
    print("  - Can identify if price swept levels during gap")
    print()


def propose_hypotheses():
    """Propose session-specific hypotheses for 0030 ORB."""

    print("="*80)
    print("0030-SPECIFIC HYPOTHESES")
    print("="*80)
    print()

    hypotheses = [
        {
            'num': 1,
            'name': 'NYC Open Exhaustion',
            'description': 'First impulse after 0030 extends hard (>2x ORB size) then stalls -> fade',
            'reasoning': 'NYC volatility spike exhausts quickly, reverses to mean'
        },
        {
            'num': 2,
            'name': 'Gap Sweep Rejection',
            'description': 'Price sweeps 2300 ORB or London high/low during gap (23:05-00:30), then 0030 rejects that level',
            'reasoning': 'Liquidity grab during thin gap period gets rejected at NYC open volume'
        },
        {
            'num': 3,
            'name': 'No-Side-Chosen Trap',
            'description': 'If 0030 stays inside ORB for 15+ minutes, first sweep is a trap',
            'reasoning': 'Prolonged balance signals indecision -> first break likely false'
        },
        {
            'num': 4,
            'name': 'Double-Failure Expansion',
            'description': 'Price breaks ORB up, fails, breaks down, fails -> fade second failure',
            'reasoning': 'Two failed attempts signal no conviction, mean reversion likely'
        },
        {
            'num': 5,
            'name': 'Gap Continuation (NOT fade)',
            'description': 'If gap shows strong directional bias, 0030 continues that direction after sweep',
            'reasoning': 'Strong overnight trend continues at NYC open, sweep is retest not reversal'
        },
        {
            'num': 6,
            'name': 'Prior Day Level Magnet',
            'description': 'Price gravitates toward prior day high/low in first 30 minutes',
            'reasoning': 'NYC traders reference previous session close levels'
        },
        {
            'num': 7,
            'name': 'Small ORB Breakout Failure',
            'description': 'When ORB size < 3 ticks, breakouts fail more often (fade opportunity)',
            'reasoning': 'Tight consolidation before NYC open signals compression, fake breaks likely'
        },
        {
            'num': 8,
            'name': 'Post-Sweep Acceptance Test',
            'description': 'After level sweep, wait for 5m close ACCEPTANCE (beyond) or REJECTION (back inside) - only trade rejections',
            'reasoning': 'Differentiates true breakouts from liquidity grabs'
        }
    ]

    for h in hypotheses:
        print(f"H{h['num']}: {h['name']}")
        print(f"  Pattern: {h['description']}")
        print(f"  Reasoning: {h['reasoning']}")
        print()


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("\n")
    print("*"*80)
    print("PHASE 1 — 0030 ORB BEHAVIOR MAPPING")
    print("*"*80)
    print("\n")

    # 1. Baseline breakout analysis
    analyze_baseline_breakout(con)

    # 2. Available liquidity magnets
    check_available_liquidity_magnets(con)

    # 3. Timing context
    analyze_0030_timing_context(con)

    # 4. Hypotheses
    propose_hypotheses()

    print("="*80)
    print("PHASE 1 COMPLETE")
    print("="*80)
    print()
    print("Next: PHASE 2 - Test 5 pattern families with 2-4 states each")
    print()

    con.close()


if __name__ == '__main__':
    main()
