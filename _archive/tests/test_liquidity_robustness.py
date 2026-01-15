"""
LIQUIDITY REACTION - ROBUSTNESS TEST

Same detection logic, different exit rules.
Tests if edge persists when outliers are capped.
"""

import duckdb
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

DB_PATH = "gold.db"
SYMBOL = "MGC"
TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")
TICK_SIZE = 0.1
ENTRY_TOLERANCE_TICKS = 1.0
ENTRY_TOLERANCE = ENTRY_TOLERANCE_TICKS * TICK_SIZE


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


class LiquidityRobustnessTest:
    def __init__(self):
        self.con = duckdb.connect(DB_PATH, read_only=True)

    def get_london_high(self, trade_date: date) -> float | None:
        result = self.con.execute("""
            SELECT london_high
            FROM daily_features
            WHERE date_local = ? AND instrument = ?
        """, [trade_date, SYMBOL]).fetchone()
        return float(result[0]) if result and result[0] else None

    def get_bars(self, start_local: datetime, end_local: datetime):
        start_utc = start_local.astimezone(TZ_UTC)
        end_utc = end_local.astimezone(TZ_UTC)
        return self.con.execute("""
            SELECT ts_utc, open, high, low, close, volume
            FROM bars_1m
            WHERE symbol = ? AND ts_utc >= ? AND ts_utc < ?
            ORDER BY ts_utc
        """, [SYMBOL, start_utc, end_utc]).fetchall()

    def test_single_day_variant(self, trade_date: date, exit_variant: str) -> dict | None:
        """
        Test with different exit rules:
        - "cap_2r": Hard cap at +2R
        - "cap_3r": Hard cap at +3R
        - "time_15m": 15min time exit only (no VWAP)
        - "time_30m": 30min time exit only (no VWAP)
        """
        london_high = self.get_london_high(trade_date)
        if not london_high:
            return None

        scan_start = _dt_local(trade_date, 23, 0)
        scan_end = _dt_local(trade_date + timedelta(days=1), 2, 0)
        bars = self.get_bars(scan_start, scan_end)
        if not bars:
            return None

        # Phase 1: Find sweep
        sweep_idx = None
        sweep_high = None
        for i, (ts_utc, o, h, l, c, v) in enumerate(bars):
            if float(c) > london_high:
                sweep_idx = i
                sweep_high = float(h)
                break

        if sweep_idx is None:
            return None

        # Phase 2: Acceptance failure
        acceptance_failure_idx = None
        for i in range(sweep_idx + 1, min(sweep_idx + 4, len(bars))):
            if float(bars[i][4]) < london_high:
                acceptance_failure_idx = i
                break

        if acceptance_failure_idx is None:
            return None

        # Phase 3: Entry
        entry_idx = None
        entry_price = None
        for i in range(acceptance_failure_idx, len(bars)):
            l, h = float(bars[i][3]), float(bars[i][2])
            if abs(l - london_high) <= ENTRY_TOLERANCE or abs(h - london_high) <= ENTRY_TOLERANCE:
                entry_idx = i
                entry_price = london_high
                break

        if entry_idx is None:
            return None

        # Phase 4: Trade setup
        stop_price = sweep_high
        risk = abs(entry_price - stop_price)
        if risk <= 0:
            return None

        # Phase 5: Exit rules (VARIANT)
        if exit_variant == "cap_2r":
            target_price = entry_price - 2.0 * risk
            max_time = None
        elif exit_variant == "cap_3r":
            target_price = entry_price - 3.0 * risk
            max_time = None
        elif exit_variant == "time_15m":
            target_price = None
            max_time = bars[entry_idx][0] + timedelta(minutes=15)
        elif exit_variant == "time_30m":
            target_price = None
            max_time = bars[entry_idx][0] + timedelta(minutes=30)
        else:
            raise ValueError(f"Unknown exit variant: {exit_variant}")

        # Phase 6: Outcome scan
        outcome = None
        exit_price = None
        r_multiple = None

        for i in range(entry_idx, len(bars)):
            ts_utc, o, h, l, c, v = bars[i]
            h = float(h)
            l = float(l)
            c = float(c)

            # Stop hit
            if h >= stop_price:
                outcome = "LOSS"
                exit_price = stop_price
                r_multiple = -1.0
                break

            # Target hit (if using cap)
            if target_price and l <= target_price:
                outcome = "WIN"
                exit_price = target_price
                r_multiple = abs(entry_price - target_price) / risk
                break

            # Time exit (if using time)
            if max_time and ts_utc >= max_time:
                outcome = "TIME_EXIT"
                exit_price = c
                r_multiple = (entry_price - c) / risk  # SHORT
                break

        if outcome is None:
            return None

        return {
            "date": trade_date,
            "outcome": outcome,
            "r_multiple": r_multiple,
        }

    def run_variant(self, start_date: date, end_date: date, exit_variant: str):
        trades = []
        cur = start_date
        while cur <= end_date:
            result = self.test_single_day_variant(cur, exit_variant)
            if result:
                trades.append(result)
            cur += timedelta(days=1)

        return trades

    def close(self):
        self.con.close()


