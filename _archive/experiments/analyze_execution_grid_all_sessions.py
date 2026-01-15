"""
Analyze execution grid results across ALL sessions

Finds best execution configurations for each session based on:
- Avg R performance
- Temporal stability
- Trade count
- Win rate
"""

import duckdb
import pandas as pd

DB_PATH = "gold.db"

def analyze_grid_for_session(con, orb_time):
    """Analyze all configs for a single session."""

    print("="*80)
    print(f"{orb_time} ORB - EXECUTION GRID ANALYSIS")
    print("="*80)
    print()

    # Get all configs
    configs = con.execute("""
        SELECT
            config_id,
            orb_minutes,
            entry_method,
            buffer_ticks,
            sl_mode,
            close_confirmations,
            rr
        FROM execution_grid_configs
        ORDER BY config_id
    """).df()

    print(f"Total configurations: {len(configs)}")
    print()

    # Analyze each config
    results = []

    for _, cfg in configs.iterrows():
        config_id = cfg['config_id']

        # Get trades for this config
        trades = con.execute(f"""
            SELECT
                date_local,
                orb_{orb_time}_break_dir as break_dir,
                orb_{orb_time}_outcome as outcome,
                orb_{orb_time}_r_multiple as r_multiple
            FROM execution_grid_results
            WHERE config_id = ?
                AND orb_{orb_time}_break_dir IN ('UP', 'DOWN')
                AND orb_{orb_time}_outcome IN ('WIN', 'LOSS')
        """, [config_id]).df()

        if len(trades) < 40:
            continue

        avg_r = trades['r_multiple'].mean()
        win_rate = (trades['outcome'] == 'WIN').sum() * 100.0 / len(trades)

        # Temporal stability
        trades_sorted = trades.sort_values('date_local')
        n = len(trades_sorted)
        chunk_size = n // 3

        chunk1 = trades_sorted.iloc[:chunk_size]
        chunk2 = trades_sorted.iloc[chunk_size:2*chunk_size]
        chunk3 = trades_sorted.iloc[2*chunk_size:]

        c1_avg = chunk1['r_multiple'].mean()
        c2_avg = chunk2['r_multiple'].mean()
        c3_avg = chunk3['r_multiple'].mean()

        positive_chunks = sum([c1_avg > 0, c2_avg > 0, c3_avg > 0])

        results.append({
            'config_id': config_id,
            'orb_minutes': cfg['orb_minutes'],
            'entry_method': cfg['entry_method'],
            'buffer_ticks': cfg['buffer_ticks'],
            'sl_mode': cfg['sl_mode'],
            'confirmations': cfg['close_confirmations'],
            'rr': cfg['rr'],
            'n_trades': len(trades),
            'avg_r': avg_r,
            'win_rate': win_rate,
            'positive_chunks': positive_chunks,
            'c1': c1_avg,
            'c2': c2_avg,
            'c3': c3_avg
        })

    if len(results) == 0:
        print("[NO CONFIGS WITH >=40 TRADES]")
        print()
        return []

    # Sort by avg R
    results_df = pd.DataFrame(results).sort_values('avg_r', ascending=False)

    # Print top 10
    print("TOP 10 CONFIGURATIONS (by Avg R):")
    print("-"*80)

    for idx, r in results_df.head(10).iterrows():
        config_str = f"{r['orb_minutes']}min, {r['entry_method']}, buf={r['buffer_ticks']}, {r['sl_mode']}, {r['confirmations']}-bar, RR={r['rr']}"
        print(f"Config {r['config_id']:3d}: {config_str}")
        print(f"  {r['n_trades']} trades, {r['avg_r']:+.3f}R avg, {r['win_rate']:.1f}% win, {r['positive_chunks']}/3 chunks")
        print(f"  Temporal: {r['c1']:+.3f}R / {r['c2']:+.3f}R / {r['c3']:+.3f}R")
        print()

    # Find validated configs (>=+0.10R, 3/3 chunks)
    validated = results_df[(results_df['avg_r'] >= 0.10) & (results_df['positive_chunks'] == 3)]

    if len(validated) > 0:
        print(f"[VALIDATED CONFIGS]: {len(validated)} configs meet >=+0.10R and 3/3 chunks")
        print()
        for idx, r in validated.iterrows():
            config_str = f"{r['orb_minutes']}min, {r['entry_method']}, buf={r['buffer_ticks']}, {r['sl_mode']}, {r['confirmations']}-bar, RR={r['rr']}"
            print(f"  Config {r['config_id']:3d}: {config_str}")
            print(f"    {r['n_trades']} trades, {r['avg_r']:+.3f}R avg, 3/3 chunks")
    else:
        print("[NO VALIDATED CONFIGS]")

    print()

    return results


def main():
    con = duckdb.connect(DB_PATH, read_only=True)

    print("="*80)
    print("EXECUTION GRID ANALYSIS - ALL SESSIONS")
    print("="*80)
    print()

    # Check if grid table exists
    tables = con.execute("SHOW TABLES").fetchall()
    if not any('execution_grid_results' in str(t) for t in tables):
        print("ERROR: execution_grid_results table not found!")
        print("Run: python build_execution_grid_features.py 2024-01-01 2026-01-10")
        con.close()
        exit(1)

    # Get config count
    config_count = con.execute("SELECT COUNT(*) FROM execution_grid_configs").fetchone()[0]
    print(f"Total configurations tested: {config_count}")
    print()

    sessions = ['0900', '1000', '1100', '1800', '2300', '0030']

    all_validated = {}

    for orb in sessions:
        results = analyze_grid_for_session(con, orb)
        if results:
            validated = [r for r in results if r['avg_r'] >= 0.10 and r['positive_chunks'] == 3]
            if validated:
                all_validated[orb] = validated

    # Final summary
    print("="*80)
    print("FINAL SUMMARY - VALIDATED CONFIGS ACROSS ALL SESSIONS")
    print("="*80)
    print()

    if len(all_validated) == 0:
        print("[NO VALIDATED CONFIGS FOUND ACROSS ALL SESSIONS]")
    else:
        print(f"Sessions with validated configs: {len(all_validated)}")
        print()

        for orb, validated in all_validated.items():
            print(f"{orb} ORB: {len(validated)} validated config(s)")
            for r in validated[:3]:  # Top 3 per session
                config_str = f"{r['orb_minutes']}min, {r['entry_method']}, buf={r['buffer_ticks']}, {r['sl_mode']}, {r['confirmations']}-bar, RR={r['rr']}"
                print(f"  Config {r['config_id']}: {r['n_trades']} trades, {r['avg_r']:+.3f}R")
            print()

    con.close()

    print("="*80)
    print("GRID ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
