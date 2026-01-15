import duckdb
con=duckdb.connect("gold.db")
print(con.execute("SELECT rr, COUNT(*) c FROM orb_trades_1m_exec GROUP BY rr ORDER BY rr").fetchall())
con.close()
