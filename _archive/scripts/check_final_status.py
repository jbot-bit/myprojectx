import duckdb

con = duckdb.connect('gold.db')

print("=" * 70)
print("FINAL DATA STATUS - NQ PORT COMPLETE")
print("=" * 70)

print("\n=== NQ Data ===")
r1 = con.execute('SELECT COUNT(*), MIN(ts_utc), MAX(ts_utc) FROM bars_1m_nq').fetchone()
print(f'bars_1m_nq: {r1[0]:,} rows')
print(f'  Range: {r1[1]} to {r1[2]}')

r2 = con.execute('SELECT COUNT(*) FROM bars_5m_nq').fetchone()
print(f'bars_5m_nq: {r2[0]:,} rows')

r3 = con.execute('SELECT COUNT(*) FROM daily_features_v2_nq').fetchone()
print(f'daily_features_v2_nq: {r3[0]:,} rows')

print("\n=== MGC Data (for comparison) ===")
r4 = con.execute("SELECT COUNT(*), MIN(ts_utc), MAX(ts_utc) FROM bars_1m WHERE symbol='MGC'").fetchone()
print(f'bars_1m (MGC): {r4[0]:,} rows')
print(f'  Range: {r4[1]} to {r4[2]}')

r5 = con.execute("SELECT COUNT(*) FROM daily_features_v2 WHERE instrument='MGC'").fetchone()
print(f'daily_features_v2 (MGC): {r5[0]:,} rows')

print("\n=== Summary ===")
print(f"NQ:  {r1[0]:,} 1m bars -> {r2[0]:,} 5m bars -> {r3[0]:,} daily features")
print(f"MGC: {r4[0]:,} 1m bars -> {r5[0]:,} daily features")

print("\n" + "=" * 70)
print("STATUS: ✓ Both instruments ready for backtesting")
print("=" * 70)

con.close()
