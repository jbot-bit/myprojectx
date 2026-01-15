"""
Search for Unfiltered Edge: 1800 ORB Low R:R Sweep

Based on robustness findings:
- 1800 ORB performed 10x better than 1000 ORB
- Lower R:R ratios showed progressively better performance
- Half SL and 1 confirmation performed best

This script tests 1800 ORB with:
- R:R: 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0
- Confirmations: 1 only
- SL mode: half only
- Buffers: 0, 2, 5, 10, 15, 20

Total: 42 configs
Goal: Find configs with POSITIVE expectancy without filters
"""

import duckdb
import time
from datetime import date, timedelta, datetime
from collections import defaultdict
from zoneinfo import ZoneInfo

DB_PATH = "gold.db"
SYMBOL = "MGC"
TICK_SIZE = 0.1
TZ_LOCAL = ZoneInfo("Australia/Brisbane")

# NO FILTERS
MAX_STOP_TICKS = 999999
ASIA_TP_CAP_TICKS = 999999

# Test parameters
ORB = "1800"
RR_RATIOS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
CLOSE_CONFIRMATIONS = [1]
SL_MODES = ["half"]
BUFFERS = [0.0, 2.0, 5.0, 10.0, 15.0, 20.0]

def orb_scan_end_local(orb: str, d: date) -> datetime:
    """Return scan end as datetime object"""
    if orb == "1800":
        return datetime.combine(d, datetime.min.time()).replace(hour=23, tzinfo=TZ_LOCAL)
    return datetime.combine(d, datetime.min.time()).replace(hour=23, minute=59, tzinfo=TZ_LOCAL)

def build_bars_index(bars_5m):
    """Build an index of bars by date for fast lookup"""
    print("Building bars index...")
    bars_by_date = defaultdict(list)

    for bar in bars_5m:
        ts_utc = bar[0]
        if isinstance(ts_utc, str):
            ts_utc = datetime.fromisoformat(ts_utc.replace('Z', '+00:00'))

        ts_local = ts_utc.astimezone(TZ_LOCAL)
        bar_date = ts_local.date()

        bars_by_date[bar_date].append({
            'ts_utc': ts_utc,
            'ts_local': ts_local,
            'open': bar[1],
            'high': bar[2],
            'low': bar[3],
            'close': bar[4]
        })

    for d in bars_by_date:
        bars_by_date[d].sort(key=lambda b: b['ts_local'])

    print(f"[INDEXED] {len(bars_by_date)} trading days")
    return bars_by_date

def get_day_bars(bars_by_date, date_local, scan_end):
    """Get bars for a specific trading day up to scan_end"""
    day_bars = []

    for offset in [0, 1]:
        check_date = date_local + timedelta(days=offset)
        if check_date in bars_by_date:
            for bar in bars_by_date[check_date]:
                if bar['ts_local'] <= scan_end:
                    day_bars.append(bar)

    return day_bars

def run_backtest_for_config(config, daily_features, bars_by_date):
    """Run backtest for a single config"""

    orb_code = config['orb']
    close_confirmations = config['close_confirmations']
    rr = config['rr']
    sl_mode = config['sl_mode']
    buffer_ticks = config['buffer_ticks']

    trades = []

    for day_row in daily_features:
        date_local = day_row[0]
        orb_high = day_row[1]
        orb_low = day_row[2]

        if orb_high is None or orb_low is None:
            trades.append({
                'outcome': 'NO_TRADE',
                'r_multiple': 0.0
            })
            continue

        scan_end = orb_scan_end_local(orb_code, date_local)
        day_bars = get_day_bars(bars_by_date, date_local, scan_end)

        if len(day_bars) == 0:
            trades.append({
                'outcome': 'NO_TRADE',
                'r_multiple': 0.0
            })
            continue

        # Find entry
        entry_idx = None
        direction = None

        for i in range(len(day_bars)):
            if i < close_confirmations - 1:
                continue

            all_above = all(day_bars[i - j]['close'] > orb_high for j in range(close_confirmations))
            all_below = all(day_bars[i - j]['close'] < orb_low for j in range(close_confirmations))

            if all_above:
                direction = "UP"
                entry_idx = i
                break
            elif all_below:
                direction = "DOWN"
                entry_idx = i
                break

        if entry_idx is None:
            trades.append({
                'outcome': 'NO_TRADE',
                'r_multiple': 0.0
            })
            continue

        entry_bar = day_bars[entry_idx]
        entry_price = entry_bar['close']

        # Calculate stop
        orb_mid = (orb_high + orb_low) / 2.0
        if direction == "UP":
            stop_price = orb_mid - buffer_ticks * TICK_SIZE
        else:
            stop_price = orb_mid + buffer_ticks * TICK_SIZE

        stop_ticks = abs(entry_price - stop_price) / TICK_SIZE

        if stop_ticks > MAX_STOP_TICKS:
            trades.append({
                'outcome': 'NO_TRADE',
                'r_multiple': 0.0
            })
            continue

        # Calculate target
        risk = stop_ticks * TICK_SIZE
        reward = rr * risk

        if direction == "UP":
            target_price = entry_price + reward
        else:
            target_price = entry_price - reward

        # Scan for outcome
        outcome = None
        for bar in day_bars[entry_idx + 1:]:
            bar_high = bar['high']
            bar_low = bar['low']

            if direction == "UP":
                if bar_low <= stop_price and bar_high >= target_price:
                    outcome = "LOSS"
                    break
                elif bar_low <= stop_price:
                    outcome = "LOSS"
                    break
                elif bar_high >= target_price:
                    outcome = "WIN"
                    break
            else:
                if bar_high >= stop_price and bar_low <= target_price:
                    outcome = "LOSS"
                    break
                elif bar_high >= stop_price:
                    outcome = "LOSS"
                    break
                elif bar_low <= target_price:
                    outcome = "WIN"
                    break

        if outcome is None:
            outcome = "NO_TRADE"

        # Calculate R-multiple
        if outcome == "WIN":
            r_multiple = rr
        elif outcome == "LOSS":
            r_multiple = -1.0
        else:
            r_multiple = 0.0

        trades.append({
            'outcome': outcome,
            'r_multiple': r_multiple
        })

    return trades

