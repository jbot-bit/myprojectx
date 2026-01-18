#!/usr/bin/env python3
"""
Consolidate bars tables only - keep daily_features as-is.
"""

import duckdb
from datetime import datetime

conn = duckdb.connect('gold.db')

print("=" * 70)
print("CONSOLIDATING BARS TABLES ONLY")
print("=" * 70)

# Consolidate bars_1m
print("\n[1/2] Consolidating bars_1m...")
mgc_1m = conn.execute("SELECT COUNT(*) FROM bars_1m").fetchone()[0]
mpl_1m = conn.execute("SELECT COUNT(*) FROM bars_1m_mpl").fetchone()[0]
nq_1m = conn.execute("SELECT COUNT(*) FROM bars_1m_nq").fetchone()[0]
expected_1m = mgc_1m + mpl_1m + nq_1m

print(f"  MGC: {mgc_1m:,}")
print(f"  MPL: {mpl_1m:,}")
print(f"  NQ: {nq_1m:,}")
print(f"  Expected: {expected_1m:,}")

conn.execute("""
    CREATE TABLE bars_1m_consolidated AS
    SELECT * FROM bars_1m
    UNION ALL SELECT * FROM bars_1m_mpl
    UNION ALL SELECT * FROM bars_1m_nq
""")

actual_1m = conn.execute("SELECT COUNT(*) FROM bars_1m_consolidated").fetchone()[0]
assert actual_1m == expected_1m, f"Mismatch: {actual_1m} != {expected_1m}"
print(f"  Result: {actual_1m:,} [OK]")

# Consolidate bars_5m
print("\n[2/2] Consolidating bars_5m...")
mgc_5m = conn.execute("SELECT COUNT(*) FROM bars_5m").fetchone()[0]
mpl_5m = conn.execute("SELECT COUNT(*) FROM bars_5m_mpl").fetchone()[0]
nq_5m = conn.execute("SELECT COUNT(*) FROM bars_5m_nq").fetchone()[0]
expected_5m = mgc_5m + mpl_5m + nq_5m

print(f"  MGC: {mgc_5m:,}")
print(f"  MPL: {mpl_5m:,}")
print(f"  NQ: {nq_5m:,}")
print(f"  Expected: {expected_5m:,}")

conn.execute("""
    CREATE TABLE bars_5m_consolidated AS
    SELECT * FROM bars_5m
    UNION ALL SELECT * FROM bars_5m_mpl
    UNION ALL SELECT * FROM bars_5m_nq
""")

actual_5m = conn.execute("SELECT COUNT(*) FROM bars_5m_consolidated").fetchone()[0]
assert actual_5m == expected_5m, f"Mismatch: {actual_5m} != {expected_5m}"
print(f"  Result: {actual_5m:,} [OK]")

# Archive old tables
print("\n[3/3] Archiving old tables...")
timestamp = datetime.now().strftime("%Y%m%d_%H%M")

for table in ['bars_1m', 'bars_1m_mpl', 'bars_1m_nq', 'bars_5m', 'bars_5m_mpl', 'bars_5m_nq']:
    conn.execute(f"ALTER TABLE {table} RENAME TO _archive_{timestamp}_{table}")
    print(f"  Archived: {table}")

# Promote consolidated
conn.execute("ALTER TABLE bars_1m_consolidated RENAME TO bars_1m")
conn.execute("ALTER TABLE bars_5m_consolidated RENAME TO bars_5m")

print("\n[DONE] Bars consolidated")
print(f"  bars_1m: {actual_1m:,} rows (MGC, MPL, NQ)")
print(f"  bars_5m: {actual_5m:,} rows (MGC, MPL, NQ)")

conn.close()
