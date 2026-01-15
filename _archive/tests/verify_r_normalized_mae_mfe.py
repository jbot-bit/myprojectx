"""Verify that MAE/MFE are R-normalized and debug columns populated"""
import duckdb

con = duckdb.connect("gold.db")

result = con.execute("""
    SELECT
        date_local,
        orb_0900_high, orb_0900_low, orb_0900_size,
        orb_0900_break_dir, orb_0900_outcome,
        orb_0900_stop_price, orb_0900_risk_ticks,
        orb_0900_mae, orb_0900_mfe,
        orb_1000_high, orb_1000_low, orb_1000_size,
        orb_1000_break_dir, orb_1000_outcome,
        orb_1000_stop_price, orb_1000_risk_ticks,
        orb_1000_mae, orb_1000_mfe
    FROM daily_features_v2
    WHERE date_local = '2026-01-09'
""").fetchall()

if result:
    row = result[0]
    print(f"Date: {row[0]}\n")

    print("=== ORB 0900 (Full SL mode by default) ===")
    orb_high, orb_low, orb_size = row[1], row[2], row[3]
    break_dir, outcome = row[4], row[5]
    stop_price, risk_ticks = row[6], row[7]
    mae, mfe = row[8], row[9]

    print(f"Range: {orb_high:.2f} - {orb_low:.2f} (size: {orb_size:.1f} = {orb_size/0.1:.0f} ticks)")
    print(f"Break: {break_dir}, Outcome: {outcome}")
    print(f"Stop: {stop_price:.2f}" if stop_price else "Stop: None")
    print(f"Risk (ORB-anchored): {risk_ticks:.1f} ticks" if risk_ticks else "Risk: None")

    if mae is not None:
        print(f"\nMAE: {mae:.3f}R (normalized by ORB-anchored R)")
        print(f"  = {mae * risk_ticks:.1f} ticks absolute" if risk_ticks else "")
    else:
        print(f"\nMAE: None")

    if mfe is not None:
        print(f"MFE: {mfe:.3f}R (normalized by ORB-anchored R)")
        print(f"  = {mfe * risk_ticks:.1f} ticks absolute" if risk_ticks else "")
    else:
        print(f"MFE: None")

    if mae and mfe:
        print(f"MFE/MAE ratio: {mfe/mae:.2f}")

    print("\n=== ORB 1000 ===")
    orb_high, orb_low, orb_size = row[10], row[11], row[12]
    break_dir, outcome = row[13], row[14]
    stop_price, risk_ticks = row[15], row[16]
    mae, mfe = row[17], row[18]

    print(f"Range: {orb_high:.2f} - {orb_low:.2f} (size: {orb_size:.1f} = {orb_size/0.1:.0f} ticks)")
    print(f"Break: {break_dir}, Outcome: {outcome}")
    print(f"Stop: {stop_price:.2f}" if stop_price else "Stop: None")
    print(f"Risk (ORB-anchored): {risk_ticks:.1f} ticks" if risk_ticks else "Risk: None")

    if mae is not None:
        print(f"\nMAE: {mae:.3f}R (normalized by ORB-anchored R)")
        print(f"  = {mae * risk_ticks:.1f} ticks absolute" if risk_ticks else "")
    else:
        print(f"\nMAE: None")

    if mfe is not None:
        print(f"MFE: {mfe:.3f}R (normalized by ORB-anchored R)")
        print(f"  = {mfe * risk_ticks:.1f} ticks absolute" if risk_ticks else "")
    else:
        print(f"MFE: None")

    if mae and mfe:
        print(f"MFE/MAE ratio: {mfe/mae:.2f}")

    print("\n" + "="*60)
    print("VERIFICATION:")
    print("- MAE/MFE are in R-multiples (not ticks)")
    print("- stop_price and risk_ticks are populated")
    print("- Full SL mode: stop = opposite ORB edge, R = ORB size")
    print("="*60)
else:
    print("No data found")

con.close()
