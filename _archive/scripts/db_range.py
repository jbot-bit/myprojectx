import duckdb

DB = "gold.db"

with duckdb.connect(DB) as con:
    row = con.execute("""
        SELECT
          MIN(DATE(ts_utc AT TIME ZONE 'Australia/Brisbane')) AS start_date,
          MAX(DATE(ts_utc AT TIME ZONE 'Australia/Brisbane')) AS end_date,
          COUNT(*) AS bars_1m
        FROM bars_1m
        WHERE symbol = 'MGC'
    """).fetchone()

print(row)
