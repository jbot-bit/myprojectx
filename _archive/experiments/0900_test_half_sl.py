"""
Test 0900 with HALF-SL (ORB mid stop) configuration
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

con = duckdb.connect(DB_PATH, read_only=True)

print("="*80)
print("0900 ORB WITH HALF-SL (ORB MID STOP) CONFIGURATION")
print("="*80)
print()

# Check what columns exist in v_orb_trades_half
print("Checking v_orb_trades_half table structure:")
cols = con.execute("DESCRIBE v_orb_trades_half").fetchall()
print("Columns:")
for col in cols:
    print(f"  {col[0]}: {col[1]}")
print()

# Get baseline with half-SL
baseline = con.execute("""
    SELECT
        COUNT(*) as n_trades,
        AVG(r_multiple) as avg_r,
        SUM(r_multiple) as total_r,
        SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
    FROM v_orb_trades_half
    WHERE orb_time = '0900'
""").fetchone()

if baseline is None:
    print("No data in v_orb_trades_half for 0900")
    con.close()
    exit()

n_trades, avg_r, total_r, win_rate = baseline

print("BASELINE 0900 WITH HALF-SL (ORB MID STOP):")
print(f"  Trades: {n_trades}")
print(f"  Avg R: {avg_r:+.3f}R")
print(f"  Total R: {total_r:+.2f}R")
print(f"  Win rate: {win_rate:.1f}%")
print()

# Compare to full-SL
full_sl = con.execute("""
    SELECT
        COUNT(*) as n_trades,
        AVG(r_multiple) as avg_r
    FROM orb_trades_1m_exec_nofilters
    WHERE orb = '0900'
        AND close_confirmations = 1
        AND rr = 1.0
""").fetchone()

print("COMPARISON:")
print(f"  Half-SL: {avg_r:+.3f}R ({n_trades} trades)")
print(f"  Full-SL: {full_sl[1]:+.3f}R ({full_sl[0]} trades)")
print(f"  Delta: {avg_r - full_sl[1]:+.3f}R improvement")
print()

# Test with state filtering
print("="*80)
print("HALF-SL WITH STATE FILTERING")
print("="*80)
print()

query = """
    SELECT
        t.date_local,
        t.r_multiple,
        t.break_dir,
        s.range_bucket,
        s.disp_bucket
    FROM v_orb_trades_half t
    JOIN day_state_features s
        ON t.date_local = s.date_local
        AND s.orb_code = '0900'
    WHERE t.orb_time = '0900'
        AND s.range_bucket IS NOT NULL
"""

df = con.execute(query).df()

print(f"Total trades with state data: {len(df)}")
print()

# Test states
states = [
    ('All', None, None),
    ('NORMAL', 'NORMAL', None),
    ('TIGHT', 'TIGHT', None),
    ('WIDE', 'WIDE', None),
    ('NORMAL + D_SMALL', 'NORMAL', 'D_SMALL'),
    ('TIGHT + D_SMALL', 'TIGHT', 'D_SMALL'),
]

results = []

for state_name, range_b, disp_b in states:
    if range_b is None:
        filtered = df
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

    delta = avg_r - avg_r  # vs half-SL baseline (for now, just show absolute)

    results.append({
        'state': state_name,
        'n_trades': len(filtered),
        'avg_r': avg_r,
        'positive_chunks': positive_chunks,
        'c1': c1_avg,
        'c2': c2_avg,
        'c3': c3_avg
    })

# Print results
print("STATE-FILTERED HALF-SL RESULTS:")
print("-"*80)
print(f"{'State':<25} {'Trades':<10} {'Avg R':<12} {'Chunks':<10}")
print("-"*80)

for r in sorted(results, key=lambda x: x['avg_r'], reverse=True):
    print(f"{r['state']:<25} {r['n_trades']:<10} {r['avg_r']:+.3f}R      {r['positive_chunks']}/3")
    print(f"{'':25}           Early: {r['c1']:+.3f}R, Mid: {r['c2']:+.3f}R, Late: {r['c3']:+.3f}R")

print()

# Check for validation
print("="*80)
print("VALIDATION CHECK (>=40 trades, >=+0.10R avg, 3/3 chunks positive):")
print("="*80)
print()

validated = [r for r in results if r['n_trades'] >= 40 and r['avg_r'] >= 0.10 and r['positive_chunks'] == 3]

if len(validated) > 0:
    print(f"[VALIDATED EDGES FOUND]: {len(validated)}")
    for r in validated:
        print(f"  - {r['state']}: {r['n_trades']} trades, {r['avg_r']:+.3f}R avg, 3/3 chunks")
        print(f"      Early: {r['c1']:+.3f}R, Mid: {r['c2']:+.3f}R, Late: {r['c3']:+.3f}R")
else:
    best = max(results, key=lambda x: x['avg_r']) if results else None
    if best:
        print(f"[NO VALIDATED EDGES]")
        print(f"Best result: {best['state']} with {best['n_trades']} trades, {best['avg_r']:+.3f}R avg")
        if best['n_trades'] < 40:
            print(f"  (failed: < 40 trades)")
        elif best['avg_r'] < 0.10:
            print(f"  (failed: avg < +0.10R)")
        elif best['positive_chunks'] < 3:
            print(f"  (failed: only {best['positive_chunks']}/3 chunks positive)")
            print(f"      Early: {best['c1']:+.3f}R, Mid: {best['c2']:+.3f}R, Late: {best['c3']:+.3f}R")

print()

con.close()
