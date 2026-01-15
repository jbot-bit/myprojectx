"""
PARTIAL CASCADES TEST - Failed Second Sweep

Tests middle layer between Single Liquidity and Full Cascades:
- First level swept (London sweeps Asia)
- Second level ATTEMPTED but FAILS (at 23:00, attempts London level but doesn't hold)
- Entry on failure confirmation

Expected:
- More frequent than full cascades (full cascade = 9.3%)
- Positive expectancy (target: between single liquidity +1.44R and cascades +1.95R)
- Captures "almost cascades" that fail

Structure (EXACT, no optimization):
1. First sweep: London sweeps Asia high/low (during 18:00-23:00)
2. Second attempt: At 23:00+, price ATTEMPTS to sweep London level
   - Gets close (within 1-2 ticks) OR briefly touches but doesn't close beyond
3. Failure: Close back inside prior range within 3 bars
4. Entry: Retest of failed level
5. Stop: Beyond furthest extreme of attempt
6. Exit: Structure trail OR session end

NO grid search. ONE test.
"""

import duckdb
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

DB_PATH = "gold.db"
SYMBOL = "MGC"
TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")

# Fixed thresholds (not optimized)
ATTEMPT_TOLERANCE = 0.2  # "Attempt" = gets within 0.2pts of level
FAILURE_BARS = 3  # Check next 3 bars for failure
ENTRY_TOLERANCE = 0.1  # Entry within 0.1pts


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


