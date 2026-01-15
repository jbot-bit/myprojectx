"""
NY => ASIA CASCADE TEST

Different pattern from Asia=>London=>NY:
- NY overnight (23:00-02:00) establishes high/low
- Asia open (09:00+) sweeps NY overnight level
- Failure to hold => cascade back

Structure:
1. First level: NY overnight high/low (D 23:00 to D+1 02:00)
2. Second level: Asia session sweeps it (D+1 09:00 onwards)
3. Failure: Can't hold, closes back through
4. Cascade: Unwinds back through NY level

Hypothesis: Same forced positioning logic should work
"""

import duckdb
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

DB_PATH = "gold.db"
SYMBOL = "MGC"
TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")
TICK_SIZE = 0.1
MEDIAN_GAP = 9.5
ENTRY_TOLERANCE = 1.0 * TICK_SIZE


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


class NYtoAsiaCascadeTest:
    def __init__(self):
        self.con = duckdb.connect(DB_PATH, read_only=True)

    def get_bars(self, start_local: datetime, end_local: datetime):
        start_utc = start_local.astimezone(TZ_UTC)
        end_utc = end_local.astimezone(TZ_UTC)
        return self.con.execute("""
            SELECT ts_utc, open, high, low, close, volume
            FROM bars_1m
            WHERE symbol = ? AND ts_utc >= ? AND ts_utc < ?
            ORDER BY ts_utc
        """, [SYMBOL, start_utc, end_utc]).fetchall()

    def test_single_day(self, trade_date: date) -> dict | None:
        """
        Test NY overnight => Asia cascade.

        Structure:
        - NY overnight high/low: D 23:00 to D+1 02:00
        - Asia sweeps it: D+1 09:00 onwards
        - Entry on failure
        """
        # Get NY overnight levels (previous night)
        ny_start = _dt_local(trade_date, 23, 0)
        ny_end = _dt_local(trade_date + timedelta(days=1), 2, 0)
        ny_bars = self.get_bars(ny_start, ny_end)

        if not ny_bars:
            return None

        ny_high = max(float(b[2]) for b in ny_bars)
        ny_low = min(float(b[3]) for b in ny_bars)

        # Get Asia session (starts 09:00 same day as trade_date+1)
        asia_start = _dt_local(trade_date + timedelta(days=1), 9, 0)
        asia_end = _dt_local(trade_date + timedelta(days=1), 17, 0)
        asia_bars = self.get_bars(asia_start, asia_end)

        if not asia_bars:
            return None

        # Test UPSIDE cascade: Asia sweeps NY high
        for i, (ts_utc, o, h, l, c, v) in enumerate(asia_bars):
            c = float(c)
            h = float(h)

            # First sweep: Asia breaks above NY high
            if c > ny_high:
                sweep_high = h

                # Check for acceptance failure (next 3 bars)
                for j in range(i+1, min(i+4, len(asia_bars))):
                    next_c = float(asia_bars[j][4])

                    if next_c < ny_high:
                        # Failure detected
                        gap = sweep_high - ny_low  # Distance from sweep to opposite level

                        # Entry on retrace to NY high
                        entry_idx = None
                        for k in range(j, len(asia_bars)):
                            bar_l, bar_h = float(asia_bars[k][3]), float(asia_bars[k][2])
                            if abs(bar_l - ny_high) <= ENTRY_TOLERANCE or abs(bar_h - ny_high) <= ENTRY_TOLERANCE:
                                entry_idx = k
                                break

                        if entry_idx is None:
                            continue

                        # Trade setup
                        entry_price = ny_high
                        stop_price = sweep_high
                        risk = abs(entry_price - stop_price)

                        if risk <= 0:
                            continue

                        # Scan for outcome (rest of Asia session)
                        outcome = None
                        r_multiple = None

                        for m in range(entry_idx, len(asia_bars)):
                            bar_h, bar_l, bar_c = [float(x) for x in asia_bars[m][2:5]]

                            # Stop hit
                            if bar_h >= stop_price:
                                outcome = "LOSS"
                                r_multiple = -1.0
                                break

                            # Target: NY low (full cascade to opposite level)
                            if bar_l <= ny_low:
                                outcome = "CASCADE_FULL"
                                r_multiple = abs(entry_price - ny_low) / risk
                                break

                        if outcome is None:
                            outcome = "TIME_EXIT"
                            r_multiple = (entry_price - float(asia_bars[-1][4])) / risk

                        return {
                            "date": trade_date,
                            "direction": "SHORT",
                            "ny_high": ny_high,
                            "ny_low": ny_low,
                            "gap": gap,
                            "sweep_high": sweep_high,
                            "entry_price": entry_price,
                            "stop_price": stop_price,
                            "risk": risk,
                            "outcome": outcome,
                            "r_multiple": r_multiple,
                        }

        # Test DOWNSIDE cascade: Asia sweeps NY low
        for i, (ts_utc, o, h, l, c, v) in enumerate(asia_bars):
            c = float(c)
            l = float(l)

            if c < ny_low:
                sweep_low = l

                for j in range(i+1, min(i+4, len(asia_bars))):
                    next_c = float(asia_bars[j][4])

                    if next_c > ny_low:
                        gap = ny_high - sweep_low

                        entry_idx = None
                        for k in range(j, len(asia_bars)):
                            bar_l, bar_h = float(asia_bars[k][3]), float(asia_bars[k][2])
                            if abs(bar_l - ny_low) <= ENTRY_TOLERANCE or abs(bar_h - ny_low) <= ENTRY_TOLERANCE:
                                entry_idx = k
                                break

                        if entry_idx is None:
                            continue

                        entry_price = ny_low
                        stop_price = sweep_low
                        risk = abs(entry_price - stop_price)

                        if risk <= 0:
                            continue

                        outcome = None
                        r_multiple = None

                        for m in range(entry_idx, len(asia_bars)):
                            bar_h, bar_l, bar_c = [float(x) for x in asia_bars[m][2:5]]

                            if bar_l <= stop_price:
                                outcome = "LOSS"
                                r_multiple = -1.0
                                break

                            if bar_h >= ny_high:
                                outcome = "CASCADE_FULL"
                                r_multiple = abs(ny_high - entry_price) / risk
                                break

                        if outcome is None:
                            outcome = "TIME_EXIT"
                            r_multiple = (float(asia_bars[-1][4]) - entry_price) / risk

                        return {
                            "date": trade_date,
                            "direction": "LONG",
                            "ny_high": ny_high,
                            "ny_low": ny_low,
                            "gap": gap,
                            "sweep_low": sweep_low,
                            "entry_price": entry_price,
                            "stop_price": stop_price,
                            "risk": risk,
                            "outcome": outcome,
                            "r_multiple": r_multiple,
                        }

        return None

    def run_test(self, start_date: date, end_date: date):
        print("="*80)
        print("NY OVERNIGHT => ASIA CASCADE TEST")
        print("="*80)
        print()
        print("Pattern:")
        print("  1. NY overnight (D 23:00 - D+1 02:00) establishes levels")
        print("  2. Asia session (D+1 09:00+) sweeps those levels")
        print("  3. Failure to hold => cascade back")
        print()
        print(f"Date range: {start_date} to {end_date}")
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

        print(f"Total setups found: {len(trades)}")
        print()

        if not trades:
            print("No NY=>Asia cascade setups found")
            return

        # Analyze
        shorts = [t for t in trades if t["direction"] == "SHORT"]
        longs = [t for t in trades if t["direction"] == "LONG"]

        print(f"SHORT (Asia swept NY high): {len(shorts)}")
        print(f"LONG (Asia swept NY low): {len(longs)}")
        print()

        for name, segment in [("SHORT", shorts), ("LONG", longs)]:
            if not segment:
                continue

            print(f"{name} RESULTS:")
            cascade_full = [t for t in segment if t["outcome"] == "CASCADE_FULL"]
            losses = [t for t in segment if t["outcome"] == "LOSS"]

            if losses + cascade_full:
                wr = len(cascade_full) / (len(cascade_full) + len(losses))
                print(f"  Win rate: {wr:.1%}")

            total_r = sum(t["r_multiple"] for t in segment)
            avg_r = total_r / len(segment)

            print(f"  Avg R: {avg_r:+.2f}R")
            print(f"  Total R: {total_r:+.2f}R")

            avg_gap = sum(t["gap"] for t in segment) / len(segment)
            large_gap = [t for t in segment if t["gap"] > avg_gap]

            if large_gap:
                large_r = sum(t["r_multiple"] for t in large_gap) / len(large_gap)
                print(f"  Large gap (>{avg_gap:.1f}): {large_r:+.2f}R")

            print()

        print("Sample trades:")
        for t in trades[:10]:
            print(f"  {t['date']} | {t['direction']} | Gap: {t['gap']:.1f} | "
                  f"Outcome: {t['outcome']} | R: {t['r_multiple']:+.2f}R")

        print()

    def close(self):
        self.con.close()


if __name__ == "__main__":
    import sys

    start = date(2024, 1, 1)
    end = date(2026, 1, 10)

    test = NYtoAsiaCascadeTest()
    test.run_test(start, end)
    test.close()
