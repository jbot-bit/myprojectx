"""
LONDON => NEXT DAY ASIA CASCADE TEST

Test if previous day's London session creates levels that Asia sweeps next morning.

Pattern:
- London high/low (D 18:00-23:00)
- Next Asia session (D+1 09:00-17:00) sweeps it
- Failure => cascade

This tests if FULL SESSION levels (London) create forced positioning
that resolves the next trading day.
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


class LondonToNextAsiaTest:
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
        # Get previous London session
        london_start = _dt_local(trade_date, 18, 0)
        london_end = _dt_local(trade_date, 23, 0)
        london_bars = self.get_bars(london_start, london_end)

        if not london_bars:
            return None

        london_high = max(float(b[2]) for b in london_bars)
        london_low = min(float(b[3]) for b in london_bars)

        # Get next day's Asia session
        next_asia_start = _dt_local(trade_date + timedelta(days=1), 9, 0)
        next_asia_end = _dt_local(trade_date + timedelta(days=1), 17, 0)
        asia_bars = self.get_bars(next_asia_start, next_asia_end)

        if not asia_bars:
            return None

        # Test upside: Asia sweeps London high
        for i, (ts_utc, o, h, l, c) in enumerate(asia_bars):
            if float(c) > london_high:
                sweep_high = float(h)

                # Check failure
                for j in range(i+1, min(i+4, len(asia_bars))):
                    if float(asia_bars[j][4]) < london_high:
                        # Find entry
                        entry_idx = None
                        for k in range(j, len(asia_bars)):
                            if abs(float(asia_bars[k][3]) - london_high) <= ENTRY_TOLERANCE:
                                entry_idx = k
                                break

                        if entry_idx is None:
                            continue

                        risk = abs(london_high - sweep_high)
                        if risk <= 0:
                            continue

                        # Outcome
                        outcome = None
                        r_mult = None

                        for m in range(entry_idx, len(asia_bars)):
                            bar_h, bar_l = float(asia_bars[m][2]), float(asia_bars[m][3])

                            if bar_h >= sweep_high:
                                outcome = "LOSS"
                                r_mult = -1.0
                                break

                            if bar_l <= london_low:
                                outcome = "CASCADE_FULL"
                                r_mult = abs(london_high - london_low) / risk
                                break

                        if outcome is None:
                            outcome = "TIME_EXIT"
                            r_mult = (london_high - float(asia_bars[-1][4])) / risk

                        return {
                            "date": trade_date,
                            "direction": "SHORT",
                            "gap": london_high - london_low,
                            "outcome": outcome,
                            "r_multiple": r_mult,
                        }

        # Test downside
        for i, (ts_utc, o, h, l, c) in enumerate(asia_bars):
            if float(c) < london_low:
                sweep_low = float(l)

                for j in range(i+1, min(i+4, len(asia_bars))):
                    if float(asia_bars[j][4]) > london_low:
                        entry_idx = None
                        for k in range(j, len(asia_bars)):
                            if abs(float(asia_bars[k][2]) - london_low) <= ENTRY_TOLERANCE:
                                entry_idx = k
                                break

                        if entry_idx is None:
                            continue

                        risk = abs(london_low - sweep_low)
                        if risk <= 0:
                            continue

                        outcome = None
                        r_mult = None

                        for m in range(entry_idx, len(asia_bars)):
                            bar_h, bar_l = float(asia_bars[m][2]), float(asia_bars[m][3])

                            if bar_l <= sweep_low:
                                outcome = "LOSS"
                                r_mult = -1.0
                                break

                            if bar_h >= london_high:
                                outcome = "CASCADE_FULL"
                                r_mult = abs(london_high - london_low) / risk
                                break

                        if outcome is None:
                            outcome = "TIME_EXIT"
                            r_mult = (float(asia_bars[-1][4]) - london_low) / risk

                        return {
                            "date": trade_date,
                            "direction": "LONG",
                            "gap": london_high - london_low,
                            "outcome": outcome,
                            "r_multiple": r_mult,
                        }

        return None

    def run_test(self, start_date: date, end_date: date):
        print("="*80)
        print("LONDON => NEXT DAY ASIA TEST")
        print("="*80)
        print()
        print("Pattern: Previous day London levels swept by next day Asia")
        print()

        trades = []
        cur = start_date

        while cur <= end_date:
            result = self.test_single_day(cur)
            if result:
                trades.append(result)
            cur += timedelta(days=1)

        print(f"Total setups: {len(trades)}")

        if not trades:
            print("No setups found")
            return

        shorts = [t for t in trades if t["direction"] == "SHORT"]
        longs = [t for t in trades if t["direction"] == "LONG"]

        print(f"SHORT: {len(shorts)}")
        print(f"LONG: {len(longs)}")
        print()

        for name, segment in [("SHORT", shorts), ("LONG", longs)]:
            if not segment:
                continue

            avg_r = sum(t["r_multiple"] for t in segment) / len(segment)
            print(f"{name}: Avg R = {avg_r:+.2f}R")

        print()

    def close(self):
        self.con.close()


if __name__ == "__main__":
    test = LondonToNextAsiaTest()
    test.run_test(date(2024, 1, 1), date(2026, 1, 10))
    test.close()
