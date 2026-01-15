"""
Final Backtest: All 6 ORBs with Optimal Filters Applied
========================================================

Apply the best filter to each ORB (only if improvement > 5%):

- 0900: NO FILTER (baseline best)
- 1000: Prior 0900 hit 1R MFE (+13.8%)
- 1100: NO FILTER (only +3.9%, noise)
- 1800: NO FILTER (baseline best)
- 2300: NO FILTER (only +3.6%, noise)
- 0030: Pre-NY travel > 167 ticks (+33.0%)

Configuration:
- Execution: 1-minute
- SL: Half (ORB midpoint)
- R: ORB-anchored
- TP: ORB-anchored
- R:R: 1.5 (optimal from previous analysis)
"""

import duckdb
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")
SYMBOL = "MGC"
DB_PATH = "gold.db"
TICK_SIZE = 0.1

# ORB configuration with filters
ORB_CONFIG = {
    "0900": {
        "hour": 9, "min": 0, "scan_hour": 17, "scan_min": 0, "next_day": False,
        "filter": None  # NO FILTER
    },
    "1000": {
        "hour": 10, "min": 0, "scan_hour": 17, "scan_min": 0, "next_day": False,
        "filter": "prior_0900_1r"  # Prior 0900 hit 1R MFE
    },
    "1100": {
        "hour": 11, "min": 0, "scan_hour": 17, "scan_min": 0, "next_day": False,
        "filter": None  # NO FILTER (improvement too small)
    },
    "1800": {
        "hour": 18, "min": 0, "scan_hour": 23, "scan_min": 0, "next_day": False,
        "filter": None  # NO FILTER
    },
    "2300": {
        "hour": 23, "min": 0, "scan_hour": 0, "scan_min": 30, "next_day": True,
        "filter": None  # NO FILTER (improvement too small)
    },
    "0030": {
        "hour": 0, "min": 30, "scan_hour": 2, "scan_min": 0, "next_day": True,
        "filter": "pre_ny_travel"  # Pre-NY travel > 167 ticks
    },
}

RR = 1.5


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


def simulate_trade_orb_anchored(con, date_local, orb_config, rr):
    """Simulate trade with ORB-anchored TP."""
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


def check_filter(con, date_local, filter_type):
    """Check if filter condition is met for this date."""
    if filter_type is None:
        return True

    if filter_type == "prior_0900_1r":
        # Check if 0900 ORB hit 1R MFE
        result = con.execute("""
            SELECT orb_0900_mfe
            FROM daily_features_v2_half
            WHERE date_local = ?
        """, [date_local]).fetchone()
        if result and result[0] is not None and result[0] >= 1.0:
            return True
        return False

    if filter_type == "pre_ny_travel":
        # Check if pre_ny_range > 167 ticks (16.7 points)
        result = con.execute("""
            SELECT pre_ny_range
            FROM daily_features_v2_half
            WHERE date_local = ?
        """, [date_local]).fetchone()
        if result and result[0] is not None and result[0] > 16.7:
            return True
        return False

    return True


