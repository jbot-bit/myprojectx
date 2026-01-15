import duckdb

con = duckdb.connect('gold.db')

print("NQ Feature Summary")
print("=" * 70)

for orb in ['0900', '1000', '1100', '1800', '2300', '0030']:
    result = con.execute(f"""
        SELECT
            COUNT(*) AS trades,
            SUM(CASE WHEN orb_{orb}_outcome='WIN' THEN 1 ELSE 0 END) AS wins,
            AVG(orb_{orb}_r_multiple) AS avg_r
        FROM daily_features_v2_nq
        WHERE orb_{orb}_outcome IN ('WIN', 'LOSS')
    """).fetchone()

    if result[0] > 0:
        wr = result[1] / result[0] * 100
        print(f"{orb} ORB: {result[0]:3d} trades | {result[1]:3d} wins | {wr:5.1f}% WR | {result[2]:+.3f}R avg")

con.close()
