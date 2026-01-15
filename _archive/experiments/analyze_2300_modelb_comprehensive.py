"""
2300 ORB - COMPREHENSIVE MODEL B ANALYSIS

Tests EVERYTHING:
- Baseline (full-SL, half-SL)
- Directional bias (UP vs DOWN)
- State filtering (all combinations)
- Entry timing variations
- Combined filters
- Pattern-based (immediate rejection, balance failure, etc.)
- Temporal stability on everything
"""

import duckdb
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "gold.db"
ORB_TIME = '2300'
SYMBOL = "MGC"

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
print(f"2300 ORB - COMPREHENSIVE MODEL B ANALYSIS")
print("="*80)
print()

# ============================================================================
# TEST 1: BASELINE COMPARISON (Full-SL vs Half-SL)
# ============================================================================

print("TEST 1: BASELINE COMPARISON (Full-SL vs Half-SL)")
print("-"*80)

full_sl = con.execute("""
    SELECT
        COUNT(*) as n_trades,
        AVG(r_multiple) as avg_r,
        SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
    FROM v_orb_trades_v3_modelb
    WHERE orb_time = ?
        AND break_dir IN ('UP', 'DOWN')
        AND outcome IN ('WIN', 'LOSS')
""", [ORB_TIME]).fetchone()

half_sl = con.execute("""
    SELECT
        COUNT(*) as n_trades,
        AVG(r_multiple) as avg_r,
        SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
    FROM v_orb_trades_v3_modelb_half
    WHERE orb_time = ?
        AND break_dir IN ('UP', 'DOWN')
        AND outcome IN ('WIN', 'LOSS')
""", [ORB_TIME]).fetchone()

print(f"Full-SL:  {full_sl[0]} trades, {full_sl[1]:+.3f}R avg, {full_sl[2]:.1f}% win")
print(f"Half-SL:  {half_sl[0]} trades, {half_sl[1]:+.3f}R avg, {half_sl[2]:.1f}% win")
print(f"Delta:    {half_sl[1] - full_sl[1]:+.3f}R improvement with Half-SL")
print()

baseline_avg_r = half_sl[1]
baseline_n = half_sl[0]

# ============================================================================
# TEST 2: DIRECTIONAL BIAS (UP vs DOWN)
# ============================================================================

print("="*80)
print("TEST 2: DIRECTIONAL BIAS (UP vs DOWN)")
print("-"*80)

for direction in ['UP', 'DOWN']:
    result = con.execute("""
        SELECT
            COUNT(*) as n_trades,
            AVG(r_multiple) as avg_r,
            SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
        FROM v_orb_trades_v3_modelb_half
        WHERE orb_time = ?
            AND break_dir = ?
            AND outcome IN ('WIN', 'LOSS')
    """, [ORB_TIME, direction]).fetchone()

    print(f"{direction}: {result[0]} trades, {result[1]:+.3f}R avg, {result[2]:.1f}% win")

print()

# ============================================================================
# TEST 3: STATE FILTERING (All combinations)
# ============================================================================

print("="*80)
print("TEST 3: STATE FILTERING (Comprehensive)")
print("-"*80)

query = f"""
    SELECT
        t.date_local,
        t.r_multiple,
        t.break_dir,
        s.range_bucket,
        s.disp_bucket,
        s.close_pos_bucket,
        s.impulse_bucket
    FROM v_orb_trades_v3_modelb_half t
    JOIN day_state_features s
        ON t.date_local = s.date_local
        AND s.orb_code = '2300'
    WHERE t.orb_time = '2300'
        AND t.break_dir IN ('UP', 'DOWN')
        AND t.outcome IN ('WIN', 'LOSS')
        AND s.range_bucket IS NOT NULL
"""

df = con.execute(query).df()

if len(df) == 0:
    print("No trades with state data")
