"""
LAGGED FEATURE TEST - ALL ORBS

Quick SQL-based test to determine if PREVIOUS DAY session structure
predicts NEXT DAY ORB performance across all ORB sessions.

Uses LAG() window functions on day_state_features.
Joins with realistic-entry ORB trade outcomes.

Output: GO/NO-GO recommendation for full lagged feature implementation.
"""

import duckdb
import pandas as pd
import sys

DB_PATH = "gold.db"

# Test configuration
MIN_SAMPLE_SIZE = 30  # Minimum trades per bucket
SIGNIFICANT_DELTA = 0.15  # Minimum avgR improvement to be meaningful

# ORB configurations to test (matching validated results)
ORB_CONFIGS = {
    '0900': {'rr': 2.0, 'sl_mode': 'half', 'close_conf': 1},
    '1000': {'rr': 2.0, 'sl_mode': 'half', 'close_conf': 1},
    '1100': {'rr': 2.0, 'sl_mode': 'half', 'close_conf': 1},
    '1800': {'rr': 2.0, 'sl_mode': 'half', 'close_conf': 1},
    '2300': {'rr': 2.0, 'sl_mode': 'half', 'close_conf': 1},
    '0030': {'rr': 2.0, 'sl_mode': 'half', 'close_conf': 1}
}


def create_lagged_features_view(con):
    """Create temp view with lagged features using window functions."""
    print("\n" + "="*80)
    print("CREATING LAGGED FEATURES VIEW")
    print("="*80)

    con.execute("""
        CREATE OR REPLACE TEMP VIEW day_state_with_lags AS
        SELECT
            date_local,
            orb_code,

            -- Current day features
            pre_orb_range,
            pre_orb_disp,
            asia_high,
            asia_low,
            asia_range,
            asia_close_pos,
            asia_impulse,
            london_high,
            london_low,
            london_range,
            london_close_pos,
            london_impulse,
            london_swept_asia_high,
            london_swept_asia_low,
            range_bucket,
            disp_bucket,

            -- LAGGED (PREVIOUS DAY) FEATURES
            LAG(asia_high, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_asia_high,
            LAG(asia_low, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_asia_low,
            LAG(asia_range, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_asia_range,
            LAG(asia_close_pos, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_asia_close_pos,
            LAG(asia_impulse, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_asia_impulse,

            LAG(london_high, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_london_high,
            LAG(london_low, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_london_low,
            LAG(london_range, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_london_range,
            LAG(london_close_pos, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_london_close_pos,
            LAG(london_impulse, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_london_impulse,

            LAG(london_swept_asia_high, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_london_swept_asia_high,
            LAG(london_swept_asia_low, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_london_swept_asia_low,

            LAG(range_bucket, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_range_bucket,
            LAG(disp_bucket, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_disp_bucket,

            LAG(pre_orb_range, 1) OVER (PARTITION BY orb_code ORDER BY date_local) AS prev_pre_orb_range

        FROM day_state_features
        WHERE orb_code IN ('0900', '1000', '1100', '1800', '2300', '0030')
    """)

    # Verify view
    count = con.execute("SELECT COUNT(*) FROM day_state_with_lags").fetchone()[0]
    print(f"[OK] Created view with {count} rows (includes lagged features)")

    # Check lag availability by ORB
    print("\nLagged feature availability by ORB:")
    lag_counts = con.execute("""
        SELECT
            orb_code,
            COUNT(*) as total_rows,
            SUM(CASE WHEN prev_asia_range IS NOT NULL THEN 1 ELSE 0 END) as rows_with_lag
        FROM day_state_with_lags
        GROUP BY orb_code
        ORDER BY orb_code
    """).df()
    print(lag_counts.to_string(index=False))


def get_baseline_performance(con, orb_code, config):
    """Get baseline ORB performance (no lagged conditioning)."""
    query = f"""
        SELECT
            COUNT(*) as total_trades,
            AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
            AVG(r_multiple) as avg_r,
            MEDIAN(r_multiple) as median_r,
            SUM(r_multiple) as total_r,
            STDDEV(r_multiple) as std_r
        FROM orb_trades_5m_exec_orbr
        WHERE orb = '{orb_code}'
            AND rr = {config['rr']}
            AND sl_mode = '{config['sl_mode']}'
            AND close_confirmations = {config['close_conf']}
            AND buffer_ticks = 0
    """

    result = con.execute(query).df()
    return result.iloc[0].to_dict()


