"""Find the latest date with actual ORB data"""
import duckdb

con = duckdb.connect("gold.db")

# Find latest date with actual break data
result = con.execute("""
    SELECT date_local, orb_0900_break_dir, orb_1000_break_dir, orb_1100_break_dir
    FROM daily_features_v2
    WHERE orb_0900_break_dir IS NOT NULL
       OR orb_1000_break_dir IS NOT NULL
       OR orb_1100_break_dir IS NOT NULL
    ORDER BY date_local DESC
    LIMIT 5
""").fetchall()

print("Latest dates with ORB data:")
for row in result:
    print(f"  {row[0]}: 0900={row[1]}, 1000={row[2]}, 1100={row[3]}")

con.close()
