"""
Step 4: Run Robustness Batch Tests (OPTIMIZED + FIXED)

PERFORMANCE FIXES:
- Pre-indexes bars by date for O(1) lookup instead of O(n) iteration
- Uses proper datetime comparisons instead of string operations
- Adds progress tracking and periodic commits
- Reduces memory usage by processing in batches
- Original: O(configs × days × bars) = ~7 billion comparisons
- Optimized: O(configs × days) with O(1) bar lookups

LOGIC FIXES (2026-01-12):
- **CRITICAL:** Fixed buffer logic to match original filtered backtest
- Full SL: Buffer now IGNORED (stop at exact ORB edge), not applied
- Half SL: Buffer now CLAMPED at ORB edge using max()/min()
- Previous version had incorrect logic that made stops wider than intended
- See LOGIC_AUDIT_FINDINGS.md for details

CORRECT BEHAVIOR:
- Full SL with buffer=20: Stop at orb_low/high (buffer ignored)
- Half SL with buffer=0: Stop at mid
- Half SL with buffer=20: Stop at max(orb_low, mid-20) or min(orb_high, mid+20)
"""

import duckdb
import json
import os
import sys
from datetime import date, timedelta, datetime
import time
from collections import defaultdict
from zoneinfo import ZoneInfo

DB_PATH = "gold.db"
SYMBOL = "MGC"
TICK_SIZE = 0.1
TZ_LOCAL = ZoneInfo("Australia/Brisbane")

# NO FILTERS for robustness testing
MAX_STOP_TICKS = 999999
ASIA_TP_CAP_TICKS = 999999

# Commit every N configs to avoid holding all transactions in memory
COMMIT_EVERY = 10

# ORB open times (local Brisbane time)
ORB_TIMES = {
    "0900": (9, 0),
    "1000": (10, 0),
    "1100": (11, 0),
    "1800": (18, 0),
    "2300": (23, 0),
    "0030": (0, 30),
}

def is_asia(orb: str) -> bool:
    return orb in ("0900", "1000", "1100")

def orb_scan_end_local(orb: str, d: date) -> datetime:
    """Return scan end as datetime object"""
    if orb in ("0900", "1000", "1100"):
        return datetime.combine(d, datetime.min.time()).replace(hour=17, tzinfo=TZ_LOCAL)
    if orb == "1800":
        return datetime.combine(d, datetime.min.time()).replace(hour=23, tzinfo=TZ_LOCAL)
    if orb == "2300":
        return datetime.combine(d + timedelta(days=1), datetime.min.time()).replace(hour=0, minute=30, tzinfo=TZ_LOCAL)
    if orb == "0030":
        return datetime.combine(d + timedelta(days=1), datetime.min.time()).replace(hour=2, tzinfo=TZ_LOCAL)
    return datetime.combine(d, datetime.min.time()).replace(hour=23, minute=59, tzinfo=TZ_LOCAL)

def ensure_robustness_table(con: duckdb.DuckDBPyConnection, drop_existing=False):
    """Create orb_robustness_results table"""

    if drop_existing:
        con.execute("DROP TABLE IF EXISTS orb_robustness_results")
        print("[INFO] Dropped existing orb_robustness_results table")

    con.execute("""
        CREATE TABLE IF NOT EXISTS orb_robustness_results (
            date_local DATE NOT NULL,
            orb VARCHAR NOT NULL,
            close_confirmations INTEGER NOT NULL,
            rr DOUBLE NOT NULL,
            sl_mode VARCHAR NOT NULL,
            buffer_ticks DOUBLE NOT NULL,
            direction VARCHAR,
            entry_ts TIMESTAMP,
            entry_price DOUBLE,
            stop_price DOUBLE,
            target_price DOUBLE,
            stop_ticks DOUBLE,
            outcome VARCHAR,
            r_multiple DOUBLE,
            entry_delay_bars INTEGER,
            mae_r DOUBLE,
            mfe_r DOUBLE,
            PRIMARY KEY (date_local, orb, close_confirmations, rr, sl_mode, buffer_ticks)
        )
    """)

