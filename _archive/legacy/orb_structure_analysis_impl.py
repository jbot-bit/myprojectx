"""
ORB Structural Analysis - Implementation

Complete implementation of structural analysis framework.
1-minute data only, no optimization, pure descriptive statistics.
"""

import duckdb
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from collections import defaultdict
import statistics

DB_PATH = "gold.db"
SYMBOL = "MGC"
TICK_SIZE = 0.1
TZ_LOCAL = ZoneInfo("Australia/Brisbane")

# ORB times
ORB_TIMES = {
    "0900": (9, 0),
    "1000": (10, 0),
    "1100": (11, 0),
    "1800": (18, 0),
    "2300": (23, 0),
    "0030": (0, 30),
}

def get_orb_end_time(orb: str, d: date) -> datetime:
    """Get ORB end time (5 minutes after start)"""
    h, m = ORB_TIMES[orb]

    if orb == "0030":
        orb_date = d + timedelta(days=1)
    else:
        orb_date = d

    return datetime.combine(orb_date, datetime.min.time()).replace(hour=h, minute=m+5, tzinfo=TZ_LOCAL)


def get_scan_end_time(orb: str, d: date) -> datetime:
    """Get end of scanning period"""
    if orb in ("0900", "1000", "1100"):
        return datetime.combine(d, datetime.min.time()).replace(hour=17, tzinfo=TZ_LOCAL)
    if orb == "1800":
        return datetime.combine(d, datetime.min.time()).replace(hour=23, tzinfo=TZ_LOCAL)
    if orb == "2300":
        return datetime.combine(d + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=30, tzinfo=TZ_LOCAL)
    if orb == "0030":
        return datetime.combine(d + timedelta(days=1), datetime.min.time()).replace(hour=2, tzinfo=TZ_LOCAL)
    return datetime.combine(d, datetime.min.time()).replace(hour=23, minute=59, tzinfo=TZ_LOCAL)


