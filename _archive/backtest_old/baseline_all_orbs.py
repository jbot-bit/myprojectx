"""
Baseline Backtest - All 6 ORBs (Asia + London + NY)
====================================================

Configuration:
- ORBs: 0900, 1000, 1100, 1800, 2300, 0030
- Execution: 1-minute
- SL: Half (stop at ORB midpoint)
- R: ORB-anchored (edge to stop)
- TP: ORB-anchored (edge +/- rr × R)
- R:R ratios: 1.0, 1.25, 1.5
- NO FILTERS

Purpose: Test if edge is Asia-only or portable to London/NY.
"""

import duckdb
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict

TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")
SYMBOL = "MGC"
DB_PATH = "gold.db"
TICK_SIZE = 0.1

# All 6 ORBs
ORB_CONFIG = {
    "0900": {"hour": 9, "min": 0, "scan_hour": 17, "scan_min": 0, "next_day": False},
    "1000": {"hour": 10, "min": 0, "scan_hour": 17, "scan_min": 0, "next_day": False},
    "1100": {"hour": 11, "min": 0, "scan_hour": 17, "scan_min": 0, "next_day": False},
    "1800": {"hour": 18, "min": 0, "scan_hour": 23, "scan_min": 0, "next_day": False},
    "2300": {"hour": 23, "min": 0, "scan_hour": 0, "scan_min": 30, "next_day": True},
    "0030": {"hour": 0, "min": 30, "scan_hour": 2, "scan_min": 0, "next_day": True},
}

RR_RATIOS = [1.0, 1.25, 1.5]


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


def simulate_trade_orb_anchored(con, date_local, orb_config, rr):
    """
    Simulate trade with ORB-anchored TP.
    Entry price is ONLY for fill simulation.
    """
    orb_start = _dt_local(date_local, orb_config["hour"], orb_config["min"])
    orb_end = orb_start + timedelta(minutes=5)

    if orb_config["next_day"]:
        scan_end = _dt_local(date_local + timedelta(days=1), orb_config["scan_hour"], orb_config["scan_min"])
    else:
        scan_end = _dt_local(date_local, orb_config["scan_hour"], orb_config["scan_min"])

    orb_start_utc = orb_start.astimezone(TZ_UTC)
    orb_end_utc = orb_end.astimezone(TZ_UTC)
    scan_end_utc = scan_end.astimezone(TZ_UTC)

    # Get ORB
    orb_bars = con.execute(
        "SELECT MAX(high) as h, MIN(low) as l FROM bars_1m WHERE symbol = ? AND ts_utc >= ? AND ts_utc < ?",
        [SYMBOL, orb_start_utc, orb_end_utc]
    ).fetchone()

    if not orb_bars or orb_bars[0] is None:
        return None

    orb_high, orb_low = float(orb_bars[0]), float(orb_bars[1])
    orb_mid = (orb_high + orb_low) / 2.0

    # Get bars after ORB
    bars_after = con.execute(
        "SELECT ts_utc, high, low, close FROM bars_1m WHERE symbol = ? AND ts_utc >= ? AND ts_utc < ? ORDER BY ts_utc",
        [SYMBOL, orb_end_utc, scan_end_utc]
    ).fetchall()

    if not bars_after:
        return None

    # Find first break
    break_dir = None
    entry_ts = None

    for ts_utc, h, l, c in bars_after:
        c = float(c)
        if c > orb_high:
            break_dir = "UP"
            entry_ts = ts_utc
            break
        if c < orb_low:
            break_dir = "DOWN"
            entry_ts = ts_utc
            break

    if not break_dir:
        return None

    # ORB-anchored calculations
    stop = orb_mid
    orb_edge = orb_high if break_dir == "UP" else orb_low
    r_orb = abs(orb_edge - stop)

    if r_orb <= 0:
        return None

    # ORB-anchored target
    target = orb_edge + rr * r_orb if break_dir == "UP" else orb_edge - rr * r_orb

    # Check outcome
    checking = False
    for ts_utc, h, l, c in bars_after:
        if ts_utc == entry_ts:
            checking = True
            continue
        if not checking:
            continue

        h = float(h)
        l = float(l)

        if break_dir == "UP":
            hit_stop = l <= stop
            hit_target = h >= target
            if hit_stop and hit_target:
                return {"outcome": "LOSS", "r_multiple": -1.0}
            if hit_target:
                return {"outcome": "WIN", "r_multiple": rr}
            if hit_stop:
                return {"outcome": "LOSS", "r_multiple": -1.0}
        else:
            hit_stop = h >= stop
            hit_target = l <= target
            if hit_stop and hit_target:
                return {"outcome": "LOSS", "r_multiple": -1.0}
            if hit_target:
                return {"outcome": "WIN", "r_multiple": rr}
            if hit_stop:
                return {"outcome": "LOSS", "r_multiple": -1.0}

    return None


