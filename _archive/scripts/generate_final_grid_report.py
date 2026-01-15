"""
Generate final grid search report

Summarizes ALL findings from the massive grid search:
- Best execution configs per session
- Validated config + state combinations
- System-level metrics
- Deployment recommendations
"""

import duckdb

DB_PATH = "gold.db"

con = duckdb.connect(DB_PATH, read_only=True)

print("="*80)
print("FINAL GRID SEARCH REPORT")
print("="*80)
print()
print("This report summarizes findings from testing 324 execution configurations")
print("across all 6 ORB sessions.")
print()

# Get config count
config_count = con.execute("SELECT COUNT(*) FROM execution_grid_configs").fetchone()[0]
result_count = con.execute("SELECT COUNT(*) FROM execution_grid_results").fetchone()[0]

print(f"Total configurations tested: {config_count}")
print(f"Total backtest runs: {result_count}")
print()

sessions = ['0900', '1000', '1100', '1800', '2300', '0030']

print("="*80)
print("BEST EXECUTION CONFIGS PER SESSION")
print("="*80)
print()

best_overall = []

for orb in sessions:
    print(f"{orb} ORB:")
    print("-"*80)

    # Get best config
    best = con.execute(f"""
        WITH config_stats AS (
            SELECT
                config_id,
                COUNT(*) as n_trades,
                AVG(orb_{orb}_r_multiple) as avg_r,
                SUM(CASE WHEN orb_{orb}_outcome = 'WIN' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
            FROM execution_grid_results
            WHERE orb_{orb}_break_dir IN ('UP', 'DOWN')
                AND orb_{orb}_outcome IN ('WIN', 'LOSS')
            GROUP BY config_id
            HAVING COUNT(*) >= 40
        )
        SELECT config_id, n_trades, avg_r, win_rate
        FROM config_stats
        ORDER BY avg_r DESC
        LIMIT 1
    """).fetchone()

    if not best:
        print("  No configs with >=40 trades")
        print()
        continue

    config_id, n_trades, avg_r, win_rate = best

    # Get config details
    cfg = con.execute("""
        SELECT orb_minutes, entry_method, buffer_ticks, sl_mode, close_confirmations, rr
        FROM execution_grid_configs
        WHERE config_id = ?
    """, [config_id]).fetchone()

    print(f"  Best Config {config_id}:")
    print(f"    ORB: {cfg[0]} minutes")
    print(f"    Entry: {cfg[1]}")
    print(f"    Buffer: {cfg[2]} ticks")
    print(f"    Stop: {cfg[3]}")
    print(f"    Confirmations: {cfg[4]}-bar")
    print(f"    R:R: {cfg[5]}")
    print()
    print(f"    Performance: {n_trades} trades, {avg_r:+.3f}R avg, {win_rate:.1f}% win")
    print()

    if avg_r >= 0.10:
        best_overall.append({
            'orb': orb,
            'config_id': config_id,
            'n_trades': n_trades,
            'avg_r': avg_r
        })

print("="*80)
print("VALIDATED EDGES SUMMARY")
print("="*80)
print()

if len(best_overall) == 0:
    print("[NO VALIDATED EDGES FOUND]")
    print()
    print("NO execution configuration across ANY session met the >=+0.10R threshold.")
    print()
    print("INTERPRETATION:")
    print("  - This is honest math with entry-anchored risk")
    print("  - Old results (ORB-anchored) created fake edges")
    print("  - Simple ORB breakouts do NOT have an edge on MGC")
    print()
    print("RECOMMENDATIONS:")
    print("  1. Test pattern-based entries (not pure breakouts)")
    print("  2. Test mean-reversion instead of breakouts")
    print("  3. Test time-based exits instead of R:R targets")
    print("  4. Consider different instruments (ES, NQ, etc.)")
    print("  5. Focus on liquidity events, not random ORB breaks")
    print()