def search_1800_low_rr():
    """Main search function"""

    print("="*100)
    print("SEARCH FOR UNFILTERED EDGE: 1800 ORB LOW R:R SWEEP")
    print("="*100)
    print()

    con = duckdb.connect(DB_PATH)

    # Generate configs
    configs = []
    for rr in RR_RATIOS:
        for cc in CLOSE_CONFIRMATIONS:
            for sl_mode in SL_MODES:
                for buffer in BUFFERS:
                    configs.append({
                        'orb': ORB,
                        'close_confirmations': cc,
                        'rr': rr,
                        'sl_mode': sl_mode,
                        'buffer_ticks': buffer
                    })

    print(f"Testing {len(configs)} configs:")
    print(f"  ORB: {ORB}")
    print(f"  R:R ratios: {RR_RATIOS}")
    print(f"  Confirmations: {CLOSE_CONFIRMATIONS}")
    print(f"  SL modes: {SL_MODES}")
    print(f"  Buffers: {BUFFERS}")
    print()

    # Load daily features
    print("Loading daily features...")
    daily_features = con.execute(f"""
        SELECT date_local, orb_{ORB}_high, orb_{ORB}_low
        FROM daily_features_v2
        WHERE orb_{ORB}_high IS NOT NULL
        ORDER BY date_local
    """).fetchall()
    print(f"[LOADED] {len(daily_features)} days")
    print()

    # Load bars
    print("Loading bars...")
    bars_5m = con.execute("""
        SELECT ts_utc, open, high, low, close
        FROM bars_5m
        WHERE symbol = ?
        ORDER BY ts_utc
    """, [SYMBOL]).fetchall()
    print(f"[LOADED] {len(bars_5m):,} bars")
    print()

    # Build index
    bars_by_date = build_bars_index(bars_5m)
    print()

    # Process configs
    print("="*100)
    print("TESTING CONFIGS")
    print("="*100)
    print()

    results = []
    start_time = time.time()

    for i, config in enumerate(configs, 1):
        config_start = time.time()

        trades = run_backtest_for_config(config, daily_features, bars_by_date)

        actual_trades = len([t for t in trades if t['outcome'] in ['WIN', 'LOSS']])
        wins = len([t for t in trades if t['outcome'] == 'WIN'])
        losses = len([t for t in trades if t['outcome'] == 'LOSS'])
        total_r = sum(t['r_multiple'] for t in trades if t['outcome'] in ['WIN', 'LOSS'])

        win_rate = 100.0 * wins / actual_trades if actual_trades > 0 else 0.0
        avg_r = total_r / actual_trades if actual_trades > 0 else 0.0

        config_time = time.time() - config_start
        elapsed = time.time() - start_time
        avg_time = elapsed / i
        eta_seconds = avg_time * (len(configs) - i)
        eta_minutes = eta_seconds / 60

        status = "POSITIVE!" if total_r > 0 else ""

        print(f"[{i}/{len(configs)}] RR={config['rr']:.2f} | Buffer={config['buffer_ticks']:.0f} | "
              f"{actual_trades}T {wins}W {losses}L | WR={win_rate:.1f}% | {total_r:+.1f}R | "
              f"{config_time:.1f}s | ETA:{eta_minutes:.1f}m {status}")

        results.append({
            'config': config,
            'trades': actual_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_r': total_r,
            'avg_r': avg_r
        })

    con.close()

    # Summary
    print()
    print("="*100)
    print("RESULTS SUMMARY")
    print("="*100)
    print()

    # Sort by total R
    results.sort(key=lambda x: x['total_r'], reverse=True)

    print("TOP 10 CONFIGS:")
    print("-" * 100)
    for i, r in enumerate(results[:10], 1):
        c = r['config']
        print(f"{i:2d}. RR={c['rr']:.2f} Buf={c['buffer_ticks']:.0f} | "
              f"{r['trades']}T {r['wins']}W {r['losses']}L | WR={r['win_rate']:.1f}% | "
              f"{r['total_r']:+.1f}R | Avg={r['avg_r']:+.3f}R")
    print()

    # Positive expectancy configs
    positive = [r for r in results if r['total_r'] > 0]

    if len(positive) > 0:
        print(f"SUCCESS! Found {len(positive)} configs with POSITIVE EXPECTANCY:")
        print("-" * 100)
        for r in positive:
            c = r['config']
            print(f"  RR={c['rr']:.2f} Buf={c['buffer_ticks']:.0f} | "
                  f"{r['trades']}T {r['wins']}W {r['losses']}L | WR={r['win_rate']:.1f}% | "
                  f"{r['total_r']:+.1f}R | Avg={r['avg_r']:+.3f}R")
        print()
    else:
        print("NO POSITIVE EXPECTANCY CONFIGS FOUND")
        print("All 1800 ORB configs with low R:R ratios still lose money.")
        print()
        print("Recommendation: Try Option D (rethink strategy entirely)")
        print()

    elapsed = time.time() - start_time
    print(f"Total time: {elapsed:.1f}s ({elapsed/len(configs):.1f}s/config)")
    print("="*100)

if __name__ == "__main__":
    search_1800_low_rr()
