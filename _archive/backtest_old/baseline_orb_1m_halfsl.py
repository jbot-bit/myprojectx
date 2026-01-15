"""
Baseline ORB Backtest - Clean Implementation
=============================================

Requirements:
- 1-minute execution
- Half SL mode (stop at ORB midpoint)
- ORBs: 0900, 1000, 1100 only
- R:R ratios: 1.0, 1.25, 1.5
- NO FILTERS
- Report MAE/MFE distributions BEFORE P&L

MAE/MFE are ORB-anchored (measured from ORB edge, not entry).
"""

import duckdb
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict
import sys

TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")
SYMBOL = "MGC"
DB_PATH = "gold.db"
TICK_SIZE = 0.1

# Configuration
ORB_TIMES = ["0900", "1000", "1100"]
RR_RATIOS = [1.0, 1.25, 1.5]
SL_MODE = "half"  # stop at ORB midpoint


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


def simulate_trade_1m_halfsl(con, date_local, orb_hour, orb_min, scan_end_hour, scan_end_min, rr):
    """
    Simulate 1-minute execution with Half SL for a single ORB.

    Returns:
        dict with keys: orb_high, orb_low, orb_size, break_dir, outcome, r_multiple, mae, mfe
    """
    orb_start = _dt_local(date_local, orb_hour, orb_min)
    orb_end = orb_start + timedelta(minutes=5)

    # Scan end might be next day
    if scan_end_hour < orb_hour:
        scan_end = _dt_local(date_local + timedelta(days=1), scan_end_hour, scan_end_min)
    else:
        scan_end = _dt_local(date_local, scan_end_hour, scan_end_min)

    orb_start_utc = orb_start.astimezone(TZ_UTC)
    orb_end_utc = orb_end.astimezone(TZ_UTC)
    scan_end_utc = scan_end.astimezone(TZ_UTC)

    # Get ORB range from 1m bars
    orb_bars = con.execute(
        """
        SELECT MAX(high) as h, MIN(low) as l
        FROM bars_1m
        WHERE symbol = ? AND ts_utc >= ? AND ts_utc < ?
        """,
        [SYMBOL, orb_start_utc, orb_end_utc]
    ).fetchone()

    if not orb_bars or orb_bars[0] is None:
        return None

    orb_high, orb_low = float(orb_bars[0]), float(orb_bars[1])
    orb_size = orb_high - orb_low
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
        return {
            "orb_high": orb_high, "orb_low": orb_low, "orb_size": orb_size,
            "break_dir": "NONE", "outcome": "NO_TRADE", "r_multiple": None,
            "mae": None, "mfe": None
        }

    # Find first 1m close outside ORB
    break_dir = "NONE"
    entry_ts = None
    entry_price = None

    for ts_utc, h, l, c in bars_after:
        c = float(c)
        if c > orb_high:
            break_dir = "UP"
            entry_ts = ts_utc
            entry_price = c
            break
        if c < orb_low:
            break_dir = "DOWN"
            entry_ts = ts_utc
            entry_price = c
            break

    if break_dir == "NONE":
        return {
            "orb_high": orb_high, "orb_low": orb_low, "orb_size": orb_size,
            "break_dir": "NONE", "outcome": "NO_TRADE", "r_multiple": None,
            "mae": None, "mfe": None
        }

    # Calculate stop and target (Half SL mode)
    # Entry price is ONLY for fill simulation. All TP/R calculations are ORB-anchored.
    stop = orb_mid
    orb_edge = orb_high if break_dir == "UP" else orb_low
    r_orb = abs(orb_edge - stop)

    if r_orb <= 0:
        return {
            "orb_high": orb_high, "orb_low": orb_low, "orb_size": orb_size,
            "break_dir": break_dir, "outcome": "NO_TRADE", "r_multiple": None,
            "mae": None, "mfe": None
        }

    # ORB-anchored target (NOT entry-anchored)
    target = orb_edge + rr * r_orb if break_dir == "UP" else orb_edge - rr * r_orb

    # Track MAE/MFE from ORB EDGE (not entry)
    mae_ticks = 0.0
    mfe_ticks = 0.0

    # Check bars after entry
    checking = False
    for ts_utc, h, l, c in bars_after:
        if ts_utc == entry_ts:
            checking = True
            continue
        if not checking:
            continue

        h = float(h)
        l = float(l)

        # Update MAE/MFE from ORB EDGE
        if break_dir == "UP":
            mae_ticks = max(mae_ticks, (orb_edge - l) / TICK_SIZE)
            mfe_ticks = max(mfe_ticks, (h - orb_edge) / TICK_SIZE)

            hit_stop = l <= stop
            hit_target = h >= target

            if hit_stop and hit_target:
                return {
                    "orb_high": orb_high, "orb_low": orb_low, "orb_size": orb_size,
                    "break_dir": break_dir, "outcome": "LOSS", "r_multiple": -1.0,
                    "mae": mae_ticks, "mfe": mfe_ticks
                }
            if hit_target:
                return {
                    "orb_high": orb_high, "orb_low": orb_low, "orb_size": orb_size,
                    "break_dir": break_dir, "outcome": "WIN", "r_multiple": rr,
                    "mae": mae_ticks, "mfe": mfe_ticks
                }
            if hit_stop:
                return {
                    "orb_high": orb_high, "orb_low": orb_low, "orb_size": orb_size,
                    "break_dir": break_dir, "outcome": "LOSS", "r_multiple": -1.0,
                    "mae": mae_ticks, "mfe": mfe_ticks
                }
        else:  # DOWN
            mae_ticks = max(mae_ticks, (h - orb_edge) / TICK_SIZE)
            mfe_ticks = max(mfe_ticks, (orb_edge - l) / TICK_SIZE)

            hit_stop = h >= stop
            hit_target = l <= target

            if hit_stop and hit_target:
                return {
                    "orb_high": orb_high, "orb_low": orb_low, "orb_size": orb_size,
                    "break_dir": break_dir, "outcome": "LOSS", "r_multiple": -1.0,
                    "mae": mae_ticks, "mfe": mfe_ticks
                }
            if hit_target:
                return {
                    "orb_high": orb_high, "orb_low": orb_low, "orb_size": orb_size,
                    "break_dir": break_dir, "outcome": "WIN", "r_multiple": rr,
                    "mae": mae_ticks, "mfe": mfe_ticks
                }
            if hit_stop:
                return {
                    "orb_high": orb_high, "low": orb_low, "orb_size": orb_size,
                    "break_dir": break_dir, "outcome": "LOSS", "r_multiple": -1.0,
                    "mae": mae_ticks, "mfe": mfe_ticks
                }

    # No exit
    return {
        "orb_high": orb_high, "orb_low": orb_low, "orb_size": orb_size,
        "break_dir": break_dir, "outcome": "NO_TRADE", "r_multiple": None,
        "mae": mae_ticks if mae_ticks > 0 else None,
        "mfe": mfe_ticks if mfe_ticks > 0 else None
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python baseline_orb_1m_halfsl.py START_DATE END_DATE")
        print("Example: python baseline_orb_1m_halfsl.py 2024-01-01 2026-01-09")
        sys.exit(1)

    start_date = date.fromisoformat(sys.argv[1])
    end_date = date.fromisoformat(sys.argv[2])

    con = duckdb.connect(DB_PATH)

    print("=" * 80)
    print("BASELINE ORB BACKTEST - 1-Minute Execution, Half SL")
    print("=" * 80)
    print(f"Date range: {start_date} to {end_date}")
    print(f"ORBs: {', '.join(ORB_TIMES)}")
    print(f"R:R ratios: {', '.join(map(str, RR_RATIOS))}")
    print(f"SL mode: {SL_MODE}")
    print(f"Filters: NONE")
    print()

    # Collect all trades for all RR ratios
    all_trades = {rr: {orb_time: [] for orb_time in ORB_TIMES} for rr in RR_RATIOS}
    mae_mfe_data = {orb_time: [] for orb_time in ORB_TIMES}  # Independent of RR

    cur_date = start_date
    while cur_date <= end_date:
        # 0900 ORB (scan until 17:00)
        trade_0900 = simulate_trade_1m_halfsl(con, cur_date, 9, 0, 17, 0, 1.0)  # Use RR=1.0 for MAE/MFE collection
        if trade_0900 and trade_0900["break_dir"] != "NONE":
            mae_mfe_data["0900"].append({
                "date": cur_date,
                "mae": trade_0900.get("mae"),
                "mfe": trade_0900.get("mfe"),
                "orb_size": trade_0900["orb_size"]
            })

        # 1000 ORB (scan until 17:00)
        trade_1000 = simulate_trade_1m_halfsl(con, cur_date, 10, 0, 17, 0, 1.0)
        if trade_1000 and trade_1000["break_dir"] != "NONE":
            mae_mfe_data["1000"].append({
                "date": cur_date,
                "mae": trade_1000.get("mae"),
                "mfe": trade_1000.get("mfe"),
                "orb_size": trade_1000["orb_size"]
            })

        # 1100 ORB (scan until 17:00)
        trade_1100 = simulate_trade_1m_halfsl(con, cur_date, 11, 0, 17, 0, 1.0)
        if trade_1100 and trade_1100["break_dir"] != "NONE":
            mae_mfe_data["1100"].append({
                "date": cur_date,
                "mae": trade_1100.get("mae"),
                "mfe": trade_1100.get("mfe"),
                "orb_size": trade_1100["orb_size"]
            })

        # Now simulate for each RR ratio
        for rr in RR_RATIOS:
            trade_0900_rr = simulate_trade_1m_halfsl(con, cur_date, 9, 0, 17, 0, rr)
            if trade_0900_rr:
                all_trades[rr]["0900"].append(trade_0900_rr)

            trade_1000_rr = simulate_trade_1m_halfsl(con, cur_date, 10, 0, 17, 0, rr)
            if trade_1000_rr:
                all_trades[rr]["1000"].append(trade_1000_rr)

            trade_1100_rr = simulate_trade_1m_halfsl(con, cur_date, 11, 0, 17, 0, rr)
            if trade_1100_rr:
                all_trades[rr]["1100"].append(trade_1100_rr)

        cur_date += timedelta(days=1)

    con.close()

    # ====================
    # PART 1: MAE/MFE DISTRIBUTIONS (BEFORE P&L)
    # ====================
    print("=" * 80)
    print("MAE/MFE DISTRIBUTIONS (ORB-Anchored, from ORB Edge)")
    print("=" * 80)
    print()

    for orb_time in ORB_TIMES:
        data = mae_mfe_data[orb_time]
        if not data:
            continue

        maes = [d["mae"] for d in data if d["mae"] is not None]
        mfes = [d["mfe"] for d in data if d["mfe"] is not None]
        orb_sizes = [d["orb_size"] / TICK_SIZE for d in data]

        print(f"--- ORB {orb_time} ---")
        print(f"Breaks: {len(data)}")
        print(f"Avg ORB size: {sum(orb_sizes)/len(orb_sizes):.1f} ticks")
        print()

        if maes:
            maes_sorted = sorted(maes)
            print(f"MAE (from ORB edge):")
            print(f"  Mean: {sum(maes)/len(maes):.1f} ticks")
            print(f"  Median: {maes_sorted[len(maes)//2]:.1f} ticks")
            print(f"  P25: {maes_sorted[len(maes)//4]:.1f} ticks")
            print(f"  P75: {maes_sorted[3*len(maes)//4]:.1f} ticks")
            print(f"  P90: {maes_sorted[int(0.9*len(maes))]:.1f} ticks")
            print(f"  Max: {max(maes):.1f} ticks")
        else:
            print("MAE: No data")

        print()

        if mfes:
            mfes_sorted = sorted(mfes)
            print(f"MFE (from ORB edge):")
            print(f"  Mean: {sum(mfes)/len(mfes):.1f} ticks")
            print(f"  Median: {mfes_sorted[len(mfes)//2]:.1f} ticks")
            print(f"  P25: {mfes_sorted[len(mfes)//4]:.1f} ticks")
            print(f"  P75: {mfes_sorted[3*len(mfes)//4]:.1f} ticks")
            print(f"  P90: {mfes_sorted[int(0.9*len(mfes))]:.1f} ticks")
            print(f"  Max: {max(mfes):.1f} ticks")
        else:
            print("MFE: No data")

        print()

        if maes and mfes:
            ratios = [mfe/mae for mae, mfe in zip(maes, mfes) if mae > 0]
            if ratios:
                print(f"MFE/MAE ratio: {sum(ratios)/len(ratios):.2f}x")

        print()

    # ====================
    # PART 2: P&L RESULTS
    # ====================
    print("=" * 80)
    print("P&L RESULTS BY R:R RATIO")
    print("=" * 80)
    print()

    for rr in RR_RATIOS:
        print(f"--- R:R = {rr} ---")
        print()

        total_r = 0.0
        total_trades = 0
        wins = 0
        losses = 0
        no_exits = 0

        for orb_time in ORB_TIMES:
            trades = all_trades[rr][orb_time]
            orb_r = sum(t["r_multiple"] for t in trades if t["r_multiple"] is not None)
            orb_wins = sum(1 for t in trades if t["outcome"] == "WIN")
            orb_losses = sum(1 for t in trades if t["outcome"] == "LOSS")
            orb_no_exits = sum(1 for t in trades if t["outcome"] == "NO_TRADE")
            orb_trades = len([t for t in trades if t["break_dir"] != "NONE"])

            print(f"  {orb_time}: {orb_trades} trades, {orb_wins}W / {orb_losses}L / {orb_no_exits}N, Total R: {orb_r:+.1f}R")

            total_r += orb_r
            total_trades += orb_trades
            wins += orb_wins
            losses += orb_losses
            no_exits += orb_no_exits

        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

        print()
        print(f"  TOTAL: {total_trades} trades")
        print(f"  WIN: {wins} ({win_rate:.1f}%)")
        print(f"  LOSS: {losses}")
        print(f"  NO EXIT: {no_exits}")
        print(f"  Net P&L: {total_r:+.1f}R")
        print()

    print("=" * 80)


if __name__ == "__main__":
    main()
