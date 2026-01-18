"""Check daily_features table schemas"""
import duckdb

conn = duckdb.connect('gold.db', read_only=True)

tables = ['daily_features_v2', 'daily_features_v2_mpl', 'daily_features_v2_nq']

print("\n=== DAILY FEATURES SCHEMA CHECK ===\n")

for table in tables:
    try:
        columns = [col[1] for col in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        has_instrument = 'instrument' in columns

        # Get row count and instruments
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        if has_instrument:
            instruments = conn.execute(f"SELECT DISTINCT instrument FROM {table}").fetchall()
            inst_str = ', '.join([i[0] for i in instruments])
            print(f"{table:25s}: {count:>4} rows, HAS instrument column ({inst_str})")
        else:
            print(f"{table:25s}: {count:>4} rows, NO instrument column")
    except Exception as e:
        print(f"{table:25s}: ERROR - {e}")

print("\n=== RECOMMENDATION ===\n")
print("OPTION 1: Consolidated approach (current)")
print("  - Use daily_features_v2 with instrument column")
print("  - Add MPL and NQ data to daily_features_v2")
print("  - Delete separate _mpl and _nq tables")
print()
print("OPTION 2: Separate tables approach (simpler)")
print("  - Keep daily_features_v2 (MGC only)")
print("  - Keep daily_features_v2_mpl (MPL only)")
print("  - Keep daily_features_v2_nq (NQ only)")
print("  - Update apps to query correct table based on instrument")

conn.close()
