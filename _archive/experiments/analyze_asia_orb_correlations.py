"""
ASIA ORB CORRELATION ANALYSIS

Analyze correlations between Asia ORBs (09:00, 10:00, 11:00) to identify
patterns that increase probability.

Questions:
1. Does 09:00 outcome predict 10:00 performance?
2. Does 10:00 outcome predict 11:00 performance?
3. Do specific sequences improve expectancy?
4. Is there a 3-ORB system with higher probability?

Data source: v_orb_trades_half (RR=1.0, realistic entry)
"""

import duckdb
import sys

# Configuration
MIN_SAMPLE_SIZE = 30
SIGNIFICANT_DELTA = 0.15  # R improvement threshold

def main():
    con = duckdb.connect('gold.db', read_only=True)

    print("=" * 80)
    print("ASIA ORB CORRELATION ANALYSIS")
    print("=" * 80)
    print()

    # Step 1: Get baseline performance for each Asia ORB
    print("STEP 1: BASELINE PERFORMANCE (UNCONDITIONAL)")
    print("-" * 80)

    baselines = {}
    for orb_code in ['0900', '1000', '1100']:
        result = con.execute("""
            SELECT
                COUNT(*) as trades,
                AVG(r_multiple) as avg_r,
                AVG(CASE WHEN r_multiple > 0 THEN 1.0 ELSE 0.0 END) as win_rate
            FROM v_orb_trades_half
            WHERE orb_code = ?
        """, [orb_code]).fetchone()

        baselines[orb_code] = {
            'trades': result[0],
            'avg_r': result[1],
            'win_rate': result[2]
        }

        print(f"{orb_code} ORB:")
        print(f"  Trades: {result[0]}")
        print(f"  Avg R: {result[1]:+.3f}R")
        print(f"  Win Rate: {result[2]*100:.1f}%")
        print()

    # Step 2: Analyze same-day occurrences
    print("STEP 2: SAME-DAY OCCURRENCE ANALYSIS")
    print("-" * 80)

    # Get days with multiple ORBs
    multi_orb_days = con.execute("""
        SELECT
            date_local,
            COUNT(*) as orb_count,
            STRING_AGG(orb_code || ':' || direction || ':' ||
                      CASE WHEN r_multiple > 0 THEN 'WIN' ELSE 'LOSS' END,
                      ', ' ORDER BY orb_code) as orb_sequence
        FROM v_orb_trades_half
        WHERE orb_code IN ('0900', '1000', '1100')
        GROUP BY date_local
        HAVING COUNT(*) >= 2
        ORDER BY date_local
    """).fetchall()

    print(f"Days with 2+ Asia ORBs: {len(multi_orb_days)}")

    # Count sequence patterns
    three_orb_days = [d for d in multi_orb_days if d[1] == 3]
    two_orb_days = [d for d in multi_orb_days if d[1] == 2]

    print(f"Days with exactly 2 ORBs: {len(two_orb_days)}")
    print(f"Days with all 3 ORBs: {len(three_orb_days)}")
    print()

    # Step 3: Test 09:00 → 10:00 correlation
    print("STEP 3: 09:00 ORB → 10:00 ORB CORRELATION")
    print("-" * 80)

    # Join 09:00 and 10:00 on same day
    correlation_0900_1000 = con.execute("""
        WITH orb_0900 AS (
            SELECT
                date_local,
                direction as dir_0900,
                r_multiple as r_0900,
                CASE WHEN r_multiple > 0 THEN 'WIN' ELSE 'LOSS' END as outcome_0900
            FROM v_orb_trades_half
            WHERE orb_code = '0900'
        ),
        orb_1000 AS (
            SELECT
                date_local,
                direction as dir_1000,
                r_multiple as r_1000,
                CASE WHEN r_multiple > 0 THEN 'WIN' ELSE 'LOSS' END as outcome_1000
            FROM v_orb_trades_half
            WHERE orb_code = '1000'
        )
        SELECT
            a.outcome_0900,
            a.dir_0900,
            COUNT(*) as trades,
            AVG(b.r_1000) as avg_r_1000,
            AVG(CASE WHEN b.r_1000 > 0 THEN 1.0 ELSE 0.0 END) as win_rate_1000,
            SUM(CASE WHEN a.dir_0900 = b.dir_1000 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as same_dir_pct
        FROM orb_0900 a
        INNER JOIN orb_1000 b ON a.date_local = b.date_local
        GROUP BY a.outcome_0900, a.dir_0900
        ORDER BY a.outcome_0900, a.dir_0900
    """).fetchall()

    baseline_1000 = baselines['1000']['avg_r']

    for row in correlation_0900_1000:
        outcome_0900, dir_0900, trades, avg_r_1000, win_rate_1000, same_dir_pct = row
        delta = avg_r_1000 - baseline_1000

        print(f"When 09:00 = {outcome_0900} ({dir_0900}):")
        print(f"  10:00 ORB trades: {trades}")
        print(f"  10:00 ORB avg R: {avg_r_1000:+.3f}R (baseline: {baseline_1000:+.3f}R, delta: {delta:+.3f}R)")
        print(f"  10:00 ORB win rate: {win_rate_1000*100:.1f}%")
        print(f"  Same direction: {same_dir_pct*100:.1f}%")

        if abs(delta) >= SIGNIFICANT_DELTA and trades >= MIN_SAMPLE_SIZE:
            print(f"  >>> SIGNIFICANT IMPROVEMENT: {delta:+.3f}R")

        print()

    # Step 4: Test 10:00 → 11:00 correlation
    print("STEP 4: 10:00 ORB → 11:00 ORB CORRELATION")
    print("-" * 80)

    correlation_1000_1100 = con.execute("""
        WITH orb_1000 AS (
            SELECT
                date_local,
                direction as dir_1000,
                r_multiple as r_1000,
                CASE WHEN r_multiple > 0 THEN 'WIN' ELSE 'LOSS' END as outcome_1000
            FROM v_orb_trades_half
            WHERE orb_code = '1000'
        ),
        orb_1100 AS (
            SELECT
                date_local,
                direction as dir_1100,
                r_multiple as r_1100,
                CASE WHEN r_multiple > 0 THEN 'WIN' ELSE 'LOSS' END as outcome_1100
            FROM v_orb_trades_half
            WHERE orb_code = '1100'
        )
        SELECT
            a.outcome_1000,
            a.dir_1000,
            COUNT(*) as trades,
            AVG(b.r_1100) as avg_r_1100,
            AVG(CASE WHEN b.r_1100 > 0 THEN 1.0 ELSE 0.0 END) as win_rate_1100,
            SUM(CASE WHEN a.dir_1000 = b.dir_1100 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as same_dir_pct
        FROM orb_1000 a
        INNER JOIN orb_1100 b ON a.date_local = b.date_local
        GROUP BY a.outcome_1000, a.dir_1000
        ORDER BY a.outcome_1000, a.dir_1000
    """).fetchall()

    baseline_1100 = baselines['1100']['avg_r']

    for row in correlation_1000_1100:
        outcome_1000, dir_1000, trades, avg_r_1100, win_rate_1100, same_dir_pct = row
        delta = avg_r_1100 - baseline_1100

        print(f"When 10:00 = {outcome_1000} ({dir_1000}):")
        print(f"  11:00 ORB trades: {trades}")
        print(f"  11:00 ORB avg R: {avg_r_1100:+.3f}R (baseline: {baseline_1100:+.3f}R, delta: {delta:+.3f}R)")
        print(f"  11:00 ORB win rate: {win_rate_1100*100:.1f}%")
        print(f"  Same direction: {same_dir_pct*100:.1f}%")

        if abs(delta) >= SIGNIFICANT_DELTA and trades >= MIN_SAMPLE_SIZE:
            print(f"  >>> SIGNIFICANT IMPROVEMENT: {delta:+.3f}R")

        print()

    # Step 5: Test 09:00 → 11:00 correlation (skip 10:00)
    print("STEP 5: 09:00 ORB → 11:00 ORB CORRELATION (DIRECT)")
    print("-" * 80)

    correlation_0900_1100 = con.execute("""
        WITH orb_0900 AS (
            SELECT
                date_local,
                direction as dir_0900,
                r_multiple as r_0900,
                CASE WHEN r_multiple > 0 THEN 'WIN' ELSE 'LOSS' END as outcome_0900
            FROM v_orb_trades_half
            WHERE orb_code = '0900'
        ),
        orb_1100 AS (
            SELECT
                date_local,
                direction as dir_1100,
                r_multiple as r_1100,
                CASE WHEN r_multiple > 0 THEN 'WIN' ELSE 'LOSS' END as outcome_1100
            FROM v_orb_trades_half
            WHERE orb_code = '1100'
        )
        SELECT
            a.outcome_0900,
            a.dir_0900,
            COUNT(*) as trades,
            AVG(b.r_1100) as avg_r_1100,
            AVG(CASE WHEN b.r_1100 > 0 THEN 1.0 ELSE 0.0 END) as win_rate_1100,
            SUM(CASE WHEN a.dir_0900 = b.dir_1100 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as same_dir_pct
        FROM orb_0900 a
        INNER JOIN orb_1100 b ON a.date_local = b.date_local
        GROUP BY a.outcome_0900, a.dir_0900
        ORDER BY a.outcome_0900, a.dir_0900
    """).fetchall()

    for row in correlation_0900_1100:
        outcome_0900, dir_0900, trades, avg_r_1100, win_rate_1100, same_dir_pct = row
        delta = avg_r_1100 - baseline_1100

        print(f"When 09:00 = {outcome_0900} ({dir_0900}):")
        print(f"  11:00 ORB trades: {trades}")
        print(f"  11:00 ORB avg R: {avg_r_1100:+.3f}R (baseline: {baseline_1100:+.3f}R, delta: {delta:+.3f}R)")
        print(f"  11:00 ORB win rate: {win_rate_1100*100:.1f}%")
        print(f"  Same direction: {same_dir_pct*100:.1f}%")

        if abs(delta) >= SIGNIFICANT_DELTA and trades >= MIN_SAMPLE_SIZE:
            print(f"  >>> SIGNIFICANT IMPROVEMENT: {delta:+.3f}R")

        print()

    # Step 6: Test 3-ORB sequences
    print("STEP 6: 3-ORB SEQUENCE ANALYSIS")
    print("-" * 80)

    three_orb_sequences = con.execute("""
        WITH orb_0900 AS (
            SELECT date_local, direction as dir_0900,
                   CASE WHEN r_multiple > 0 THEN 'WIN' ELSE 'LOSS' END as outcome_0900
            FROM v_orb_trades_half WHERE orb_code = '0900'
        ),
        orb_1000 AS (
            SELECT date_local, direction as dir_1000, r_multiple as r_1000,
                   CASE WHEN r_multiple > 0 THEN 'WIN' ELSE 'LOSS' END as outcome_1000
            FROM v_orb_trades_half WHERE orb_code = '1000'
        ),
        orb_1100 AS (
            SELECT date_local, direction as dir_1100, r_multiple as r_1100,
                   CASE WHEN r_multiple > 0 THEN 'WIN' ELSE 'LOSS' END as outcome_1100
            FROM v_orb_trades_half WHERE orb_code = '1100'
        )
        SELECT
            a.outcome_0900 || '-' || b.outcome_1000 as sequence_0900_1000,
            a.dir_0900,
            b.dir_1000,
            COUNT(*) as trades,
            AVG(c.r_1100) as avg_r_1100,
            AVG(CASE WHEN c.r_1100 > 0 THEN 1.0 ELSE 0.0 END) as win_rate_1100
        FROM orb_0900 a
        INNER JOIN orb_1000 b ON a.date_local = b.date_local
        INNER JOIN orb_1100 c ON a.date_local = c.date_local
        GROUP BY a.outcome_0900, b.outcome_1000, a.dir_0900, b.dir_1000
        HAVING COUNT(*) >= ?
        ORDER BY AVG(c.r_1100) DESC
    """, [MIN_SAMPLE_SIZE]).fetchall()

    print(f"Analyzing 3-ORB sequences with >= {MIN_SAMPLE_SIZE} trades:")
    print()

    if three_orb_sequences:
        for row in three_orb_sequences:
            sequence, dir_0900, dir_1000, trades, avg_r_1100, win_rate_1100 = row
            delta = avg_r_1100 - baseline_1100

            print(f"Sequence: {sequence} (09:00 {dir_0900}, 10:00 {dir_1000}):")
            print(f"  11:00 ORB trades: {trades}")
            print(f"  11:00 ORB avg R: {avg_r_1100:+.3f}R (baseline: {baseline_1100:+.3f}R, delta: {delta:+.3f}R)")
            print(f"  11:00 ORB win rate: {win_rate_1100*100:.1f}%")

            if abs(delta) >= SIGNIFICANT_DELTA:
                print(f"  >>> SIGNIFICANT: {delta:+.3f}R improvement")

            print()
    else:
        print("No 3-ORB sequences with sufficient sample size.")
        print()

    # Step 7: Direction persistence analysis
    print("STEP 7: DIRECTION PERSISTENCE ANALYSIS")
    print("-" * 80)

    # Check if all 3 ORBs going same direction improves results
    all_same_dir = con.execute("""
        WITH orb_0900 AS (
            SELECT date_local, direction as dir_0900, r_multiple as r_0900
            FROM v_orb_trades_half WHERE orb_code = '0900'
        ),
        orb_1000 AS (
            SELECT date_local, direction as dir_1000, r_multiple as r_1000
            FROM v_orb_trades_half WHERE orb_code = '1000'
        ),
        orb_1100 AS (
            SELECT date_local, direction as dir_1100, r_multiple as r_1100
            FROM v_orb_trades_half WHERE orb_code = '1100'
        )
        SELECT
            CASE
                WHEN a.dir_0900 = b.dir_1000 AND b.dir_1000 = c.dir_1100 THEN 'ALL_SAME'
                ELSE 'MIXED'
            END as direction_pattern,
            a.dir_0900 as direction,
            COUNT(*) as days,
            AVG(a.r_0900) as avg_r_0900,
            AVG(b.r_1000) as avg_r_1000,
            AVG(c.r_1100) as avg_r_1100,
            AVG((a.r_0900 + b.r_1000 + c.r_1100) / 3.0) as avg_combined_r
        FROM orb_0900 a
        INNER JOIN orb_1000 b ON a.date_local = b.date_local
        INNER JOIN orb_1100 c ON a.date_local = c.date_local
        GROUP BY
            CASE WHEN a.dir_0900 = b.dir_1000 AND b.dir_1000 = c.dir_1100 THEN 'ALL_SAME' ELSE 'MIXED' END,
            a.dir_0900
        HAVING COUNT(*) >= ?
        ORDER BY direction_pattern, direction
    """, [MIN_SAMPLE_SIZE]).fetchall()

    for row in all_same_dir:
        pattern, direction, days, avg_r_0900, avg_r_1000, avg_r_1100, avg_combined = row

        print(f"Pattern: {pattern} ({direction}):")
        print(f"  Days: {days}")
        print(f"  09:00 avg R: {avg_r_0900:+.3f}R")
        print(f"  10:00 avg R: {avg_r_1000:+.3f}R")
        print(f"  11:00 avg R: {avg_r_1100:+.3f}R")
        print(f"  Combined avg: {avg_combined:+.3f}R")
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY AND RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("Analysis complete. Review findings above for:")
    print("1. Cross-ORB outcome correlations (WIN/LOSS dependencies)")
    print("2. Direction persistence patterns (same direction all day)")
    print("3. Sequence-based expectancy improvements (>= +0.15R)")
    print("4. Sample size validation (>= 30 trades per pattern)")
    print()
    print("Recommendations will be based on patterns with both:")
    print("- Significant improvement (>= +0.15R)")
    print("- Sufficient sample size (>= 30 trades)")
    print()

    con.close()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