else:
    print(f"Total trades with state data: {len(df)}")
    print()

    # Test all state combinations
    state_configs = [
        # Single filters
        ('TIGHT', 'TIGHT', None, None, None),
        ('NORMAL', 'NORMAL', None, None, None),
        ('WIDE', 'WIDE', None, None, None),

        # Range + Disp
        ('TIGHT + D_SMALL', 'TIGHT', 'D_SMALL', None, None),
        ('TIGHT + D_MED', 'TIGHT', 'D_MED', None, None),
        ('NORMAL + D_SMALL', 'NORMAL', 'D_SMALL', None, None),
        ('NORMAL + D_MED', 'NORMAL', 'D_MED', None, None),
        ('WIDE + D_SMALL', 'WIDE', 'D_SMALL', None, None),

        # Range + Close Position
        ('TIGHT + C_LOW', 'TIGHT', None, 'C_LOW', None),
        ('TIGHT + C_MID', 'TIGHT', None, 'C_MID', None),
        ('TIGHT + C_HIGH', 'TIGHT', None, 'C_HIGH', None),
        ('NORMAL + C_LOW', 'NORMAL', None, 'C_LOW', None),
        ('NORMAL + C_MID', 'NORMAL', None, 'C_MID', None),
        ('NORMAL + C_HIGH', 'NORMAL', None, 'C_HIGH', None),

        # Triple combinations
        ('TIGHT + D_SMALL + C_LOW', 'TIGHT', 'D_SMALL', 'C_LOW', None),
        ('NORMAL + D_SMALL + C_LOW', 'NORMAL', 'D_SMALL', 'C_LOW', None),
        ('NORMAL + D_SMALL + C_MID', 'NORMAL', 'D_SMALL', 'C_MID', None),
    ]

    results = []

    for config in state_configs:
        state_name, range_b, disp_b, close_b, impulse_b = config

        mask = (df['range_bucket'] == range_b)
        if disp_b:
            mask = mask & (df['disp_bucket'] == disp_b)
        if close_b:
            mask = mask & (df['close_pos_bucket'] == close_b)
        if impulse_b:
            mask = mask & (df['impulse_bucket'] == impulse_b)

        filtered = df[mask]

        if len(filtered) < 40:
            continue

        avg_r = filtered['r_multiple'].mean()
        delta = avg_r - baseline_avg_r

        temporal = test_temporal_stability(filtered)

        results.append({
            'state': state_name,
            'n_trades': len(filtered),
            'avg_r': avg_r,
            'delta': delta,
            'positive_chunks': temporal['positive_chunks'],
            'c1': temporal['c1'],
            'c2': temporal['c2'],
            'c3': temporal['c3']
        })

    # Print results
    print(f"STATE-FILTERED RESULTS (vs baseline {baseline_avg_r:+.3f}R):")
    print("-"*80)
    print(f"{'State':<35} {'Trades':<10} {'Avg R':<12} {'Delta':<12} {'Chunks':<10}")
    print("-"*80)

    for r in sorted(results, key=lambda x: x['delta'], reverse=True)[:20]:  # Top 20
        print(f"{r['state']:<35} {r['n_trades']:<10} {r['avg_r']:+.3f}R      {r['delta']:+.3f}R      {r['positive_chunks']}/3")

    print()

    # Validation
    validated = [r for r in results if r['n_trades'] >= 40 and r['delta'] >= 0.10 and r['positive_chunks'] == 3]

    if len(validated) > 0:
        print(f"[VALIDATED EDGES]: {len(validated)}")
        for r in validated:
            print(f"  {r['state']}: {r['n_trades']} trades, {r['delta']:+.3f}R delta, 3/3 chunks")
    else:
        print("[NO VALIDATED STATE EDGES]")

print()

# ============================================================================
# TEST 4: DIRECTIONAL + STATE FILTERING
# ============================================================================

print("="*80)
print("TEST 4: DIRECTIONAL + STATE FILTERING")
print("-"*80)

