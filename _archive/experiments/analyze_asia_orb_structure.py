"""
ASIA ORB STRUCTURAL CORRELATION ANALYSIS

Analyze structural relationships between Asia ORBs (09:00, 10:00, 11:00):
1. Outcome correlations (WIN/LOSS dependencies)
2. Directional persistence (same direction patterns)
3. ORB positioning relationships (10:00 near 09:00 bottom/top, etc.)
4. Price action patterns (drop-lift-form scenarios)

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
    print("ASIA ORB STRUCTURAL CORRELATION ANALYSIS")
    print("=" * 80)
    print()

    # Step 1: Get baseline performance for each Asia ORB
    print("STEP 1: BASELINE PERFORMANCE (UNCONDITIONAL)")
    print("-" * 80)

    baselines = {}
    for orb_time in ['0900', '1000', '1100']:
        result = con.execute("""
            SELECT
                COUNT(*) as trades,
                AVG(r_multiple) as avg_r,
                AVG(CASE WHEN r_multiple > 0 THEN 1.0 ELSE 0.0 END) as win_rate
            FROM v_orb_trades_half
            WHERE orb_time = ?
        """, [orb_time]).fetchone()

        baselines[orb_time] = {
            'trades': result[0],
            'avg_r': result[1],
            'win_rate': result[2]
        }

        print(f"{orb_time} ORB:")
        print(f"  Trades: {result[0]}")
        print(f"  Avg R: {result[1]:+.3f}R")
        print(f"  Win Rate: {result[2]*100:.1f}%")
        print()

    # Step 2: Structural positioning analysis
    print("STEP 2: ORB POSITIONING ANALYSIS")
    print("-" * 80)
    print("Analyzing where subsequent ORBs form relative to previous ORBs...")
    print()

    # Get all ORB data for days with multiple Asia ORBs
    multi_orb_data = con.execute("""
        WITH orb_0900 AS (
            SELECT
                date_local,
                orb_high as high_0900,
                orb_low as low_0900,
                orb_size as size_0900,
                break_dir as dir_0900,
                outcome as outcome_0900,
                r_multiple as r_0900
            FROM v_orb_trades_half
            WHERE orb_time = '0900'
        ),
        orb_1000 AS (
            SELECT
                date_local,
                orb_high as high_1000,
                orb_low as low_1000,
                orb_size as size_1000,
                break_dir as dir_1000,
                outcome as outcome_1000,
                r_multiple as r_1000
            FROM v_orb_trades_half
            WHERE orb_time = '1000'
        ),
        orb_1100 AS (
            SELECT
                date_local,
                orb_high as high_1100,
                orb_low as low_1100,
                orb_size as size_1100,
                break_dir as dir_1100,
                outcome as outcome_1100,
                r_multiple as r_1100
            FROM v_orb_trades_half
            WHERE orb_time = '1100'
        )
        SELECT
            a.date_local,
            -- 09:00 data
            a.high_0900, a.low_0900, a.size_0900, a.dir_0900, a.outcome_0900, a.r_0900,
            -- 10:00 data
            b.high_1000, b.low_1000, b.size_1000, b.dir_1000, b.outcome_1000, b.r_1000,
            -- 11:00 data
            c.high_1100, c.low_1100, c.size_1100, c.dir_1100, c.outcome_1100, c.r_1100
        FROM orb_0900 a
        LEFT JOIN orb_1000 b ON a.date_local = b.date_local
        LEFT JOIN orb_1100 c ON a.date_local = c.date_local
        ORDER BY a.date_local
    """).fetchall()

    # Analyze 10:00 positioning relative to 09:00
    print("A. 10:00 ORB POSITIONING RELATIVE TO 09:00 ORB")
    print()

    positioning_0900_1000 = {
        'near_bottom': [],  # 10:00 mid within 0.5 of 09:00 low
        'near_top': [],     # 10:00 mid within 0.5 of 09:00 high
        'below': [],        # 10:00 entirely below 09:00
        'above': [],        # 10:00 entirely above 09:00
        'overlap': []       # 10:00 overlaps 09:00
    }

    for row in multi_orb_data:
        if row[7] is None:  # No 10:00 ORB
            continue

        date_local = row[0]
        high_0900, low_0900, dir_0900, outcome_0900, r_0900 = row[1], row[2], row[4], row[5], row[6]
        high_1000, low_1000, dir_1000, outcome_1000, r_1000 = row[7], row[8], row[10], row[11], row[12]

        mid_1000 = (high_1000 + low_1000) / 2.0

        # Classify positioning
        if high_1000 < low_0900:
            positioning_0900_1000['below'].append(r_1000)
        elif low_1000 > high_0900:
            positioning_0900_1000['above'].append(r_1000)
        elif abs(mid_1000 - low_0900) <= 0.5:
            positioning_0900_1000['near_bottom'].append(r_1000)
        elif abs(mid_1000 - high_0900) <= 0.5:
            positioning_0900_1000['near_top'].append(r_1000)
        else:
            positioning_0900_1000['overlap'].append(r_1000)

    baseline_1000 = baselines['1000']['avg_r']

    for position, r_values in positioning_0900_1000.items():
        if len(r_values) >= MIN_SAMPLE_SIZE:
            avg_r = sum(r_values) / len(r_values)
            win_rate = sum(1 for r in r_values if r > 0) / len(r_values)
            delta = avg_r - baseline_1000

            print(f"{position.upper().replace('_', ' ')}:")
            print(f"  Occurrences: {len(r_values)}")
            print(f"  10:00 avg R: {avg_r:+.3f}R (baseline: {baseline_1000:+.3f}R, delta: {delta:+.3f}R)")
            print(f"  10:00 win rate: {win_rate*100:.1f}%")

            if abs(delta) >= SIGNIFICANT_DELTA:
                print(f"  >>> SIGNIFICANT: {delta:+.3f}R improvement")

            print()

    # Analyze 11:00 positioning relative to 10:00
    print("B. 11:00 ORB POSITIONING RELATIVE TO 10:00 ORB")
    print()

    positioning_1000_1100 = {
        'near_bottom': [],
        'near_top': [],
        'below': [],
        'above': [],
        'overlap': []
    }

    for row in multi_orb_data:
        if row[7] is None or row[13] is None:  # Missing 10:00 or 11:00
            continue

        high_1000, low_1000 = row[7], row[8]
        high_1100, low_1100, r_1100 = row[13], row[14], row[18]

        mid_1100 = (high_1100 + low_1100) / 2.0

        # Classify positioning
        if high_1100 < low_1000:
            positioning_1000_1100['below'].append(r_1100)
        elif low_1100 > high_1000:
            positioning_1000_1100['above'].append(r_1100)
        elif abs(mid_1100 - low_1000) <= 0.5:
            positioning_1000_1100['near_bottom'].append(r_1100)
        elif abs(mid_1100 - high_1000) <= 0.5:
            positioning_1000_1100['near_top'].append(r_1100)
        else:
            positioning_1000_1100['overlap'].append(r_1100)

    baseline_1100 = baselines['1100']['avg_r']

    for position, r_values in positioning_1000_1100.items():
        if len(r_values) >= MIN_SAMPLE_SIZE:
            avg_r = sum(r_values) / len(r_values)
            win_rate = sum(1 for r in r_values if r > 0) / len(r_values)
            delta = avg_r - baseline_1100

            print(f"{position.upper().replace('_', ' ')}:")
            print(f"  Occurrences: {len(r_values)}")
            print(f"  11:00 avg R: {avg_r:+.3f}R (baseline: {baseline_1100:+.3f}R, delta: {delta:+.3f}R)")
            print(f"  11:00 win rate: {win_rate*100:.1f}%")

            if abs(delta) >= SIGNIFICANT_DELTA:
                print(f"  >>> SIGNIFICANT: {delta:+.3f}R improvement")

            print()

    # Step 3: Outcome correlations
    print("STEP 3: OUTCOME CORRELATION ANALYSIS")
    print("-" * 80)

    # 09:00 → 10:00
    print("A. 09:00 OUTCOME -> 10:00 PERFORMANCE")
    print()

    correlation_0900_1000 = con.execute("""
        WITH orb_0900 AS (
            SELECT
                date_local,
                break_dir as dir_0900,
                outcome as outcome_0900
            FROM v_orb_trades_half
            WHERE orb_time = '0900'
        ),
        orb_1000 AS (
            SELECT
                date_local,
                break_dir as dir_1000,
                r_multiple as r_1000,
                outcome as outcome_1000
            FROM v_orb_trades_half
            WHERE orb_time = '1000'
        )
        SELECT
            a.outcome_0900,
            a.dir_0900,
            COUNT(*) as trades,
            AVG(b.r_1000) as avg_r_1000,
            AVG(CASE WHEN b.outcome_1000 = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate_1000,
            SUM(CASE WHEN a.dir_0900 = b.dir_1000 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as same_dir_pct
        FROM orb_0900 a
        INNER JOIN orb_1000 b ON a.date_local = b.date_local
        GROUP BY a.outcome_0900, a.dir_0900
        ORDER BY a.outcome_0900, a.dir_0900
    """).fetchall()

    for row in correlation_0900_1000:
        outcome_0900, dir_0900, trades, avg_r_1000, win_rate_1000, same_dir_pct = row

        if avg_r_1000 is None:
            continue

        delta = avg_r_1000 - baseline_1000

        print(f"When 09:00 = {outcome_0900} ({dir_0900}):")
        print(f"  10:00 trades: {trades}")
        print(f"  10:00 avg R: {avg_r_1000:+.3f}R (baseline: {baseline_1000:+.3f}R, delta: {delta:+.3f}R)")
        print(f"  10:00 win rate: {win_rate_1000*100:.1f}%")
        print(f"  Same direction: {same_dir_pct*100:.1f}%")

        if abs(delta) >= SIGNIFICANT_DELTA and trades >= MIN_SAMPLE_SIZE:
            print(f"  >>> SIGNIFICANT: {delta:+.3f}R")

        print()

    # 10:00 -> 11:00
    print("B. 10:00 OUTCOME -> 11:00 PERFORMANCE")
    print()

    correlation_1000_1100 = con.execute("""
        WITH orb_1000 AS (
            SELECT
                date_local,
                break_dir as dir_1000,
                outcome as outcome_1000
            FROM v_orb_trades_half
            WHERE orb_time = '1000'
        ),
        orb_1100 AS (
            SELECT
                date_local,
                break_dir as dir_1100,
                r_multiple as r_1100,
                outcome as outcome_1100
            FROM v_orb_trades_half
            WHERE orb_time = '1100'
        )
        SELECT
            a.outcome_1000,
            a.dir_1000,
            COUNT(*) as trades,
            AVG(b.r_1100) as avg_r_1100,
            AVG(CASE WHEN b.outcome_1100 = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate_1100,
            SUM(CASE WHEN a.dir_1000 = b.dir_1100 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as same_dir_pct
        FROM orb_1000 a
        INNER JOIN orb_1100 b ON a.date_local = b.date_local
        GROUP BY a.outcome_1000, a.dir_1000
        ORDER BY a.outcome_1000, a.dir_1000
    """).fetchall()

    for row in correlation_1000_1100:
        outcome_1000, dir_1000, trades, avg_r_1100, win_rate_1100, same_dir_pct = row

        if avg_r_1100 is None:
            continue

        delta = avg_r_1100 - baseline_1100

        print(f"When 10:00 = {outcome_1000} ({dir_1000}):")
        print(f"  11:00 trades: {trades}")
        print(f"  11:00 avg R: {avg_r_1100:+.3f}R (baseline: {baseline_1100:+.3f}R, delta: {delta:+.3f}R)")
        print(f"  11:00 win rate: {win_rate_1100*100:.1f}%")
        print(f"  Same direction: {same_dir_pct*100:.1f}%")

        if abs(delta) >= SIGNIFICANT_DELTA and trades >= MIN_SAMPLE_SIZE:
            print(f"  >>> SIGNIFICANT: {delta:+.3f}R")

        print()

    # Step 4: Direction persistence
    print("STEP 4: DIRECTION PERSISTENCE ANALYSIS")
    print("-" * 80)

    persistence = con.execute("""
        WITH orb_0900 AS (
            SELECT date_local, break_dir as dir_0900, r_multiple as r_0900
            FROM v_orb_trades_half WHERE orb_time = '0900'
        ),
        orb_1000 AS (
            SELECT date_local, break_dir as dir_1000, r_multiple as r_1000
            FROM v_orb_trades_half WHERE orb_time = '1000'
        ),
        orb_1100 AS (
            SELECT date_local, break_dir as dir_1100, r_multiple as r_1100
            FROM v_orb_trades_half WHERE orb_time = '1100'
        )
        SELECT
            CASE
                WHEN a.dir_0900 = b.dir_1000 AND b.dir_1000 = c.dir_1100 THEN 'ALL_SAME'
                WHEN a.dir_0900 = b.dir_1000 OR b.dir_1000 = c.dir_1100 THEN 'PARTIAL'
                ELSE 'ALL_DIFFERENT'
            END as persistence_pattern,
            a.dir_0900 as primary_direction,
            COUNT(*) as days,
            AVG(a.r_0900) as avg_r_0900,
            AVG(b.r_1000) as avg_r_1000,
            AVG(c.r_1100) as avg_r_1100,
            AVG((a.r_0900 + b.r_1000 + c.r_1100) / 3.0) as avg_combined_r
        FROM orb_0900 a
        INNER JOIN orb_1000 b ON a.date_local = b.date_local
        INNER JOIN orb_1100 c ON a.date_local = c.date_local
        GROUP BY
            CASE
                WHEN a.dir_0900 = b.dir_1000 AND b.dir_1000 = c.dir_1100 THEN 'ALL_SAME'
                WHEN a.dir_0900 = b.dir_1000 OR b.dir_1000 = c.dir_1100 THEN 'PARTIAL'
                ELSE 'ALL_DIFFERENT'
            END,
            a.dir_0900
        HAVING COUNT(*) >= ?
        ORDER BY persistence_pattern, primary_direction
    """, [MIN_SAMPLE_SIZE]).fetchall()

    for row in persistence:
        pattern, direction, days, avg_r_0900, avg_r_1000, avg_r_1100, avg_combined = row

        print(f"Pattern: {pattern} (Primary: {direction}):")
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
    print("Key findings to review:")
    print()
    print("1. POSITIONING PATTERNS:")
    print("   - Where does 10:00 form relative to 09:00 bottom/top?")
    print("   - Where does 11:00 form relative to 10:00 bottom/top?")
    print("   - Do specific positions show improved expectancy?")
    print()
    print("2. OUTCOME CORRELATIONS:")
    print("   - Does 09:00 WIN/LOSS predict 10:00 performance?")
    print("   - Does 10:00 WIN/LOSS predict 11:00 performance?")
    print()
    print("3. DIRECTION PERSISTENCE:")
    print("   - When all 3 ORBs go same direction, what is expectancy?")
    print("   - Is there an advantage to directional coherence?")
    print()
    print("Look for patterns with:")
    print("- Significant improvement >= +0.15R")
    print("- Sample size >= 30 occurrences")
    print()

    con.close()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
