"""
Analyze optimal R:R ratio - only test higher ratios if they improve expectancy.

Sequential testing:
1. Test 1.0R first (baseline)
2. Only test 1.25R if it improves expectancy over 1.0R
3. Only test 1.5R if it improves expectancy over 1.25R
"""

import duckdb
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")
SYMBOL = "MGC"
DB_PATH = "gold.db"
TICK_SIZE = 0.1

ORB_TIMES = ["0900", "1000", "1100"]


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


def simulate_trade_orb_anchored(con, date_local, orb_hour, orb_min, scan_end_hour, scan_end_min, rr):
    """
    Simulate trade with ORB-anchored TP (NOT entry-anchored).
    Entry price is ONLY for fill simulation.
    """
    orb_start = _dt_local(date_local, orb_hour, orb_min)
    orb_end = orb_start + timedelta(minutes=5)

    if scan_end_hour < orb_hour:
        scan_end = _dt_local(date_local + timedelta(days=1), scan_end_hour, scan_end_min)
    else:
        scan_end = _dt_local(date_local, scan_end_hour, scan_end_min)

    orb_start_utc = orb_start.astimezone(TZ_UTC)
    orb_end_utc = orb_end.astimezone(TZ_UTC)
    scan_end_utc = scan_end.astimezone(TZ_UTC)

    # Get ORB range
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
    stop = orb_mid  # Half SL
    orb_edge = orb_high if break_dir == "UP" else orb_low
    r_orb = abs(orb_edge - stop)

    if r_orb <= 0:
        return None

    # ORB-anchored target (NOT entry-anchored)
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


def test_rr_ratio(con, start_date, end_date, rr):
    """Test a specific R:R ratio and return expectancy."""
    trades = []

    cur_date = start_date
    while cur_date <= end_date:
        # 0900 ORB
        trade = simulate_trade_orb_anchored(con, cur_date, 9, 0, 17, 0, rr)
        if trade:
            trades.append(trade)

        # 1000 ORB
        trade = simulate_trade_orb_anchored(con, cur_date, 10, 0, 17, 0, rr)
        if trade:
            trades.append(trade)

        # 1100 ORB
        trade = simulate_trade_orb_anchored(con, cur_date, 11, 0, 17, 0, rr)
        if trade:
            trades.append(trade)

        cur_date += timedelta(days=1)

    if not trades:
        return None

    total_r = sum(t["r_multiple"] for t in trades if t["r_multiple"] is not None)
    n_trades = len(trades)
    wins = sum(1 for t in trades if t["outcome"] == "WIN")
    losses = sum(1 for t in trades if t["outcome"] == "LOSS")
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    expectancy = total_r / n_trades if n_trades > 0 else 0

    return {
        "rr": rr,
        "n_trades": n_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_r": total_r,
        "expectancy": expectancy
    }


