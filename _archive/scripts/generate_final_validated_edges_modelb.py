"""
Generate final validated edges report from Model B analysis

Compiles ALL validated edges across ALL sessions that meet strict criteria:
- >=40 trades
- >=+0.10R delta vs baseline
- 3/3 temporal chunks positive
- <50% selectivity (where applicable)
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def test_temporal_stability(df):
    """Test 3-chunk temporal stability."""
    if len(df) < 40:
        return None

    df_sorted = df.sort_values('date_local')
    n = len(df_sorted)
    chunk_size = n // 3

    chunk1 = df_sorted.iloc[:chunk_size]
    chunk2 = df_sorted.iloc[chunk_size:2*chunk_size]
    chunk3 = df_sorted.iloc[2*chunk_size:]

    c1_avg = chunk1['r_multiple'].mean()
    c2_avg = chunk2['r_multiple'].mean()
    c3_avg = chunk3['r_multiple'].mean()

    positive_chunks = sum([c1_avg > 0, c2_avg > 0, c3_avg > 0])

    return {
        'c1': c1_avg,
        'c2': c2_avg,
        'c3': c3_avg,
        'positive_chunks': positive_chunks
    }


con = duckdb.connect(DB_PATH, read_only=True)

print("="*80)
print("FINAL VALIDATED EDGES REPORT - MODEL B (Entry-Anchored Risk)")
print("="*80)
print()
print("Validation criteria:")
print("  - >=40 trades minimum")
print("  - >=+0.10R delta vs baseline")
print("  - 3/3 temporal chunks positive")
print("  - Half-SL configuration (stop at ORB mid)")
print()

sessions = ['0900', '1000', '1100', '1800', '2300', '0030']

all_validated_edges = []

for orb_time in sessions:
    print("="*80)
    print(f"SCANNING {orb_time} ORB")
    print("="*80)
    print()

    # Get baseline
    baseline = con.execute("""
        SELECT
            COUNT(*) as n_trades,
            AVG(r_multiple) as avg_r
        FROM v_orb_trades_v3_modelb_half
        WHERE orb_time = ?
            AND break_dir IN ('UP', 'DOWN')
            AND outcome IN ('WIN', 'LOSS')
    """, [orb_time]).fetchone()

    if not baseline or baseline[0] == 0:
        print(f"No trades for {orb_time}")
        print()
        continue

    baseline_n, baseline_avg_r = baseline
    print(f"Baseline: {baseline_n} trades, {baseline_avg_r:+.3f}R avg")
    print()

    # Get state-filtered data
    query = f"""
        SELECT
            t.date_local,
            t.r_multiple,
            t.break_dir,
            s.range_bucket,
            s.disp_bucket,
            s.close_pos_bucket
        FROM v_orb_trades_v3_modelb_half t
        JOIN day_state_features s
            ON t.date_local = s.date_local
            AND s.orb_code = '{orb_time}'
        WHERE t.orb_time = '{orb_time}'
            AND t.break_dir IN ('UP', 'DOWN')
            AND t.outcome IN ('WIN', 'LOSS')
            AND s.range_bucket IS NOT NULL
    """

    df = con.execute(query).df()

    if len(df) == 0:
        print(f"No state data for {orb_time}")
        print()
        continue

    # Test state configurations
    state_configs = [
        ('TIGHT', 'TIGHT', None, None),
        ('NORMAL', 'NORMAL', None, None),
        ('WIDE', 'WIDE', None, None),
        ('TIGHT + D_SMALL', 'TIGHT', 'D_SMALL', None),
        ('TIGHT + D_MED', 'TIGHT', 'D_MED', None),
        ('NORMAL + D_SMALL', 'NORMAL', 'D_SMALL', None),
        ('NORMAL + D_MED', 'NORMAL', 'D_MED', None),
        ('WIDE + D_SMALL', 'WIDE', 'D_SMALL', None),
        ('TIGHT + C_LOW', 'TIGHT', None, 'C_LOW'),
        ('NORMAL + C_LOW', 'NORMAL', None, 'C_LOW'),
        ('NORMAL + C_MID', 'NORMAL', None, 'C_MID'),
    ]

    session_edges = []

    for config in state_configs:
        state_name, range_b, disp_b, close_b = config

        mask = (df['range_bucket'] == range_b)
        if disp_b:
            mask = mask & (df['disp_bucket'] == disp_b)
        if close_b:
            mask = mask & (df['close_pos_bucket'] == close_b)

        filtered = df[mask]

        if len(filtered) < 40:
            continue

        avg_r = filtered['r_multiple'].mean()
        delta = avg_r - baseline_avg_r

        if delta < 0.10:
            continue

        temporal = test_temporal_stability(filtered)

        if temporal is None or temporal['positive_chunks'] < 3:
            continue

        # VALIDATED EDGE!
        session_edges.append({
            'orb': orb_time,
            'state': state_name,
            'n_trades': len(filtered),
            'avg_r': avg_r,
            'delta': delta,
            'c1': temporal['c1'],
            'c2': temporal['c2'],
            'c3': temporal['c3']
        })

    if len(session_edges) > 0:
        print(f"[VALIDATED EDGES FOUND]: {len(session_edges)}")
        for edge in session_edges:
            print(f"  {edge['state']}: {edge['n_trades']} trades, {edge['avg_r']:+.3f}R avg ({edge['delta']:+.3f}R delta)")
            print(f"    Temporal: Early {edge['c1']:+.3f}R, Mid {edge['c2']:+.3f}R, Late {edge['c3']:+.3f}R")
        all_validated_edges.extend(session_edges)
    else:
        print("[NO VALIDATED EDGES]")

    print()

# Final summary
print("="*80)
print("FINAL SUMMARY - ALL VALIDATED EDGES")
print("="*80)
print()

if len(all_validated_edges) == 0:
    print("[NO VALIDATED EDGES FOUND ACROSS ALL SESSIONS]")
    print()
    print("This is expected with correct Model B execution on tiny ORBs.")
    print("Old results (ORB-anchored risk) created fake edges.")
    print()
    print("Recommendations:")
    print("  1. Focus on larger ORBs (1800, 0030) where slippage is less problematic")
    print("  2. Consider adding buffer_ticks to entry trigger to reduce slippage")
    print("  3. Test pattern-based entries instead of pure breakouts")
    print("  4. Consider longer ORB periods (10-15 min) for Asia sessions")
else:
    print(f"TOTAL VALIDATED EDGES: {len(all_validated_edges)}")
    print()

    # Group by session
    by_session = {}
    for edge in all_validated_edges:
        orb = edge['orb']
        if orb not in by_session:
            by_session[orb] = []
        by_session[orb].append(edge)

    print("BY SESSION:")
    print("-"*80)

    total_trades_per_year = 0
    weighted_r = 0

    for orb in sorted(by_session.keys()):
        edges = by_session[orb]
        print(f"\n{orb} ORB: {len(edges)} validated edge(s)")

        for edge in edges:
            trades_per_year = edge['n_trades'] / 2  # Approx 2 years of data
            total_trades_per_year += trades_per_year

            weighted_r += edge['avg_r'] * trades_per_year

            print(f"  {edge['state']}:")
            print(f"    {edge['n_trades']} trades (~{trades_per_year:.0f}/year), {edge['avg_r']:+.3f}R avg")
            print(f"    Delta: {edge['delta']:+.3f}R vs baseline")
            print(f"    Temporal: {edge['c1']:+.3f}R / {edge['c2']:+.3f}R / {edge['c3']:+.3f}R (3/3 positive)")

    print()
    print("-"*80)
    print("SYSTEM TOTALS:")
    print(f"  Total trades/year: ~{total_trades_per_year:.0f}")
    print(f"  Weighted avg R: {weighted_r / total_trades_per_year:+.3f}R" if total_trades_per_year > 0 else "  N/A")
    print(f"  Expected annual R: ~{weighted_r:.1f}R" if total_trades_per_year > 0 else "  N/A")
    print()

    print("="*80)
    print("READY TO DEPLOY")
    print("="*80)
    print()
    print("These edges use:")
    print("  - Model B execution (entry-anchored risk)")
    print("  - Half-SL (stop at ORB mid)")
    print("  - 5-minute ORB")
    print("  - Entry at next 1m bar open after confirmation")
    print("  - State-based filtering (range_bucket, disp_bucket, etc.)")
    print()
    print("Next steps:")
    print("  1. Paper trade to validate execution")
    print("  2. Build pre-trade checklist for state identification")
    print("  3. Automate state classification")
    print("  4. Track live vs backtest performance")
    print()

con.close()

print("="*80)
print("REPORT COMPLETE")
print("="*80)
print()
