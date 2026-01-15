"""
ASIA => LONDON CASCADE - EARLY EXIT TEST

Tests if two-level cascade (Asia => London) can be captured DURING London session
without waiting for 23:00 NY third sweep.

Pattern:
- London sweeps Asia high/low (first sweep at 18:00-23:00)
- Failure to hold during London session
- Entry and exit WITHIN London session (before 23:00)

This tests:
1. Is 23:00 timing critical? (70% of cascades enter at 23:00)
2. Can we capture two-level moves earlier?
3. Does the third sweep add value or is two-level enough?

Comparison to full cascade:
- Full cascade (Asia => London => NY at 23:00): +1.95R average
- This test: Exit by 23:00, no third sweep wait
"""

import duckdb
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

DB_PATH = "gold.db"
SYMBOL = "MGC"
TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")
ENTRY_TOLERANCE = 0.1


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


class AsiaLondonEarlyExitTest:
    def __init__(self):
        self.con = duckdb.connect(DB_PATH, read_only=True)

    def get_bars(self, start_local: datetime, end_local: datetime):
        start_utc = start_local.astimezone(TZ_UTC)
        end_utc = end_local.astimezone(TZ_UTC)
        return self.con.execute("""
            SELECT ts_utc, open, high, low, close FROM bars_1m
            WHERE symbol = ? AND ts_utc >= ? AND ts_utc < ?
            ORDER BY ts_utc
        """, [SYMBOL, start_utc, end_utc]).fetchall()

    def test_single_day(self, trade_date: date) -> dict | None:
        """Test Asia => London cascade with early exit (before 23:00)."""
        # Get Asia session
        asia_start = _dt_local(trade_date, 9, 0)
        asia_end = _dt_local(trade_date, 17, 0)
        asia_bars = self.get_bars(asia_start, asia_end)

        if not asia_bars:
            return None

        asia_high = max(float(b[2]) for b in asia_bars)
        asia_low = min(float(b[3]) for b in asia_bars)

        # Get London session (18:00-23:00)
        london_start = _dt_local(trade_date, 18, 0)
        london_end = _dt_local(trade_date, 23, 0)
        london_bars = self.get_bars(london_start, london_end)

        if not london_bars:
            return None

        # Test UPSIDE: London sweeps Asia high
        for i, (ts_utc, o, h, l, c) in enumerate(london_bars):
            if float(c) > asia_high:
                sweep_high = float(h)

                # Check for failure (next 3 bars)
                for j in range(i+1, min(i+4, len(london_bars))):
                    if float(london_bars[j][4]) < asia_high:
                        # Entry on retrace
                        entry_idx = None
                        for k in range(j, len(london_bars)):
                            if abs(float(london_bars[k][3]) - asia_high) <= ENTRY_TOLERANCE:
                                entry_idx = k
                                break

                        if entry_idx is None:
                            continue

                        risk = abs(asia_high - sweep_high)
                        if risk <= 0:
                            continue

                        # Exit at end of London session (23:00)
                        # This is the key difference: NO THIRD SWEEP WAIT
                        exit_price = float(london_bars[-1][4])
                        r_mult = (asia_high - exit_price) / risk

                        # Track max R during London
                        max_r = -1.0
                        for m in range(entry_idx, len(london_bars)):
                            bar_l = float(london_bars[m][3])
                            potential_r = (asia_high - bar_l) / risk
                            if potential_r > max_r:
                                max_r = potential_r

                        return {
                            "date": trade_date,
                            "direction": "SHORT",
                            "gap": asia_high - asia_low,
                            "entry_time": london_bars[entry_idx][0].astimezone(TZ_LOCAL).strftime("%H:%M"),
                            "exit_time": "23:00",
                            "r_multiple": r_mult,
                            "max_r": max_r,
                            "pct_captured": (r_mult / max_r * 100) if max_r > 0 else 0,
                        }

        # Test DOWNSIDE: London sweeps Asia low
        for i, (ts_utc, o, h, l, c) in enumerate(london_bars):
            if float(c) < asia_low:
                sweep_low = float(l)

                for j in range(i+1, min(i+4, len(london_bars))):
                    if float(london_bars[j][4]) > asia_low:
                        entry_idx = None
                        for k in range(j, len(london_bars)):
                            if abs(float(london_bars[k][2]) - asia_low) <= ENTRY_TOLERANCE:
                                entry_idx = k
                                break

                        if entry_idx is None:
                            continue

                        risk = abs(asia_low - sweep_low)
                        if risk <= 0:
                            continue

                        exit_price = float(london_bars[-1][4])
                        r_mult = (exit_price - asia_low) / risk

                        max_r = -1.0
                        for m in range(entry_idx, len(london_bars)):
                            bar_h = float(london_bars[m][2])
                            potential_r = (bar_h - asia_low) / risk
                            if potential_r > max_r:
                                max_r = potential_r

                        return {
                            "date": trade_date,
                            "direction": "LONG",
                            "gap": asia_high - asia_low,
                            "entry_time": london_bars[entry_idx][0].astimezone(TZ_LOCAL).strftime("%H:%M"),
                            "exit_time": "23:00",
                            "r_multiple": r_mult,
                            "max_r": max_r,
                            "pct_captured": (r_mult / max_r * 100) if max_r > 0 else 0,
                        }

        return None

    def run_test(self, start_date: date, end_date: date):
        print("="*80)
        print("ASIA => LONDON CASCADE - EARLY EXIT TEST")
        print("="*80)
        print()
        print("Pattern: London sweeps Asia => failure => entry => EXIT BY 23:00")
        print("         (NO third sweep wait at 23:00, captures two-level only)")
        print()
        print("Comparison:")
        print("  Full cascade (waits for 23:00 third sweep): +1.95R average")
        print("  This test (exits at 23:00 London close):    ???")
        print()
        print("-"*80)
        print()

        trades = []
        cur = start_date

        while cur <= end_date:
            result = self.test_single_day(cur)
            if result:
                trades.append(result)
            cur += timedelta(days=1)

        print(f"Total setups: {len(trades)}")
        print()

        if not trades:
            print("No setups found")
            return

        shorts = [t for t in trades if t["direction"] == "SHORT"]
        longs = [t for t in trades if t["direction"] == "LONG"]

        print(f"SHORT (swept Asia high): {len(shorts)}")
        print(f"LONG (swept Asia low): {len(longs)}")
        print()

        for name, segment in [("SHORT", shorts), ("LONG", longs)]:
            if not segment:
                continue

            avg_r = sum(t["r_multiple"] for t in segment) / len(segment)
            avg_max_r = sum(t["max_r"] for t in segment) / len(segment)
            avg_pct = sum(t["pct_captured"] for t in segment) / len(segment)

            print(f"{name} RESULTS:")
            print(f"  Avg R at 23:00 exit: {avg_r:+.2f}R")
            print(f"  Avg Max R during London: {avg_max_r:+.2f}R")
            print(f"  Avg % captured: {avg_pct:.0f}%")

            # Gap analysis
            large_gap = [t for t in segment if t["gap"] > 9.5]
            small_gap = [t for t in segment if t["gap"] <= 9.5]

            if large_gap:
                large_r = sum(t["r_multiple"] for t in large_gap) / len(large_gap)
                print(f"  Large gap (>9.5): {large_r:+.2f}R ({len(large_gap)} setups)")

            if small_gap:
                small_r = sum(t["r_multiple"] for t in small_gap) / len(small_gap)
                print(f"  Small gap (<=9.5): {small_r:+.2f}R ({len(small_gap)} setups)")

            print()

        print()
        print("="*80)
        print("CONCLUSION")
        print("="*80)
        print()

        total_avg_r = sum(t["r_multiple"] for t in trades) / len(trades)
        print(f"Combined average R: {total_avg_r:+.2f}R")
        print()
        print("Comparison to full cascade (+1.95R):")
        if total_avg_r < 0:
            print(f"  >>> EARLY EXIT DESTROYS EDGE ({total_avg_r:+.2f}R vs +1.95R)")
            print("  >>> 23:00 third sweep timing is CRITICAL")
        elif total_avg_r < 1.0:
            print(f"  >>> EARLY EXIT REDUCES EDGE ({total_avg_r:+.2f}R vs +1.95R)")
            print("  >>> 23:00 third sweep adds significant value")
        else:
            print(f"  >>> EARLY EXIT WORKS ({total_avg_r:+.2f}R)")
            print("  >>> Two-level cascade sufficient, 23:00 wait optional")

        print()

    def close(self):
        self.con.close()


if __name__ == "__main__":
    test = AsiaLondonEarlyExitTest()
    test.run_test(date(2024, 1, 1), date(2026, 1, 10))
    test.close()
