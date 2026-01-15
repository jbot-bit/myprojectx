"""Quick verification that MAE/MFE was calculated correctly"""
import duckdb

con = duckdb.connect("gold.db")

result = con.execute("""
    SELECT
        date_local,
        orb_0900_break_dir, orb_0900_outcome, orb_0900_mae, orb_0900_mfe,
        orb_1000_break_dir, orb_1000_outcome, orb_1000_mae, orb_1000_mfe,
        orb_1100_break_dir, orb_1100_outcome, orb_1100_mae, orb_1100_mfe
    FROM daily_features_v2
    WHERE date_local = '2026-01-10'
""").fetchall()

if result:
    row = result[0]
    print(f"Date: {row[0]}")
    print("\nORB 0900:")
    print(f"  Break: {row[1]}, Outcome: {row[2]}")
    print(f"  MAE: {row[3]} ticks, MFE: {row[4]} ticks")
    print("\nORB 1000:")
    print(f"  Break: {row[5]}, Outcome: {row[6]}")
    print(f"  MAE: {row[7]} ticks, MFE: {row[8]} ticks")
    print("\nORB 1100:")
    print(f"  Break: {row[9]}, Outcome: {row[10]}")
    print(f"  MAE: {row[11]} ticks, MFE: {row[12]} ticks")
else:
    print("No data found")

con.close()
