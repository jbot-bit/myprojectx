"""
CASCADE TIMING ANALYSIS

Three questions:
1. When do cascades start? (entry time clusters)
2. When is max R made? (hold duration to peak)
3. When do they die? (time after which edge decays)

No optimization. Just distributions.
"""

import duckdb
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from collections import defaultdict

DB_PATH = "gold.db"
SYMBOL = "MGC"
TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")
TICK_SIZE = 0.1
ENTRY_TOLERANCE_TICKS = 1.0
ENTRY_TOLERANCE = ENTRY_TOLERANCE_TICKS * TICK_SIZE


def _dt_local(d: date, hh: int, mm: int) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ_LOCAL)


class CascadeTimingAnalysis:
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
            SELECT ts_utc, open, high, low, close, volume
            FROM bars_1m
            WHERE symbol = ? AND ts_utc >= ? AND ts_utc < ?
            ORDER BY ts_utc
        """, [SYMBOL, start_utc, end_utc]).fetchall()

    def analyze_upside_cascade(self, trade_date: date, levels: dict, bars: list) -> dict | None:
        """Upside cascade with timing metrics."""
        asia_high = levels["asia_high"]
        london_high = levels["london_high"]

        if london_high <= asia_high:
            return None

        # Find sweep
        sweep_idx = None
        sweep_high = None
        for i, (ts_utc, o, h, l, c, v) in enumerate(bars):
            if float(c) > london_high:
                sweep_idx = i
                sweep_high = float(h)
                break

        if sweep_idx is None:
            return None

        # Acceptance failure
        acceptance_failure_idx = None
        for i in range(sweep_idx + 1, min(sweep_idx + 4, len(bars))):
            if float(bars[i][4]) < london_high:
                acceptance_failure_idx = i
                break

        if acceptance_failure_idx is None:
            return None

        # Entry
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

        stop_price = sweep_high
        risk = abs(entry_price - stop_price)
        if risk <= 0:
            return None

        entry_time = bars[entry_idx][0].astimezone(TZ_LOCAL)

        # Track R at specific intervals and find max R
        max_r = -1.0  # Start at worst case (stopped out)
        max_r_time = None
        r_at_15m = None
        r_at_30m = None
        r_at_60m = None
        end_of_session_r = None

        entry_ts = bars[entry_idx][0]
        session_end = entry_ts + timedelta(minutes=90)

        for i in range(entry_idx, len(bars)):
            ts_utc, o, h, l, c, v = bars[i]
            h, l, c = float(h), float(l), float(c)

            # Stop hit - cascade fails
            if h >= stop_price:
                max_r = -1.0
                max_r_time = (ts_utc - entry_ts).total_seconds() / 60
                break

            # Calculate current R (best price so far for SHORT)
            best_price = min([float(bars[j][3]) for j in range(entry_idx, i+1)])  # lowest low
            current_r = (entry_price - best_price) / risk

            if current_r > max_r:
                max_r = current_r
                max_r_time = (ts_utc - entry_ts).total_seconds() / 60

            # Snapshots at intervals
            elapsed = (ts_utc - entry_ts).total_seconds() / 60
            if r_at_15m is None and elapsed >= 15:
                r_at_15m = (entry_price - c) / risk
            if r_at_30m is None and elapsed >= 30:
                r_at_30m = (entry_price - c) / risk
            if r_at_60m is None and elapsed >= 60:
                r_at_60m = (entry_price - c) / risk

            # End of session
            if ts_utc >= session_end:
                end_of_session_r = (entry_price - c) / risk
                break

        if max_r_time is None:
            return None

        return {
            "date": trade_date,
            "direction": "SHORT",
            "cascade_gap": london_high - asia_high,
            "entry_time_local": entry_time,
            "entry_hour": entry_time.hour + entry_time.minute/60,
            "time_to_max_r": max_r_time,
            "max_r": max_r,
            "r_at_15m": r_at_15m if r_at_15m is not None else max_r,
            "r_at_30m": r_at_30m if r_at_30m is not None else max_r,
            "r_at_60m": r_at_60m if r_at_60m is not None else max_r,
            "end_of_session_r": end_of_session_r if end_of_session_r is not None else max_r,
        }

    def analyze_downside_cascade(self, trade_date: date, levels: dict, bars: list) -> dict | None:
        """Downside cascade with timing metrics."""
        asia_low = levels["asia_low"]
        london_low = levels["london_low"]

        if london_low >= asia_low:
            return None

        # Find sweep
        sweep_idx = None
        sweep_low = None
        for i, (ts_utc, o, h, l, c, v) in enumerate(bars):
            if float(c) < london_low:
                sweep_idx = i
                sweep_low = float(l)
                break

        if sweep_idx is None:
            return None

        # Acceptance failure
        acceptance_failure_idx = None
        for i in range(sweep_idx + 1, min(sweep_idx + 4, len(bars))):
            if float(bars[i][4]) > london_low:
                acceptance_failure_idx = i
                break

        if acceptance_failure_idx is None:
            return None

        # Entry
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

        stop_price = sweep_low
        risk = abs(entry_price - stop_price)
        if risk <= 0:
            return None

        entry_time = bars[entry_idx][0].astimezone(TZ_LOCAL)

        # Track R at specific intervals and find max R
        max_r = -1.0
        max_r_time = None
        r_at_15m = None
        r_at_30m = None
        r_at_60m = None
        end_of_session_r = None

        entry_ts = bars[entry_idx][0]
        session_end = entry_ts + timedelta(minutes=90)

        for i in range(entry_idx, len(bars)):
            ts_utc, o, h, l, c, v = bars[i]
            h, l, c = float(h), float(l), float(c)

            # Stop hit
            if l <= stop_price:
                max_r = -1.0
                max_r_time = (ts_utc - entry_ts).total_seconds() / 60
                break

            # Calculate current R (best price so far for LONG)
            best_price = max([float(bars[j][2]) for j in range(entry_idx, i+1)])  # highest high
            current_r = (best_price - entry_price) / risk

            if current_r > max_r:
                max_r = current_r
                max_r_time = (ts_utc - entry_ts).total_seconds() / 60

            # Snapshots
            elapsed = (ts_utc - entry_ts).total_seconds() / 60
            if r_at_15m is None and elapsed >= 15:
                r_at_15m = (c - entry_price) / risk
            if r_at_30m is None and elapsed >= 30:
                r_at_30m = (c - entry_price) / risk
            if r_at_60m is None and elapsed >= 60:
                r_at_60m = (c - entry_price) / risk

            if ts_utc >= session_end:
                end_of_session_r = (c - entry_price) / risk
                break

        if max_r_time is None:
            return None

        return {
            "date": trade_date,
            "direction": "LONG",
            "cascade_gap": asia_low - london_low,
            "entry_time_local": entry_time,
            "entry_hour": entry_time.hour + entry_time.minute/60,
            "time_to_max_r": max_r_time,
            "max_r": max_r,
            "r_at_15m": r_at_15m if r_at_15m is not None else max_r,
            "r_at_30m": r_at_30m if r_at_30m is not None else max_r,
            "r_at_60m": r_at_60m if r_at_60m is not None else max_r,
            "end_of_session_r": end_of_session_r if end_of_session_r is not None else max_r,
        }

    def test_single_day(self, trade_date: date) -> dict | None:
        levels = self.get_session_levels(trade_date)
        if not levels:
            return None

        scan_start = _dt_local(trade_date, 23, 0)
        scan_end = _dt_local(trade_date + timedelta(days=1), 2, 0)
        bars = self.get_bars(scan_start, scan_end)
        if not bars:
            return None

        upside = self.analyze_upside_cascade(trade_date, levels, bars)
        if upside:
            return upside

        downside = self.analyze_downside_cascade(trade_date, levels, bars)
        if downside:
            return downside

        return None

    def run_analysis(self, start_date: date, end_date: date):
        print("="*80)
        print("CASCADE TIMING ANALYSIS")
        print("="*80)
        print()
        print("Collecting timing metrics for all cascade trades...")
        print()

        trades = []
        cur = start_date

        while cur <= end_date:
            result = self.test_single_day(cur)
            if result:
                trades.append(result)
            cur += timedelta(days=1)

        if not trades:
            print("No trades found")
            return

        print(f"Total cascades: {len(trades)}")
        print()

        # Segment trades
        shorts = [t for t in trades if t["direction"] == "SHORT"]
        longs = [t for t in trades if t["direction"] == "LONG"]

        avg_gap_short = sum(t["cascade_gap"] for t in shorts) / len(shorts) if shorts else 0
        avg_gap_long = sum(t["cascade_gap"] for t in longs) / len(longs) if longs else 0

        short_large = [t for t in shorts if t["cascade_gap"] > avg_gap_short]
        short_small = [t for t in shorts if t["cascade_gap"] <= avg_gap_short]
        long_large = [t for t in longs if t["cascade_gap"] > avg_gap_long]
        long_small = [t for t in longs if t["cascade_gap"] <= avg_gap_long]

        segments = [
            ("SHORT (all)", shorts),
            ("SHORT (large gap)", short_large),
            ("SHORT (small gap)", short_small),
            ("LONG (all)", longs),
            ("LONG (large gap)", long_large),
            ("LONG (small gap)", long_small),
        ]

        for name, segment in segments:
            if not segment:
                continue

            print("="*80)
            print(f"{name} - {len(segment)} trades")
            print("="*80)
            print()

            # Q1: When do cascades start?
            entry_hours = [t["entry_hour"] for t in segment]
            avg_entry = sum(entry_hours) / len(entry_hours)
            print(f"Q1: WHEN DO CASCADES START?")
            print(f"  Average entry time: {int(avg_entry):02d}:{int((avg_entry % 1)*60):02d} local")

            # Entry clustering
            hour_buckets = defaultdict(int)
            for h in entry_hours:
                bucket = int(h)
                hour_buckets[bucket] += 1

            print(f"  Entry time distribution:")
            for hour in sorted(hour_buckets.keys()):
                count = hour_buckets[hour]
                pct = count / len(segment) * 100
                bar = "#" * int(pct / 5)
                print(f"    {hour:02d}:00 | {count:3d} ({pct:5.1f}%) {bar}")
            print()

            # Q2: When is max R made?
            times_to_max = [t["time_to_max_r"] for t in segment]
            avg_time_to_max = sum(times_to_max) / len(times_to_max)
            median_time_to_max = sorted(times_to_max)[len(times_to_max)//2]

            print(f"Q2: WHEN IS MAX R MADE?")
            print(f"  Average time to max R: {avg_time_to_max:.1f} minutes")
            print(f"  Median time to max R: {median_time_to_max:.1f} minutes")
            print()

            # Q3: When do they die? (R decay analysis)
            avg_15m = sum(t["r_at_15m"] for t in segment) / len(segment)
            avg_30m = sum(t["r_at_30m"] for t in segment) / len(segment)
            avg_60m = sum(t["r_at_60m"] for t in segment) / len(segment)
            avg_end = sum(t["end_of_session_r"] for t in segment) / len(segment)
            avg_max = sum(t["max_r"] for t in segment) / len(segment)

            print(f"Q3: WHEN DO THEY DIE? (R decay)")
            print(f"  Avg R at 15min: {avg_15m:+.2f}R ({avg_15m/avg_max*100:.0f}% of max)")
            print(f"  Avg R at 30min: {avg_30m:+.2f}R ({avg_30m/avg_max*100:.0f}% of max)")
            print(f"  Avg R at 60min: {avg_60m:+.2f}R ({avg_60m/avg_max*100:.0f}% of max)")
            print(f"  Avg R at session end (90min): {avg_end:+.2f}R ({avg_end/avg_max*100:.0f}% of max)")
            print(f"  Max R achieved: {avg_max:+.2f}R")
            print()

    def close(self):
        self.con.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("start_date", type=str)
    parser.add_argument("end_date", type=str, nargs="?", default=None)
    args = parser.parse_args()

    start = date.fromisoformat(args.start_date)
    end = date.fromisoformat(args.end_date) if args.end_date else start

    analysis = CascadeTimingAnalysis()
    analysis.run_analysis(start, end)
    analysis.close()
