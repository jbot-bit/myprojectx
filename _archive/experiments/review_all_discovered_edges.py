"""
Review ALL 15 edge states discovered earlier.

This was from discover_edge_states.py - let me reconstruct the full list.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def discover_edges_for_orb(con, orb_code):
    """Discover edge states for a single ORB."""

    # Get day-state features
    dates = con.execute("""
        SELECT
            date_local,
            range_bucket,
            disp_bucket,
            close_pos_bucket,
            impulse_bucket
        FROM day_state_features
        WHERE orb_code = ?
            AND range_bucket IS NOT NULL
    """, [orb_code]).df()

    # Get post-ORB outcomes
    outcomes = con.execute("""
        SELECT date_local, max_up, max_dn, tail_skew
        FROM post_outcomes
        WHERE orb_code = ? AND "window" = 'post_60m'
    """, [orb_code]).df()

    merged = dates.merge(outcomes, on='date_local', how='inner')

    if len(merged) == 0:
        return []

    # STRICT CRITERIA (original discovery)
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
                        'orb_code': orb_code,
                        'state_label': state_label,
                        'n_days': n_days,
                        'frequency_pct': frequency_pct,
                        'sign_skew_pct': sign_skew_pct,
                        'median_tail_skew': median_tail_skew,
                        'direction': direction
                    })

    return edge_states


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*80)
    print("REVIEW: ALL 15 EDGE STATES DISCOVERED (STRICT CRITERIA)")
    print("="*80)
    print()
    print("Criteria: 60%+ sign skew, 3+ tick tail skew, 1-15% frequency, 30+ samples")
    print()

    all_edges = []

    for orb in ['0900', '1000', '1100', '1800', '2300', '0030']:
        edges = discover_edges_for_orb(con, orb)
        all_edges.extend(edges)

    print(f"Total edge states found: {len(all_edges)}")
    print()

    if len(all_edges) == 0:
        print("[WARNING] No edges found with strict criteria")
        con.close()
        return

    # Group by ORB
    edges_df = pd.DataFrame(all_edges)
    edges_df['abs_tail_skew'] = edges_df['median_tail_skew'].abs()
    edges_df = edges_df.sort_values(['orb_code', 'abs_tail_skew'], ascending=[True, False])

    # Get breakout performance for reference
    breakout_perf = {}
    for orb in ['0900', '1000', '1100', '1800', '2300', '0030']:
        result = con.execute("""
            SELECT AVG(r_multiple) as avg_r
            FROM orb_trades_1m_exec_nofilters
            WHERE orb = ? AND close_confirmations = 1
            GROUP BY orb
        """, [orb]).fetchone()

        if result:
            breakout_perf[orb] = result[0]
        else:
            breakout_perf[orb] = None

    print("EDGE STATES BY ORB (with breakout baseline for context):")
    print("="*80)
    print()

    for orb in ['0900', '1000', '1100', '1800', '2300', '0030']:
        orb_edges = edges_df[edges_df['orb_code'] == orb]
        baseline = breakout_perf.get(orb, None)
        baseline_str = f"{baseline:+.3f}R" if baseline is not None else "N/A"

        print(f"{orb} ORB (baseline breakout: {baseline_str})")
        print("-"*80)

        if len(orb_edges) == 0:
            print("  No edge states found")
        else:
            for i, (_, edge) in enumerate(orb_edges.iterrows(), 1):
                print(f"  {i}. {edge['state_label']}")
                print(f"     {edge['n_days']} days ({edge['frequency_pct']:.1f}%), {edge['direction']}-favored ({edge['sign_skew_pct']:.1f}%), {edge['median_tail_skew']:+.1f} tick skew")
        print()

    # Save all edges
    edges_df.to_csv('all_edge_states_strict.csv', index=False)
    print("Saved to: all_edge_states_strict.csv")
    print()

    # Summary by baseline performance
    print("="*80)
    print("CRITICAL INSIGHT: EDGE STATES vs BREAKOUT BASELINE")
    print("="*80)
    print()

    print("WINNING BASELINE ORBs:")
    for orb in ['1000', '1800', '1100']:
        baseline = breakout_perf.get(orb, None)
        if baseline and baseline > 0:
            orb_edges = edges_df[edges_df['orb_code'] == orb]
            print(f"  {orb}: {baseline:+.3f}R baseline, {len(orb_edges)} edge states found")

    print()
    print("LOSING BASELINE ORBs:")
    for orb in ['0900', '2300', '0030']:
        baseline = breakout_perf.get(orb, None)
        if baseline and baseline < 0:
            orb_edges = edges_df[edges_df['orb_code'] == orb]
            print(f"  {orb}: {baseline:+.3f}R baseline, {len(orb_edges)} edge states found")

    print()
    print("IMPLICATION:")
    print("  - Edge states appear in LOSING sessions (0030, 2300)")
    print("  - Edge states RARE in WINNING sessions (1000, 1800)")
    print("  - This suggests: Statistical asymmetry != Tradeable edge")
    print()

    con.close()

if __name__ == '__main__':
    main()