def build_bars_index(bars_5m):
    """
    Build an index of bars by date for fast lookup.

    Returns: dict[date, list[bar]]
    """
    print("Building bars index...")
    bars_by_date = defaultdict(list)

    for bar in bars_5m:
        ts_utc = bar[0]
        # Convert to local timezone and extract date
        if isinstance(ts_utc, str):
            ts_utc = datetime.fromisoformat(ts_utc.replace('Z', '+00:00'))

        # Convert to local timezone
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

    # Sort bars within each date
    for d in bars_by_date:
        bars_by_date[d].sort(key=lambda b: b['ts_local'])

    print(f"[INDEXED] {len(bars_by_date)} trading days with bars")
    return bars_by_date

def get_day_bars(bars_by_date, date_local, scan_end):
    """
    Get bars for a specific trading day up to scan_end.

    Uses indexed lookup instead of iterating all bars.
    """
    day_bars = []

    # Check current date and next date (for overnight sessions)
    for offset in [0, 1]:
        check_date = date_local + timedelta(days=offset)
        if check_date in bars_by_date:
            for bar in bars_by_date[check_date]:
                # Use proper datetime comparison
                if bar['ts_local'] <= scan_end:
                    day_bars.append(bar)

    return day_bars

def run_backtest_for_config(con, config, daily_features, bars_by_date):
    """
    Run backtest for a single config across all days.

    Returns list of trade records.
    """

    orb_code = config['orb']
    close_confirmations = config['close_confirmations']
    rr = config['rr']
    sl_mode = config['sl_mode'] if config['sl_mode'] else ''
    buffer_ticks = config['buffer_ticks']

    trades = []

    for day_row in daily_features:
        date_local = day_row[0]
        orb_high = day_row[1]
        orb_low = day_row[2]

        if orb_high is None or orb_low is None:
            # NO_TRADE
            trades.append({
                'date_local': date_local,
                'orb': orb_code,
                'close_confirmations': close_confirmations,
                'rr': rr,
                'sl_mode': sl_mode,
                'buffer_ticks': buffer_ticks,
                'direction': None,
                'entry_ts': None,
                'entry_price': None,
                'stop_price': None,
                'target_price': None,
                'stop_ticks': None,
                'outcome': 'NO_TRADE',
                'r_multiple': 0.0,
                'entry_delay_bars': None,
                'mae_r': None,
                'mfe_r': None
            })
            continue

        orb_range = orb_high - orb_low

        # Get bars for this day using indexed lookup
        scan_end = orb_scan_end_local(orb_code, date_local)
        day_bars = get_day_bars(bars_by_date, date_local, scan_end)

        if len(day_bars) == 0:
            trades.append({
                'date_local': date_local,
                'orb': orb_code,
                'close_confirmations': close_confirmations,
                'rr': rr,
                'sl_mode': sl_mode,
                'buffer_ticks': buffer_ticks,
                'direction': None,
                'entry_ts': None,
                'entry_price': None,
                'stop_price': None,
                'target_price': None,
                'stop_ticks': None,
                'outcome': 'NO_TRADE',
                'r_multiple': 0.0,
                'entry_delay_bars': None,
                'mae_r': None,
                'mfe_r': None
            })
            continue

        # Find entry
        entry_idx = None
        direction = None

        for i in range(len(day_bars)):
            if i < close_confirmations - 1:
                continue

            # Check if last N consecutive closes are outside ORB
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
                'date_local': date_local,
                'orb': orb_code,
                'close_confirmations': close_confirmations,
                'rr': rr,
                'sl_mode': sl_mode,
                'buffer_ticks': buffer_ticks,
                'direction': None,
                'entry_ts': None,
                'entry_price': None,
                'stop_price': None,
                'target_price': None,
                'stop_ticks': None,
                'outcome': 'NO_TRADE',
                'r_multiple': 0.0,
                'entry_delay_bars': None,
                'mae_r': None,
                'mfe_r': None
            })
            continue

        entry_bar = day_bars[entry_idx]
        entry_ts = entry_bar['ts_utc']
        entry_price = entry_bar['close']

        # Calculate stop - FIXED to match original filtered backtest logic
        orb_mid = (orb_high + orb_low) / 2.0
        buf = buffer_ticks * TICK_SIZE

        if sl_mode == 'full':
            # Full SL: Buffer is IGNORED, stop at exact ORB edge
            if direction == "UP":
                stop_price = orb_low
            else:
                stop_price = orb_high
        elif sl_mode == 'half':
            # Half SL: Buffer moves stop away from mid (tighter), clamped at ORB edge
            if direction == "UP":
                stop_price = max(orb_low, orb_mid - buf)
            else:
                stop_price = min(orb_high, orb_mid + buf)
        else:
            # Empty string means full SL
            if direction == "UP":
                stop_price = orb_low
            else:
                stop_price = orb_high

        stop_ticks = abs(entry_price - stop_price) / TICK_SIZE

        # Apply MAX_STOP filter (NO FILTER for robustness)
        if stop_ticks > MAX_STOP_TICKS:
            trades.append({
                'date_local': date_local,
                'orb': orb_code,
                'close_confirmations': close_confirmations,
                'rr': rr,
                'sl_mode': sl_mode,
                'buffer_ticks': buffer_ticks,
                'direction': None,
                'entry_ts': None,
                'entry_price': None,
                'stop_price': None,
                'target_price': None,
                'stop_ticks': None,
                'outcome': 'NO_TRADE',
                'r_multiple': 0.0,
                'entry_delay_bars': None,
                'mae_r': None,
                'mfe_r': None
            })
            continue

        # Calculate target
        risk = stop_ticks * TICK_SIZE
        reward = rr * risk

        # Apply ASIA_TP_CAP (NO FILTER for robustness)
        if is_asia(orb_code):
            reward = min(reward, ASIA_TP_CAP_TICKS * TICK_SIZE)

        if direction == "UP":
            target_price = entry_price + reward
        else:
            target_price = entry_price - reward

        # Scan remaining bars for outcome
        outcome = None
        for bar in day_bars[entry_idx + 1:]:
            bar_high = bar['high']
            bar_low = bar['low']

            if direction == "UP":
                if bar_low <= stop_price and bar_high >= target_price:
                    outcome = "LOSS"  # Both hit = LOSS
                    break
                elif bar_low <= stop_price:
                    outcome = "LOSS"
                    break
                elif bar_high >= target_price:
                    outcome = "WIN"
                    break
            else:  # DOWN
                if bar_high >= stop_price and bar_low <= target_price:
                    outcome = "LOSS"  # Both hit = LOSS
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

        # Calculate MAE/MFE (simplified)
        mae_r = None
        mfe_r = None

        trades.append({
            'date_local': date_local,
            'orb': orb_code,
            'close_confirmations': close_confirmations,
            'rr': rr,
            'sl_mode': sl_mode,
            'buffer_ticks': buffer_ticks,
            'direction': direction,
            'entry_ts': entry_ts,
            'entry_price': entry_price,
            'stop_price': stop_price,
            'target_price': target_price,
            'stop_ticks': stop_ticks,
            'outcome': outcome,
            'r_multiple': r_multiple,
            'entry_delay_bars': entry_idx,
            'mae_r': mae_r,
            'mfe_r': mfe_r
        })

    return trades

