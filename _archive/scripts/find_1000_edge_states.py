"""
Find edge states for 1000 ORB (best breakout performer).

1000 ORB showed +0.094R avg in breakout tests.
Now testing if edge states can make it even better.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*80)
    print("EDGE STATE SEARCH - 1000 ORB (BEST BREAKOUT PERFORMER)")
    print("="*80)
    print()
    print("Baseline breakout performance: +0.094R avg (RR=4.0)")
    print()

    # Get all 1000 ORB day-state feature combinations
    # Test each state for post-ORB asymmetry

    print("STEP 1: Query 1000 ORB dates with day-state features")
    print("-"*80)

    dates_1000 = con.execute("""
        SELECT
            date_local,
            range_bucket,
            disp_bucket,
            close_pos_bucket,
            impulse_bucket,
            pre_orb_range,
            pre_orb_disp,
            pre_orb_close_pos,
            impulse_score
        FROM day_state_features
        WHERE orb_code = '1000'
            AND range_bucket IS NOT NULL
            AND disp_bucket IS NOT NULL
            AND close_pos_bucket IS NOT NULL
            AND impulse_bucket IS NOT NULL
        ORDER BY date_local
    """).df()

    print(f"Total 1000 ORB dates: {len(dates_1000)}")
    print()

    # Show bucket distributions
    print("Bucket distributions:")
    for bucket_col in ['range_bucket', 'disp_bucket', 'close_pos_bucket', 'impulse_bucket']:
        counts = dates_1000[bucket_col].value_counts().sort_index()
        print(f"  {bucket_col}:")
        for val, cnt in counts.items():
            print(f"    {val}: {cnt} ({cnt/len(dates_1000)*100:.1f}%)")
    print()

    # STEP 2: Get post-ORB outcomes for all 1000 dates
    print("STEP 2: Get post-ORB outcomes")
    print("-"*80)

    outcomes = con.execute("""
        SELECT
            date_local,
            "window",
            max_up,
            max_dn,
            tail_skew
        FROM post_outcomes
        WHERE orb_code = '1000'
    """).df()

    # Pivot to get 60m outcomes
    outcomes_60m = outcomes[outcomes['window'] == 'post_60m'][['date_local', 'max_up', 'max_dn', 'tail_skew']]
    outcomes_60m.columns = ['date_local', 'max_up_60m', 'max_dn_60m', 'tail_skew_60m']

    print(f"Post-ORB outcomes: {len(outcomes_60m)} dates")
    print()

    # STEP 3: Join features + outcomes
    merged = dates_1000.merge(outcomes_60m, on='date_local', how='inner')
    print(f"Merged dataset: {len(merged)} dates")
    print()

    # STEP 4: Test all state combinations
    print("STEP 3: Testing state combinations for edge")
    print("-"*80)
    print()

    # Define edge criteria
    SIGN_SKEW_THRESHOLD = 60.0
    TAIL_SKEW_THRESHOLD = 3.0
    MIN_FREQUENCY_PCT = 1.0
    MAX_FREQUENCY_PCT = 15.0
    MIN_SAMPLE_SIZE = 30

    edge_states = []

    # Test all 4-way combinations
    for range_b in merged['range_bucket'].unique():
        for disp_b in merged['disp_bucket'].unique():
            for close_b in merged['close_pos_bucket'].unique():
                for impulse_b in merged['impulse_bucket'].unique():

                    state_mask = (
                        (merged['range_bucket'] == range_b) &
                        (merged['disp_bucket'] == disp_b) &
                        (merged['close_pos_bucket'] == close_b) &
                        (merged['impulse_bucket'] == impulse_b)
                    )

                    state_data = merged[state_mask]

                    if len(state_data) == 0:
                        continue

                    n_days = len(state_data)
                    frequency_pct = n_days / len(merged) * 100

                    # Rarity filter
                    if frequency_pct < MIN_FREQUENCY_PCT or frequency_pct > MAX_FREQUENCY_PCT:
                        continue

                    if n_days < MIN_SAMPLE_SIZE:
                        continue

                    # Sign skew: % of days where max_up > max_dn
                    up_favored = (state_data['max_up_60m'] > state_data['max_dn_60m']).sum()
                    sign_skew_pct = (up_favored / n_days) * 100

                    # Tail skew: median
                    median_tail_skew = state_data['tail_skew_60m'].median()

                    # Check edge criteria
                    if sign_skew_pct >= SIGN_SKEW_THRESHOLD and median_tail_skew >= TAIL_SKEW_THRESHOLD:
                        direction = "UP"
                    elif sign_skew_pct <= (100 - SIGN_SKEW_THRESHOLD) and median_tail_skew <= -TAIL_SKEW_THRESHOLD:
                        direction = "DN"
                    else:
                        continue

                    # Edge found
                    state_label = f"{range_b} + {disp_b} + {close_b} + {impulse_b}"

                    edge_states.append({
                        'orb_code': '1000',
                        'state_label': state_label,
                        'range_bucket': range_b,
                        'disp_bucket': disp_b,
                        'close_pos_bucket': close_b,
                        'impulse_bucket': impulse_b,
                        'n_days': n_days,
                        'frequency_pct': frequency_pct,
                        'sign_skew_60m': sign_skew_pct,
                        'median_tail_skew_60m': median_tail_skew,
                        'direction': direction
                    })

    print(f"Edge states found: {len(edge_states)}")
    print()

    if len(edge_states) == 0:
        print("[WARNING] No edge states found for 1000 ORB")
        print()
        print("Possible reasons:")
        print("  1. Strict criteria (60%+ sign skew, 3+ tick tail skew, 30+ samples)")
        print("  2. 1000 ORB may not have strong conditional asymmetries")
        print("  3. Edge may be unconditional (all 1000 setups similar)")
        print()
        print("Recommendation: Trade 1000 ORB breakout as-is (+0.094R avg)")
        con.close()
        return

    # Sort by absolute tail skew (strongest edges first)
    edge_df = pd.DataFrame(edge_states).sort_values('median_tail_skew_60m', key=abs, ascending=False)

    print("EDGE STATES RANKED BY STRENGTH:")
    print("-"*80)
    print()

    for i, (_, state) in enumerate(edge_df.iterrows(), 1):
        print(f"{i}. {state['state_label']}")
        print(f"   Sample: {state['n_days']} days ({state['frequency_pct']:.1f}%)")
        print(f"   Direction: {state['direction']}-favored ({state['sign_skew_60m']:.1f}%)")
        print(f"   Tail skew: {state['median_tail_skew_60m']:+.1f} ticks (post_60m)")
        print()

    # Save results
    edge_df.to_csv('edge_states_1000_orb.csv', index=False)
    print(f"Results saved to: edge_states_1000_orb.csv")
    print()

    # STEP 5: Recommend strongest state for testing
    print("="*80)
    print("RECOMMENDATION")
    print("="*80)
    print()

    strongest = edge_df.iloc[0]

    print(f"Test this state first:")
    print(f"  ORB: 1000")
    print(f"  State: {strongest['state_label']}")
    print(f"  Sample: {strongest['n_days']} days")
    print(f"  Edge: {strongest['direction']}-favored ({strongest['sign_skew_60m']:.1f}%), {strongest['median_tail_skew_60m']:+.1f} tick skew")
    print()
    print("Next action:")
    print(f"  python prepare_manual_replay_1000.py")
    print()

    con.close()

if __name__ == '__main__':
    main()
