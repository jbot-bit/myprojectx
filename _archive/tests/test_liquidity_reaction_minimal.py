"""
LIQUIDITY REACTION - MINIMAL TEST

Core hypothesis:
"After a liquidity sweep (forced stops hit), does price react predictably?"

Test structure:
- Event: Sweep of London High (1m close above it)
- Acceptance failure: 1m close back below London High within 3 minutes
- Entry: First retrace to level (within 1 tick)
- Stop: Sweep high (beyond the liquidity)
- Exit: 15 minutes after entry OR first VWAP touch

NO optimization. NO grid search. Just prove the pattern exists.
"""

import duckdb
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

DB_PATH = "gold.db"
SYMBOL = "MGC"
TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")
TICK_SIZE = 0.1

# Entry tolerance: how close to level for "retrace"
ENTRY_TOLERANCE_TICKS = 1.0
ENTRY_TOLERANCE = ENTRY_TOLERANCE_TICKS * TICK_SIZE


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


class LiquidityReactionTest:
    def __init__(self):
        self.con = duckdb.connect(DB_PATH, read_only=True)

    def get_london_high(self, trade_date: date) -> float | None:
        """Get London High from daily_features."""
        result = self.con.execute("""
            SELECT london_high
            FROM daily_features
            WHERE date_local = ? AND instrument = ?
        """, [trade_date, SYMBOL]).fetchone()

        return float(result[0]) if result and result[0] else None

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
        Test liquidity reaction for a single day.

        Returns trade result if setup occurred, None otherwise.
        """
        london_high = self.get_london_high(trade_date)
        if not london_high:
            return None

        # Scan window: London close (23:00) through next day 02:00
        # This is when we can trade the London High sweep
        scan_start = _dt_local(trade_date, 23, 0)
        scan_end = _dt_local(trade_date + timedelta(days=1), 2, 0)

        bars = self.get_bars(scan_start, scan_end)
        if not bars:
            return None

        # Phase 1: Find sweep of London High
        sweep_idx = None
        sweep_high = None

        for i, (ts_utc, o, h, l, c, v) in enumerate(bars):
            c = float(c)
            h = float(h)

            # Sweep = close above London High
            if c > london_high:
                sweep_idx = i
                sweep_high = h  # Track highest point during sweep
                break

        if sweep_idx is None:
            return None  # No sweep occurred

        # Phase 2: Check for acceptance failure (close back below within 3 minutes)
        acceptance_failure_idx = None

        for i in range(sweep_idx + 1, min(sweep_idx + 4, len(bars))):  # Next 3 bars
            c = float(bars[i][4])

            if c < london_high:
                acceptance_failure_idx = i
                break

        if acceptance_failure_idx is None:
            return None  # Price held above = no setup

        # Phase 3: Find entry (first retrace to level within tolerance)
        entry_idx = None
        entry_price = None

        for i in range(acceptance_failure_idx, len(bars)):
            o, h, l, c = [float(x) for x in bars[i][1:5]]

            # Check if price retraces to london_high (within tolerance)
            if abs(l - london_high) <= ENTRY_TOLERANCE or abs(h - london_high) <= ENTRY_TOLERANCE:
                # Enter at the level
                entry_idx = i
                entry_price = london_high
                break

        if entry_idx is None:
            return None  # Never retraced to level

        # Phase 4: Trade management
        stop_price = sweep_high  # Stop beyond the liquidity
        risk = abs(entry_price - stop_price)

        if risk <= 0:
            return None  # Invalid setup

        direction = "SHORT"  # We're shorting after failed breakout

        # Calculate VWAP for exit target (session VWAP from London start)
        london_start = _dt_local(trade_date, 18, 0)
        vwap_bars = self.get_bars(london_start, scan_end)

        vwap = None
        if vwap_bars:
            total_pv = sum(float(c) * float(v) for _, _, _, _, c, v in vwap_bars)
            total_v = sum(float(v) for _, _, _, _, _, v in vwap_bars)
            if total_v > 0:
                vwap = total_pv / total_v

        # Phase 5: Scan for exit (15 min fixed time OR VWAP touch)
        exit_time = bars[entry_idx][0] + timedelta(minutes=15)
        outcome = None
        exit_price = None
        r_multiple = None

        for i in range(entry_idx, len(bars)):
            ts_utc, o, h, l, c, v = bars[i]
            h = float(h)
            l = float(l)
            c = float(c)

            # Check stop hit (price goes above stop)
            if h >= stop_price:
                outcome = "LOSS"
                exit_price = stop_price
                r_multiple = -1.0
                break

            # Check VWAP target (if available)
            if vwap and l <= vwap:
                outcome = "WIN"
                exit_price = vwap
                r_multiple = abs(entry_price - vwap) / risk
                break

            # Check time exit (15 min)
            if ts_utc >= exit_time:
                outcome = "TIME_EXIT"
                exit_price = c
                r_multiple = (entry_price - c) / risk  # SHORT position
                break

        if outcome is None:
            outcome = "NO_EXIT"
            return None

        return {
            "date": trade_date,
            "london_high": london_high,
            "sweep_time": bars[sweep_idx][0],
            "sweep_high": sweep_high,
            "acceptance_failure_time": bars[acceptance_failure_idx][0],
            "entry_time": bars[entry_idx][0],
            "entry_price": entry_price,
            "stop_price": stop_price,
            "risk": risk,
            "vwap": vwap,
            "outcome": outcome,
            "exit_price": exit_price,
            "r_multiple": r_multiple,
        }

    def run_test(self, start_date: date, end_date: date):
        """Run test across date range."""
        print("="*80)
        print("LIQUIDITY REACTION - MINIMAL TEST")
        print("="*80)
        print()
        print("Hypothesis: After London High sweep + acceptance failure,")
        print("            does price react predictably?")
        print()
        print(f"Date range: {start_date} to {end_date}")
        print(f"Event: Sweep of London High")
        print(f"Condition: 1m close back below within 3 minutes")
        print(f"Entry: First retrace to level (±{ENTRY_TOLERANCE_TICKS} ticks)")
        print(f"Stop: Sweep high")
        print(f"Exit: 15 min fixed time OR VWAP touch")
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
            if days_scanned % 50 == 0:
                print(f"[Scanned {days_scanned} days, found {len(trades)} setups]")

            cur += timedelta(days=1)

        print()
        print("="*80)
        print("RESULTS")
        print("="*80)
        print()
        print(f"Days scanned: {days_scanned}")
        print(f"Setups found: {len(trades)}")
        print()

        if not trades:
            print("No setups found. Cannot evaluate hypothesis.")
            return

        # Analyze results
        wins = [t for t in trades if t["outcome"] == "WIN"]
        losses = [t for t in trades if t["outcome"] == "LOSS"]
        time_exits = [t for t in trades if t["outcome"] == "TIME_EXIT"]

        print(f"Wins: {len(wins)}")
        print(f"Losses: {len(losses)}")
        print(f"Time exits: {len(time_exits)}")
        print()

        if len(wins) + len(losses) > 0:
            win_rate = len(wins) / (len(wins) + len(losses))
            print(f"Win rate (W/L only): {win_rate:.1%}")

        total_r = sum(t["r_multiple"] for t in trades)
        avg_r = total_r / len(trades)

        print(f"Total R: {total_r:.2f}R")
        print(f"Average R: {avg_r:.2f}R")
        print()

        if avg_r > 0:
            print("[+] HYPOTHESIS SUPPORTED: Pattern shows positive expectancy")
        else:
            print("[-] HYPOTHESIS REJECTED: Pattern shows negative expectancy")

        print()
        print("-"*80)
        print("Sample trades:")
        print("-"*80)
        for t in trades[:10]:
            print(f"{t['date']} | Entry: {t['entry_price']:.1f} | "
                  f"Stop: {t['stop_price']:.1f} | Risk: {t['risk']:.1f} | "
                  f"Outcome: {t['outcome']} | R: {t['r_multiple']:+.2f}R")

        if len(trades) > 10:
            print(f"... and {len(trades) - 10} more")

        print()

    def close(self):
        self.con.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test liquidity reaction hypothesis")
    parser.add_argument("start_date", type=str)
    parser.add_argument("end_date", type=str, nargs="?", default=None)
    args = parser.parse_args()

    start = date.fromisoformat(args.start_date)
    end = date.fromisoformat(args.end_date) if args.end_date else start

    test = LiquidityReactionTest()
    test.run_test(start, end)
    test.close()
