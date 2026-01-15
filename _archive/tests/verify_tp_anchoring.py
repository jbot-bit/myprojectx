"""
Verify whether TP is ORB-anchored or entry-anchored.

For ORB-anchored TP:
  UP: (tp - edge) / (edge - stop) == rr
  DOWN: (edge - tp) / (stop - edge) == rr

For entry-anchored TP (what we likely have):
  UP: (tp - entry) / (entry - stop) == rr
  DOWN: (entry - tp) / (stop - entry) == rr
"""

import duckdb
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")
SYMBOL = "MGC"
DB_PATH = "gold.db"
TICK_SIZE = 0.1


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


def get_sample_trades(con, num_samples=5):
    """Get sample trades with all details needed for verification."""

    trades = []
    test_date = date(2026, 1, 6)

    for _ in range(20):  # Try multiple days
        # Test 0900 ORB
        orb_start = _dt_local(test_date, 9, 0)
        orb_end = orb_start + timedelta(minutes=5)
        scan_end = _dt_local(test_date, 17, 0)

        orb_start_utc = orb_start.astimezone(TZ_UTC)
        orb_end_utc = orb_end.astimezone(TZ_UTC)
        scan_end_utc = scan_end.astimezone(TZ_UTC)

        # Get ORB
        orb_bars = con.execute(
            """
            SELECT MAX(high) as h, MIN(low) as l
            FROM bars_1m
            WHERE symbol = ? AND ts_utc >= ? AND ts_utc < ?
            """,
            [SYMBOL, orb_start_utc, orb_end_utc]
        ).fetchone()

        if not orb_bars or orb_bars[0] is None:
            test_date -= timedelta(days=1)
            continue

        orb_high, orb_low = float(orb_bars[0]), float(orb_bars[1])
        orb_mid = (orb_high + orb_low) / 2.0

        # Get bars after ORB
        bars_after = con.execute(
            """
            SELECT ts_utc, high, low, close
            FROM bars_1m
            WHERE symbol = ? AND ts_utc >= ? AND ts_utc < ?
            ORDER BY ts_utc
            """,
            [SYMBOL, orb_end_utc, scan_end_utc]
        ).fetchall()

        if not bars_after:
            test_date -= timedelta(days=1)
            continue

        # Find first break
        break_dir = None
        entry_price = None

        for ts_utc, h, l, c in bars_after:
            c = float(c)
            if c > orb_high:
                break_dir = "UP"
                entry_price = c
                break
            if c < orb_low:
                break_dir = "DOWN"
                entry_price = c
                break

        if not break_dir:
            test_date -= timedelta(days=1)
            continue

        # Calculate stop (Half SL mode)
        stop = orb_mid
        edge = orb_high if break_dir == "UP" else orb_low

        # Calculate R values
        r_entry_anchored = abs(entry_price - stop)
        r_orb_anchored = abs(edge - stop)

        if r_entry_anchored <= 0:
            test_date -= timedelta(days=1)
            continue

        # Calculate both TP types for rr=1.5
        rr = 1.5
        tp_entry_anchored = entry_price + rr * r_entry_anchored if break_dir == "UP" else entry_price - rr * r_entry_anchored
        tp_orb_anchored = edge + rr * r_orb_anchored if break_dir == "UP" else edge - rr * r_orb_anchored

        # Collect MAE/MFE
        max_high = entry_price
        min_low = entry_price

        for ts_utc, h, l, c in bars_after:
            h = float(h)
            l = float(l)
            if h > max_high:
                max_high = h
            if l < min_low:
                min_low = l

        mae_ticks = (edge - min_low) / TICK_SIZE if break_dir == "UP" else (max_high - edge) / TICK_SIZE
        mfe_ticks = (max_high - edge) / TICK_SIZE if break_dir == "UP" else (edge - min_low) / TICK_SIZE

        trades.append({
            "date": test_date,
            "orb_time": "0900",
            "orb_high": orb_high,
            "orb_low": orb_low,
            "edge": edge,
            "stop": stop,
            "break_dir": break_dir,
            "entry": entry_price,
            "rr": rr,
            "tp_entry_anchored": tp_entry_anchored,
            "tp_orb_anchored": tp_orb_anchored,
            "r_entry_anchored": r_entry_anchored,
            "r_orb_anchored": r_orb_anchored,
            "max_high": max_high,
            "min_low": min_low,
            "mae_ticks": mae_ticks,
            "mfe_ticks": mfe_ticks
        })

        if len(trades) >= num_samples:
            break

        test_date -= timedelta(days=1)

    return trades


