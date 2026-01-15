import duckdb
import sys

DB_PATH = "gold.db"

SQL = """
WITH x AS (
  SELECT
    orb,
    rr,
    sl_mode,
    buffer_ticks,
    outcome,
    r_multiple
  FROM orb_trades_5m_exec
  WHERE outcome IN ('WIN','LOSS')
)
SELECT
  orb,
  rr,
  sl_mode,
  buffer_ticks,
  COUNT(*) AS trades,
  ROUND(AVG(CASE WHEN outcome='WIN' THEN 1.0 ELSE 0.0 END), 4) AS win_rate,
  ROUND(AVG(r_multiple), 4) AS avg_r,
  ROUND(SUM(r_multiple), 2) AS total_r
FROM x
GROUP BY orb, rr, sl_mode, buffer_ticks
ORDER BY avg_r DESC;
"""

def main():
    try:
        con = duckdb.connect(DB_PATH, read_only=True)

        # sanity: table exists?
        has_table = con.execute("""
            SELECT COUNT(*) > 0
            FROM information_schema.tables
            WHERE lower(table_name) = 'orb_trades_5m_exec'
        """).fetchone()[0]

        if not has_table:
            print("ERROR: table orb_trades_5m_exec not found in gold.db")
            sys.exit(1)

        # print results
        df = con.execute(SQL).fetchdf()
        if df.empty:
            print("No WIN/LOSS rows found in orb_trades_5m_exec yet.")
        else:
            print(df.to_string(index=False))

        con.close()

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
