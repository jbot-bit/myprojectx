"""
Find edge states for 1800 ORB (second best performer).

1800 ORB showed +0.062R avg in breakout tests.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*80)
    print("EDGE STATE SEARCH - 1800 ORB (SECOND BEST PERFORMER)")
    print("="*80)
    print()
    print("Baseline breakout performance: +0.062R avg")
    print()

    # Get data
    dates_1800 = con.execute("""
        SELECT
            date_local,
            range_bucket,
            disp_bucket,
            close_pos_bucket,
            impulse_bucket
        FROM day_state_features
        WHERE orb_code = '1800'
            AND range_bucket IS NOT NULL
    """).df()

    outcomes = con.execute("""
        SELECT date_local, max_up, max_dn, tail_skew
        FROM post_outcomes
        WHERE orb_code = '1800' AND "window" = 'post_60m'
    """).df()

    merged = dates_1800.merge(outcomes, on='date_local', how='inner')

    print(f"Total 1800 ORB dates: {len(merged)}")
    print()

    # Show bucket distributions
    print("Bucket distributions:")
    for bucket_col in ['range_bucket', 'disp_bucket', 'close_pos_bucket', 'impulse_bucket']:
        counts = merged[bucket_col].value_counts().sort_index()
        print(f"  {bucket_col}:")
        for val, cnt in counts.items():
            print(f"    {val}: {cnt} ({cnt/len(merged)*100:.1f}%)")
    print()

    # Use RELAXED criteria (strict found nothing for 1000)
    SIGN_SKEW_THRESHOLD = 55.0
    TAIL_SKEW_THRESHOLD = 2.0
    MIN_FREQUENCY_PCT = 5.0
    MAX_FREQUENCY_PCT = 20.0
    MIN_SAMPLE_SIZE = 25

    print("CRITERIA (relaxed):")
    print(f"  Sign skew: >={SIGN_SKEW_THRESHOLD}%")
    print(f"  Tail skew: >={TAIL_SKEW_THRESHOLD} ticks")
    print(f"  Frequency: {MIN_FREQUENCY_PCT}-{MAX_FREQUENCY_PCT}%")
    print(f"  Min sample: {MIN_SAMPLE_SIZE} days")
    print()

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
                    n_days = len(state_data)

                    if n_days == 0:
                        continue

                    frequency_pct = n_days / len(merged) * 100

                    if frequency_pct < MIN_FREQUENCY_PCT or frequency_pct > MAX_FREQUENCY_PCT:
                        continue

                    if n_days < MIN_SAMPLE_SIZE:
                        continue

                    up_favored = (state_data['max_up'] > state_data['max_dn']).sum()
                    sign_skew_pct = (up_favored / n_days) * 100
                    median_tail_skew = state_data['tail_skew'].median()

                    # Check edge (UP or DN)
                    if sign_skew_pct >= SIGN_SKEW_THRESHOLD and median_tail_skew >= TAIL_SKEW_THRESHOLD:
                        direction = "UP"
                    elif sign_skew_pct <= (100 - SIGN_SKEW_THRESHOLD) and median_tail_skew <= -TAIL_SKEW_THRESHOLD:
                        direction = "DN"
                    else:
                        continue

                    state_label = f"{range_b} + {disp_b} + {close_b} + {impulse_b}"

                    edge_states.append({
                        'state_label': state_label,
                        'range_bucket': range_b,
                        'disp_bucket': disp_b,
                        'close_pos_bucket': close_b,
                        'impulse_bucket': impulse_b,
                        'n_days': n_days,
                        'frequency_pct': frequency_pct,
                        'sign_skew_pct': sign_skew_pct,
                        'median_tail_skew': median_tail_skew,
                        'direction': direction
                    })

    print(f"Edge states found: {len(edge_states)}")
    print()

    if len(edge_states) == 0:
        print("[RESULT] No edge states found for 1800 ORB")
        print()
        print("Implication: 1800 ORB edge is also UNCONDITIONAL")
        print("  - Trade all 1800 ORB setups with baseline parameters")
        print()
    else:
        edge_df = pd.DataFrame(edge_states).sort_values('median_tail_skew', key=abs, ascending=False)

        print("EDGE STATES FOUND:")
        print("-"*80)

        for i, (_, s) in enumerate(edge_df.iterrows(), 1):
            print(f"{i}. {s['state_label']}")
            print(f"   {s['n_days']} days ({s['frequency_pct']:.1f}%), {s['direction']}-favored ({s['sign_skew_pct']:.1f}%), {s['median_tail_skew']:+.1f} tick skew")
            print()

        edge_df.to_csv('edge_states_1800_relaxed.csv', index=False)
        print("Saved to: edge_states_1800_relaxed.csv")
        print()

    con.close()

if __name__ == '__main__':
    main()
