"""Check what instrument data we have in gold.db"""
import duckdb

conn = duckdb.connect('gold.db', read_only=True)

# Get all bars tables
tables = conn.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'main'
    AND table_name LIKE 'bars%'
    ORDER BY table_name
""").fetchall()

print("\n=== BARS TABLES IN gold.db ===\n")
for (table,) in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    # Check if table has symbol column
    columns = [col[0] for col in conn.execute(f"PRAGMA table_info({table})").fetchall()]

    if 'symbol' in columns:
        instruments = conn.execute(f"SELECT DISTINCT symbol FROM {table} ORDER BY symbol").fetchall()
        instruments_str = ', '.join([i[0] for i in instruments])
        print(f"{table:20s}: {count:>10,} rows ({instruments_str})")
    else:
        print(f"{table:20s}: {count:>10,} rows")

# Get daily_features tables
print("\n=== DAILY FEATURES TABLES ===\n")
features_tables = conn.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'main'
    AND table_name LIKE 'daily_features%'
    ORDER BY table_name
""").fetchall()

for (table,) in features_tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    # Check if has instrument column
    columns = [col[0] for col in conn.execute(f"PRAGMA table_info({table})").fetchall()]

    if 'instrument' in columns:
        instruments = conn.execute(f"SELECT DISTINCT instrument FROM {table} ORDER BY instrument").fetchall()
        instruments_str = ', '.join([i[0] for i in instruments])
        print(f"{table:20s}: {count:>10,} rows ({instruments_str})")
    else:
        # Assume MGC only
        print(f"{table:20s}: {count:>10,} rows (MGC)")

# Summary
print("\n=== RECOMMENDATION ===\n")
print("Current architecture: Separate tables per instrument")
print("- bars_1m (MGC), bars_1m_mpl (MPL), bars_1m_nq (NQ)")
print("- bars_5m (MGC), bars_5m_mpl (MPL), bars_5m_nq (NQ)")
print("- daily_features_v2 (MGC only)")
print("\nThis is CLEAN and SIMPLE:")
print("  ✓ No consolidation complexity")
print("  ✓ Easy to query per instrument")
print("  ✓ No schema confusion")
print("  ✓ Can add ES, RTY, etc. as separate tables")

conn.close()