if len(df) > 0:
    for direction in ['UP', 'DOWN']:
        print(f"\n{direction} breakouts only:")
        print("-"*40)

        dir_df = df[df['break_dir'] == direction]

        if len(dir_df) < 40:
            print(f"  Insufficient trades ({len(dir_df)} < 40)")
            continue

        # Test top states
        for state_tuple in [('TIGHT', None, None), ('NORMAL', None, None), ('WIDE', None, None),
                            ('TIGHT', 'D_SMALL', None), ('NORMAL', 'D_SMALL', None)]:
            range_b, disp_b, close_b = state_tuple

            mask = (dir_df['range_bucket'] == range_b)
            if disp_b:
                mask = mask & (dir_df['disp_bucket'] == disp_b)

            filtered = dir_df[mask]

            if len(filtered) < 40:
                continue

            avg_r = filtered['r_multiple'].mean()
            temporal = test_temporal_stability(filtered)

            state_name = f"{range_b}"
            if disp_b:
                state_name += f" + {disp_b}"

            print(f"  {state_name}: {len(filtered)} trades, {avg_r:+.3f}R, {temporal['positive_chunks']}/3 chunks")

print()

# ============================================================================
# TEST 5: PATTERN-BASED FILTERING (Immediate Rejection)
# ============================================================================

print("="*80)
print("TEST 5: PATTERN-BASED FILTERING")
print("-"*80)
print()
print("Testing immediate rejection pattern (from Phase 1 behavior mapping)...")
print()

# Get dates with immediate rejection behavior
# (This requires bars_1m analysis - simplified version)

print("[TODO: Implement pattern-based filtering using bars_1m analysis]")
print()

# ============================================================================
# TEST 6: ENTRY TIMING VARIATIONS
# ============================================================================

print("="*80)
print("TEST 6: ENTRY TIMING VARIATIONS")
print("-"*80)
print()
print("Testing different entry confirmation requirements...")
print()

# Compare 1-bar confirmation vs 2-bar confirmation
# (This would require rebuilding features with different confirmation settings)

print("[TODO: Test multi-bar confirmation - requires feature rebuild]")
print()

# ============================================================================
# TEST 7: ORB SIZE FILTERING
# ============================================================================

print("="*80)
print("TEST 7: ORB SIZE FILTERING")
print("-"*80)

orb_sizes = con.execute(f"""
    SELECT
        t.date_local,
        t.orb_size,
        t.r_multiple,
        t.outcome
    FROM v_orb_trades_v3_modelb_half t
    WHERE t.orb_time = '2300'
        AND t.break_dir IN ('UP', 'DOWN')
        AND t.outcome IN ('WIN', 'LOSS')
""").df()

if len(orb_sizes) > 0:
    print(f"\nORB size distribution (ticks):")
    print(f"  Median: {orb_sizes['orb_size'].median() / 0.1:.1f} ticks")
    print(f"  Mean: {orb_sizes['orb_size'].mean() / 0.1:.1f} ticks")
    print(f"  Min: {orb_sizes['orb_size'].min() / 0.1:.1f} ticks")
    print(f"  Max: {orb_sizes['orb_size'].max() / 0.1:.1f} ticks")
    print()

    # Test performance by ORB size quartiles
    quartiles = orb_sizes['orb_size'].quantile([0.25, 0.5, 0.75]).values

    size_ranges = [
        ('Tiny (Q1)', 0, quartiles[0]),
        ('Small (Q2)', quartiles[0], quartiles[1]),
        ('Medium (Q3)', quartiles[1], quartiles[2]),
        ('Large (Q4)', quartiles[2], 999)
    ]

    print("Performance by ORB size:")
    for label, min_size, max_size in size_ranges:
        size_df = orb_sizes[(orb_sizes['orb_size'] > min_size) & (orb_sizes['orb_size'] <= max_size)]

        if len(size_df) > 0:
            avg_r = size_df['r_multiple'].mean()
            print(f"  {label}: {len(size_df)} trades, {avg_r:+.3f}R avg")

print()

# ============================================================================
# SUMMARY
# ============================================================================

print("="*80)
print(f"2300 COMPREHENSIVE ANALYSIS COMPLETE")
print("="*80)
print()

con.close()
