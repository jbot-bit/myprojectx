import duckdb

con = duckdb.connect("gold.db")

sql = """
SELECT COUNT(*)
FROM bars_1m
WHERE symbol = 'MGC'
  AND ts_utc >= TIMESTAMPTZ '2024-05-19 14:00:00+00'
  AND ts_utc <  TIMESTAMPTZ '2024-05-20 14:00:00+00'
"""

print(con.execute(sql).fetchone())

con.close()