def test_lagged_feature(con, orb_code, config, lag_feature, lag_column, bin_definition):
    """Test a specific lagged feature for predictive power."""

    query = f"""
        WITH trades_with_lags AS (
            SELECT
                t.date_local,
                t.outcome,
                t.r_multiple,
                l.{lag_column},
                {bin_definition} AS lag_bin
            FROM orb_trades_5m_exec_orbr t
            LEFT JOIN day_state_with_lags l
                ON t.date_local = l.date_local
                AND l.orb_code = '{orb_code}'
            WHERE t.orb = '{orb_code}'
                AND t.rr = {config['rr']}
                AND t.sl_mode = '{config['sl_mode']}'
                AND t.close_confirmations = {config['close_conf']}
                AND t.buffer_ticks = 0
                AND l.{lag_column} IS NOT NULL
        )
        SELECT
            lag_bin,
            COUNT(*) as trades,
            AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) as win_rate,
            AVG(r_multiple) as avg_r,
            MEDIAN(r_multiple) as median_r,
            SUM(r_multiple) as total_r
        FROM trades_with_lags
        WHERE lag_bin IS NOT NULL
        GROUP BY lag_bin
        HAVING COUNT(*) >= {MIN_SAMPLE_SIZE}
        ORDER BY avg_r DESC
    """

    try:
        results = con.execute(query).df()
        return results
    except Exception as e:
        print(f"  [WARN] Error testing {lag_feature}: {e}")
        return None


def analyze_orb_with_lags(con, orb_code, config):
    """Analyze one ORB with all lagged features."""
    print("\n" + "="*80)
    print(f"ANALYZING {orb_code} ORB WITH LAGGED FEATURES")
    print("="*80)

    # Get baseline
    baseline = get_baseline_performance(con, orb_code, config)
    print(f"\nBASELINE (no lagged conditioning):")
    print(f"  Trades: {baseline['total_trades']}")
    print(f"  Win Rate: {baseline['win_rate']*100:.1f}%")
    print(f"  Avg R: {baseline['avg_r']:.3f}R")
    print(f"  Median R: {baseline['median_r']:.3f}R")
    print(f"  Total R: {baseline['total_r']:.1f}R")

    # Define lagged features to test
    lag_tests = [
        # Previous Asia features
        {
            'name': 'PREV_ASIA_RANGE',
            'column': 'prev_asia_range',
            'bins': """
                CASE
                    WHEN prev_asia_range <= 5.0 THEN 'SMALL'
                    WHEN prev_asia_range <= 15.0 THEN 'MEDIUM'
                    ELSE 'LARGE'
                END
            """
        },
        {
            'name': 'PREV_ASIA_CLOSE_POS',
            'column': 'prev_asia_close_pos',
            'bins': """
                CASE
                    WHEN prev_asia_close_pos <= 0.3 THEN 'LOW'
                    WHEN prev_asia_close_pos <= 0.7 THEN 'MID'
                    ELSE 'HIGH'
                END
            """
        },
        {
            'name': 'PREV_ASIA_IMPULSE',
            'column': 'prev_asia_impulse',
            'bins': """
                CASE
                    WHEN prev_asia_impulse <= 0.3 THEN 'LOW'
                    WHEN prev_asia_impulse <= 0.7 THEN 'MEDIUM'
                    ELSE 'HIGH'
                END
            """
        },
        # Previous London features
        {
            'name': 'PREV_LONDON_RANGE',
            'column': 'prev_london_range',
            'bins': """
                CASE
                    WHEN prev_london_range <= 5.0 THEN 'SMALL'
                    WHEN prev_london_range <= 15.0 THEN 'MEDIUM'
                    ELSE 'LARGE'
                END
            """
        },
        {
            'name': 'PREV_LONDON_CLOSE_POS',
            'column': 'prev_london_close_pos',
            'bins': """
                CASE
                    WHEN prev_london_close_pos <= 0.3 THEN 'LOW'
                    WHEN prev_london_close_pos <= 0.7 THEN 'MID'
                    ELSE 'HIGH'
                END
            """
        },
        # Previous sweep flags
        {
            'name': 'PREV_LONDON_SWEPT_ASIA_HIGH',
            'column': 'prev_london_swept_asia_high',
            'bins': """
                CASE
                    WHEN prev_london_swept_asia_high = true THEN 'YES'
                    WHEN prev_london_swept_asia_high = false THEN 'NO'
                    ELSE NULL
                END
            """
        },
        {
            'name': 'PREV_LONDON_SWEPT_ASIA_LOW',
            'column': 'prev_london_swept_asia_low',
            'bins': """
                CASE
                    WHEN prev_london_swept_asia_low = true THEN 'YES'
                    WHEN prev_london_swept_asia_low = false THEN 'NO'
                    ELSE NULL
                END
            """
        }
    ]

    # Test each lagged feature
    best_findings = []

    for test in lag_tests:
        print(f"\n--- Testing: {test['name']} ---")
        results = test_lagged_feature(con, orb_code, config, test['name'], test['column'], test['bins'])

        if results is None or len(results) == 0:
            print(f"  No valid buckets with >={MIN_SAMPLE_SIZE} trades")
            continue

        print(results.to_string(index=False))

        # Find best and worst buckets
        best_row = results.iloc[0]
        worst_row = results.iloc[-1]

        delta_best = best_row['avg_r'] - baseline['avg_r']
        delta_worst = worst_row['avg_r'] - baseline['avg_r']

        print(f"\n  BEST bucket: {best_row['lag_bin']}")
        print(f"    Avg R: {best_row['avg_r']:.3f}R (Delta {delta_best:+.3f}R vs baseline)")
        print(f"    Trades: {int(best_row['trades'])}")

        if len(results) > 1:
            print(f"  WORST bucket: {worst_row['lag_bin']}")
            print(f"    Avg R: {worst_row['avg_r']:.3f}R (Delta {delta_worst:+.3f}R vs baseline)")
            print(f"    Trades: {int(worst_row['trades'])}")

        # Store if significant improvement found
        if delta_best >= SIGNIFICANT_DELTA:
            best_findings.append({
                'orb': orb_code,
                'feature': test['name'],
                'best_bucket': best_row['lag_bin'],
                'best_avg_r': best_row['avg_r'],
                'delta_r': delta_best,
                'trades': int(best_row['trades']),
                'win_rate': best_row['win_rate']
            })

    return baseline, best_findings