def main():
    print("="*80)
    print("LIQUIDITY REACTION - ROBUSTNESS TEST")
    print("="*80)
    print()
    print("Testing 4 exit variants to check if edge persists:")
    print("  A: Hard cap at +2R")
    print("  B: Hard cap at +3R")
    print("  C: 15min time exit only (no VWAP)")
    print("  D: 30min time exit only (no VWAP)")
    print()
    print("-"*80)
    print()

    start_date = date(2024, 1, 1)
    end_date = date(2026, 1, 10)

    test = LiquidityRobustnessTest()

    variants = {
        "A (cap +2R)": "cap_2r",
        "B (cap +3R)": "cap_3r",
        "C (time 15m)": "time_15m",
        "D (time 30m)": "time_30m",
    }

    results = {}

    for name, variant_id in variants.items():
        print(f"Running variant {name}...")
        trades = test.run_variant(start_date, end_date, variant_id)
        results[name] = trades
        print(f"  Found {len(trades)} setups")

    test.close()

    print()
    print("="*80)
    print("RESULTS COMPARISON")
    print("="*80)
    print()

    print(f"{'Variant':<20} {'Trades':<10} {'Win %':<10} {'Avg R':<10} {'Median R':<10} {'Max R':<10}")
    print("-"*80)

    for name, trades in results.items():
        if not trades:
            print(f"{name:<20} {'0':<10} {'-':<10} {'-':<10} {'-':<10} {'-':<10}")
            continue

        wins = [t for t in trades if t["outcome"] == "WIN"]
        losses = [t for t in trades if t["outcome"] == "LOSS"]

        if len(wins) + len(losses) > 0:
            win_rate = len(wins) / (len(wins) + len(losses)) * 100
        else:
            win_rate = 0

        r_values = sorted([t["r_multiple"] for t in trades])
        avg_r = sum(r_values) / len(r_values)
        median_r = r_values[len(r_values)//2]
        max_r = r_values[-1]

        print(f"{name:<20} {len(trades):<10} {win_rate:<10.1f} {avg_r:<10.2f} {median_r:<10.2f} {max_r:<10.2f}")

    print()
    print("="*80)
    print("VERDICT")
    print("="*80)
    print()

    any_positive = False
    for name, trades in results.items():
        if trades:
            avg_r = sum(t["r_multiple"] for t in trades) / len(trades)
            if avg_r > 0.15:
                print(f"[+] {name}: Avg R = {avg_r:.2f}R - edge persists")
                any_positive = True

    if not any_positive:
        print("[-] No variant shows Avg R > +0.15R")
        print("[-] Edge does not persist when outliers are capped")
        print("[-] Pattern is NOT tradeable")

    print()


if __name__ == "__main__":
    main()
