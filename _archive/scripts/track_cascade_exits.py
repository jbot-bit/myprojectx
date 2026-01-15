"""
CASCADE EXIT TRACKER - Structure-Based

Tracks trade execution with structure-based exits:
- Phase 1: Move stop to breakeven at +1R (first 5-10 min)
- Phase 2: Trail behind structural pivots (after 15 min)

Logs for analysis:
- Time to max R
- R at 15/30/60/90 min intervals
- Structure vs fixed-time exit comparison
- Structural pivot tracking (lower highs SHORT, higher lows LONG)

Usage:
  python track_cascade_exits.py --entry 2711.5 --stop 2713.0 --direction SHORT --date 2025-01-10
"""

import argparse
import duckdb
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

DB_PATH = "gold.db"
SYMBOL = "MGC"
TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")


class CascadeExitTracker:
    def __init__(self, entry_price: float, stop_price: float, direction: str, entry_time: datetime):
        self.entry_price = entry_price
        self.stop_price = stop_price
        self.direction = direction
        self.entry_time = entry_time
        self.risk = abs(entry_price - stop_price)

        self.con = duckdb.connect(DB_PATH, read_only=True)

        # Tracking variables
        self.current_r = 0.0
        self.max_r = -1.0  # Worst case
        self.max_r_time = None
        self.stop_moved_to_be = False
        self.last_pivot = None

        # Snapshots
        self.r_15m = None
        self.r_30m = None
        self.r_60m = None
        self.r_90m = None

        # Exit tracking
        self.exit_reason = None
        self.exit_price = None
        self.exit_time = None
        self.final_r = None

    def get_bars_from_entry(self, duration_minutes: int = 90):
        """Get bars starting from entry time."""
        end_time = self.entry_time + timedelta(minutes=duration_minutes)

        return self.con.execute("""
            SELECT ts_utc, open, high, low, close, volume
            FROM bars_1m
            WHERE symbol = ?
              AND ts_utc >= ? AND ts_utc < ?
            ORDER BY ts_utc
        """, [SYMBOL, self.entry_time, end_time]).fetchall()

    def calculate_current_r(self, current_price: float) -> float:
        """Calculate current R based on direction."""
        if self.direction == "SHORT":
            return (self.entry_price - current_price) / self.risk
        else:  # LONG
            return (current_price - self.entry_price) / self.risk

    def check_pivot(self, bars_so_far: list, current_idx: int) -> float | None:
        """
        Identify structural pivot for trailing stop.
        SHORT: last lower high
        LONG: last higher low
        """
        if current_idx < 3:  # Need at least 3 bars for pivot
            return None

        if self.direction == "SHORT":
            # Look for lower high (pivot high that's lower than previous pivot)
            for i in range(current_idx - 1, max(0, current_idx - 10), -1):
                bar_high = float(bars_so_far[i][2])

                # Check if it's a pivot (higher than bars around it)
                if i > 0 and i < len(bars_so_far) - 1:
                    prev_high = float(bars_so_far[i-1][2])
                    next_high = float(bars_so_far[i+1][2])

                    if bar_high > prev_high and bar_high > next_high:
                        # It's a pivot high
                        if self.last_pivot is None or bar_high < self.last_pivot:
                            return bar_high  # Lower high found

        else:  # LONG
            # Look for higher low
            for i in range(current_idx - 1, max(0, current_idx - 10), -1):
                bar_low = float(bars_so_far[i][3])

                if i > 0 and i < len(bars_so_far) - 1:
                    prev_low = float(bars_so_far[i-1][3])
                    next_low = float(bars_so_far[i+1][3])

                    if bar_low < prev_low and bar_low < next_low:
                        # It's a pivot low
                        if self.last_pivot is None or bar_low > self.last_pivot:
                            return bar_low  # Higher low found

        return None

    def track_trade(self):
        """Track trade from entry through exit with structure-based logic."""
        bars = self.get_bars_from_entry(90)

        if not bars:
            print("No bars available from entry time")
            return

        print("="*80)
        print("CASCADE EXIT TRACKING")
        print("="*80)
        print()
        print(f"Entry:     {self.entry_price:.1f}")
        print(f"Stop:      {self.stop_price:.1f}")
        print(f"Direction: {self.direction}")
        print(f"Risk:      {self.risk:.1f} points")
        print(f"Entry time: {self.entry_time.astimezone(TZ_LOCAL).strftime('%Y-%m-%d %H:%M')}")
        print()
        print("-"*80)
        print("TRADE PROGRESSION")
        print("-"*80)
        print()

        current_stop = self.stop_price

        for i, (ts_utc, o, h, l, c, v) in enumerate(bars):
            ts_local = ts_utc.astimezone(TZ_LOCAL)
            h, l, c = float(h), float(l), float(c)
            elapsed_min = (ts_utc - self.entry_time).total_seconds() / 60

            # Calculate current R
            self.current_r = self.calculate_current_r(c)

            # Track max R
            if self.direction == "SHORT":
                best_price = l  # Lowest low is best for SHORT
            else:
                best_price = h  # Highest high is best for LONG

            potential_r = self.calculate_current_r(best_price)
            if potential_r > self.max_r:
                self.max_r = potential_r
                self.max_r_time = elapsed_min

            # Snapshots at intervals
            if self.r_15m is None and elapsed_min >= 15:
                self.r_15m = self.current_r
            if self.r_30m is None and elapsed_min >= 30:
                self.r_30m = self.current_r
            if self.r_60m is None and elapsed_min >= 60:
                self.r_60m = self.current_r
            if self.r_90m is None and elapsed_min >= 90:
                self.r_90m = self.current_r

            # PHASE 1: Check for +1R to move stop to breakeven (first 10 min)
            if not self.stop_moved_to_be and elapsed_min <= 10:
                if self.current_r >= 1.0:
                    current_stop = self.entry_price
                    self.stop_moved_to_be = True
                    print(f"[{ts_local.strftime('%H:%M')}] +1R HIT - Stop moved to BREAKEVEN")
                    print(f"    Current R: {self.current_r:+.2f}R | New Stop: {current_stop:.1f}")
                    print()

            # PHASE 2: Trail behind structure (after 15 min)
            if elapsed_min > 15:
                pivot = self.check_pivot(bars[:i+1], i)
                if pivot is not None and pivot != self.last_pivot:
                    self.last_pivot = pivot

                    # Update trailing stop
                    if self.direction == "SHORT":
                        if pivot < current_stop:  # Lower high = tighter stop
                            current_stop = pivot
                            print(f"[{ts_local.strftime('%H:%M')}] STRUCTURE TRAIL - Lower high pivot")
                            print(f"    Pivot: {pivot:.1f} | New Stop: {current_stop:.1f}")
                            print()
                    else:  # LONG
                        if pivot > current_stop:  # Higher low = tighter stop
                            current_stop = pivot
                            print(f"[{ts_local.strftime('%H:%M')}] STRUCTURE TRAIL - Higher low pivot")
                            print(f"    Pivot: {pivot:.1f} | New Stop: {current_stop:.1f}")
                            print()

            # Check for stop hit
            if self.direction == "SHORT":
                if h >= current_stop:
                    self.exit_reason = "STOP"
                    self.exit_price = current_stop
                    self.exit_time = ts_utc
                    self.final_r = self.calculate_current_r(current_stop)
                    print(f"[{ts_local.strftime('%H:%M')}] STOPPED OUT")
                    print(f"    Exit: {self.exit_price:.1f} | Final R: {self.final_r:+.2f}R")
                    print()
                    break
            else:  # LONG
                if l <= current_stop:
                    self.exit_reason = "STOP"
                    self.exit_price = current_stop
                    self.exit_time = ts_utc
                    self.final_r = self.calculate_current_r(current_stop)
                    print(f"[{ts_local.strftime('%H:%M')}] STOPPED OUT")
                    print(f"    Exit: {self.exit_price:.1f} | Final R: {self.final_r:+.2f}R")
                    print()
                    break

            # Progress updates every 15 minutes
            if i > 0 and int(elapsed_min) % 15 == 0 and int((elapsed_min-1)) % 15 != 0:
                print(f"[{ts_local.strftime('%H:%M')}] {int(elapsed_min)} min | R: {self.current_r:+.2f}R | Max R: {self.max_r:+.2f}R")

        # If not stopped out by end of 90 min
        if self.exit_reason is None:
            self.exit_reason = "TIME_90MIN"
            self.exit_price = c
            self.exit_time = bars[-1][0]
            self.final_r = self.current_r

        print()
        print("-"*80)
        print("TRADE SUMMARY")
        print("-"*80)
        print()
        print(f"Exit reason:     {self.exit_reason}")
        print(f"Exit price:      {self.exit_price:.1f}")
        print(f"Final R:         {self.final_r:+.2f}R")
        print(f"Max R achieved:  {self.max_r:+.2f}R (at {self.max_r_time:.1f} min)")
        print(f"R captured:      {(self.final_r/self.max_r)*100:.0f}% of max")
        print()
        print(f"R at 15 min:     {self.r_15m:+.2f}R" if self.r_15m else "R at 15 min:     N/A")
        print(f"R at 30 min:     {self.r_30m:+.2f}R" if self.r_30m else "R at 30 min:     N/A")
        print(f"R at 60 min:     {self.r_60m:+.2f}R" if self.r_60m else "R at 60 min:     N/A")
        print(f"R at 90 min:     {self.r_90m:+.2f}R" if self.r_90m else "R at 90 min:     N/A")
        print()

        # Compare to fixed-time exits
        print("-"*80)
        print("FIXED-TIME EXIT COMPARISON")
        print("-"*80)
        print()
        if self.r_15m:
            pct = (self.r_15m / self.max_r) * 100 if self.max_r > 0 else 0
            print(f"15min exit: {self.r_15m:+.2f}R ({pct:.0f}% of max)")
        if self.r_30m:
            pct = (self.r_30m / self.max_r) * 100 if self.max_r > 0 else 0
            print(f"30min exit: {self.r_30m:+.2f}R ({pct:.0f}% of max)")
        if self.r_60m:
            pct = (self.r_60m / self.max_r) * 100 if self.max_r > 0 else 0
            print(f"60min exit: {self.r_60m:+.2f}R ({pct:.0f}% of max)")

        print()
        print(f"Structure-based: {self.final_r:+.2f}R ({(self.final_r/self.max_r)*100:.0f}% of max)")
        print()

        if self.final_r > (self.r_30m or -999):
            print("[+] STRUCTURE-BASED EXIT SUPERIOR to 30min fixed exit")

        print()
        print("="*80)
        print()

    def close(self):
        self.con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track cascade exit with structure-based logic")
    parser.add_argument("--entry", type=float, required=True, help="Entry price")
    parser.add_argument("--stop", type=float, required=True, help="Initial stop price")
    parser.add_argument("--direction", type=str, required=True, choices=["SHORT", "LONG"], help="Trade direction")
    parser.add_argument("--date", type=str, required=True, help="Entry date YYYY-MM-DD")
    parser.add_argument("--time", type=str, default="23:05", help="Entry time HH:MM (default 23:05)")

    args = parser.parse_args()

    # Parse entry datetime
    trade_date = date.fromisoformat(args.date)
    hour, minute = map(int, args.time.split(":"))

    if hour < 9:  # If entry after midnight, it's next day
        entry_dt = datetime(trade_date.year, trade_date.month, trade_date.day, hour, minute, tzinfo=TZ_LOCAL) + timedelta(days=1)
    else:
        entry_dt = datetime(trade_date.year, trade_date.month, trade_date.day, hour, minute, tzinfo=TZ_LOCAL)

    entry_dt_utc = entry_dt.astimezone(TZ_UTC)

    # Track the trade
    tracker = CascadeExitTracker(args.entry, args.stop, args.direction, entry_dt_utc)
    tracker.track_trade()
    tracker.close()