def main():
    start_date = date(2024, 1, 2)
    end_date = date(2026, 1, 10)

    con = duckdb.connect(DB_PATH)

    print("=" * 100)
    print("BASELINE BACKTEST - ALL 6 ORBs (Asia + London + NY)")
    print("=" * 100)
    print(f"Date range: {start_date} to {end_date}")
    print(f"ORBs: {', '.join(ORB_CONFIG.keys())}")
    print(f"R:R ratios: {', '.join(map(str, RR_RATIOS))}")
    print(f"Execution: 1-minute")
    print(f"SL mode: Half (stop at ORB midpoint)")
    print(f"R definition: ORB-anchored (edge to stop)")
    print(f"Filters: NONE")
    print()

    # Collect trades for all RR ratios
    all_trades = {rr: {orb_time: [] for orb_time in ORB_CONFIG.keys()} for rr in RR_RATIOS}

    cur_date = start_date
    while cur_date <= end_date:
        for orb_time, orb_config in ORB_CONFIG.items():
            for rr in RR_RATIOS:
                trade = simulate_trade_orb_anchored(con, cur_date, orb_config, rr)
                if trade:
                    all_trades[rr][orb_time].append(trade)

        cur_date += timedelta(days=1)

    con.close()

    # Print results
    print("=" * 100)
    print("RESULTS BY R:R RATIO")
    print("=" * 100)
    print()

    for rr in RR_RATIOS:
        print(f"--- R:R = {rr} ---")
        print()

        total_r = 0.0
        total_trades = 0
        wins = 0
        losses = 0

        for orb_time in ORB_CONFIG.keys():
            trades = all_trades[rr][orb_time]
            orb_r = sum(t["r_multiple"] for t in trades if t["r_multiple"] is not None)
            orb_wins = sum(1 for t in trades if t["outcome"] == "WIN")
            orb_losses = sum(1 for t in trades if t["outcome"] == "LOSS")
            orb_trades = len(trades)
            orb_win_rate = (orb_wins / (orb_wins + orb_losses) * 100) if (orb_wins + orb_losses) > 0 else 0
            orb_expectancy = orb_r / orb_trades if orb_trades > 0 else 0

            print(f"  {orb_time}: {orb_trades:4} trades | {orb_wins:3}W / {orb_losses:3}L | WR: {orb_win_rate:5.1f}% | Total: {orb_r:+7.1f}R | Exp: {orb_expectancy:+.4f}R")

            total_r += orb_r
            total_trades += orb_trades
            wins += orb_wins
            losses += orb_losses

        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        expectancy = total_r / total_trades if total_trades > 0 else 0

        print()
        print(f"  TOTAL: {total_trades} trades")
        print(f"  WIN: {wins} ({win_rate:.1f}%)")
        print(f"  LOSS: {losses}")
        print(f"  Net P&L: {total_r:+.1f}R")
        print(f"  Expectancy: {expectancy:+.4f}R per trade")
        print()

    # Session breakdown
    print("=" * 100)
    print("SESSION COMPARISON (R:R = 1.5, optimal from Run #1)")
    print("=" * 100)
    print()

    rr = 1.5
    sessions = {
        "ASIA": ["0900", "1000", "1100"],
        "LONDON": ["1800"],
        "NY": ["2300", "0030"]
    }

    for session_name, orb_times in sessions.items():
        session_trades = []
        for orb_time in orb_times:
            session_trades.extend(all_trades[rr][orb_time])

        if not session_trades:
            continue

        total_r = sum(t["r_multiple"] for t in session_trades if t["r_multiple"] is not None)
        n_trades = len(session_trades)
        wins = sum(1 for t in session_trades if t["outcome"] == "WIN")
        losses = sum(1 for t in session_trades if t["outcome"] == "LOSS")
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        expectancy = total_r / n_trades if n_trades > 0 else 0

        print(f"{session_name}:")
        print(f"  ORBs: {', '.join(orb_times)}")
        print(f"  Trades: {n_trades}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Total R: {total_r:+.1f}R")
        print(f"  Expectancy: {expectancy:+.4f}R per trade")
        print()

    print("=" * 100)
    print("KEY FINDING: Is the edge Asia-only or portable?")
    print("=" * 100)


if __name__ == "__main__":
    main()
