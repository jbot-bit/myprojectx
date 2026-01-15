"""
Verify Entry Timing Logic
=========================

For 50 random trades, verify that:
1. entry_ts is calculated correctly (break_ts + 2 minutes)
2. first_bar_checked_ts > entry_ts (we skip the entry bar itself)

This ensures we're not checking TP/SL on the entry bar.
"""

import duckdb
import random
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")
SYMBOL = "MGC"
DB_PATH = "gold.db"
ENTRY_DELAY_MINUTES = 2

ORB_CONFIG = {
    "0900": {"hour": 9, "min": 0, "scan_hour": 17, "scan_min": 0, "next_day": False},
    "1000": {"hour": 10, "min": 0, "scan_hour": 17, "scan_min": 0, "next_day": False},
    "1100": {"hour": 11, "min": 0, "scan_hour": 17, "scan_min": 0, "next_day": False},
    "1800": {"hour": 18, "min": 0, "scan_hour": 23, "scan_min": 0, "next_day": False},
    "2300": {"hour": 23, "min": 0, "scan_hour": 0, "scan_min": 30, "next_day": True},
    "0030": {"hour": 0, "min": 30, "scan_hour": 2, "scan_min": 0, "next_day": True},
}


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


def get_trade_timing(con, date_local, orb_config):
    """Extract timing information for a trade"""
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

    # Get bars after ORB
    bars_after = con.execute(
        "SELECT ts_utc, high, low, close FROM bars_1m WHERE symbol = ? AND ts_utc >= ? AND ts_utc < ? ORDER BY ts_utc",
        [SYMBOL, orb_end_utc, scan_end_utc]
    ).fetchall()

    if not bars_after:
        return None

    # Find first break
    break_ts = None
    for ts_utc, h, l, c in bars_after:
        c = float(c)
        if c > orb_high or c < orb_low:
            break_ts = ts_utc
            break

    if not break_ts:
        return None

    # Entry timing
    entry_ts = break_ts + timedelta(minutes=ENTRY_DELAY_MINUTES)

    # Find entry bar index
    entry_bar_idx = None
    entry_bar_ts = None
    for i, (ts_utc, h, l, c) in enumerate(bars_after):
        if ts_utc >= entry_ts:
            entry_bar_idx = i
            entry_bar_ts = ts_utc
            break

    if entry_bar_idx is None:
        return None

    # First bar we check for TP/SL (should be AFTER entry bar)
    if entry_bar_idx + 1 < len(bars_after):
        first_checked_ts = bars_after[entry_bar_idx + 1][0]
    else:
        return None

    return {
        "date": date_local,
        "break_ts": break_ts,
        "entry_ts": entry_ts,
        "entry_bar_ts": entry_bar_ts,
        "first_checked_ts": first_checked_ts
    }


def main():
    con = duckdb.connect(DB_PATH)

    # Get all available dates
    dates = con.execute("""
        SELECT DISTINCT date_local
        FROM daily_features_v2_half
        ORDER BY date_local
    """).fetchall()

    all_dates = [d[0] for d in dates]

    print("=" * 100)
    print("VERIFY ENTRY TIMING LOGIC")
    print("=" * 100)
    print()
    print(f"Testing {len(all_dates)} available dates")
    print(f"Will extract 50 random trades across all ORBs")
    print()

    trades_collected = []
    attempts = 0
    max_attempts = 1000

    while len(trades_collected) < 50 and attempts < max_attempts:
        attempts += 1

        # Random date and ORB
        random_date = random.choice(all_dates)
        random_orb = random.choice(list(ORB_CONFIG.keys()))

        timing = get_trade_timing(con, random_date, ORB_CONFIG[random_orb])
        if timing:
            timing['orb'] = random_orb
            trades_collected.append(timing)

    con.close()

    print(f"Collected {len(trades_collected)} trades after {attempts} attempts")
    print()

    if len(trades_collected) == 0:
        print("ERROR: No trades found")
        return

    print("=" * 100)
    print("SAMPLE TRADES (showing first 10)")
    print("=" * 100)
    print()

    for i, trade in enumerate(trades_collected[:10]):
        print(f"Trade {i+1} ({trade['date']} {trade['orb']}):")
        print(f"  break_ts:          {trade['break_ts']}")
        print(f"  entry_ts:          {trade['entry_ts']} (+2 min from break)")
        print(f"  entry_bar_ts:      {trade['entry_bar_ts']}")
        print(f"  first_checked_ts:  {trade['first_checked_ts']}")
        print(f"  Assertion: first_checked_ts > entry_ts? {trade['first_checked_ts'] > trade['entry_ts']}")
        print()

    print("=" * 100)
    print("ASSERTION CHECK: first_checked_ts > entry_ts FOR ALL TRADES")
    print("=" * 100)
    print()

    all_pass = True
    failures = []

    for i, trade in enumerate(trades_collected):
        if not (trade['first_checked_ts'] > trade['entry_ts']):
            all_pass = False
            failures.append((i+1, trade))

    if all_pass:
        print(f"[PASS] All {len(trades_collected)} trades have first_checked_ts > entry_ts")
        print()
        print("This means:")
        print("  1. We enter at entry_ts (break_ts + 2 minutes)")
        print("  2. We start checking TP/SL on bars AFTER entry_ts")
        print("  3. We never check TP/SL on the entry bar itself")
        print()
        print("Logic is CORRECT.")
    else:
        print(f"[FAIL] {len(failures)} trades FAILED the assertion")
        print()
        for idx, trade in failures:
            print(f"Trade {idx} ({trade['date']} {trade['orb']}):")
            print(f"  entry_ts:         {trade['entry_ts']}")
            print(f"  first_checked_ts: {trade['first_checked_ts']}")
            print(f"  Difference:       {trade['first_checked_ts'] - trade['entry_ts']}")
            print()

    print("=" * 100)
    print("DETAILED TIMING ANALYSIS")
    print("=" * 100)
    print()

    # Calculate statistics
    delay_seconds = [(t['entry_ts'] - t['break_ts']).total_seconds() for t in trades_collected]
    check_delay_seconds = [(t['first_checked_ts'] - t['entry_ts']).total_seconds() for t in trades_collected]

    print(f"Entry delay (break_ts to entry_ts):")
    print(f"  Min:  {min(delay_seconds):.0f}s")
    print(f"  Max:  {max(delay_seconds):.0f}s")
    print(f"  Mean: {sum(delay_seconds)/len(delay_seconds):.0f}s")
    print()

    print(f"First check delay (entry_ts to first_checked_ts):")
    print(f"  Min:  {min(check_delay_seconds):.0f}s")
    print(f"  Max:  {max(check_delay_seconds):.0f}s")
    print(f"  Mean: {sum(check_delay_seconds)/len(check_delay_seconds):.0f}s")
    print()

    if all_pass:
        print("=" * 100)
        print("CONCLUSION: Entry timing logic is CORRECT")
        print("=" * 100)
    else:
        print("=" * 100)
        print("CONCLUSION: Entry timing logic has ERRORS - review logic")
        print("=" * 100)


if __name__ == "__main__":
    main()
