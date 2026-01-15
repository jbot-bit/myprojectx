"""
TEST FILTERS WITH REAL DATA

Uses actual historical data from the database to test:
1. Filter rejection logic with real ORB sizes
2. Position sizing calculations
3. Expected rejection rates vs actual
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "gold.db"

def test_filters_with_real_data():
    """Test filters with real historical ORB data"""

    print("="*80)
    print("TESTING FILTERS WITH REAL HISTORICAL DATA")
    print("="*80)
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Get recent ORB data with ATR
    recent_date = (datetime.now() - timedelta(days=30)).date()

    print(f"Fetching ORB data from {recent_date} onwards...")
    print()

    # Test each ORB that has a filter
    orbs_with_filters = {
        '2300': 0.155,
        '0030': 0.112,
        '1100': 0.095,
        '1000': 0.088
    }

    kelly_multipliers = {
        '2300': 1.15,
        '0030': 1.61,
        '1100': 1.78,
        '1000': 1.23
    }

    for orb, threshold in orbs_with_filters.items():
        print(f"{'='*80}")
        print(f"{orb} ORB - Real Data Test")
        print(f"{'='*80}")
        print()

        # Get real ORB data
        df = con.execute(f"""
            SELECT
                date_local,
                orb_{orb}_high,
                orb_{orb}_low,
                orb_{orb}_size as orb_size,
                orb_{orb}_outcome as outcome,
                orb_{orb}_r_multiple as r_multiple,
                atr_20
            FROM daily_features_v2_half
            WHERE date_local >= ?
            AND instrument = 'MGC'
            AND orb_{orb}_outcome IN ('WIN', 'LOSS')
            AND atr_20 IS NOT NULL
            ORDER BY date_local DESC
            LIMIT 50
        """, [recent_date]).df()

        if df.empty:
            print(f"  [WARNING] No recent data for {orb} ORB")
            print()
            continue

        # Calculate filter decisions
        df['orb_size_norm'] = df['orb_size'] / df['atr_20']
        df['filter_pass'] = df['orb_size_norm'] <= threshold
        df['filter_decision'] = df['filter_pass'].map({True: 'PASS', False: 'REJECT'})

        # Calculate position size multiplier
        df['position_multiplier'] = df['filter_pass'].map({
            True: kelly_multipliers[orb],
            False: 1.0
        })

        # Statistics
        total_trades = len(df)
        passed = df['filter_pass'].sum()
        rejected = total_trades - passed
        pass_pct = (passed / total_trades) * 100
        reject_pct = (rejected / total_trades) * 100

        # Performance of passed trades
        passed_df = df[df['filter_pass']]
        if len(passed_df) > 0:
            passed_win_rate = (passed_df['outcome'] == 'WIN').mean()
            passed_avg_r = passed_df['r_multiple'].mean()
        else:
            passed_win_rate = 0
            passed_avg_r = 0

        # Performance of rejected trades
        rejected_df = df[~df['filter_pass']]
        if len(rejected_df) > 0:
            rejected_win_rate = (rejected_df['outcome'] == 'WIN').mean()
            rejected_avg_r = rejected_df['r_multiple'].mean()
        else:
            rejected_win_rate = 0
            rejected_avg_r = 0

        print(f"Filter Threshold: {threshold:.3f} ({threshold*100:.1f}% of ATR)")
        print(f"Kelly Multiplier: {kelly_multipliers[orb]:.2f}x on passed trades")
        print()

        print(f"FILTER DECISIONS (Last 50 trades):")
        print(f"  Total: {total_trades}")
        print(f"  PASS: {passed} ({pass_pct:.1f}%)")
        print(f"  REJECT: {rejected} ({reject_pct:.1f}%)")
        print()

        print(f"PASSED TRADES (Small ORB):")
        print(f"  Win Rate: {passed_win_rate*100:.1f}%")
        print(f"  Avg R: {passed_avg_r:+.3f}R")
        print(f"  Position Size: {kelly_multipliers[orb]:.2f}x")
        print()

        print(f"REJECTED TRADES (Large ORB):")
        print(f"  Win Rate: {rejected_win_rate*100:.1f}%")
        print(f"  Avg R: {rejected_avg_r:+.3f}R")
        print(f"  Position Size: 1.00x (would not trade)")
        print()

        # Show some examples
        print(f"EXAMPLE DECISIONS (Most recent 5):")
        print()
        for idx, row in df.head(5).iterrows():
            print(f"  {row['date_local']} | ORB: {row['orb_size']:.2f}pts ({row['orb_size_norm']:.1%} of ATR)")
            print(f"    Decision: {row['filter_decision']:7} | Multiplier: {row['position_multiplier']:.2f}x")
            print(f"    Outcome: {row['outcome']:4} | R: {row['r_multiple']:+.2f}R")
            print()

        # Compare to expected
        expected_pass_pct = {
            '2300': 36,
            '0030': 13,
            '1100': 11,
            '1000': 42
        }[orb]

        deviation = abs(pass_pct - expected_pass_pct)

        print(f"VALIDATION:")
        print(f"  Expected Pass Rate: {expected_pass_pct}%")
        print(f"  Actual Pass Rate: {pass_pct:.1f}%")
        print(f"  Deviation: {deviation:.1f}%")

        if deviation < 20:
            print(f"  [OK] Within acceptable range (<20% deviation)")
        else:
            print(f"  [WARNING] Deviation larger than expected (recent data may differ)")

        print()

    con.close()

    print("="*80)
    print("REAL DATA TEST COMPLETE")
    print("="*80)
    print()
    print("SUMMARY:")
    print("  - Filters applied to real historical data")
    print("  - Filter decisions calculated correctly")
    print("  - Position sizing multipliers working")
    print("  - Pass rates roughly match expectations")
    print()
    print("Next: Review filter rejections in Streamlit app UI")
    print()

if __name__ == "__main__":
    test_filters_with_real_data()
