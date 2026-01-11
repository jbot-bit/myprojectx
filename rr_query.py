import duckdb
import pandas as pd

DB = "gold.db"
TABLE = "orb_trades_1m_exec"

SQL = f"""
SELECT
  rr,
  COUNT(*) FILTER (WHERE outcome IN ('WIN','LOSS')) AS trades,
  AVG(CASE WHEN outcome='WIN' THEN 1 ELSE 0 END) AS win_rate,

  AVG(r_multiple) AS avg_r,
  MEDIAN(r_multiple) AS med_r,
  STDDEV_SAMP(r_multiple) AS std_r,

  SUM(r_multiple) AS total_r,

  AVG(CASE WHEN outcome='WIN'  THEN r_multiple END) AS avg_win_r,
  AVG(CASE WHEN outcome='LOSS' THEN r_multiple END) AS avg_loss_r,

  SUM(CASE WHEN outcome='WIN'  THEN r_multiple ELSE 0 END) AS sum_win_r,
  SUM(CASE WHEN outcome='LOSS' THEN -r_multiple ELSE 0 END) AS sum_loss_r,
  (SUM(CASE WHEN outcome='WIN' THEN r_multiple ELSE 0 END) /
   NULLIF(SUM(CASE WHEN outcome='LOSS' THEN -r_multiple ELSE 0 END), 0)) AS profit_factor,

  AVG(mae_r) AS avg_mae_r,
  MEDIAN(mae_r) AS med_mae_r,
  AVG(mfe_r) AS avg_mfe_r,
  MEDIAN(mfe_r) AS med_mfe_r,

  QUANTILE_CONT(r_multiple, 0.05) AS r_p05,
  QUANTILE_CONT(r_multiple, 0.50) AS r_p50,
  QUANTILE_CONT(r_multiple, 0.95) AS r_p95
FROM {TABLE}
GROUP BY rr
ORDER BY rr;
"""

con = duckdb.connect(DB)
df = con.execute(SQL).fetchdf()
con.close()

pd.set_option("display.width", 0)
pd.set_option("display.max_columns", 200)
print(df)
