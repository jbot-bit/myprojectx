"""
MULTI-LIQUIDITY CASCADE - BIDIRECTIONAL TEST

Tests BOTH directions to confirm structural validity:

UPSIDE CASCADE:
1. London high > Asia high (first sweep)
2. Post-London sweeps London high (second sweep)
3. Price fails to hold => SHORT
4. Target: Unwind to Asia high and beyond

DOWNSIDE CASCADE:
1. London low < Asia low (first sweep)
2. Post-London sweeps London low (second sweep)
3. Price fails to hold => LONG
4. Target: Unwind to Asia low and beyond

Hypothesis: Both directions show similar asymmetry if edge is structural.
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


class BidirectionalCascadeTest:
    def __init__(self):
        self.con = duckdb.connect(DB_PATH, read_only=True)

    def get_session_levels(self, trade_date: date) -> dict | None:
        """Get Asia and London high/low from daily_features."""
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
        """Fetch 1m bars for time range."""
        start_utc = start_local.astimezone(TZ_UTC)
        end_utc = end_local.astimezone(TZ_UTC)

        return self.con.execute("""
            SELECT ts_utc, open, high, low, close, volume
            FROM bars_1m
            WHERE symbol = ?
              AND ts_utc >= ? AND ts_utc < ?
            ORDER BY ts_utc
        """, [SYMBOL, start_utc, end_utc]).fetchall()

    def test_upside_cascade(self, trade_date: date, levels: dict, bars: list) -> dict | None:
        """Test upside cascade (sweep highs => fail => short)."""
        asia_high = levels["asia_high"]
        london_high = levels["london_high"]

        # Condition: London swept Asia high
        if london_high <= asia_high:
            return None

        # Find sweep of London high
        sweep_idx = None
        sweep_high = None

        for i, (ts_utc, o, h, l, c, v) in enumerate(bars):
            if float(c) > london_high:
                sweep_idx = i
                sweep_high = float(h)
                break

        if sweep_idx is None:
            return None

        # Acceptance failure (back below London high within 3 bars)
        acceptance_failure_idx = None
        for i in range(sweep_idx + 1, min(sweep_idx + 4, len(bars))):
            if float(bars[i][4]) < london_high:
                acceptance_failure_idx = i
                break

        if acceptance_failure_idx is None:
            return None

        # Entry on retrace to London high
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

        # Trade setup (SHORT)
        stop_price = sweep_high
        risk = abs(entry_price - stop_price)
        if risk <= 0:
            return None

        target_asia = asia_high
        target_full = asia_high - risk

        # Outcome scan
        outcome = None
        exit_price = None
        r_multiple = None
        hit_target_level = False
        max_time = bars[entry_idx][0] + timedelta(minutes=90)

        for i in range(entry_idx, len(bars)):
            ts_utc, o, h, l, c, v = bars[i]
            h, l, c = float(h), float(l), float(c)

            if h >= stop_price:
                outcome = "LOSS"
                exit_price = stop_price
                r_multiple = -1.0
                break

            if l <= target_asia:
                hit_target_level = True

            if l <= target_full:
                outcome = "CASCADE_FULL"
                exit_price = target_full
                r_multiple = abs(entry_price - target_full) / risk
                break

            if ts_utc >= max_time:
                outcome = "TIME_EXIT"
                exit_price = c
                r_multiple = (entry_price - c) / risk
                break

        if outcome is None:
            return None

        return {
            "date": trade_date,
            "direction": "SHORT",
            "level_1": asia_high,
            "level_2": london_high,
            "sweep_extreme": sweep_high,
            "cascade_gap": london_high - asia_high,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "risk": risk,
            "hit_target_level": hit_target_level,
            "outcome": outcome,
            "exit_price": exit_price,
            "r_multiple": r_multiple,
        }

    def test_downside_cascade(self, trade_date: date, levels: dict, bars: list) -> dict | None:
        """Test downside cascade (sweep lows => fail => long)."""
        asia_low = levels["asia_low"]
        london_low = levels["london_low"]

        # Condition: London swept Asia low
        if london_low >= asia_low:
            return None

        # Find sweep of London low
        sweep_idx = None
        sweep_low = None

        for i, (ts_utc, o, h, l, c, v) in enumerate(bars):
            if float(c) < london_low:
                sweep_idx = i
                sweep_low = float(l)
                break

        if sweep_idx is None:
            return None

        # Acceptance failure (back above London low within 3 bars)
        acceptance_failure_idx = None
        for i in range(sweep_idx + 1, min(sweep_idx + 4, len(bars))):
            if float(bars[i][4]) > london_low:
                acceptance_failure_idx = i
                break

        if acceptance_failure_idx is None:
            return None

        # Entry on retrace to London low
        entry_idx = None
        entry_price = None

        for i in range(acceptance_failure_idx, len(bars)):
            l, h = float(bars[i][3]), float(bars[i][2])
            if abs(l - london_low) <= ENTRY_TOLERANCE or abs(h - london_low) <= ENTRY_TOLERANCE:
                entry_idx = i
                entry_price = london_low
                break

        if entry_idx is None:
            return None

        # Trade setup (LONG)
        stop_price = sweep_low
        risk = abs(entry_price - stop_price)
        if risk <= 0:
            return None

        target_asia = asia_low
        target_full = asia_low + risk

        # Outcome scan
        outcome = None
        exit_price = None
        r_multiple = None
        hit_target_level = False
        max_time = bars[entry_idx][0] + timedelta(minutes=90)

        for i in range(entry_idx, len(bars)):
            ts_utc, o, h, l, c, v = bars[i]
            h, l, c = float(h), float(l), float(c)

            if l <= stop_price:
                outcome = "LOSS"
                exit_price = stop_price
                r_multiple = -1.0
                break

            if h >= target_asia:
                hit_target_level = True

            if h >= target_full:
                outcome = "CASCADE_FULL"
                exit_price = target_full
                r_multiple = abs(exit_price - entry_price) / risk
                break

            if ts_utc >= max_time:
                outcome = "TIME_EXIT"
                exit_price = c
                r_multiple = (c - entry_price) / risk
                break

        if outcome is None:
            return None

        return {
            "date": trade_date,
            "direction": "LONG",
            "level_1": asia_low,
            "level_2": london_low,
            "sweep_extreme": sweep_low,
            "cascade_gap": asia_low - london_low,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "risk": risk,
            "hit_target_level": hit_target_level,
            "outcome": outcome,
            "exit_price": exit_price,
            "r_multiple": r_multiple,
        }

    def test_single_day(self, trade_date: date) -> dict | None:
        """Test both directions, return whichever setup occurs first."""
        levels = self.get_session_levels(trade_date)
        if not levels:
            return None

        # Scan window: Post-London (23:00) through next day 02:00
        scan_start = _dt_local(trade_date, 23, 0)
        scan_end = _dt_local(trade_date + timedelta(days=1), 2, 0)

        bars = self.get_bars(scan_start, scan_end)
        if not bars:
            return None

        # Test both directions
        upside = self.test_upside_cascade(trade_date, levels, bars)
        downside = self.test_downside_cascade(trade_date, levels, bars)

        # Return whichever occurred (prefer upside if both somehow)
        if upside:
            return upside
        if downside:
            return downside

        return None

    def run_test(self, start_date: date, end_date: date):
        """Run bidirectional cascade test."""
        print("="*80)
        print("BIDIRECTIONAL CASCADE TEST")
        print("="*80)
        print()
        print("Testing BOTH directions to confirm structural validity:")
        print()
        print("UPSIDE: London high > Asia high => sweep => fail => SHORT => unwind")
        print("DOWNSIDE: London low < Asia low => sweep => fail => LONG => unwind")
        print()
        print(f"Date range: {start_date} to {end_date}")
        print()
        print("-"*80)
        print()

        trades = []
        cur = start_date
        days_scanned = 0

        while cur <= end_date:
            result = self.test_single_day(cur)
            if result:
                trades.append(result)

            days_scanned += 1
            if days_scanned % 100 == 0:
                print(f"[Scanned {days_scanned} days, found {len(trades)} cascades]")

            cur += timedelta(days=1)

        print()
        print("="*80)
        print("RESULTS BY DIRECTION")
        print("="*80)
        print()

        shorts = [t for t in trades if t["direction"] == "SHORT"]
        longs = [t for t in trades if t["direction"] == "LONG"]

        print(f"Total cascades found: {len(trades)}")
        print(f"  SHORT (upside cascade): {len(shorts)}")
        print(f"  LONG (downside cascade): {len(longs)}")
        print()

        # Analyze each direction
        for direction_name, direction_trades in [("SHORT", shorts), ("LONG", longs)]:
            if not direction_trades:
                print(f"{direction_name}: No setups found")
                print()
                continue

            cascade_full = [t for t in direction_trades if t["outcome"] == "CASCADE_FULL"]
            losses = [t for t in direction_trades if t["outcome"] == "LOSS"]
            time_exits = [t for t in direction_trades if t["outcome"] == "TIME_EXIT"]

            print(f"{direction_name} RESULTS:")
            print(f"  Setups: {len(direction_trades)}")
            print(f"  Full cascades: {len(cascade_full)}")
            print(f"  Losses: {len(losses)}")
            print(f"  Time exits: {len(time_exits)}")

            if len(cascade_full) + len(losses) > 0:
                win_rate = len(cascade_full) / (len(cascade_full) + len(losses))
                print(f"  Win rate: {win_rate:.1%}")

            r_values = [t["r_multiple"] for t in direction_trades]
            total_r = sum(r_values)
            avg_r = total_r / len(r_values)
            median_r = sorted(r_values)[len(r_values)//2]
            max_r = max(r_values)

            print(f"  Total R: {total_r:+.2f}R")
            print(f"  Average R: {avg_r:+.2f}R")
            print(f"  Median R: {median_r:+.2f}R")
            print(f"  Max R: {max_r:+.2f}R")

            # Gap analysis
            avg_gap = sum(t["cascade_gap"] for t in direction_trades) / len(direction_trades)
            large_gap = [t for t in direction_trades if t["cascade_gap"] > avg_gap]
            small_gap = [t for t in direction_trades if t["cascade_gap"] <= avg_gap]

            if large_gap:
                large_gap_r = sum(t["r_multiple"] for t in large_gap) / len(large_gap)
                print(f"  Large gap (>{avg_gap:.1f}): {len(large_gap)} trades, Avg R = {large_gap_r:+.2f}R")

            if small_gap:
                small_gap_r = sum(t["r_multiple"] for t in small_gap) / len(small_gap)
                print(f"  Small gap (<={avg_gap:.1f}): {len(small_gap)} trades, Avg R = {small_gap_r:+.2f}R")

            print()

        print("="*80)
        print("DIRECTIONAL COMPARISON")
        print("="*80)
        print()

        if shorts and longs:
            short_avg = sum(t["r_multiple"] for t in shorts) / len(shorts)
            long_avg = sum(t["r_multiple"] for t in longs) / len(longs)

            print(f"SHORT avg R: {short_avg:+.2f}R ({len(shorts)} setups)")
            print(f"LONG avg R: {long_avg:+.2f}R ({len(longs)} setups)")
            print()

            if abs(short_avg - long_avg) < 0.5:
                print("[+] SYMMETRIC: Both directions show similar payoff")
                print("    => Edge is STRUCTURAL (not directional bias)")
            else:
                better = "SHORT" if short_avg > long_avg else "LONG"
                print(f"[!] ASYMMETRIC: {better} side shows stronger edge")
                print("    => Market has directional bias or one side not fully exploited")
        elif shorts and not longs:
            print("[!] Only SHORT side has setups")
            print("    => Market may be trending up (never sweeps lows)")
        elif longs and not shorts:
            print("[!] Only LONG side has setups")
            print("    => Market may be trending down (never sweeps highs)")

        print()
        print("-"*80)
        print("Sample trades (first 5 each direction):")
        print("-"*80)

        print("\nSHORT cascades:")
        for t in shorts[:5]:
            print(f"  {t['date']} | Gap: {t['cascade_gap']:.1f} | "
                  f"Entry: {t['entry_price']:.1f} | Risk: {t['risk']:.1f} | "
                  f"Outcome: {t['outcome']} | R: {t['r_multiple']:+.2f}R")

        print("\nLONG cascades:")
        for t in longs[:5]:
            print(f"  {t['date']} | Gap: {t['cascade_gap']:.1f} | "
                  f"Entry: {t['entry_price']:.1f} | Risk: {t['risk']:.1f} | "
                  f"Outcome: {t['outcome']} | R: {t['r_multiple']:+.2f}R")

        print()

    def close(self):
        self.con.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test bidirectional cascade hypothesis")
    parser.add_argument("start_date", type=str)
    parser.add_argument("end_date", type=str, nargs="?", default=None)
    args = parser.parse_args()

    start = date.fromisoformat(args.start_date)
    end = date.fromisoformat(args.end_date) if args.end_date else start

    test = BidirectionalCascadeTest()
    test.run_test(start, end)
    test.close()
