"""
CASCADE MONITORING SYSTEM - LIVE

Real-time monitoring for multi-liquidity cascade setups.

Tracks:
- Asia session high/low (09:00-17:00 local)
- London session high/low (18:00-23:00 local)
- First sweep: London sweeps Asia level
- Second sweep potential at 23:00 (NY futures open)
- Gap size calculation and flagging
- Displacement after failure

Usage:
  python monitor_cascade_live.py 2026-01-13  (for specific date)
  python monitor_cascade_live.py              (for today)
"""

import duckdb
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
import sys

DB_PATH = "gold.db"
SYMBOL = "MGC"
TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")

# Cascade thresholds
MEDIAN_GAP = 9.5  # points, from historical analysis
ENTRY_TOLERANCE_TICKS = 1.0
TICK_SIZE = 0.1


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


class CascadeMonitor:
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

    def monitor_day(self, trade_date: date):
        """Monitor a single trading day for cascade setups."""
        print("="*80)
        print(f"CASCADE MONITOR - {trade_date}")
        print("="*80)
        print()

        # Step 1: Track Asia session (09:00-17:00)
        print("[1] ASIA SESSION (09:00-17:00)")
        asia_start = _dt_local(trade_date, 9, 0)
        asia_end = _dt_local(trade_date, 17, 0)
        asia_bars = self.get_bars(asia_start, asia_end)

        if not asia_bars:
            print("    No data for Asia session (weekend/holiday)")
            print()
            return

        asia_high = max(float(b[2]) for b in asia_bars)
        asia_low = min(float(b[3]) for b in asia_bars)
        asia_range = asia_high - asia_low

        print(f"    Asia High: {asia_high:.1f}")
        print(f"    Asia Low:  {asia_low:.1f}")
        print(f"    Range:     {asia_range:.1f} points")
        print()

        # Step 2: Track London session (18:00-23:00)
        print("[2] LONDON SESSION (18:00-23:00)")
        london_start = _dt_local(trade_date, 18, 0)
        london_end = _dt_local(trade_date, 23, 0)
        london_bars = self.get_bars(london_start, london_end)

        if not london_bars:
            print("    No data for London session")
            print()
            return

        london_high = max(float(b[2]) for b in london_bars)
        london_low = min(float(b[3]) for b in london_bars)
        london_range = london_high - london_low

        print(f"    London High: {london_high:.1f}")
        print(f"    London Low:  {london_low:.1f}")
        print(f"    Range:       {london_range:.1f} points")
        print()

        # Step 3: Check for first sweep (London vs Asia)
        print("[3] FIRST SWEEP ANALYSIS")

        swept_asia_high = london_high > asia_high
        swept_asia_low = london_low < asia_low

        if swept_asia_high:
            gap_high = london_high - asia_high
            print(f"    [!] LONDON SWEPT ASIA HIGH")
            print(f"        Asia High:   {asia_high:.1f}")
            print(f"        London High: {london_high:.1f}")
            print(f"        Gap:         {gap_high:.1f} points")
            if gap_high > MEDIAN_GAP:
                print(f"        >>> GAP > MEDIAN ({MEDIAN_GAP} pts) - LARGE GAP SETUP <<<")
            else:
                print(f"        Gap < median ({MEDIAN_GAP} pts) - small gap")
            print()

        if swept_asia_low:
            gap_low = asia_low - london_low
            print(f"    [!] LONDON SWEPT ASIA LOW")
            print(f"        Asia Low:   {asia_low:.1f}")
            print(f"        London Low: {london_low:.1f}")
            print(f"        Gap:        {gap_low:.1f} points")
            if gap_low > MEDIAN_GAP:
                print(f"        >>> GAP > MEDIAN ({MEDIAN_GAP} pts) - LARGE GAP SETUP <<<")
            else:
                print(f"        Gap < median ({MEDIAN_GAP} pts) - small gap")
            print()

        if not swept_asia_high and not swept_asia_low:
            print("    No first sweep - London stayed within Asia range")
            print("    CASCADE SETUP NOT POSSIBLE")
            print()
            return

        # Step 4: Monitor 23:00 window for second sweep
        print("[4] NY FUTURES OPEN (23:00-02:00) - SECOND SWEEP WINDOW")
        ny_start = _dt_local(trade_date, 23, 0)
        ny_end = _dt_local(trade_date + timedelta(days=1), 2, 0)
        ny_bars = self.get_bars(ny_start, ny_end)

        if not ny_bars:
            print("    No data for NY window")
            print()
            return

        # Track for upside cascade (if London swept Asia high)
        if swept_asia_high:
            print()
            print("    UPSIDE CASCADE WATCH:")
            print(f"    - Looking for sweep of London High ({london_high:.1f})")
            print(f"    - Then failure to hold (close back below)")
            print(f"    - Entry SHORT at {london_high:.1f}")
            print(f"    - Target cascade to Asia High ({asia_high:.1f}) and below")
            print()

            # Check each bar
            for i, (ts_utc, o, h, l, c, v) in enumerate(ny_bars[:30]):  # First 30 bars
                ts_local = ts_utc.astimezone(TZ_LOCAL)
                c = float(c)
                h = float(h)
                l = float(l)

                # Second sweep detected
                if c > london_high:
                    print(f"    [{ts_local.strftime('%H:%M')}] SECOND SWEEP DETECTED!")
                    print(f"        Close: {c:.1f} (above London High {london_high:.1f})")
                    print(f"        >>> WATCHING FOR FAILURE TO HOLD <<<")

                    # Check next 3 bars for acceptance failure
                    for j in range(i+1, min(i+4, len(ny_bars))):
                        next_ts, next_o, next_h, next_l, next_c, next_v = ny_bars[j]
                        next_ts_local = next_ts.astimezone(TZ_LOCAL)
                        next_c = float(next_c)

                        if next_c < london_high:
                            print(f"    [{next_ts_local.strftime('%H:%M')}] ACCEPTANCE FAILURE!")
                            print(f"        Close: {next_c:.1f} (back below {london_high:.1f})")
                            print()
                            print("    " + "="*76)
                            print("    CASCADE SETUP CONFIRMED - SHORT")
                            print("    " + "="*76)
                            print(f"    Entry:  {london_high:.1f} (on retrace to level)")
                            print(f"    Stop:   {h:.1f} (sweep high)")
                            print(f"    Risk:   {abs(london_high - h):.1f} points")
                            print(f"    Target: {asia_high:.1f} (first level)")
                            print(f"    Target: {asia_high - abs(london_high - h):.1f} (full cascade)")
                            print(f"    Gap:    {gap_high:.1f} points ({'+LARGE' if gap_high > MEDIAN_GAP else 'small'})")
                            print("    " + "="*76)
                            print()
                            return

        # Track for downside cascade (if London swept Asia low)
        if swept_asia_low:
            print()
            print("    DOWNSIDE CASCADE WATCH:")
            print(f"    - Looking for sweep of London Low ({london_low:.1f})")
            print(f"    - Then failure to hold (close back above)")
            print(f"    - Entry LONG at {london_low:.1f}")
            print(f"    - Target cascade to Asia Low ({asia_low:.1f}) and above")
            print()

            # Check each bar
            for i, (ts_utc, o, h, l, c, v) in enumerate(ny_bars[:30]):
                ts_local = ts_utc.astimezone(TZ_LOCAL)
                c = float(c)
                h = float(h)
                l = float(l)

                # Second sweep detected
                if c < london_low:
                    print(f"    [{ts_local.strftime('%H:%M')}] SECOND SWEEP DETECTED!")
                    print(f"        Close: {c:.1f} (below London Low {london_low:.1f})")
                    print(f"        >>> WATCHING FOR FAILURE TO HOLD <<<")

                    # Check next 3 bars for acceptance failure
                    for j in range(i+1, min(i+4, len(ny_bars))):
                        next_ts, next_o, next_h, next_l, next_c, next_v = ny_bars[j]
                        next_ts_local = next_ts.astimezone(TZ_LOCAL)
                        next_c = float(next_c)

                        if next_c > london_low:
                            print(f"    [{next_ts_local.strftime('%H:%M')}] ACCEPTANCE FAILURE!")
                            print(f"        Close: {next_c:.1f} (back above {london_low:.1f})")
                            print()
                            print("    " + "="*76)
                            print("    CASCADE SETUP CONFIRMED - LONG")
                            print("    " + "="*76)
                            print(f"    Entry:  {london_low:.1f} (on retrace to level)")
                            print(f"    Stop:   {l:.1f} (sweep low)")
                            print(f"    Risk:   {abs(london_low - l):.1f} points")
                            print(f"    Target: {asia_low:.1f} (first level)")
                            print(f"    Target: {asia_low + abs(london_low - l):.1f} (full cascade)")
                            print(f"    Gap:    {gap_low:.1f} points ({'+LARGE' if gap_low > MEDIAN_GAP else 'small'})")
                            print("    " + "="*76)
                            print()
                            return

        print("    No second sweep or acceptance failure detected in first 30 bars")
        print()

    def close(self):
        self.con.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        trade_date = date.fromisoformat(sys.argv[1])
    else:
        trade_date = date.today()

    print()
    print("="*80)
    print("MULTI-LIQUIDITY CASCADE MONITOR")
    print("="*80)
    print()
    print("Monitoring for:")
    print("  1. London sweeps Asia level (first sweep)")
    print("  2. NY sweeps London level at 23:00 (second sweep)")
    print("  3. Failure to hold => CASCADE SETUP")
    print()
    print(f"Gap threshold: {MEDIAN_GAP} points (large gap = higher payoff)")
    print()

    monitor = CascadeMonitor()
    monitor.monitor_day(trade_date)
    monitor.close()

    print()
    print("="*80)
    print("Monitoring complete")
    print("="*80)
    print()
