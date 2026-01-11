import duckdb

con = duckdb.connect("gold.db")

sql = """
SELECT
  rr,
  COUNT(1) FILTER (WHERE outcome IN ('WIN','LOSS')) AS trades,
  AVG(CASE WHEN outcome='WIN' THEN 1 ELSE 0 END) AS win_rate,
  AVG(r_multiple) AS avg_r,
  SUM(r_multiple) AS total_r,
  AVG(mae_r) AS avg_mae_r,
  AVG(mfe_r) AS avg_mfe_r
FROM orb_trades_1m_exec
GROUP BY rr
ORDER BY rr
"""

df = con.execute(sql).fetchdf()
print(df)

con.close()
