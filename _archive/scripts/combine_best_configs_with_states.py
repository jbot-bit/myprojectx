"""
For the BEST execution configs from each session, test state filtering

Takes top 3 configs per session and combines with state filters.
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def test_config_with_states(con, orb_time, config_id):
    """Test a single config with state filtering."""

    # Get trades for this config
    trades = con.execute(f"""
        SELECT
            date_local,
            orb_{orb_time}_r_multiple as r_multiple,
            orb_{orb_time}_outcome as outcome
        FROM execution_grid_results
        WHERE config_id = ?
            AND orb_{orb_time}_break_dir IN ('UP', 'DOWN')
            AND orb_{orb_time}_outcome IN ('WIN', 'LOSS')
    """, [config_id]).df()

    if len(trades) < 40:
        return []

    baseline_avg_r = trades['r_multiple'].mean()

    # Join with states
    query = f"""
        SELECT
            g.date_local,
            g.orb_{orb_time}_r_multiple as r_multiple,
            s.range_bucket,
            s.disp_bucket
        FROM execution_grid_results g
        JOIN day_state_features s
            ON g.date_local = s.date_local
            AND s.orb_code = '{orb_time}'
        WHERE g.config_id = ?
            AND g.orb_{orb_time}_break_dir IN ('UP', 'DOWN')
            AND g.orb_{orb_time}_outcome IN ('WIN', 'LOSS')
            AND s.range_bucket IS NOT NULL
    """

    df = con.execute(query, [config_id]).df()

    if len(df) == 0:
        return []

    # Test states
    state_configs = [
        ('TIGHT', 'TIGHT', None),
        ('NORMAL', 'NORMAL', None),
        ('WIDE', 'WIDE', None),
        ('TIGHT + D_SMALL', 'TIGHT', 'D_SMALL'),
        ('NORMAL + D_SMALL', 'NORMAL', 'D_SMALL'),
    ]

    results = []

    for state_tuple in state_configs:
        state_name, range_b, disp_b = state_tuple

        mask = (df['range_bucket'] == range_b)
        if disp_b:
            mask = mask & (df['disp_bucket'] == disp_b)

        filtered = df[mask]

        if len(filtered) < 40:
            continue

        avg_r = filtered['r_multiple'].mean()
        delta = avg_r - baseline_avg_r

        if delta < 0.10:
            continue

        # Temporal stability
        filtered_sorted = filtered.sort_values('date_local')
        n = len(filtered_sorted)
        chunk_size = n // 3

        chunk1 = filtered_sorted.iloc[:chunk_size]
        chunk2 = filtered_sorted.iloc[chunk_size:2*chunk_size]
        chunk3 = filtered_sorted.iloc[2*chunk_size:]

        c1_avg = chunk1['r_multiple'].mean()
        c2_avg = chunk2['r_multiple'].mean()
        c3_avg = chunk3['r_multiple'].mean()

        positive_chunks = sum([c1_avg > 0, c2_avg > 0, c3_avg > 0])

        if positive_chunks < 3:
            continue

        # VALIDATED!
        results.append({
            'state': state_name,
            'n_trades': len(filtered),
            'avg_r': avg_r,
            'delta': delta,
            'c1': c1_avg,
            'c2': c2_avg,
            'c3': c3_avg
        })

    return results


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*80)
    print("COMBINING BEST CONFIGS WITH STATE FILTERING")
    print("="*80)
    print()

    sessions = ['0900', '1000', '1100', '1800', '2300', '0030']

    all_validated = {}

    for orb in sessions:
        print("="*80)
        print(f"{orb} ORB - TESTING TOP CONFIGS WITH STATE FILTERING")
        print("="*80)
        print()

        # Get top 3 configs by avg R
        top_configs = con.execute(f"""
            WITH config_stats AS (
                SELECT
                    config_id,
                    COUNT(*) as n_trades,
                    AVG(orb_{orb}_r_multiple) as avg_r
                FROM execution_grid_results
                WHERE orb_{orb}_break_dir IN ('UP', 'DOWN')
                    AND orb_{orb}_outcome IN ('WIN', 'LOSS')
                GROUP BY config_id
                HAVING COUNT(*) >= 40
            )
            SELECT config_id, n_trades, avg_r
            FROM config_stats
            ORDER BY avg_r DESC
            LIMIT 3
        """).fetchall()

        if not top_configs:
            print(f"No configs with >=40 trades for {orb}")
            print()
            continue

        print(f"Testing top {len(top_configs)} configs with state filtering:")
        print()

        session_validated = []

        for config_id, n_trades, avg_r in top_configs:
            # Get config details
            cfg = con.execute("""
                SELECT orb_minutes, entry_method, buffer_ticks, sl_mode, close_confirmations, rr
                FROM execution_grid_configs
                WHERE config_id = ?
            """, [config_id]).fetchone()

            config_str = f"{cfg[0]}min, {cfg[1]}, buf={cfg[2]}, {cfg[3]}, {cfg[4]}-bar, RR={cfg[5]}"

            print(f"Config {config_id}: {config_str}")
            print(f"  Baseline: {n_trades} trades, {avg_r:+.3f}R")

            # Test with states
            state_results = test_config_with_states(con, orb, config_id)

            if len(state_results) > 0:
                print(f"  [VALIDATED STATES]: {len(state_results)}")
                for sr in state_results:
                    print(f"    {sr['state']}: {sr['n_trades']} trades, {sr['avg_r']:+.3f}R ({sr['delta']:+.3f}R delta)")
                    session_validated.append({
                        'config_id': config_id,
                        'config_str': config_str,
                        **sr
                    })
            else:
                print(f"  [NO VALIDATED STATES]")

            print()

        if session_validated:
            all_validated[orb] = session_validated

    # Final summary
    print("="*80)
    print("FINAL SUMMARY - CONFIGS + STATES")
    print("="*80)
    print()

    if len(all_validated) == 0:
        print("[NO VALIDATED CONFIG + STATE COMBINATIONS]")
    else:
        print(f"Sessions with validated combinations: {len(all_validated)}")
        print()

        for orb, validated in all_validated.items():
            print(f"{orb} ORB: {len(validated)} validated combination(s)")
            for v in validated[:5]:  # Top 5
                print(f"  Config {v['config_id']} + {v['state']}")
                print(f"    {v['n_trades']} trades, {v['avg_r']:+.3f}R ({v['delta']:+.3f}R delta)")
            print()

    con.close()

    print("="*80)
    print("STATE FILTERING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