class PartialCascadeTest:
    def __init__(self):
        self.con = duckdb.connect(DB_PATH, read_only=True)

    def get_session_levels(self, trade_date: date) -> dict | None:
        result = self.con.execute("""
            SELECT asia_high, asia_low, london_high, london_low
            FROM daily_features
            WHERE date_local = ? AND instrument = ?
        """, [trade_date, SYMBOL]).fetchone()

        if not result or any(x is None for x in result):
            return None

        return {
            "asia_high": float(result[0]),
            "asia_low": float(result[1]),
            "london_high": float(result[2]),
            "london_low": float(result[3]),
        }

    def get_bars(self, start_local: datetime, end_local: datetime):
        start_utc = start_local.astimezone(TZ_UTC)
        end_utc = end_local.astimezone(TZ_UTC)
        return self.con.execute("""
            SELECT ts_utc, open, high, low, close FROM bars_1m
            WHERE symbol = ? AND ts_utc >= ? AND ts_utc < ?
            ORDER BY ts_utc
        """, [SYMBOL, start_utc, end_utc]).fetchall()

    def test_single_day(self, trade_date: date) -> dict | None:
        """
        Test for partial cascade:
        1. London sweeps Asia level (first sweep confirmed)
        2. At 23:00, attempts London level but FAILS
        3. Entry on failure
        """
        levels = self.get_session_levels(trade_date)
        if not levels:
            return None

        asia_high = levels["asia_high"]
        asia_low = levels["asia_low"]
        london_high = levels["london_high"]
        london_low = levels["london_low"]

        # UPSIDE: London swept Asia high
        if london_high > asia_high:
            # Now look for FAILED attempt to sweep London high at 23:00
            ny_start = _dt_local(trade_date, 23, 0)
            ny_end = _dt_local(trade_date + timedelta(days=1), 2, 0)
            ny_bars = self.get_bars(ny_start, ny_end)

            if not ny_bars:
                return None

            # Look for ATTEMPT (not full sweep) of London high
            for i, (ts_utc, o, h, l, c) in enumerate(ny_bars):
                h, l, c = float(h), float(l), float(c)

                # Attempt detected: gets close to London high but doesn't close beyond
                attempt_detected = False
                furthest_high = h

                # Case 1: High gets close to London high
                if abs(h - london_high) <= ATTEMPT_TOLERANCE and c <= london_high:
                    attempt_detected = True
                    furthest_high = h

                # Case 2: Briefly touches/breaks London high but closes back below
                if h > london_high and c < london_high:
                    attempt_detected = True
                    furthest_high = h

                if attempt_detected:
                    # Check next FAILURE_BARS for close back inside prior range
                    for j in range(i+1, min(i+FAILURE_BARS+1, len(ny_bars))):
                        close_j = float(ny_bars[j][4])

                        # Failure: closes back below London high (deeper inside range)
                        if close_j < london_high - 0.5:  # Clear failure, not just hovering
                            # Look for entry on retest of London high
                            for k in range(j, len(ny_bars)):
                                bar_h, bar_l = float(ny_bars[k][2]), float(ny_bars[k][3])

                                # Entry: retest London high
                                if abs(bar_l - london_high) <= ENTRY_TOLERANCE:
                                    entry_price = london_high
                                    stop_price = furthest_high
                                    risk = abs(entry_price - stop_price)

                                    if risk <= 0:
                                        continue

                                    # Scan for outcome
                                    outcome = None
                                    exit_price = None

                                    for m in range(k, len(ny_bars)):
                                        bar_h, bar_l, bar_c = [float(x) for x in ny_bars[m][2:5]]

                                        # Stop hit
                                        if bar_h >= stop_price:
                                            outcome = "LOSS"
                                            exit_price = stop_price
                                            break

                                        # Target: Asia high or deeper (partial cascade reversal)
                                        if bar_l <= asia_high:
                                            outcome = "PARTIAL_REVERSAL"
                                            exit_price = bar_l
                                            break

                                    if outcome is None:
                                        outcome = "TIME_EXIT"
                                        exit_price = float(ny_bars[-1][4])

                                    r_mult = (entry_price - exit_price) / risk

                                    return {
                                        "date": trade_date,
                                        "setup": "UPSIDE",
                                        "direction": "SHORT",
                                        "first_sweep": f"London swept Asia high ({asia_high:.1f})",
                                        "second_attempt": f"Attempted London high ({london_high:.1f}) but failed",
                                        "gap": london_high - asia_high,
                                        "entry_price": entry_price,
                                        "stop_price": stop_price,
                                        "risk": risk,
                                        "outcome": outcome,
                                        "r_multiple": r_mult,
                                    }

        # DOWNSIDE: London swept Asia low
        if london_low < asia_low:
            ny_start = _dt_local(trade_date, 23, 0)
            ny_end = _dt_local(trade_date + timedelta(days=1), 2, 0)
            ny_bars = self.get_bars(ny_start, ny_end)

            if not ny_bars:
                return None

            for i, (ts_utc, o, h, l, c) in enumerate(ny_bars):
                h, l, c = float(h), float(l), float(c)

                attempt_detected = False
                furthest_low = l

                # Attempt: gets close to London low but doesn't close beyond
                if abs(l - london_low) <= ATTEMPT_TOLERANCE and c >= london_low:
                    attempt_detected = True
                    furthest_low = l

                # Or: briefly breaks London low but closes back above
                if l < london_low and c > london_low:
                    attempt_detected = True
                    furthest_low = l

                if attempt_detected:
                    for j in range(i+1, min(i+FAILURE_BARS+1, len(ny_bars))):
                        close_j = float(ny_bars[j][4])

                        if close_j > london_low + 0.5:  # Clear failure
                            for k in range(j, len(ny_bars)):
                                bar_h, bar_l = float(ny_bars[k][2]), float(ny_bars[k][3])

                                if abs(bar_h - london_low) <= ENTRY_TOLERANCE:
                                    entry_price = london_low
                                    stop_price = furthest_low
                                    risk = abs(entry_price - stop_price)

                                    if risk <= 0:
                                        continue

                                    outcome = None
                                    exit_price = None

                                    for m in range(k, len(ny_bars)):
                                        bar_h, bar_l, bar_c = [float(x) for x in ny_bars[m][2:5]]

                                        if bar_l <= stop_price:
                                            outcome = "LOSS"
                                            exit_price = stop_price
                                            break

                                        if bar_h >= asia_low:
                                            outcome = "PARTIAL_REVERSAL"
                                            exit_price = bar_h
                                            break

                                    if outcome is None:
                                        outcome = "TIME_EXIT"
                                        exit_price = float(ny_bars[-1][4])

                                    r_mult = (exit_price - entry_price) / risk

                                    return {
                                        "date": trade_date,
                                        "setup": "DOWNSIDE",
                                        "direction": "LONG",
                                        "first_sweep": f"London swept Asia low ({asia_low:.1f})",
                                        "second_attempt": f"Attempted London low ({london_low:.1f}) but failed",
                                        "gap": asia_low - london_low,
                                        "entry_price": entry_price,
                                        "stop_price": stop_price,
                                        "risk": risk,
                                        "outcome": outcome,
                                        "r_multiple": r_mult,
                                    }

        return None

    def run_test(self, start_date: date, end_date: date):
        print("="*80)
        print("PARTIAL CASCADES TEST - Failed Second Sweep")
        print("="*80)
        print()
        print("Structure:")
        print("  1. First sweep: London sweeps Asia level")
        print("  2. Second attempt: At 23:00, attempts London level but FAILS")
        print("     - Gets within 0.2pts OR briefly touches but doesn't close beyond")
        print("  3. Failure: Close back inside range within 3 bars")
        print("  4. Entry: Retest of failed level")
        print("  5. Stop: Beyond furthest extreme")
        print("  6. Exit: Reversal to Asia level OR session end")
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

        total_days = (end_date - start_date).days + 1
        frequency = len(trades) / total_days * 100

        print(f"Total setups: {len(trades)}")
        print(f"Frequency: {frequency:.1f}% of days ({len(trades)}/{total_days})")
        print()

        if not trades:
            print("No partial cascade setups found")
            print()
            print("This means: Liquidity attempts either succeed (full cascade)")
            print("            or don't happen (no second attempt)")
            print()
            return

        # Calculate metrics
        avg_r = sum(t["r_multiple"] for t in trades) / len(trades)
        sorted_r = sorted(t["r_multiple"] for t in trades)
        median_r = sorted_r[len(sorted_r)//2]
        max_r = max(t["r_multiple"] for t in trades)
        min_r = min(t["r_multiple"] for t in trades)

        wins = [t for t in trades if t["r_multiple"] > 0]
        win_rate = len(wins) / len(trades) * 100

        print("="*80)
        print("RESULTS")
        print("="*80)
        print()
        print(f"Average R:   {avg_r:+.2f}R")
        print(f"Median R:    {median_r:+.2f}R")
        print(f"Max R:       {max_r:+.2f}R")
        print(f"Min R:       {min_r:+.2f}R")
        print(f"Win rate:    {win_rate:.1f}%")
        print()

        # Direction breakdown
        shorts = [t for t in trades if t["direction"] == "SHORT"]
        longs = [t for t in trades if t["direction"] == "LONG"]

        if shorts:
            avg_r_short = sum(t["r_multiple"] for t in shorts) / len(shorts)
            print(f"SHORT (upside attempt failed): {len(shorts)} trades, {avg_r_short:+.2f}R avg")

        if longs:
            avg_r_long = sum(t["r_multiple"] for t in longs) / len(longs)
            print(f"LONG (downside attempt failed): {len(longs)} trades, {avg_r_long:+.2f}R avg")

        print()

        # Gap analysis
        if "gap" in trades[0]:
            large_gap = [t for t in trades if t["gap"] > 9.5]
            small_gap = [t for t in trades if t["gap"] <= 9.5]

            if large_gap:
                large_r = sum(t["r_multiple"] for t in large_gap) / len(large_gap)
                print(f"Large gap (>9.5pts): {len(large_gap)} trades, {large_r:+.2f}R avg")

            if small_gap:
                small_r = sum(t["r_multiple"] for t in small_gap) / len(small_gap)
                print(f"Small gap (<=9.5pts): {len(small_gap)} trades, {small_r:+.2f}R avg")

            print()

        print("="*80)
        print("COMPARISON")
        print("="*80)
        print()
        print(f"Partial Cascades:  {frequency:5.1f}% freq, {avg_r:+.2f}R avg, {win_rate:4.1f}% WR")
        print()
        print("VS Existing Strategies:")
        print("  Full Cascades:     9.3% freq, +1.95R avg, 19-27% WR (PRIMARY)")
        print("  Single Liquidity: 16.0% freq, +1.44R avg, 33.7% WR (BACKUP)")
        print("  00:30 ORB:        56.0% freq, +1.54R avg, 50.8% WR (SECONDARY)")
        print("  23:00 ORB:        63.0% freq, +1.08R avg, 41.5% WR (SECONDARY)")
        print()

        # Verdict
        print("="*80)
        print("VERDICT")
        print("="*80)
        print()

        if frequency < 10:
            print(">>> TOO RARE - Frequency below 10% threshold")
            print(f"    ({frequency:.1f}% vs target >10%)")
            print()

        if avg_r <= 0:
            print(">>> NEGATIVE EDGE - Average R is negative or zero")
            print(f"    ({avg_r:+.2f}R)")
            print()

        if frequency < 10 or avg_r <= 0:
            print(">>> DISCARD - Does not meet minimum criteria")
        elif avg_r > 1.44:
            print(">>> SUCCESS - Middle layer found!")
            print(f"    Sits between Single Liquidity (+1.44R) and Full Cascades (+1.95R)")
            print(f"    More frequent than cascades ({frequency:.1f}% vs 9.3%)")
            print("    Captures failed cascade attempts with positive edge")
        elif avg_r > 1.08:
            print(">>> POSSIBLE MIDDLE LAYER")
            print(f"    Better than night ORBs (+1.08R), weaker than single liquidity (+1.44R)")
            print(f"    Frequency: {frequency:.1f}% (between cascades and single liquidity)")
        else:
            print(">>> WEAK EDGE")
            print(f"    Similar to or weaker than night ORBs")
            print(f"    Not a strong middle layer")

        print()

        # Sample trades
        print("Sample trades:")
        for t in trades[:5]:
            print(f"  {t['date']} | {t['direction']:5s} | {t['first_sweep']}")
            print(f"           | {t['second_attempt']}")
            print(f"           | Outcome: {t['outcome']:15s} | R: {t['r_multiple']:+.2f}R")
            print()

    def close(self):
        self.con.close()


if __name__ == "__main__":
    test = PartialCascadeTest()
    test.run_test(date(2024, 1, 1), date(2026, 1, 10))
    test.close()
