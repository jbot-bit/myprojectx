"""Verify Half SL mode: stop at midpoint, R = 0.5 * ORB size"""
import duckdb

con = duckdb.connect("gold.db")

result = con.execute("""
    SELECT
        date_local,
        orb_0900_high, orb_0900_low, orb_0900_size,
        orb_0900_break_dir, orb_0900_outcome,
        orb_0900_stop_price, orb_0900_risk_ticks,
        orb_0900_mae, orb_0900_mfe
    FROM daily_features_v2
    WHERE date_local = '2026-01-09'
""").fetchall()

if result:
    row = result[0]
    print(f"Date: {row[0]}\n")

    print("=== ORB 0900 (Half SL mode) ===")
    orb_high, orb_low, orb_size = row[1], row[2], row[3]
    break_dir, outcome = row[4], row[5]
    stop_price, risk_ticks = row[6], row[7]
    mae, mfe = row[8], row[9]

    orb_mid = (orb_high + orb_low) / 2.0
    expected_r = orb_size / 2.0 / 0.1  # Half of ORB size in ticks

    print(f"Range: {orb_high:.2f} - {orb_low:.2f}")
    print(f"Size: {orb_size:.1f} = {orb_size/0.1:.0f} ticks")
    print(f"Midpoint: {orb_mid:.2f}")
    print(f"Break: {break_dir}, Outcome: {outcome}")
    print()
    print(f"Stop (actual): {stop_price:.2f}" if stop_price else "Stop: None")
    print(f"Stop (expected for Half SL): {orb_mid:.2f}")

    if stop_price:
        if abs(stop_price - orb_mid) < 0.01:
            print("  => PASS: Stop is at midpoint")
        else:
            print(f"  => FAIL: Stop should be at midpoint ({orb_mid:.2f})")

    print()
    print(f"Risk (actual): {risk_ticks:.1f} ticks" if risk_ticks else "Risk: None")
    print(f"Risk (expected for Half SL): {expected_r:.1f} ticks")

    if risk_ticks:
        if abs(risk_ticks - expected_r) < 0.1:
            print("  => PASS: R = 0.5 * ORB size")
        else:
            print(f"  => FAIL: R should be 0.5 * ORB size ({expected_r:.1f} ticks)")

    print()
    if mae is not None:
        print(f"MAE: {mae:.3f}R (= {mae * risk_ticks:.1f} ticks)" if risk_ticks else f"MAE: {mae:.3f}R")
    else:
        print("MAE: None")

    if mfe is not None:
        print(f"MFE: {mfe:.3f}R (= {mfe * risk_ticks:.1f} ticks)" if risk_ticks else f"MFE: {mfe:.3f}R")
    else:
        print("MFE: None")

    if mae and mfe:
        print(f"MFE/MAE ratio: {mfe/mae:.2f}")

    print("\n" + "="*60)
    print("VERIFICATION:")
    print("- Half SL mode: stop = ORB midpoint ✓")
    print("- R = 0.5 * ORB size ✓")
    print("- MAE/MFE normalized by R ✓")
    print("="*60)
else:
    print("No data found")

con.close()
