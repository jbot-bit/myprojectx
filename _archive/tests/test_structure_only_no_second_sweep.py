"""
STRUCTURE-ONLY CASCADE TEST

Tests if London sweeping Asia is sufficient by itself at 23:00,
WITHOUT requiring the second sweep + acceptance failure.

Pattern:
- London swept Asia level (first sweep confirmed)
- Enter SHORT/LONG at 23:00 at the Asia level
- NO second sweep required, NO acceptance failure required
- Just "structure exists + 23:00 timing"

This tests:
1. Is the second sweep + failure mandatory?
2. Or is "London swept Asia" by itself a valid 23:00 entry signal?
3. Does selectivity matter? (requiring failure filters setups)

Comparison:
- Full cascade (requires second sweep + failure): +1.95R, 69 setups
- This test (structure only, no second sweep): ???
"""

import duckdb
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

DB_PATH = "gold.db"
SYMBOL = "MGC"
TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


class StructureOnlyTest:
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

    def test_single_day(self, trade_date: date) -> list:
        """Test structure-only entry at 23:00 (no second sweep required)."""
        # Get Asia session
        asia_start = _dt_local(trade_date, 9, 0)
        asia_end = _dt_local(trade_date, 17, 0)
        asia_bars = self.get_bars(asia_start, asia_end)

        if not asia_bars:
            return []

        asia_high = max(float(b[2]) for b in asia_bars)
        asia_low = min(float(b[3]) for b in asia_bars)

        # Get London session
        london_start = _dt_local(trade_date, 18, 0)
        london_end = _dt_local(trade_date, 23, 0)
        london_bars = self.get_bars(london_start, london_end)

        if not london_bars:
            return []

        london_high = max(float(b[2]) for b in london_bars)
        london_low = min(float(b[3]) for b in london_bars)

        # Get NY session (23:00-02:00) for outcome
        ny_start = _dt_local(trade_date, 23, 0)
        ny_end = _dt_local(trade_date + timedelta(days=1), 2, 0)
        ny_bars = self.get_bars(ny_start, ny_end)

        if not ny_bars:
            return []

        results = []

        # SHORT setup: If London swept Asia high, enter SHORT at 23:00
        if london_high > asia_high:
            gap = london_high - asia_high
            entry_price = asia_high
            stop_price = london_high
            risk = abs(entry_price - stop_price)

            if risk > 0:
                # Scan NY session for outcome
                for bar in ny_bars:
                    bar_h, bar_l = float(bar[2]), float(bar[3])

                    # Stop hit
                    if bar_h >= stop_price:
                        r_mult = -1.0
                        results.append({
                            "date": trade_date,
                            "direction": "SHORT",
                            "gap": gap,
                            "outcome": "LOSS",
                            "r_multiple": r_mult,
                        })
                        break

                    # Target: Asia low (full cascade)
                    if bar_l <= asia_low:
                        r_mult = abs(entry_price - asia_low) / risk
                        results.append({
                            "date": trade_date,
                            "direction": "SHORT",
                            "gap": gap,
                            "outcome": "CASCADE_FULL",
                            "r_multiple": r_mult,
                        })
                        break
                else:
                    # Time exit
                    r_mult = (entry_price - float(ny_bars[-1][4])) / risk
                    results.append({
                        "date": trade_date,
                        "direction": "SHORT",
                        "gap": gap,
                        "outcome": "TIME_EXIT",
                        "r_multiple": r_mult,
                    })

        # LONG setup: If London swept Asia low, enter LONG at 23:00
        if london_low < asia_low:
            gap = asia_low - london_low
            entry_price = asia_low
            stop_price = london_low
            risk = abs(entry_price - stop_price)

            if risk > 0:
                for bar in ny_bars:
                    bar_h, bar_l = float(bar[2]), float(bar[3])

                    if bar_l <= stop_price:
                        r_mult = -1.0
                        results.append({
                            "date": trade_date,
                            "direction": "LONG",
                            "gap": gap,
                            "outcome": "LOSS",
                            "r_multiple": r_mult,
                        })
                        break

                    if bar_h >= asia_high:
                        r_mult = abs(asia_high - entry_price) / risk
                        results.append({
                            "date": trade_date,
                            "direction": "LONG",
                            "gap": gap,
                            "outcome": "CASCADE_FULL",
                            "r_multiple": r_mult,
                        })
                        break
                else:
                    r_mult = (float(ny_bars[-1][4]) - entry_price) / risk
                    results.append({
                        "date": trade_date,
                        "direction": "LONG",
                        "gap": gap,
                        "outcome": "TIME_EXIT",
                        "r_multiple": r_mult,
                    })

        return results

    def run_test(self, start_date: date, end_date: date):
        print("="*80)
        print("STRUCTURE-ONLY CASCADE TEST")
        print("="*80)
        print()
        print("Pattern: London swept Asia => Enter at 23:00")
        print("         (NO second sweep required, NO acceptance failure required)")
        print()
        print("Comparison:")
        print("  Full cascade (requires second sweep + failure): +1.95R, 69 setups")
        print("  This test (structure only):                     ???")
        print()
        print("-"*80)
        print()

        trades = []
        cur = start_date

        while cur <= end_date:
            results = self.test_single_day(cur)
            trades.extend(results)
            cur += timedelta(days=1)

        print(f"Total setups: {len(trades)}")
        print()

        if not trades:
            print("No setups found")
            return

        shorts = [t for t in trades if t["direction"] == "SHORT"]
        longs = [t for t in trades if t["direction"] == "LONG"]

        print(f"SHORT (London swept Asia high): {len(shorts)}")
        print(f"LONG (London swept Asia low): {len(longs)}")
        print()

        # Frequency comparison
        total_days = (end_date - start_date).days + 1
        freq = len(trades) / total_days * 100
        full_cascade_freq = 69 / 741 * 100  # From original test

        print(f"Frequency: {freq:.1f}% of days ({len(trades)}/{total_days})")
        print(f"Full cascade frequency: {full_cascade_freq:.1f}% of days (69/741)")
        print(f">>> This pattern is {freq/full_cascade_freq:.1f}x MORE FREQUENT")
        print()

        for name, segment in [("SHORT", shorts), ("LONG", longs)]:
            if not segment:
                continue

            avg_r = sum(t["r_multiple"] for t in segment) / len(segment)
            print(f"{name} RESULTS:")
            print(f"  Avg R: {avg_r:+.2f}R")

            # Win rate
            wins = [t for t in segment if t["r_multiple"] > 0]
            if wins:
                wr = len(wins) / len(segment) * 100
                print(f"  Win rate: {wr:.1f}%")

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
        print("Comparison to full cascade (+1.95R, 9.3% frequency):")

        if total_avg_r < 0:
            print(f"  >>> STRUCTURE ALONE FAILS ({total_avg_r:+.2f}R)")
            print("  >>> Second sweep + acceptance failure is MANDATORY")
            print(f"  >>> Removing that filter increased frequency {freq/full_cascade_freq:.1f}x but killed edge")
        elif total_avg_r < 1.0:
            print(f"  >>> STRUCTURE ALONE WEAKENS EDGE ({total_avg_r:+.2f}R vs +1.95R)")
            print("  >>> Second sweep filter adds significant value")
        else:
            print(f"  >>> STRUCTURE ALONE WORKS ({total_avg_r:+.2f}R)")
            print("  >>> Second sweep filter may be optional (adds selectivity)")

        print()

    def close(self):
        self.con.close()


if __name__ == "__main__":
    test = StructureOnlyTest()
    test.run_test(date(2024, 1, 1), date(2026, 1, 10))
    test.close()
