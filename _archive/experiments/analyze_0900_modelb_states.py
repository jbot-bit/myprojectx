"""
0900 ORB State-Filtered Analysis with Model B execution
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"
ORB_TIME = '0900'

con = duckdb.connect(DB_PATH, read_only=True)

print("="*80)
print(f"{ORB_TIME} ORB - MODEL B STATE-FILTERED ANALYSIS")
print("="*80)
print()

# Baseline
print("BASELINE (Half-SL, no filtering):")
print("-"*80)

baseline = con.execute("""
    SELECT
        COUNT(*) as n_trades,
        AVG(r_multiple) as avg_r,
        SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
    FROM v_orb_trades_v3_modelb_half
    WHERE orb_time = ?
        AND break_dir IN ('UP', 'DOWN')
        AND outcome IN ('WIN', 'LOSS')
""", [ORB_TIME]).fetchone()

if not baseline or baseline[0] == 0:
    print(f"No trades found for {ORB_TIME}")
    con.close()
    exit(0)

baseline_n, baseline_avg_r, baseline_win_rate = baseline
print(f"Trades: {baseline_n}")
print(f"Avg R: {baseline_avg_r:+.3f}R")
print(f"Win rate: {baseline_win_rate:.1f}%")
print()

# State-filtered analysis
print("="*80)
print("STATE-FILTERED ANALYSIS")
print("="*80)
print()

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
        AND s.orb_code = '{ORB_TIME}'
    WHERE t.orb_time = '{ORB_TIME}'
        AND t.break_dir IN ('UP', 'DOWN')
        AND t.outcome IN ('WIN', 'LOSS')
        AND s.range_bucket IS NOT NULL
"""

df = con.execute(query).df()

if len(df) == 0:
    print("No trades with state data")
    con.close()
    exit(0)

print(f"Total trades with state data: {len(df)}")
print()

# Test states
states = [
    ('TIGHT', None, None),
    ('NORMAL', None, None),
    ('WIDE', None, None),
    ('TIGHT + D_SMALL', 'TIGHT', 'D_SMALL'),
    ('NORMAL + D_SMALL', 'NORMAL', 'D_SMALL'),
    ('NORMAL + D_MED', 'NORMAL', 'D_MED'),
]

results = []

for state_tuple in states:
    state_name, range_b, disp_b = state_tuple

    if range_b is None:
        # Skip for now
        continue
    else:
        mask = (df['range_bucket'] == range_b)
        if disp_b:
            mask = mask & (df['disp_bucket'] == disp_b)
        filtered = df[mask]

    if len(filtered) < 40:
        continue

    avg_r = filtered['r_multiple'].mean()

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

    delta = avg_r - baseline_avg_r

    results.append({
        'state': state_name,
        'n_trades': len(filtered),
        'avg_r': avg_r,
        'delta': delta,
        'positive_chunks': positive_chunks,
        'c1': c1_avg,
        'c2': c2_avg,
        'c3': c3_avg
    })

# Print results
print(f"STATE-FILTERED RESULTS (vs baseline {baseline_avg_r:+.3f}R):")
print("-"*80)
print(f"{'State':<25} {'Trades':<10} {'Avg R':<12} {'Delta':<12} {'Chunks':<10}")
print("-"*80)

for r in sorted(results, key=lambda x: x['delta'], reverse=True):
    print(f"{r['state']:<25} {r['n_trades']:<10} {r['avg_r']:+.3f}R      {r['delta']:+.3f}R      {r['positive_chunks']}/3")
    print(f"{'':25}           Early: {r['c1']:+.3f}R, Mid: {r['c2']:+.3f}R, Late: {r['c3']:+.3f}R")

print()

# Validation
print("="*80)
print("VALIDATION CHECK (>=40 trades, >=+0.10R delta, 3/3 chunks positive):")
print("="*80)
print()

validated = [r for r in results if r['n_trades'] >= 40 and r['delta'] >= 0.10 and r['positive_chunks'] == 3]

if len(validated) > 0:
    print(f"[VALIDATED EDGES FOUND]: {len(validated)}")
    for r in validated:
        print(f"  - {r['state']}: {r['n_trades']} trades, {r['avg_r']:+.3f}R avg ({r['delta']:+.3f}R delta), 3/3 chunks")
        print(f"      Early: {r['c1']:+.3f}R, Mid: {r['c2']:+.3f}R, Late: {r['c3']:+.3f}R")
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
            print(f"      Early: {best['c1']:+.3f}R, Mid: {best['c2']:+.3f}R, Late: {best['c3']:+.3f}R")

print()

con.close()

print("="*80)
print(f"{ORB_TIME} ANALYSIS COMPLETE")
print("="*80)
print()