def analyze_break_behavior_impl():
    """
    ANALYSIS 1: Break Behavior Classification

    For each ORB break, classify as:
    - HOLD: Price stays outside for 5+ consecutive minutes
    - FAIL: Price returns inside ORB within 5 minutes
    - REJECT: Closes outside then immediately (next bar) back inside

    Then measure what happens AFTER each type of event.
    """

    print("="*100)
    print("ANALYSIS 1: ORB BREAK BEHAVIOR (STRUCTURAL)")
    print("="*100)
    print()

    con = duckdb.connect(DB_PATH)

    # Load data
    daily_features = con.execute("""
        SELECT
            date_local,
            orb_0900_high, orb_0900_low,
            orb_1000_high, orb_1000_low,
            orb_1100_high, orb_1100_low,
            orb_1800_high, orb_1800_low,
            orb_2300_high, orb_2300_low,
            orb_0030_high, orb_0030_low
        FROM daily_features_v2
        WHERE orb_0900_high IS NOT NULL
        ORDER BY date_local
    """).fetchall()

    bars_1m = con.execute("""
        SELECT ts_utc, open, high, low, close
        FROM bars_1m
        WHERE symbol = ?
        ORDER BY ts_utc
    """, [SYMBOL]).fetchall()

    # Index bars by date
    bars_by_date = defaultdict(list)
    for bar in bars_1m:
        ts_utc = bar[0]
        if isinstance(ts_utc, str):
            ts_utc = datetime.fromisoformat(ts_utc.replace('Z', '+00:00'))

        ts_local = ts_utc.astimezone(TZ_LOCAL)
        bar_date = ts_local.date()

        bars_by_date[bar_date].append({
            'ts_local': ts_local,
            'open': bar[1],
            'high': bar[2],
            'low': bar[3],
            'close': bar[4]
        })

    for d in bars_by_date:
        bars_by_date[d].sort(key=lambda b: b['ts_local'])

    print(f"Loaded {len(daily_features)} days, {len(bars_1m):,} bars")
    print()

    # Analyze each ORB
    results_by_orb = {}

    for orb_code in ORB_TIMES.keys():
        print(f"Analyzing {orb_code} ORB...")

        orb_idx = list(ORB_TIMES.keys()).index(orb_code)

        breaks_hold = []
        breaks_fail = []
        breaks_reject = []

        for day_row in daily_features:
            date_local = day_row[0]
            orb_high = day_row[1 + orb_idx * 2]
            orb_low = day_row[2 + orb_idx * 2]

            if orb_high is None or orb_low is None:
                continue

            # Get bars after ORB formation
            orb_end = get_orb_end_time(orb_code, date_local)
            scan_end = get_scan_end_time(orb_code, date_local)

            day_bars = [b for b in bars_by_date[date_local]
                       if orb_end <= b['ts_local'] <= scan_end]

            if len(day_bars) < 10:  # Need at least 10 bars
                continue

            # Find first break
            first_break_idx = None
            break_direction = None

            for i, bar in enumerate(day_bars):
                if bar['close'] > orb_high:
                    first_break_idx = i
                    break_direction = "UP"
                    break
                elif bar['close'] < orb_low:
                    first_break_idx = i
                    break_direction = "DOWN"
                    break

            if first_break_idx is None:
                continue  # No break

            # Classify break behavior
            # Check next 5 bars
            next_5_bars = day_bars[first_break_idx+1:first_break_idx+6]

            if len(next_5_bars) < 5:
                continue

            # REJECT: Next bar immediately back inside
            next_bar = next_5_bars[0]
            if break_direction == "UP":
                if next_bar['close'] < orb_high:
                    breaks_reject.append({
                        'date': date_local,
                        'direction': break_direction,
                        'break_price': day_bars[first_break_idx]['close'],
                        'orb_high': orb_high,
                        'orb_low': orb_low
                    })
                    continue
            else:  # DOWN
                if next_bar['close'] > orb_low:
                    breaks_reject.append({
                        'date': date_local,
                        'direction': break_direction,
                        'break_price': day_bars[first_break_idx]['close'],
                        'orb_high': orb_high,
                        'orb_low': orb_low
                    })
                    continue

            # FAIL: Returns inside within 5 bars
            returns_inside = False
            for bar in next_5_bars:
                if break_direction == "UP":
                    if bar['close'] < orb_high:
                        returns_inside = True
                        break
                else:
                    if bar['close'] > orb_low:
                        returns_inside = True
                        break

            if returns_inside:
                breaks_fail.append({
                    'date': date_local,
                    'direction': break_direction,
                    'break_price': day_bars[first_break_idx]['close'],
                    'orb_high': orb_high,
                    'orb_low': orb_low
                })
                continue

            # HOLD: Stays outside for all 5 bars
            breaks_hold.append({
                'date': date_local,
                'direction': break_direction,
                'break_price': day_bars[first_break_idx]['close'],
                'orb_high': orb_high,
                'orb_low': orb_low,
                'bars_after': day_bars[first_break_idx+6:]  # Remaining bars for expectancy
            })

        results_by_orb[orb_code] = {
            'hold': breaks_hold,
            'fail': breaks_fail,
            'reject': breaks_reject
        }

    # Print results
    print()
    print("BREAK BEHAVIOR CLASSIFICATION:")
    print("-" * 100)
    print(f"{'ORB':<8} {'Total':<10} {'HOLD':<10} {'FAIL':<10} {'REJECT':<10} {'Hold%':<10}")
    print("-" * 100)

    for orb_code in ORB_TIMES.keys():
        r = results_by_orb[orb_code]
        total = len(r['hold']) + len(r['fail']) + len(r['reject'])
        if total > 0:
            hold_pct = 100.0 * len(r['hold']) / total
            print(f"{orb_code:<8} {total:<10} {len(r['hold']):<10} {len(r['fail']):<10} {len(r['reject']):<10} {hold_pct:<10.1f}")

    print()
    print("INTERPRETATION:")
    print("  - HOLD: Break is confirmed (price stays outside 5+ min)")
    print("  - FAIL: Break fails quickly (returns inside within 5 min)")
    print("  - REJECT: Immediate rejection (next bar back inside)")
    print()

    con.close()

    return results_by_orb


