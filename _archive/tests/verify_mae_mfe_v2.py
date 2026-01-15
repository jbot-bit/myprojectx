"""Verify MAE/MFE was calculated correctly for 2026-01-09"""
import duckdb

con = duckdb.connect("gold.db")

result = con.execute("""
    SELECT
        date_local,
        orb_0900_high, orb_0900_low, orb_0900_size,
        orb_0900_break_dir, orb_0900_outcome, orb_0900_r_multiple,
        orb_0900_mae, orb_0900_mfe,
        orb_1000_high, orb_1000_low, orb_1000_size,
        orb_1000_break_dir, orb_1000_outcome, orb_1000_r_multiple,
        orb_1000_mae, orb_1000_mfe,
        orb_1100_high, orb_1100_low, orb_1100_size,
        orb_1100_break_dir, orb_1100_outcome, orb_1100_r_multiple,
        orb_1100_mae, orb_1100_mfe
    FROM daily_features_v2
    WHERE date_local = '2026-01-09'
""").fetchall()

if result:
    row = result[0]
    print(f"Date: {row[0]}")

    print("\n=== ORB 0900 ===")
    print(f"Range: {row[1]:.2f} - {row[2]:.2f} (size: {row[3]:.1f} = {row[3]/0.1:.0f} ticks)")
    print(f"Break: {row[4]}, Outcome: {row[5]}, R: {row[6]}")
    print(f"MAE: {row[7]:.1f} ticks" if row[7] else "MAE: None")
    print(f"MFE: {row[8]:.1f} ticks" if row[8] else "MFE: None")
    if row[7] and row[8]:
        print(f"MFE/MAE ratio: {row[8]/row[7]:.2f}")

    print("\n=== ORB 1000 ===")
    print(f"Range: {row[9]:.2f} - {row[10]:.2f} (size: {row[11]:.1f} = {row[11]/0.1:.0f} ticks)")
    print(f"Break: {row[12]}, Outcome: {row[13]}, R: {row[14]}")
    print(f"MAE: {row[15]:.1f} ticks" if row[15] else "MAE: None")
    print(f"MFE: {row[16]:.1f} ticks" if row[16] else "MFE: None")
    if row[15] and row[16]:
        print(f"MFE/MAE ratio: {row[16]/row[15]:.2f}")

    print("\n=== ORB 1100 ===")
    print(f"Range: {row[17]:.2f} - {row[18]:.2f} (size: {row[19]:.1f} = {row[19]/0.1:.0f} ticks)")
    print(f"Break: {row[20]}, Outcome: {row[21]}, R: {row[22]}")
    print(f"MAE: {row[23]:.1f} ticks" if row[23] else "MAE: None")
    print(f"MFE: {row[24]:.1f} ticks" if row[24] else "MFE: None")
    if row[23] and row[24]:
        print(f"MFE/MAE ratio: {row[24]/row[23]:.2f}")
else:
    print("No data found")

con.close()