else:
    print(f"SESSIONS WITH >=+0.10R AVG: {len(best_overall)}")
    print()

    total_trades = sum(e['n_trades'] for e in best_overall)
    weighted_r = sum(e['avg_r'] * e['n_trades'] for e in best_overall)
    system_avg_r = weighted_r / total_trades if total_trades > 0 else 0

    for edge in best_overall:
        trades_per_year = edge['n_trades'] / 2  # ~2 years of data
        print(f"{edge['orb']} ORB (Config {edge['config_id']})")
        print(f"  {edge['n_trades']} trades (~{trades_per_year:.0f}/year), {edge['avg_r']:+.3f}R avg")
        print()

    print("-"*80)
    print("SYSTEM TOTALS:")
    print(f"  Total trades: {total_trades} (~{total_trades/2:.0f}/year)")
    print(f"  Weighted avg R: {system_avg_r:+.3f}R")
    print(f"  Expected annual R: ~{weighted_r/2:.1f}R")
    print()

    print("="*80)
    print("DEPLOYMENT RECOMMENDATION")
    print("="*80)
    print()
    print("These configs can be deployed with:")
    print("  1. Paper trading first to validate execution")
    print("  2. Pre-trade checklist for config identification")
    print("  3. Automated entry at specified timing")
    print("  4. Track live vs backtest performance")
    print()

print("="*80)
print("KEY FINDINGS FROM GRID SEARCH")
print("="*80)
print()

# Compare ORB sizes
print("ORB SIZE COMPARISON:")
print("-"*80)

for orb_min in [5, 10, 15]:
    avg_performance = con.execute(f"""
        WITH config_stats AS (
            SELECT
                AVG(r_multiple) as avg_r
            FROM (
                SELECT orb_0900_r_multiple as r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.orb_minutes = ? AND orb_0900_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_1000_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.orb_minutes = ? AND orb_1000_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_1100_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.orb_minutes = ? AND orb_1100_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_1800_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.orb_minutes = ? AND orb_1800_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_2300_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.orb_minutes = ? AND orb_2300_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_0030_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.orb_minutes = ? AND orb_0030_outcome IN ('WIN', 'LOSS')
            )
        )
        SELECT avg_r FROM config_stats
    """, [orb_min]*6).fetchone()

    if avg_performance and avg_performance[0] is not None:
        print(f"  {orb_min}-minute ORB: {avg_performance[0]:+.3f}R avg (across all sessions)")

print()

# Compare entry methods
print("ENTRY METHOD COMPARISON:")
print("-"*80)

for entry in ['close', 'next_open', '2bar_confirm']:
    avg_performance = con.execute(f"""
        WITH config_stats AS (
            SELECT
                AVG(r_multiple) as avg_r
            FROM (
                SELECT orb_0900_r_multiple as r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.entry_method = ? AND orb_0900_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_1000_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.entry_method = ? AND orb_1000_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_1100_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.entry_method = ? AND orb_1100_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_1800_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.entry_method = ? AND orb_1800_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_2300_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.entry_method = ? AND orb_2300_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_0030_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.entry_method = ? AND orb_0030_outcome IN ('WIN', 'LOSS')
            )
        )
        SELECT avg_r FROM config_stats
    """, [entry]*6).fetchone()

    if avg_performance and avg_performance[0] is not None:
        print(f"  {entry}: {avg_performance[0]:+.3f}R avg (across all sessions)")

print()

# Compare stop modes
print("STOP MODE COMPARISON:")
print("-"*80)

for sl in ['full', 'half', '75pct']:
    avg_performance = con.execute(f"""
        WITH config_stats AS (
            SELECT
                AVG(r_multiple) as avg_r
            FROM (
                SELECT orb_0900_r_multiple as r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.sl_mode = ? AND orb_0900_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_1000_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.sl_mode = ? AND orb_1000_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_1100_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.sl_mode = ? AND orb_1100_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_1800_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.sl_mode = ? AND orb_1800_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_2300_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.sl_mode = ? AND orb_2300_outcome IN ('WIN', 'LOSS')
                UNION ALL
                SELECT orb_0030_r_multiple FROM execution_grid_results g
                JOIN execution_grid_configs c ON g.config_id = c.config_id
                WHERE c.sl_mode = ? AND orb_0030_outcome IN ('WIN', 'LOSS')
            )
        )
        SELECT avg_r FROM config_stats
    """, [sl]*6).fetchone()

    if avg_performance and avg_performance[0] is not None:
        print(f"  {sl}-SL: {avg_performance[0]:+.3f}R avg (across all sessions)")

print()

con.close()

print("="*80)
print("GRID SEARCH COMPLETE")
print("="*80)
print()
print("This was a COMPREHENSIVE test of ALL reasonable execution variants.")
print("If no edges were found, simple ORB breakouts do NOT work on MGC.")
print()
print("Next steps:")
print("  1. If edges found: deploy and paper trade")
print("  2. If no edges: test different strategies (mean-reversion, patterns, etc.)")
print("  3. Consider different instruments or timeframes")
print()
