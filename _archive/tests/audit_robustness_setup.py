"""
Step 1: Audit Database and Identify Filtered Results Table

Finds the exact table containing 570 configs, describes it,
and validates database setup before running robustness tests.
"""

import duckdb
import os
import sys

DB_PATH = "gold.db"

def audit_database():
    """Step 1: Find and describe the filtered results table"""

    print("="*100)
    print("STEP 1: AUDIT DATABASE FOR ROBUSTNESS TESTING")
    print("="*100)
    print()

    # Fail fast: Check DB exists
    if not os.path.exists(DB_PATH):
        print(f"[FAIL] Database not found: {DB_PATH}")
        sys.exit(1)

    print(f"[PASS] Database found: {DB_PATH}")
    print(f"       Size: {os.path.getsize(DB_PATH) / 1024 / 1024:.1f} MB")
    print()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Find all orb_trades_5m tables (focus on 5m data)
    print("STEP 1A: Find ORB Trade Results Tables (5m timeframe)")
    print("-"*100)

    tables = con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name LIKE 'orb_trades_5m%'
        ORDER BY table_name
    """).fetchall()

    if not tables:
        print("[FAIL] No orb_trades_5m tables found!")
        con.close()
        sys.exit(1)

    print(f"Found {len(tables)} orb_trades_5m tables:")
    for table in tables:
        print(f"  - {table[0]}")
    print()

    # Count configs in each table
    print("STEP 1B: Count Configs Per Table")
    print("-"*100)

    table_stats = []

    for table in tables:
        table_name = table[0]

        # Check if table has required columns first
        schema = con.execute(f"DESCRIBE {table_name}").fetchall()
        col_names = [row[0] for row in schema]

        has_required = all(col in col_names for col in ['orb', 'close_confirmations', 'rr', 'outcome'])

        if not has_required:
            print(f"[SKIP] {table_name} - missing required columns")
            continue

        # Build config key based on available columns
        if 'sl_mode' in col_names and 'buffer_ticks' in col_names:
            config_key = "orb || close_confirmations::text || rr::text || COALESCE(sl_mode, '') || buffer_ticks::text"
        else:
            config_key = "orb || close_confirmations::text || rr::text"

        stats = con.execute(f"""
            SELECT
                COUNT(DISTINCT {config_key}) as unique_configs,
                COUNT(*) as total_rows,
                COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) as actual_trades
            FROM {table_name}
        """).fetchone()

        table_stats.append({
            'table': table_name,
            'configs': stats[0],
            'rows': stats[1],
            'trades': stats[2]
        })

    for stat in table_stats:
        print(f"{stat['table']:40s} | Configs: {stat['configs']:4d} | Rows: {stat['rows']:7d} | Trades: {stat['trades']:7d}")

    # Identify the filtered table (should have 570 configs)
    filtered_table = None
    for stat in table_stats:
        if stat['configs'] == 570:
            filtered_table = stat['table']
            break

    if not filtered_table:
        # If not exactly 570, find the one with most configs
        filtered_table = max(table_stats, key=lambda x: x['configs'])['table']
        print()
        print(f"[WARN] No table with exactly 570 configs found")
        print(f"       Using table with most configs: {filtered_table}")

    print()
    print(f"[IDENTIFIED] Filtered results table: {filtered_table}")
    print()

    # Describe the filtered table
    print("STEP 1C: Describe Filtered Table Schema")
    print("-"*100)

    schema = con.execute(f"DESCRIBE {filtered_table}").fetchdf()
    print(schema.to_string(index=False))
    print()

    # Check for required columns
    required_cols = ['date_local', 'orb', 'close_confirmations', 'rr', 'sl_mode', 'buffer_ticks',
                     'outcome', 'r_multiple', 'stop_ticks']

    actual_cols = schema['column_name'].tolist()
    missing_cols = [col for col in required_cols if col not in actual_cols]

    if missing_cols:
        print(f"[FAIL] Missing required columns: {missing_cols}")
        con.close()
        sys.exit(1)

    print(f"[PASS] All required columns present")
    print()

    # Sample data
    print("STEP 1D: Sample Data From Filtered Table")
    print("-"*100)

    sample = con.execute(f"""
        SELECT date_local, orb, close_confirmations, rr, sl_mode, buffer_ticks,
               outcome, r_multiple, stop_ticks
        FROM {filtered_table}
        LIMIT 5
    """).fetchdf()

    print(sample.to_string(index=False))
    print()

    # Verify MAX_STOP and ASIA_TP_CAP filters are applied
    print("STEP 1E: Verify Filters Applied")
    print("-"*100)

    filter_check = con.execute(f"""
        SELECT
            MAX(stop_ticks) as max_stop,
            MAX(CASE WHEN orb IN ('0900','1000','1100')
                     THEN ABS(target_price - entry_price) / 0.1
                     END) as max_asia_tp
        FROM {filtered_table}
        WHERE outcome IN ('WIN','LOSS')
    """).fetchone()

    print(f"Max stop: {filter_check[0]:.1f} ticks (expected: 100)")
    print(f"Max Asia TP: {filter_check[1]:.1f} ticks (expected: 150)")
    print()

    if filter_check[0] <= 100.1 and filter_check[1] <= 150.1:
        print("[PASS] Filters confirmed: MAX_STOP=100, ASIA_TP_CAP=150")
    else:
        print("[WARN] Filters may not match expectations")

    print()

    # Summary
    print("="*100)
    print("AUDIT SUMMARY")
    print("="*100)
    print()
    print(f"Database: {DB_PATH}")
    print(f"Filtered table: {filtered_table}")
    print(f"Total configs: {stat['configs']} (expected: 570)")
    print(f"Total trades: {stat['trades']:,}")
    print(f"Schema: {len(actual_cols)} columns")
    print(f"Filters: MAX_STOP=100, ASIA_TP_CAP=150")
    print()
    print("[READY] Database audit complete - ready for robustness testing")
    print()
    print("="*100)

    con.close()

    return filtered_table

if __name__ == "__main__":
    filtered_table = audit_database()

    # Write table name to file for next steps
    with open('filtered_table_name.txt', 'w') as f:
        f.write(filtered_table)

    print()
    print(f"Filtered table name saved to: filtered_table_name.txt")
    print(f"Next step: Run extract_candidate_configs.py")