def generate_final_report(con):
    """Generate comprehensive report for all ORBs."""
    print("\n" + "="*80)
    print("COMPREHENSIVE LAGGED FEATURE TEST - ALL ORBS")
    print("="*80)

    all_baselines = {}
    all_findings = []

    for orb_code, config in ORB_CONFIGS.items():
        baseline, findings = analyze_orb_with_lags(con, orb_code, config)
        all_baselines[orb_code] = baseline
        all_findings.extend(findings)

    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY - SIGNIFICANT LAGGED FEATURE FINDINGS")
    print("="*80)

    if len(all_findings) == 0:
        print("\n[FAIL] NO SIGNIFICANT IMPROVEMENTS FOUND")
        print(f"\nNo lagged feature buckets showed >={SIGNIFICANT_DELTA}R improvement")
        print("over baseline with minimum sample size.")
        print("\n[OK] CONCLUSION: Current same-day features are sufficient.")
        print("   'Unconditional edge' findings remain valid.")
        print("   No need to rebuild schema with lagged features.")
        return False

    print(f"\n[OK] FOUND {len(all_findings)} SIGNIFICANT IMPROVEMENTS\n")

    # Create summary table
    findings_df = pd.DataFrame(all_findings)
    findings_df = findings_df.sort_values('delta_r', ascending=False)

    print(findings_df.to_string(index=False))

    print("\n" + "="*80)
    print("GO/NO-GO DECISION")
    print("="*80)

    # Analyze which ORBs benefit
    orbs_improved = findings_df['orb'].unique()
    print(f"\nORBs with improvements: {', '.join(orbs_improved)}")

    max_delta = findings_df['delta_r'].max()
    print(f"Maximum improvement: +{max_delta:.3f}R")

    avg_delta = findings_df['delta_r'].mean()
    print(f"Average improvement: +{avg_delta:.3f}R")

    # Decision logic
    if max_delta >= SIGNIFICANT_DELTA and len(orbs_improved) >= 2:
        print(f"\n[GO] IMPLEMENT LAGGED FEATURES")
        print(f"\nRationale:")
        print(f"  - {len(orbs_improved)} ORBs benefit from lagged conditioning")
        print(f"  - Maximum delta: +{max_delta:.3f}R")
        print(f"  - Sufficient sample sizes maintained")
        print(f"\nNext steps:")
        print(f"  1. Add lagged columns to day_state_features schema")
        print(f"  2. Rebuild feature table with LAG() calculations")
        print(f"  3. Update edge state testing scripts to include lagged features")
        print(f"  4. Retest 'unconditional edge' findings with full feature set")
        return True
    else:
        print(f"\n[MARGINAL] BORDERLINE CASE")
        print(f"\nOnly {len(orbs_improved)} ORB(s) show improvement.")
        print(f"Consider whether the complexity of lagged features justifies the gains.")
        print(f"\nRecommendation: Focus on ORBs that benefit, skip others.")
        return False


def main():
    con = duckdb.connect(DB_PATH)

    # Create lagged features view
    create_lagged_features_view(con)

    # Test all ORBs
    should_implement = generate_final_report(con)

    con.close()

    if should_implement:
        sys.exit(0)  # GO
    else:
        sys.exit(1)  # NO-GO or MARGINAL


if __name__ == "__main__":
    main()