def main():
    start_date = date(2024, 1, 2)
    end_date = date(2026, 1, 10)

    con = duckdb.connect(DB_PATH)

    print("=" * 100)
    print("FINAL BACKTEST: ALL 6 ORBs WITH OPTIMAL FILTERS")
    print("=" * 100)
    print(f"Date range: {start_date} to {end_date}")
    print(f"R:R: {RR}")
    print(f"Execution: 1-minute")
    print(f"SL: Half (ORB midpoint)")
    print(f"R & TP: ORB-anchored")
    print()

    print("FILTERS APPLIED:")
    for orb_time, config in ORB_CONFIG.items():
        filter_desc = config["filter"] if config["filter"] else "NONE"
        print(f"  {orb_time}: {filter_desc}")
    print()

    # Collect trades
    all_trades = {orb_time: [] for orb_time in ORB_CONFIG.keys()}
    filtered_out = {orb_time: 0 for orb_time in ORB_CONFIG.keys()}

    cur_date = start_date
    while cur_date <= end_date:
        for orb_time, orb_config in ORB_CONFIG.items():
            # Check filter
            if check_filter(con, cur_date, orb_config["filter"]):
                trade = simulate_trade_orb_anchored(con, cur_date, orb_config, RR)
                if trade:
                    all_trades[orb_time].append(trade)
            else:
                filtered_out[orb_time] += 1

        cur_date += timedelta(days=1)

    con.close()

    # Print results
    print("=" * 100)
    print("RESULTS BY ORB (with optimal filters)")
    print("=" * 100)
    print()

    print(f"{'ORB':<8} {'Filter':<25} {'Trades':<10} {'Filtered':<10} {'Wins':<8} {'Losses':<8} {'Win%':<10} {'Exp':<12}")
    print("-" * 100)

    total_r = 0.0
    total_trades = 0
    total_wins = 0
    total_losses = 0

    for orb_time in ORB_CONFIG.keys():
        trades = all_trades[orb_time]
        filter_desc = ORB_CONFIG[orb_time]["filter"] if ORB_CONFIG[orb_time]["filter"] else "NONE"

        if not trades:
            print(f"{orb_time:<8} {filter_desc:<25} {'0':<10} {filtered_out[orb_time]:<10} {'-':<8} {'-':<8} {'-':<10} {'-':<12}")
            continue

        orb_r = sum(t["r_multiple"] for t in trades if t["r_multiple"] is not None)
        orb_wins = sum(1 for t in trades if t["outcome"] == "WIN")
        orb_losses = sum(1 for t in trades if t["outcome"] == "LOSS")
        orb_trades = len(trades)
        orb_win_rate = (orb_wins / (orb_wins + orb_losses) * 100) if (orb_wins + orb_losses) > 0 else 0
        orb_expectancy = orb_r / orb_trades if orb_trades > 0 else 0

        print(f"{orb_time:<8} {filter_desc:<25} {orb_trades:<10} {filtered_out[orb_time]:<10} {orb_wins:<8} {orb_losses:<8} {orb_win_rate:<10.1f} {orb_expectancy:+.4f}R")

        total_r += orb_r
        total_trades += orb_trades
        total_wins += orb_wins
        total_losses += orb_losses

    total_win_rate = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
    total_expectancy = total_r / total_trades if total_trades > 0 else 0

    print("-" * 100)
    print(f"{'TOTAL':<8} {'':<25} {total_trades:<10} {'':<10} {total_wins:<8} {total_losses:<8} {total_win_rate:<10.1f} {total_expectancy:+.4f}R")

    print()
    print(f"Net P&L: {total_r:+.1f}R")
    print(f"Expectancy: {total_expectancy:+.4f}R per trade")
    print()

    # Session breakdown
    print("=" * 100)
    print("SESSION BREAKDOWN")
    print("=" * 100)
    print()

    sessions = {
        "ASIA": ["0900", "1000", "1100"],
        "LONDON": ["1800"],
        "NY": ["2300", "0030"]
    }

    for session_name, orb_times in sessions.items():
        session_trades = []
        for orb_time in orb_times:
            session_trades.extend(all_trades[orb_time])

        if not session_trades:
            continue

        total_r = sum(t["r_multiple"] for t in session_trades if t["r_multiple"] is not None)
        n_trades = len(session_trades)
        wins = sum(1 for t in session_trades if t["outcome"] == "WIN")
        losses = sum(1 for t in session_trades if t["outcome"] == "LOSS")
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        expectancy = total_r / n_trades if n_trades > 0 else 0

        print(f"{session_name}:")
        print(f"  Trades: {n_trades} | Win Rate: {win_rate:.1f}% | Total: {total_r:+.1f}R | Exp: {expectancy:+.4f}R")

    print()
    print("=" * 100)
    print("COMPARISON: No Filters vs Optimal Filters")
    print("=" * 100)
    print()
    print("Previous (no filters): 3130 trades, +1217.5R, +0.3890R per trade")
    print(f"Current (optimal filters): {total_trades} trades, {total_r:+.1f}R, {total_expectancy:+.4f}R per trade")
    print()

    if total_expectancy > 0.3890:
        improvement = (total_expectancy - 0.3890) / 0.3890 * 100
        print(f"Improvement: +{improvement:.1f}% expectancy")
    else:
        decline = (0.3890 - total_expectancy) / 0.3890 * 100
        print(f"Decline: -{decline:.1f}% expectancy")


if __name__ == "__main__":
    main()
