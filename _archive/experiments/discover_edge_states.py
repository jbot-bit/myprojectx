"""
DISCOVER EDGE STATES - POST-ORB ASYMMETRY ANALYSIS

Systematically search for rare conditional states where post-ORB price behavior
shows statistical asymmetry.

NO brute force. Use only specified bucketed features.
STRICT edge criteria. Report "NO EDGE FOUND" if nothing qualifies.
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from itertools import product

DB_PATH = "gold.db"
TICK_SIZE = 0.10

# Edge criteria thresholds
SIGN_SKEW_THRESHOLD = 60  # % of days where max_up > max_dn
MIN_SAMPLE_SIZE = 30
MAX_FREQUENCY_PCT = 15  # Discard states > 15% occurrence
MIN_FREQUENCY_PCT = 1   # Prefer >= 1% occurrence
MIN_CANDIDATES_TO_REPORT = 10  # Report up to 10 per ORB

# ORB windows (end times for post-window calculations)
ORB_TIMES = {
    '0900': (9, 5),
    '1000': (10, 5),
    '1100': (11, 5),
    '1800': (18, 5),
    '2300': (23, 5),
    '0030': (0, 35)
}


def get_orb_end_time(d, orb_code):
    """Get ORB end timestamp for given date and ORB code."""
    hour, minute = ORB_TIMES[orb_code]

    # 0030 ORB ends at 00:35 next day
    if orb_code == '0030':
        return datetime.combine(d + timedelta(days=1), datetime.min.time()) + timedelta(hours=hour, minutes=minute)
    else:
        return datetime.combine(d, datetime.min.time()) + timedelta(hours=hour, minutes=minute)


def compute_post_outcomes(con):
    """
    Compute post-ORB outcome metrics for all (date, orb_code) pairs.

    For each ORB, compute:
    - post_30m, post_60m, post_90m outcomes
    - max_up, max_dn, net, tail_skew, tail_ratio
    """
    print("Computing post-ORB outcomes...")

    # Get all day-state rows
    day_states = con.execute("""
        SELECT
            date_local,
            orb_code,
            pre_orb_close as price_at_orb
        FROM day_state_features
        ORDER BY date_local, orb_code
    """).fetchall()

    results = []

    for idx, (date_local, orb_code, price_at_orb) in enumerate(day_states):
        if idx % 500 == 0:
            print(f"  Processing row {idx}/{len(day_states)}...")

        orb_end = get_orb_end_time(date_local, orb_code)

        # Define post windows
        post_30m_end = orb_end + timedelta(minutes=30)
        post_60m_end = orb_end + timedelta(minutes=60)
        post_90m_end = orb_end + timedelta(minutes=90)

        # Query bars for each window
        for window_name, window_end in [
            ('post_30m', post_30m_end),
            ('post_60m', post_60m_end),
            ('post_90m', post_90m_end)
        ]:
            bars = con.execute("""
                SELECT
                    high,
                    low,
                    close
                FROM bars_1m
                WHERE symbol = 'MGC'
                    AND ts_utc AT TIME ZONE 'Australia/Brisbane' >= ?
                    AND ts_utc AT TIME ZONE 'Australia/Brisbane' < ?
                ORDER BY ts_utc
            """, [orb_end, window_end]).fetchall()

            if len(bars) == 0:
                continue

            # Compute outcomes
            max_high = max(b[0] for b in bars)
            min_low = min(b[1] for b in bars)
            close_at_end = bars[-1][2]

            max_up = max_high - price_at_orb
            max_dn = price_at_orb - min_low
            net = close_at_end - price_at_orb
            tail_skew = max_up - max_dn
            tail_ratio = max_up / max_dn if max_dn > 0.01 else None

            results.append({
                'date_local': date_local,
                'orb_code': orb_code,
                'window': window_name,
                'max_up': max_up,
                'max_dn': max_dn,
                'net': net,
                'tail_skew': tail_skew,
                'tail_ratio': tail_ratio
            })

    print(f"  Computed outcomes for {len(results)} (date, orb, window) combinations")

    # Save to temp table
    df = pd.DataFrame(results)
    con.execute("DROP TABLE IF EXISTS post_outcomes")
    con.execute("""
        CREATE TABLE post_outcomes AS
        SELECT * FROM df
    """)

    print("  Saved to post_outcomes table")


def create_bucketed_features(con):
    """
    Create bucketed features for state definitions.

    - close_pos_bucket: LOW (0-0.33), MID (0.33-0.66), HIGH (0.66-1.0)
    - impulse_bucket: LOW/MID/HIGH based on impulse_score tertiles per ORB
    """
    print("\nCreating bucketed features...")

    # close_pos_bucket
    con.execute("""
        ALTER TABLE day_state_features ADD COLUMN IF NOT EXISTS close_pos_bucket VARCHAR
    """)

    con.execute("""
        UPDATE day_state_features
        SET close_pos_bucket = CASE
            WHEN pre_orb_close_pos < 0.33 THEN 'LOW'
            WHEN pre_orb_close_pos < 0.66 THEN 'MID'
            ELSE 'HIGH'
        END
    """)

    # impulse_bucket (per ORB tertiles)
    con.execute("""
        ALTER TABLE day_state_features ADD COLUMN IF NOT EXISTS impulse_bucket VARCHAR
    """)

    for orb_code in ['0900', '1000', '1100', '1800', '2300', '0030']:
        # Get tertile thresholds for this ORB
        tertiles = con.execute("""
            SELECT
                PERCENTILE_CONT(0.33) WITHIN GROUP (ORDER BY impulse_score) as t1,
                PERCENTILE_CONT(0.66) WITHIN GROUP (ORDER BY impulse_score) as t2
            FROM day_state_features
            WHERE orb_code = ?
        """, [orb_code]).fetchone()

        if tertiles and tertiles[0] is not None:
            t1, t2 = tertiles

            con.execute("""
                UPDATE day_state_features
                SET impulse_bucket = CASE
                    WHEN impulse_score < ? THEN 'LOW'
                    WHEN impulse_score < ? THEN 'MID'
                    ELSE 'HIGH'
                END
                WHERE orb_code = ?
            """, [t1, t2, orb_code])

    con.commit()
    print("  Bucketed features created")


def enumerate_candidate_states(con, orb_code):
    """
    Enumerate all possible states using bucketed feature vocabulary.

    Returns: List of (state_def_dict, state_sql_where) tuples
    """
    # Base vocabulary (always available)
    range_buckets = ['TIGHT', 'NORMAL', 'WIDE']
    disp_buckets = ['D_SMALL', 'D_MED', 'D_LARGE']
    close_pos_buckets = ['LOW', 'MID', 'HIGH']
    impulse_buckets = ['LOW', 'MID', 'HIGH']

    # Context-specific features
    sweep_features = []

    if orb_code == '0030':
        sweep_features = [
            ('london_swept_asia_high', [True, False]),
            ('london_swept_asia_low', [True, False]),
            ('nypre_swept_london_high_fail', [True, False]),
            ('nypre_swept_london_low_fail', [True, False])
        ]

    # Generate states (careful not to explode combinatorics)
    # Strategy: Start with 2-3 feature combinations, then add sweep flags

    states = []

    # 2-feature states (range + disp)
    for rb, db in product(range_buckets, disp_buckets):
        state_def = {
            'range_bucket': rb,
            'disp_bucket': db
        }
        where_clause = f"range_bucket = '{rb}' AND disp_bucket = '{db}'"
        states.append((state_def, where_clause))

    # 3-feature states (range + disp + close_pos)
    for rb, db, cpb in product(range_buckets, disp_buckets, close_pos_buckets):
        state_def = {
            'range_bucket': rb,
            'disp_bucket': db,
            'close_pos_bucket': cpb
        }
        where_clause = f"range_bucket = '{rb}' AND disp_bucket = '{db}' AND close_pos_bucket = '{cpb}'"
        states.append((state_def, where_clause))

    # 3-feature states (range + disp + impulse)
    for rb, db, ib in product(range_buckets, disp_buckets, impulse_buckets):
        state_def = {
            'range_bucket': rb,
            'disp_bucket': db,
            'impulse_bucket': ib
        }
        where_clause = f"range_bucket = '{rb}' AND disp_bucket = '{db}' AND impulse_bucket = '{ib}'"
        states.append((state_def, where_clause))

    # 4-feature states (range + disp + close_pos + impulse) - rare states only
    for rb, db, cpb, ib in product(range_buckets, disp_buckets, close_pos_buckets, impulse_buckets):
        state_def = {
            'range_bucket': rb,
            'disp_bucket': db,
            'close_pos_bucket': cpb,
            'impulse_bucket': ib
        }
        where_clause = f"range_bucket = '{rb}' AND disp_bucket = '{db}' AND close_pos_bucket = '{cpb}' AND impulse_bucket = '{ib}'"
        states.append((state_def, where_clause))

    # Add sweep flag combinations (0030 only)
    if orb_code == '0030':
        # Single sweep flag states
        for sweep_name, sweep_values in sweep_features:
            for rb, db, sweep_val in product(range_buckets, disp_buckets, [True]):
                state_def = {
                    'range_bucket': rb,
                    'disp_bucket': db,
                    sweep_name: sweep_val
                }
                where_clause = f"range_bucket = '{rb}' AND disp_bucket = '{db}' AND {sweep_name} = {sweep_val}"
                states.append((state_def, where_clause))

    return states


def test_state_edge(con, orb_code, state_def, state_where):
    """
    Test if a state has statistical edge.

    Returns: dict with test results or None if no edge
    """
    # Get sample size and frequency
    total_days = con.execute(f"""
        SELECT COUNT(*) FROM day_state_features WHERE orb_code = ?
    """, [orb_code]).fetchone()[0]

    state_days = con.execute(f"""
        SELECT COUNT(*) FROM day_state_features
        WHERE orb_code = ? AND {state_where}
    """, [orb_code]).fetchall()

    if not state_days or state_days[0][0] < MIN_SAMPLE_SIZE:
        return None

    n = state_days[0][0]
    frequency_pct = (n / total_days * 100) if total_days > 0 else 0

    # Rarity filter
    if frequency_pct > MAX_FREQUENCY_PCT or frequency_pct < MIN_FREQUENCY_PCT:
        return None

    # Get outcomes for this state
    outcomes = con.execute(f"""
        SELECT
            po.window,
            po.max_up,
            po.max_dn,
            po.net,
            po.tail_skew,
            po.tail_ratio
        FROM post_outcomes po
        JOIN day_state_features ds
            ON po.date_local = ds.date_local
            AND po.orb_code = ds.orb_code
        WHERE ds.orb_code = ?
            AND {state_where}
    """, [orb_code]).fetchall()

    if len(outcomes) == 0:
        return None

    # Group by window
    outcomes_df = pd.DataFrame(outcomes, columns=['window', 'max_up', 'max_dn', 'net', 'tail_skew', 'tail_ratio'])

    results = {
        'orb_code': orb_code,
        'state_def': state_def,
        'n': n,
        'frequency_pct': frequency_pct
    }

    edge_detected = False
    consistent_direction = None

    for window in ['post_30m', 'post_60m', 'post_90m']:
        window_data = outcomes_df[outcomes_df['window'] == window]

        if len(window_data) == 0:
            continue

        # Compute edge metrics
        median_max_up = window_data['max_up'].median()
        median_max_dn = window_data['max_dn'].median()
        median_tail_skew = window_data['tail_skew'].median()
        median_tail_ratio = window_data['tail_ratio'].median()

        # Sign skew: % of days where max_up > max_dn
        up_favored = (window_data['max_up'] > window_data['max_dn']).sum()
        dn_favored = (window_data['max_dn'] > window_data['max_up']).sum()

        if up_favored > dn_favored:
            sign_skew_pct = (up_favored / len(window_data)) * 100
            direction = 'UP'
        else:
            sign_skew_pct = (dn_favored / len(window_data)) * 100
            direction = 'DN'

        results[f'{window}_median_max_up'] = median_max_up
        results[f'{window}_median_max_dn'] = median_max_dn
        results[f'{window}_median_tail_skew'] = median_tail_skew
        results[f'{window}_median_tail_ratio'] = median_tail_ratio
        results[f'{window}_sign_skew_pct'] = sign_skew_pct
        results[f'{window}_direction'] = direction

        # Check edge criteria for post_60m
        if window == 'post_60m':
            if sign_skew_pct >= SIGN_SKEW_THRESHOLD:
                edge_detected = True
                consistent_direction = direction

    # Verify consistency across windows
    if edge_detected and consistent_direction:
        # Check if direction is same across 30m, 60m, 90m
        dir_30m = results.get('post_30m_direction')
        dir_60m = results.get('post_60m_direction')
        dir_90m = results.get('post_90m_direction')

        if dir_30m == dir_60m == dir_90m == consistent_direction:
            # Check tail_skew is meaningful
            tail_skew_60m = results['post_60m_median_tail_skew']
            tail_skew_ticks = abs(tail_skew_60m) / TICK_SIZE

            if tail_skew_ticks >= 3:  # At least 3 ticks asymmetry
                return results

    return None


def get_example_dates(con, orb_code, state_where, limit=5):
    """Get example dates for chart verification."""
    dates = con.execute(f"""
        SELECT date_local
        FROM day_state_features
        WHERE orb_code = ? AND {state_where}
        ORDER BY date_local DESC
        LIMIT ?
    """, [orb_code, limit]).fetchall()

    return [d[0] for d in dates]


def analyze_orb(con, orb_code):
    """Analyze single ORB for edge states."""
    print(f"\n{'='*80}")
    print(f"ANALYZING ORB: {orb_code}")
    print(f"{'='*80}")

    # Enumerate candidate states
    candidate_states = enumerate_candidate_states(con, orb_code)
    print(f"  Total candidate states: {len(candidate_states)}")

    # Test each state
    qualified_states = []

    for idx, (state_def, state_where) in enumerate(candidate_states):
        if idx % 100 == 0 and idx > 0:
            print(f"    Tested {idx}/{len(candidate_states)} states...")

        result = test_state_edge(con, orb_code, state_def, state_where)

        if result is not None:
            # Get example dates
            result['example_dates'] = get_example_dates(con, orb_code, state_where)
            qualified_states.append(result)

    print(f"  Qualified states found: {len(qualified_states)}")

    if len(qualified_states) == 0:
        print(f"\n  ❌ NO EDGE FOUND for {orb_code}")
        return []

    # Sort by edge strength (sign_skew_pct in post_60m)
    qualified_states.sort(key=lambda x: x['post_60m_sign_skew_pct'], reverse=True)

    # Return top candidates
    top_candidates = qualified_states[:MIN_CANDIDATES_TO_REPORT]

    return top_candidates


def format_state_def(state_def):
    """Format state definition for display."""
    parts = []
    for key, value in state_def.items():
        parts.append(f"{key}={value}")
    return " AND ".join(parts)


def print_results(candidates_by_orb):
    """Print analysis results in specified format."""
    print(f"\n{'='*80}")
    print("EDGE STATE DISCOVERY RESULTS")
    print(f"{'='*80}\n")

    for orb_code in ['0900', '1000', '1100', '1800', '2300', '0030']:
        print(f"\n{'='*80}")
        print(f"ORB: {orb_code}")
        print(f"{'='*80}")

        candidates = candidates_by_orb.get(orb_code, [])

        if len(candidates) == 0:
            print(f"\n❌ NO EDGE FOUND")
            print(f"\nNo states passed edge criteria:")
            print(f"  - Sign skew >= {SIGN_SKEW_THRESHOLD}%")
            print(f"  - Median tail skew >= 3 ticks")
            print(f"  - Consistent direction across 30m/60m/90m windows")
            print(f"  - Sample size >= {MIN_SAMPLE_SIZE}")
            print(f"  - Frequency: {MIN_FREQUENCY_PCT}%-{MAX_FREQUENCY_PCT}%")
            continue

        for idx, result in enumerate(candidates, 1):
            print(f"\n--- CANDIDATE #{idx} ---")
            print(f"State: {format_state_def(result['state_def'])}")
            print(f"Sample size: {result['n']} days ({result['frequency_pct']:.1f}%)")
            print()

            # Print outcomes by window
            for window in ['post_30m', 'post_60m', 'post_90m']:
                median_up = result.get(f'{window}_median_max_up', 0)
                median_dn = result.get(f'{window}_median_max_dn', 0)
                tail_skew = result.get(f'{window}_median_tail_skew', 0)
                tail_ratio = result.get(f'{window}_median_tail_ratio', 0)
                sign_skew = result.get(f'{window}_sign_skew_pct', 0)
                direction = result.get(f'{window}_direction', '')

                print(f"{window}:")
                print(f"  Median max_up: {median_up:.2f} ({median_up/TICK_SIZE:.1f} ticks)")
                print(f"  Median max_dn: {median_dn:.2f} ({median_dn/TICK_SIZE:.1f} ticks)")
                print(f"  Sign skew: {sign_skew:.1f}% {direction}-favored")
                print(f"  Median tail_skew: {tail_skew:.2f} ({tail_skew/TICK_SIZE:.1f} ticks)")
                print(f"  Median tail_ratio: {tail_ratio:.2f}x" if tail_ratio else "  Median tail_ratio: N/A")

            print(f"\nExample dates (recent 5):")
            for date in result['example_dates']:
                print(f"  {date}")

            # Failure mode guess
            print(f"\nFailure mode guess:")
            if result['post_60m_direction'] == 'UP':
                print(f"  Likely fails when: Price exhausts upside quickly, reverses sharply")
                print(f"  Watch for: Large wick rejection at highs, rapid return to ORB midpoint")
            else:
                print(f"  Likely fails when: Price exhausts downside quickly, reverses sharply")
                print(f"  Watch for: Large wick rejection at lows, rapid return to ORB midpoint")


def main():
    print(f"\n{'='*80}")
    print("EDGE STATE DISCOVERY - POST-ORB ASYMMETRY ANALYSIS")
    print(f"{'='*80}")
    print(f"\nConfiguration:")
    print(f"  Sign skew threshold: {SIGN_SKEW_THRESHOLD}%")
    print(f"  Min sample size: {MIN_SAMPLE_SIZE}")
    print(f"  Frequency range: {MIN_FREQUENCY_PCT}%-{MAX_FREQUENCY_PCT}%")
    print(f"  Min tail skew: 3 ticks")

    con = duckdb.connect(DB_PATH)

    # Step 1: Compute post-ORB outcomes
    compute_post_outcomes(con)

    # Step 2: Create bucketed features
    create_bucketed_features(con)

    # Step 3: Analyze each ORB independently
    candidates_by_orb = {}

    for orb_code in ['0900', '1000', '1100', '1800', '2300', '0030']:
        candidates = analyze_orb(con, orb_code)
        candidates_by_orb[orb_code] = candidates

    # Step 4: Print results
    print_results(candidates_by_orb)

    con.close()

    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
