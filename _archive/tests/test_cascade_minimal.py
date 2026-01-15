"""
MULTI-LIQUIDITY CASCADE - MINIMAL TEST

Core hypothesis:
"When multiple liquidity levels are swept in sequence, then fail,
the unwind is larger than single-level reactions."

Cascade structure (LONG side example):
1. London sweeps Asia high (takes liquidity)
2. Post-London sweeps London high (takes more liquidity)
3. Price fails to hold above London high (both levels trapped)
4. Unwind cascades back through both levels

Entry: On acceptance failure of final sweep
Target: Unwind to first swept level (or beyond)
Stop: Beyond final sweep high

Expected: 10-30R moves when cascade completes.
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


class CascadeTest:
    def __init__(self):
        self.con = duckdb.connect(DB_PATH, read_only=True)

    def get_session_levels(self, trade_date: date) -> dict | None:
        """Get Asia high/low and London high/low from daily_features."""
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

    def test_single_day(self, trade_date: date) -> dict | None:
        """
        Test for upside cascade:
        1. London high > Asia high (first sweep during London)
        2. Post-London sweeps London high (second sweep)
        3. Price fails to hold above London high
        4. Entry short on failure
        5. Target: Unwind to Asia high or below
        """
        levels = self.get_session_levels(trade_date)
        if not levels:
            return None

        asia_high = levels["asia_high"]
        london_high = levels["london_high"]

        # Condition 1: London must have swept Asia high
        if london_high <= asia_high:
            return None  # No initial sweep, no cascade setup

        # Scan window: Post-London (23:00) through next day 02:00
        scan_start = _dt_local(trade_date, 23, 0)
        scan_end = _dt_local(trade_date + timedelta(days=1), 2, 0)

        bars = self.get_bars(scan_start, scan_end)
        if not bars:
            return None

        # Phase 1: Find sweep of London high (second liquidity level)
        sweep_idx = None
        sweep_high = None

        for i, (ts_utc, o, h, l, c, v) in enumerate(bars):
            c = float(c)
            h = float(h)

            if c > london_high:
                sweep_idx = i
                sweep_high = h
                break

        if sweep_idx is None:
            return None  # No second sweep, no cascade

        # Phase 2: Acceptance failure (close back below London high within 3 minutes)
        acceptance_failure_idx = None

        for i in range(sweep_idx + 1, min(sweep_idx + 4, len(bars))):
            c = float(bars[i][4])

            if c < london_high:
                acceptance_failure_idx = i
                break

        if acceptance_failure_idx is None:
            return None  # Held above = no cascade trigger

        # Phase 3: Entry on retrace to London high
        entry_idx = None
        entry_price = None

        for i in range(acceptance_failure_idx, len(bars)):
            o, h, l, c = [float(x) for x in bars[i][1:5]]

            if abs(l - london_high) <= ENTRY_TOLERANCE or abs(h - london_high) <= ENTRY_TOLERANCE:
                entry_idx = i
                entry_price = london_high
                break

        if entry_idx is None:
            return None

        # Phase 4: Trade setup
        stop_price = sweep_high  # Stop beyond the sweep
        risk = abs(entry_price - stop_price)

        if risk <= 0:
            return None

        direction = "SHORT"

        # Cascade targets:
        # Target 1: Asia high (first swept level)
        # Target 2: Below Asia high (full cascade)
        target_asia = asia_high
        target_full = asia_high - risk  # Beyond the first level

        # Phase 5: Outcome scan (track progress through cascade)
        outcome = None
        exit_price = None
        r_multiple = None
        hit_asia_high = False

        max_time = bars[entry_idx][0] + timedelta(minutes=90)  # Extended time for cascade

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

            # Check if we hit Asia high level
            if l <= target_asia:
                hit_asia_high = True

            # Full cascade (below Asia high)
            if l <= target_full:
                outcome = "CASCADE_FULL"
                exit_price = target_full
                r_multiple = abs(entry_price - target_full) / risk
                break

            # Time exit (give cascade time to develop)
            if ts_utc >= max_time:
                outcome = "TIME_EXIT"
                exit_price = c
                r_multiple = (entry_price - c) / risk  # SHORT
                break

        if outcome is None:
            return None

        return {
            "date": trade_date,
            "asia_high": asia_high,
            "london_high": london_high,
            "sweep_high": sweep_high,
            "cascade_gap": london_high - asia_high,  # Distance between swept levels
            "entry_price": entry_price,
            "stop_price": stop_price,
            "risk": risk,
            "hit_asia_high": hit_asia_high,
            "outcome": outcome,
            "exit_price": exit_price,
            "r_multiple": r_multiple,
        }

    def run_test(self, start_date: date, end_date: date):
        """Run cascade test across date range."""
        print("="*80)
        print("MULTI-LIQUIDITY CASCADE TEST")
        print("="*80)
        print()
        print("Hypothesis: When multiple liquidity levels are swept in sequence,")
        print("            then fail, the unwind produces larger moves.")
        print()
        print("Structure (upside cascade):")
        print("  1. London sweeps Asia high (first level)")
        print("  2. Post-London sweeps London high (second level)")
        print("  3. Price fails to hold above London high")
        print("  4. Entry: Short on failure at London high")
        print("  5. Target: Unwind to Asia high and beyond")
        print()
        print(f"Date range: {start_date} to {end_date}")
        print(f"Max holding time: 90 minutes (allow cascade to develop)")
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
        print("RESULTS")
        print("="*80)
        print()
        print(f"Days scanned: {days_scanned}")
        print(f"Cascades found: {len(trades)}")
        print()

        if not trades:
            print("No cascade setups found. Pattern may be too rare or conditions too strict.")
            return

        # Analyze results
        cascade_full = [t for t in trades if t["outcome"] == "CASCADE_FULL"]
        losses = [t for t in trades if t["outcome"] == "LOSS"]
        time_exits = [t for t in trades if t["outcome"] == "TIME_EXIT"]

        print(f"Full cascades (reached below Asia high): {len(cascade_full)}")
        print(f"Losses (stopped out): {len(losses)}")
        print(f"Time exits (partial moves): {len(time_exits)}")
        print()

        # How many reached Asia high level?
        reached_asia = [t for t in trades if t["hit_asia_high"]]
        print(f"Reached Asia high level: {len(reached_asia)} ({len(reached_asia)/len(trades)*100:.1f}%)")
        print()

        if len(cascade_full) + len(losses) > 0:
            win_rate = len(cascade_full) / (len(cascade_full) + len(losses))
            print(f"Win rate (full cascade vs stop): {win_rate:.1%}")

        total_r = sum(t["r_multiple"] for t in trades)
        avg_r = total_r / len(trades)

        print(f"Total R: {total_r:.2f}R")
        print(f"Average R per cascade attempt: {avg_r:.2f}R")
        print()

        # R distribution
        r_values = sorted([t["r_multiple"] for t in trades])
        median_r = r_values[len(r_values)//2]
        max_r = max(r_values)

        print(f"Median R: {median_r:.2f}R")
        print(f"Max R: {max_r:.2f}R")
        print()

        # Compare to single-level reaction
        print("-"*80)
        print("COMPARISON TO SINGLE-LEVEL REACTION")
        print("-"*80)
        print()
        print("Single-level (from previous test):")
        print("  Frequency: ~16% of days (120/741)")
        print("  Average R: +1.44R")
        print("  Median R: -1.00R")
        print()
        print("Cascade (this test):")
        print(f"  Frequency: {len(trades)/days_scanned*100:.1f}% of days ({len(trades)}/{days_scanned})")
        print(f"  Average R: {avg_r:+.2f}R")
        print(f"  Median R: {median_r:+.2f}R")
        print()

        if avg_r > 1.44:
            print("[+] CASCADE SHOWS LARGER PAYOFF than single-level")
        else:
            print("[-] CASCADE does not show larger payoff")

        print()
        print("-"*80)
        print("Sample cascade trades:")
        print("-"*80)
        for t in trades[:10]:
            cascade_size = t["cascade_gap"]
            print(f"{t['date']} | Asia: {t['asia_high']:.1f} | London: {t['london_high']:.1f} | "
                  f"Gap: {cascade_size:.1f} | Entry: {t['entry_price']:.1f} | "
                  f"Risk: {t['risk']:.1f} | Hit Asia: {t['hit_asia_high']} | "
                  f"Outcome: {t['outcome']} | R: {t['r_multiple']:+.2f}R")

        if len(trades) > 10:
            print(f"... and {len(trades) - 10} more")

        print()

        # Analyze cascade gap (distance between levels)
        avg_gap = sum(t["cascade_gap"] for t in trades) / len(trades)
        print(f"Average gap between swept levels: {avg_gap:.1f} points")
        print()

        # Check if larger gaps = larger payoffs
        large_gap_trades = [t for t in trades if t["cascade_gap"] > avg_gap]
        if large_gap_trades:
            large_gap_avg_r = sum(t["r_multiple"] for t in large_gap_trades) / len(large_gap_trades)
            print(f"Trades with above-average gap: Avg R = {large_gap_avg_r:+.2f}R")

        small_gap_trades = [t for t in trades if t["cascade_gap"] <= avg_gap]
        if small_gap_trades:
            small_gap_avg_r = sum(t["r_multiple"] for t in small_gap_trades) / len(small_gap_trades)
            print(f"Trades with below-average gap: Avg R = {small_gap_avg_r:+.2f}R")

        print()

    def close(self):
        self.con.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test multi-liquidity cascade hypothesis")
    parser.add_argument("start_date", type=str)
    parser.add_argument("end_date", type=str, nargs="?", default=None)
    args = parser.parse_args()

    start = date.fromisoformat(args.start_date)
    end = date.fromisoformat(args.end_date) if args.end_date else start

    test = CascadeTest()
    test.run_test(start, end)
    test.close()
