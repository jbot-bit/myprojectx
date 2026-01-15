"""
VERIFY ANOMALY ANALYSIS RESULTS
Quick verification that the anomaly analysis findings are correct.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def verify_orb(orb: str):
    """Verify baseline and filtered stats for an ORB"""

    con = duckdb.connect(DB_PATH, read_only=True)

    # Get baseline stats
    baseline_query = f"""
    SELECT
        orb_{orb}_r_multiple as r_multiple,
        orb_{orb}_outcome as outcome,
        orb_{orb}_size as orb_size,
        atr_20
    FROM daily_features_v2_half
    WHERE orb_{orb}_outcome IN ('WIN', 'LOSS')
    AND instrument = 'MGC'
    """

    df = con.execute(baseline_query).df()

    baseline_trades = len(df)
    baseline_r = df['r_multiple'].mean()
    baseline_wr = (df['outcome'] == 'WIN').sum() / len(df)

    print(f"\n{orb} ORB - VERIFICATION:")
    print(f"  Baseline: {baseline_trades} trades, {baseline_r:.3f}R avg, {baseline_wr*100:.1f}% WR")

    # Calculate filter threshold
    df['orb_size_norm'] = df['orb_size'] / df['atr_20']

    # Use mean-based thresholds as computed in analysis
    mean_orb_size_norm = df['orb_size_norm'].mean()

    # Test multiple thresholds as in original analysis
    print(f"  Mean ORB size / ATR: {mean_orb_size_norm:.3f}")

    thresholds_to_test = [
        (0.5 * mean_orb_size_norm, "0.5x mean"),
        (0.75 * mean_orb_size_norm, "0.75x mean"),
        (1.0 * mean_orb_size_norm, "1.0x mean"),
    ]

    print(f"\n  Testing filter thresholds (KEEP if orb_size <= threshold):")

    best_improvement = -999
    best_threshold = None
    best_filtered_r = None

    for threshold, label in thresholds_to_test:
        # Apply filter (KEEP small ORBs, REMOVE large ORBs)
        filtered_df = df[df['orb_size_norm'] <= threshold]

        if len(filtered_df) > 0:
            filtered_r = filtered_df['r_multiple'].mean()
            improvement = filtered_r - baseline_r
            pct_kept = len(filtered_df) / baseline_trades * 100

            if improvement > best_improvement:
                best_improvement = improvement
                best_threshold = threshold
                best_filtered_r = filtered_r

            print(f"    {label} ({threshold:.3f}): {len(filtered_df)} trades ({pct_kept:.1f}% kept), {filtered_r:.3f}R, {improvement:+.3f}R")

    filtered_df = df[df['orb_size_norm'] <= best_threshold]

    if len(filtered_df) > 0:
        filtered_trades = len(filtered_df)
        pct_kept = filtered_trades / baseline_trades * 100

        print(f"\n  BEST FILTER: orb_size <= {best_threshold:.3f}*ATR")
        print(f"    {filtered_trades} trades ({pct_kept:.1f}% kept, {100-pct_kept:.1f}% removed)")
        print(f"    {best_filtered_r:.3f}R avg")
        print(f"    Improvement: {best_improvement:+.3f}R ({best_improvement/baseline_r*100:+.1f}%)")
    else:
        print(f"  ERROR: No trades pass filter!")

    con.close()

if __name__ == "__main__":
    print("="*80)
    print("ANOMALY ANALYSIS VERIFICATION")
    print("="*80)

    # Verify the 4 ORBs with valid filters
    verify_orb("2300")
    verify_orb("0030")
    verify_orb("1100")
    verify_orb("1000")

    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80)