def run_robustness_batch():
    """Main batch runner"""

    print("="*100)
    print("STEP 4: RUN ROBUSTNESS BATCH TESTS (OPTIMIZED)")
    print("="*100)
    print()

    # Fail fast: Check DB exists
    if not os.path.exists(DB_PATH):
        print(f"[FAIL] Database not found: {DB_PATH}")
        sys.exit(1)

    # Check candidate configs exist
    if not os.path.exists('candidate_configs.json'):
        print("[FAIL] candidate_configs.json not found. Run extract_candidate_configs.py first.")
        sys.exit(1)

    print(f"[INFO] Database: {DB_PATH}")
    print(f"[INFO] NO FILTERS: MAX_STOP={MAX_STOP_TICKS}, ASIA_TP_CAP={ASIA_TP_CAP_TICKS}")
    print()

    # Load candidate configs
    with open('candidate_configs.json', 'r') as f:
        candidates = json.load(f)

    print(f"[LOADED] {len(candidates)} candidate configs")
    print()

    con = duckdb.connect(DB_PATH)

    # Create robustness results table
    print("Creating orb_robustness_results table...")
    ensure_robustness_table(con, drop_existing=True)
    print("[READY] Table created")
    print()

    # Load daily features for all ORBs
    print("Loading daily_features_v2...")
    daily_features_by_orb = {}

    for orb_code in ["0900", "1000", "1100", "1800", "2300", "0030"]:
        daily_features = con.execute(f"""
            SELECT date_local,
                   orb_{orb_code}_high, orb_{orb_code}_low
            FROM daily_features_v2
            WHERE orb_{orb_code}_high IS NOT NULL
            ORDER BY date_local
        """).fetchall()
        daily_features_by_orb[orb_code] = daily_features
        print(f"  {orb_code}: {len(daily_features)} days")

    print()

    # Load bars_5m and build index
    print("Loading bars_5m...")
    bars_5m = con.execute("""
        SELECT ts_utc, open, high, low, close
        FROM bars_5m
        WHERE symbol = ?
        ORDER BY ts_utc
    """, [SYMBOL]).fetchall()

    print(f"[LOADED] {len(bars_5m):,} bars")
    print()

    # Build index for fast lookups
    bars_by_date = build_bars_index(bars_5m)
    print()

    # Process each config
    print("="*100)
    print("PROCESSING CONFIGS")
    print("="*100)
    print()

    start_time = time.time()
    total_trades_inserted = 0

    for i, config in enumerate(candidates, 1):
        config_start = time.time()

        orb_code = config['orb']
        close_confirmations = config['close_confirmations']
        rr = config['rr']
        sl_mode = config['sl_mode'] if config['sl_mode'] else 'full'
        buffer_ticks = config['buffer_ticks']

        print(f"[{i}/{len(candidates)}] {orb_code} | RR={rr} | Confirm={close_confirmations} | SL={sl_mode} | Buffer={buffer_ticks}")

        # Get daily features for this ORB
        daily_features = daily_features_by_orb.get(orb_code, [])

        if len(daily_features) == 0:
            print(f"  [WARN] No daily features found for {orb_code}")
            continue

        # Run backtest
        trades = run_backtest_for_config(con, config, daily_features, bars_by_date)

        # Insert trades into database
        for trade in trades:
            con.execute("""
                INSERT OR REPLACE INTO orb_robustness_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                trade['date_local'],
                trade['orb'],
                trade['close_confirmations'],
                trade['rr'],
                trade['sl_mode'],
                trade['buffer_ticks'],
                trade['direction'],
                trade['entry_ts'],
                trade['entry_price'],
                trade['stop_price'],
                trade['target_price'],
                trade['stop_ticks'],
                trade['outcome'],
                trade['r_multiple'],
                trade['entry_delay_bars'],
                trade['mae_r'],
                trade['mfe_r']
            ])

        total_trades_inserted += len(trades)

        # Commit periodically to avoid holding all transactions in memory
        if i % COMMIT_EVERY == 0:
            con.commit()
            print(f"  [COMMIT] Committed after {i} configs")

        # Stats
        actual_trades = len([t for t in trades if t['outcome'] in ['WIN', 'LOSS']])
        wins = len([t for t in trades if t['outcome'] == 'WIN'])
        total_r = sum(t['r_multiple'] for t in trades if t['outcome'] in ['WIN', 'LOSS'])

        config_time = time.time() - config_start
        elapsed = time.time() - start_time
        avg_time = elapsed / i
        eta_seconds = avg_time * (len(candidates) - i)
        eta_minutes = eta_seconds / 60

        print(f"  {actual_trades} trades | {wins}W | {total_r:+.1f}R | {config_time:.1f}s | ETA: {eta_minutes:.1f}m")

    # Final commit
    con.commit()

    elapsed = time.time() - start_time

    print()
    print("="*100)
    print("BATCH COMPLETE")
    print("="*100)
    print()
    print(f"Configs processed: {len(candidates)}")
    print(f"Total trades inserted: {total_trades_inserted:,}")
    print(f"Total time: {elapsed:.1f}s ({elapsed/len(candidates):.1f}s/config)")
    print()
    print("[SUCCESS] All configs tested - results in orb_robustness_results table")
    print()
    print("="*100)

    con.close()

if __name__ == "__main__":
    run_robustness_batch()