def main():
    start_date = date(2024, 1, 2)
    end_date = date(2026, 1, 10)

    con = duckdb.connect(DB_PATH)

    print("=" * 100)
    print("OPTIMAL R:R ANALYSIS - Sequential Testing")
    print("=" * 100)
    print(f"Date range: {start_date} to {end_date}")
    print(f"ORBs: {', '.join(ORB_TIMES)}")
    print()

    # Test 1.0R first (baseline)
    print("Step 1: Test R:R = 1.0 (baseline)")
    print("-" * 100)
    result_1_0 = test_rr_ratio(con, start_date, end_date, 1.0)

    if not result_1_0:
        print("No trades found")
        con.close()
        return

    print(f"Trades: {result_1_0['n_trades']}")
    print(f"Wins: {result_1_0['wins']} ({result_1_0['win_rate']:.1f}%)")
    print(f"Losses: {result_1_0['losses']}")
    print(f"Total R: {result_1_0['total_r']:+.1f}R")
    print(f"Expectancy: {result_1_0['expectancy']:+.4f}R per trade")
    print()

    if result_1_0['expectancy'] <= 0:
        print("STOP: No edge at 1.0R. Do not test higher ratios.")
        con.close()
        return

    optimal_result = result_1_0
    print(f"[OK] 1.0R has positive expectancy ({result_1_0['expectancy']:+.4f}R)")
    print()

    # Test 1.25R
    print("Step 2: Test R:R = 1.25")
    print("-" * 100)
    result_1_25 = test_rr_ratio(con, start_date, end_date, 1.25)

    print(f"Trades: {result_1_25['n_trades']}")
    print(f"Wins: {result_1_25['wins']} ({result_1_25['win_rate']:.1f}%)")
    print(f"Losses: {result_1_25['losses']}")
    print(f"Total R: {result_1_25['total_r']:+.1f}R")
    print(f"Expectancy: {result_1_25['expectancy']:+.4f}R per trade")
    print()

    improvement_1_25 = result_1_25['expectancy'] - result_1_0['expectancy']
    print(f"Improvement over 1.0R: {improvement_1_25:+.4f}R per trade ({improvement_1_25 / result_1_0['expectancy'] * 100:+.1f}%)")
    print()

    if improvement_1_25 > 0:
        print(f"[OK] 1.25R improves expectancy")
        optimal_result = result_1_25
    else:
        print(f"[FAIL] 1.25R does NOT improve expectancy. Stop testing.")
        print()
        print("=" * 100)
        print(f"OPTIMAL R:R: {optimal_result['rr']}")
        print(f"Expectancy: {optimal_result['expectancy']:+.4f}R per trade")
        print("=" * 100)
        con.close()
        return

    print()

    # Test 1.5R
    print("Step 3: Test R:R = 1.5")
    print("-" * 100)
    result_1_5 = test_rr_ratio(con, start_date, end_date, 1.5)

    print(f"Trades: {result_1_5['n_trades']}")
    print(f"Wins: {result_1_5['wins']} ({result_1_5['win_rate']:.1f}%)")
    print(f"Losses: {result_1_5['losses']}")
    print(f"Total R: {result_1_5['total_r']:+.1f}R")
    print(f"Expectancy: {result_1_5['expectancy']:+.4f}R per trade")
    print()

    improvement_1_5 = result_1_5['expectancy'] - result_1_25['expectancy']
    print(f"Improvement over 1.25R: {improvement_1_5:+.4f}R per trade ({improvement_1_5 / result_1_25['expectancy'] * 100:+.1f}%)")
    print()

    if improvement_1_5 > 0:
        print(f"[OK] 1.5R improves expectancy")
        optimal_result = result_1_5
    else:
        print(f"[FAIL] 1.5R does NOT improve expectancy")

    print()
    print("=" * 100)
    print("RESULTS SUMMARY")
    print("=" * 100)
    print()

    results = [result_1_0, result_1_25, result_1_5]
    results.sort(key=lambda x: x['expectancy'], reverse=True)

    for i, result in enumerate(results, 1):
        marker = " <-- OPTIMAL" if result == optimal_result else ""
        print(f"{i}. R:R {result['rr']}: {result['expectancy']:+.4f}R per trade{marker}")

    print()
    print("=" * 100)
    print(f"OPTIMAL R:R: {optimal_result['rr']}")
    print(f"Expectancy: {optimal_result['expectancy']:+.4f}R per trade")
    print(f"Win Rate: {optimal_result['win_rate']:.1f}%")
    print(f"Total R: {optimal_result['total_r']:+.1f}R ({optimal_result['n_trades']} trades)")
    print("=" * 100)
    print()

    # Statistical significance check
    print("=" * 100)
    print("STATISTICAL NOTES")
    print("=" * 100)
    print()

    max_improvement = max(
        abs(result_1_25['expectancy'] - result_1_0['expectancy']),
        abs(result_1_5['expectancy'] - result_1_25['expectancy'])
    )

    if max_improvement < 0.01:
        print(f"WARNING: Maximum improvement is only {max_improvement:.4f}R per trade")
        print("This difference is likely within statistical noise.")
        print("Consider using 1.0R for simplicity unless higher RR is significantly better.")
    else:
        print(f"Improvement: {max_improvement:.4f}R per trade")
        print("This may be meaningful, but validate on out-of-sample data.")

    print()

    con.close()


if __name__ == "__main__":
    main()
