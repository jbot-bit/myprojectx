"""
Test 0900 UP-only breakout with state filtering

Hypothesis: Since UP breakouts are less negative (-0.015R vs -0.036R),
maybe with proper state filtering, UP-only can become positive.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def test_up_only_with_states(con):
    """Test UP breakouts only, filtered by pre-ORB states."""

    print("="*80)
    print("0900 UP-ONLY BREAKOUT WITH STATE FILTERING")
    print("="*80)
    print()

    # Get baseline UP-only (no filtering)
    baseline_up = con.execute("""
        SELECT
            COUNT(*) as n_trades,
            AVG(r_multiple) as avg_r
        FROM orb_trades_1m_exec_nofilters
        WHERE orb = '0900'
            AND close_confirmations = 1
            AND rr = 1.0
            AND direction = 'UP'
    """).fetchone()

    print(f"Baseline UP-only (no filtering):")
    print(f"  {baseline_up[0]} trades, {baseline_up[1]:+.3f}R avg")
    print()

    # Now test with state filtering
    query = """
        SELECT
            t.date_local,
            t.r_multiple,
            s.range_bucket,
            s.disp_bucket,
            s.close_pos_bucket
        FROM orb_trades_1m_exec_nofilters t
        JOIN day_state_features s
            ON t.date_local = s.date_local
            AND s.orb_code = '0900'
        WHERE t.orb = '0900'
            AND t.close_confirmations = 1
            AND t.rr = 1.0
            AND t.direction = 'UP'
            AND s.range_bucket IS NOT NULL
    """

    df = con.execute(query).df()

    print(f"Total UP trades with state data: {len(df)}")
    print()

    # Test states
    states = [
        ('TIGHT', None, None),
        ('NORMAL', None, None),
        ('WIDE', None, None),
        ('NORMAL', 'D_SMALL', None),
        ('NORMAL', 'D_MED', None),
        ('TIGHT', 'D_SMALL', None),
    ]

    results = []

    for state in states:
        range_b, disp_b, close_b = state

        mask = (df['range_bucket'] == range_b)
        if disp_b:
            mask = mask & (df['disp_bucket'] == disp_b)
        if close_b:
            mask = mask & (df['close_pos_bucket'] == close_b)

        filtered = df[mask]

        if len(filtered) < 40:
            continue

        avg_r = filtered['r_multiple'].mean()
        state_str = f"{range_b}"
        if disp_b:
            state_str += f" + {disp_b}"
        if close_b:
            state_str += f" + {close_b}"

        # Temporal check
        filtered_sorted = filtered.sort_values('date_local')
        n = len(filtered_sorted)
        chunk_size = n // 3

        chunk1 = filtered_sorted.iloc[:chunk_size]
        chunk2 = filtered_sorted.iloc[chunk_size:2*chunk_size]
        chunk3 = filtered_sorted.iloc[2*chunk_size:]

        positive_chunks = sum([
            chunk1['r_multiple'].mean() > 0,
            chunk2['r_multiple'].mean() > 0,
            chunk3['r_multiple'].mean() > 0
        ])

        results.append({
            'state': state_str,
            'n_trades': len(filtered),
            'avg_r': avg_r,
            'delta': avg_r - baseline_up[1],  # vs baseline UP
            'positive_chunks': positive_chunks
        })

    # Print results
    print("STATE-FILTERED UP-ONLY RESULTS:")
    print("-"*80)
    print(f"{'State':<25} {'Trades':<10} {'Avg R':<12} {'Delta':<12} {'Chunks':<10}")
    print("-"*80)

    for r in sorted(results, key=lambda x: x['delta'], reverse=True):
        print(f"{r['state']:<25} {r['n_trades']:<10} {r['avg_r']:+.3f}R      {r['delta']:+.3f}R      {r['positive_chunks']}/3")

    print()

    # Check for validation
    print("VALIDATION CHECK (>=40 trades, >=+0.10R delta, 3/3 chunks):")
    print("-"*80)

    validated = [r for r in results if r['n_trades'] >= 40 and r['delta'] >= 0.10 and r['positive_chunks'] == 3]

    if len(validated) > 0:
        print(f"[VALIDATED EDGES FOUND]: {len(validated)}")
        for r in validated:
            print(f"  - {r['state']}: {r['n_trades']} trades, {r['delta']:+.3f}R delta, 3/3 chunks")
    else:
        best = max(results, key=lambda x: x['delta']) if results else None
        if best:
            print(f"[NO VALIDATED EDGES]")
            print(f"Best result: {best['state']} with {best['n_trades']} trades, {best['delta']:+.3f}R delta")
            if best['n_trades'] < 40:
                print(f"  (failed: < 40 trades)")
            elif best['delta'] < 0.10:
                print(f"  (failed: delta < +0.10R)")
            elif best['positive_chunks'] < 3:
                print(f"  (failed: only {best['positive_chunks']}/3 chunks positive)")

    print()


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    test_up_only_with_states(con)

    con.close()


if __name__ == '__main__':
    main()