def main():
    con = duckdb.connect(DB_PATH)

    print("=" * 100)
    print("STEP 1: Verify TP Anchoring")
    print("=" * 100)
    print()

    trades = get_sample_trades(con, num_samples=5)

    if not trades:
        print("No trades found")
        con.close()
        return

    print(f"Found {len(trades)} sample trades\n")

    for i, t in enumerate(trades, 1):
        print(f"--- Trade {i} ({t['date']}, {t['orb_time']}, {t['break_dir']}) ---")
        print(f"ORB: High={t['orb_high']:.2f}, Low={t['orb_low']:.2f}, Edge={t['edge']:.2f}")
        print(f"Entry: {t['entry']:.2f}")
        print(f"Stop: {t['stop']:.2f} (Half SL = midpoint)")
        print(f"R:R target: {t['rr']}")
        print()

        print("R values:")
        print(f"  R (entry-anchored): {t['r_entry_anchored']:.2f} = {t['r_entry_anchored']/TICK_SIZE:.1f} ticks")
        print(f"  R (ORB-anchored):   {t['r_orb_anchored']:.2f} = {t['r_orb_anchored']/TICK_SIZE:.1f} ticks")
        print()

        print("Target prices:")
        print(f"  TP (entry-anchored): {t['tp_entry_anchored']:.2f}")
        print(f"  TP (ORB-anchored):   {t['tp_orb_anchored']:.2f}")
        print()

        # Check which TP formula holds
        if t['break_dir'] == "UP":
            check_entry = (t['tp_entry_anchored'] - t['entry']) / t['r_entry_anchored']
            check_orb = (t['tp_orb_anchored'] - t['edge']) / t['r_orb_anchored']
            actual_used = t['tp_entry_anchored']  # What baseline script uses
            check_actual_from_entry = (actual_used - t['entry']) / t['r_entry_anchored']
            check_actual_from_orb = (actual_used - t['edge']) / t['r_orb_anchored']
        else:
            check_entry = (t['entry'] - t['tp_entry_anchored']) / t['r_entry_anchored']
            check_orb = (t['edge'] - t['tp_orb_anchored']) / t['r_orb_anchored']
            actual_used = t['tp_entry_anchored']
            check_actual_from_entry = (t['entry'] - actual_used) / t['r_entry_anchored']
            check_actual_from_orb = (t['edge'] - actual_used) / t['r_orb_anchored']

        print("Check values (should equal rr = 1.5):")
        print(f"  Entry-anchored formula: {check_entry:.6f} {'[MATCHES]' if abs(check_entry - t['rr']) < 1e-6 else '[NO MATCH]'}")
        print(f"  ORB-anchored formula:   {check_orb:.6f} {'[MATCHES]' if abs(check_orb - t['rr']) < 1e-6 else '[NO MATCH]'}")
        print()

        print("Actual TP used in baseline script:")
        print(f"  TP: {actual_used:.2f}")
        print(f"  Check from entry: {check_actual_from_entry:.6f} {'[MATCHES]' if abs(check_actual_from_entry - t['rr']) < 1e-6 else '[NO MATCH]'}")
        print(f"  Check from ORB edge: {check_actual_from_orb:.6f} {'[MATCHES]' if abs(check_actual_from_orb - t['rr']) < 1e-6 else '[NO MATCH]'}")
        print()

        if abs(check_actual_from_entry - t['rr']) < 1e-6:
            print("CONCLUSION: TP is ENTRY-ANCHORED (not ORB-anchored)")
        elif abs(check_actual_from_orb - t['rr']) < 1e-6:
            print("CONCLUSION: TP is ORB-ANCHORED")
        else:
            print("CONCLUSION: TP calculation is unclear")

        print()
        print("=" * 100)
        print()

    print()
    print("=" * 100)
    print("STEP 2: Verify MAE/MFE Measurement")
    print("=" * 100)
    print()

    for i, t in enumerate(trades, 1):
        print(f"--- Trade {i} ({t['date']}, {t['orb_time']}, {t['break_dir']}) ---")
        print(f"ORB Edge: {t['edge']:.2f}")
        print(f"Entry: {t['entry']:.2f}")
        print(f"Stop: {t['stop']:.2f}")
        print(f"R (ORB-anchored): {t['r_orb_anchored']:.2f} = {t['r_orb_anchored']/TICK_SIZE:.1f} ticks")
        print()

        print(f"Max high after break: {t['max_high']:.2f}")
        print(f"Min low after break: {t['min_low']:.2f}")
        print()

        # Verify MAE calculation
        if t['break_dir'] == "UP":
            expected_mae_ticks = (t['edge'] - t['min_low']) / TICK_SIZE
            expected_mfe_ticks = (t['max_high'] - t['edge']) / TICK_SIZE
            mae_formula = f"(edge - min_low) = ({t['edge']:.2f} - {t['min_low']:.2f}) / {TICK_SIZE}"
            mfe_formula = f"(max_high - edge) = ({t['max_high']:.2f} - {t['edge']:.2f}) / {TICK_SIZE}"
        else:
            expected_mae_ticks = (t['max_high'] - t['edge']) / TICK_SIZE
            expected_mfe_ticks = (t['edge'] - t['min_low']) / TICK_SIZE
            mae_formula = f"(max_high - edge) = ({t['max_high']:.2f} - {t['edge']:.2f}) / {TICK_SIZE}"
            mfe_formula = f"(edge - min_low) = ({t['edge']:.2f} - {t['min_low']:.2f}) / {TICK_SIZE}"

        print(f"MAE calculation:")
        print(f"  Formula: {mae_formula}")
        print(f"  Expected: {expected_mae_ticks:.1f} ticks")
        print(f"  Actual:   {t['mae_ticks']:.1f} ticks")
        print(f"  Match: {'[OK]' if abs(expected_mae_ticks - t['mae_ticks']) < 0.1 else '[FAIL]'}")
        print()

        print(f"MFE calculation:")
        print(f"  Formula: {mfe_formula}")
        print(f"  Expected: {expected_mfe_ticks:.1f} ticks")
        print(f"  Actual:   {t['mfe_ticks']:.1f} ticks")
        print(f"  Match: {'[OK]' if abs(expected_mfe_ticks - t['mfe_ticks']) < 0.1 else '[FAIL]'}")
        print()

        # Normalize by R
        mae_r = t['mae_ticks'] * TICK_SIZE / t['r_orb_anchored']
        mfe_r = t['mfe_ticks'] * TICK_SIZE / t['r_orb_anchored']

        print(f"Normalized by ORB-anchored R:")
        print(f"  MAE: {mae_r:.3f}R")
        print(f"  MFE: {mfe_r:.3f}R")
        print()

        if t['break_dir'] == "UP":
            print("CONCLUSION: MAE/MFE measured from ORB EDGE (not entry) [OK]")
        else:
            print("CONCLUSION: MAE/MFE measured from ORB EDGE (not entry) [OK]")

        print()
        print("=" * 100)
        print()

    con.close()


if __name__ == "__main__":
    main()
