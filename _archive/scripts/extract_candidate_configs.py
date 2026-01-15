"""
Step 2: Extract Candidate Configs for Robustness Testing

Queries filtered table for configs meeting profitability criteria:
- trades >= 100
- total_r >= 20

Exports to candidate_configs.csv for batch processing.
"""

import duckdb
import pandas as pd
import os
import sys
import json

DB_PATH = "gold.db"

def extract_candidates():
    """Step 2: Build SQL query and export candidate configs"""

    print("="*100)
    print("STEP 2: EXTRACT CANDIDATE CONFIGS")
    print("="*100)
    print()

    # Fail fast: Check DB exists
    if not os.path.exists(DB_PATH):
        print(f"[FAIL] Database not found: {DB_PATH}")
        sys.exit(1)

    # Read filtered table name
    if not os.path.exists('filtered_table_name.txt'):
        print("[FAIL] filtered_table_name.txt not found. Run audit_robustness_setup.py first.")
        sys.exit(1)

    with open('filtered_table_name.txt', 'r') as f:
        filtered_table = f.read().strip()

    print(f"[INFO] Using filtered table: {filtered_table}")
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Build SQL query for candidate configs
    print("STEP 2A: Query Profitable Configs")
    print("-"*100)
    print()

    query = f"""
        SELECT
            orb,
            close_confirmations,
            rr,
            sl_mode,
            buffer_ticks,
            COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as trades,
            COUNT(*) FILTER (WHERE outcome = 'WIN') as wins,
            COUNT(*) FILTER (WHERE outcome = 'LOSS') as losses,
            AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END) FILTER (WHERE outcome IN ('WIN','LOSS')) as win_rate,
            SUM(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) as total_r,
            AVG(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) as avg_r
        FROM {filtered_table}
        GROUP BY orb, close_confirmations, rr, sl_mode, buffer_ticks
        HAVING COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) >= 100
           AND SUM(r_multiple) FILTER (WHERE outcome IN ('WIN','LOSS')) >= 20
        ORDER BY total_r DESC
    """

    print("SQL Query:")
    print("-"*100)
    print(query)
    print("-"*100)
    print()

    # Execute query
    candidates = con.execute(query).fetchdf()

    print(f"[FOUND] {len(candidates)} candidate configs meeting criteria")
    print()

    if len(candidates) == 0:
        print("[WARN] No candidates found. Try lowering thresholds (trades >= 50, total_r >= 10)")
        con.close()
        return

    # Display summary
    print("STEP 2B: Candidate Config Summary")
    print("-"*100)
    print()

    # Session breakdown
    session_counts = candidates.groupby('orb').agg({
        'orb': 'count',
        'total_r': 'sum',
        'trades': 'sum'
    }).rename(columns={'orb': 'num_configs'})
    session_counts = session_counts.sort_values('total_r', ascending=False)

    print("By Session:")
    for session, row in session_counts.iterrows():
        orb_name = {'0900': '09:00', '1000': '10:00', '1100': '11:00', '1800': '18:00', '2300': '23:00', '0030': '00:30'}.get(session, session)
        print(f"  {orb_name}: {int(row['num_configs']):3d} configs | {row['total_r']:+7.1f}R | {int(row['trades']):6d} trades")

    print()

    # Top 10 configs
    print("Top 10 Configs by Total R:")
    print("-"*100)

    top10 = candidates.head(10)
    for idx, row in top10.iterrows():
        sl_mode = row['sl_mode'] if row['sl_mode'] else 'full'
        print(f"{idx+1:2d}. {row['orb']} | RR={row['rr']:3.1f} | Confirm={row['close_confirmations']} | SL={sl_mode:4s} | Buffer={row['buffer_ticks']:4.1f}")
        print(f"    {row['total_r']:+6.1f}R | {int(row['trades']):4d} trades | {row['win_rate']:.1%} WR")

    print()

    # Export to CSV
    print("STEP 2C: Export Candidate Configs")
    print("-"*100)

    # Export full details to CSV
    csv_path = "candidate_configs.csv"
    candidates.to_csv(csv_path, index=False)
    print(f"[SAVED] Full details: {csv_path}")

    # Export config keys only (for batch runner)
    config_keys = candidates[['orb', 'close_confirmations', 'rr', 'sl_mode', 'buffer_ticks']].to_dict('records')

    json_path = "candidate_configs.json"
    with open(json_path, 'w') as f:
        json.dump(config_keys, f, indent=2)
    print(f"[SAVED] Config keys: {json_path}")

    print()

    # Summary stats
    print("="*100)
    print("EXTRACTION SUMMARY")
    print("="*100)
    print()
    print(f"Filtered table: {filtered_table}")
    print(f"Candidates found: {len(candidates)}")
    print(f"Total R across candidates: {candidates['total_r'].sum():+.1f}R")
    print(f"Total trades: {candidates['trades'].sum():,}")
    print()
    print("Files created:")
    print(f"  - {csv_path} (full details)")
    print(f"  - {json_path} (config keys for batch runner)")
    print()
    print("[READY] Candidate configs extracted - ready for robustness testing")
    print()
    print("="*100)

    con.close()

if __name__ == "__main__":
    extract_candidates()