def analyze_time_decay_impl():
    """
    ANALYSIS 4: Time Decay of ORB Information

    Measure directional expectancy at different time windows:
    - 0-5 min after ORB
    - 5-15 min after ORB
    - 15-30 min after ORB

    Determines when ORB information becomes useless.
    """

    print()
    print("="*100)
    print("ANALYSIS 4: TIME DECAY OF ORB INFORMATION")
    print("="*100)
    print()

    con = duckdb.connect(DB_PATH)

    # Load data
    daily_features = con.execute("""
        SELECT
            date_local,
            orb_0900_high, orb_0900_low,
            orb_1000_high, orb_1000_low,
            orb_1100_high, orb_1100_low,
            orb_1800_high, orb_1800_low,
            orb_2300_high, orb_2300_low,
            orb_0030_high, orb_0030_low
        FROM daily_features_v2
        WHERE orb_0900_high IS NOT NULL
        ORDER BY date_local
    """).fetchall()

    bars_1m = con.execute("""
        SELECT ts_utc, open, high, low, close
        FROM bars_1m
        WHERE symbol = ?
        ORDER BY ts_utc
    """, [SYMBOL]).fetchall()

    # Index bars by date
    bars_by_date = defaultdict(list)
    for bar in bars_1m:
        ts_utc = bar[0]
        if isinstance(ts_utc, str):
            ts_utc = datetime.fromisoformat(ts_utc.replace('Z', '+00:00'))

        ts_local = ts_utc.astimezone(TZ_LOCAL)
        bar_date = ts_local.date()

        bars_by_date[bar_date].append({
            'ts_local': ts_local,
            'open': bar[1],
            'high': bar[2],
            'low': bar[3],
            'close': bar[4]
        })

    for d in bars_by_date:
        bars_by_date[d].sort(key=lambda b: b['ts_local'])

    print(f"Loaded {len(daily_features)} days")
    print()

    # Analyze each ORB
    results = {}

    for orb_code in ORB_TIMES.keys():
        print(f"Analyzing {orb_code} time decay...")

        orb_idx = list(ORB_TIMES.keys()).index(orb_code)

        window_0_5 = []
        window_5_15 = []
        window_15_30 = []

        for day_row in daily_features:
            date_local = day_row[0]
            orb_high = day_row[1 + orb_idx * 2]
            orb_low = day_row[2 + orb_idx * 2]

            if orb_high is None or orb_low is None:
                continue

            orb_mid = (orb_high + orb_low) / 2.0
            orb_end = get_orb_end_time(orb_code, date_local)
            scan_end = get_scan_end_time(orb_code, date_local)

            day_bars = [b for b in bars_by_date[date_local]
                       if orb_end <= b['ts_local'] <= scan_end]

            if len(day_bars) < 30:
                continue

            # Get price at ORB close (first bar after ORB)
            orb_close_price = day_bars[0]['close']

            # 0-5 min window
            if len(day_bars) >= 5:
                price_5min = day_bars[4]['close']
                move = (price_5min - orb_close_price) / TICK_SIZE
                window_0_5.append(move)

            # 5-15 min window
            if len(day_bars) >= 15:
                price_15min = day_bars[14]['close']
                move = (price_15min - orb_close_price) / TICK_SIZE
                window_5_15.append(move)

            # 15-30 min window
            if len(day_bars) >= 30:
                price_30min = day_bars[29]['close']
                move = (price_30min - orb_close_price) / TICK_SIZE
                window_15_30.append(move)

        results[orb_code] = {
            '0_5': window_0_5,
            '5_15': window_5_15,
            '15_30': window_15_30
        }

    # Print results
    print()
    print("TIME DECAY RESULTS:")
    print("-" * 100)
    print(f"{'ORB':<8} {'Window':<12} {'Samples':<10} {'Mean Move':<12} {'Std Dev':<12} {'Info?':<10}")
    print("-" * 100)

    for orb_code in ORB_TIMES.keys():
        r = results[orb_code]

        for window_name, window_data in [('0-5 min', r['0_5']), ('5-15 min', r['5_15']), ('15-30 min', r['15_30'])]:
            if len(window_data) > 0:
                mean_move = statistics.mean(window_data)
                std_dev = statistics.stdev(window_data) if len(window_data) > 1 else 0.0

                # Determine if information exists (|mean| > 0.5 * std_dev)
                has_info = "YES" if abs(mean_move) > 0.5 * std_dev else "NO"

                print(f"{orb_code:<8} {window_name:<12} {len(window_data):<10} {mean_move:+<12.2f} {std_dev:<12.2f} {has_info:<10}")

    print()
    print("INTERPRETATION:")
    print("  Mean Move: Average price movement (ticks) from ORB close")
    print("  Info?: YES if |mean| > 0.5 * std_dev (signal > noise)")
    print()
    print("If 'Info?' = NO for all windows, ORB provides no directional edge.")
    print()

    con.close()

    return results


if __name__ == "__main__":
    print("ORB STRUCTURAL ANALYSIS - IMPLEMENTATION")
    print("="*100)
    print()
    print("Running structural analyses (no optimization, pure descriptive stats):")
    print()

    # Run analyses
    break_results = analyze_break_behavior_impl()
    time_decay_results = analyze_time_decay_impl()

    print()
    print("="*100)
    print("ANALYSIS COMPLETE")
    print("="*100)
    print()
    print("Review results above to determine if ORB has structural edge.")
    print("If no clear patterns emerge, ORB may not be useful for this market.")
