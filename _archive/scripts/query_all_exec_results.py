import duckdb

DB_PATH = "gold.db"

SQL = """
SELECT
  orb,
  sl_mode,
  buffer_ticks,
  rr,
  COUNT(*) AS trades,
  ROUND(AVG(r_multiple), 4) AS avg_r
FROM orb_trades_5m_exec
WHERE outcome IN ('WIN','LOSS')
GROUP BY orb, sl_mode, buffer_ticks, rr
HAVING COUNT(*) >= 200
ORDER BY avg_r DESC;
"""


def main():
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute(SQL).fetchdf()
    con.close()

    if df.empty:
        print("No results found.")
    else:
        print(df.to_string(index=False))

if __name__ == "__main__":
    main()
