"""
Step 4: Run Robustness Batch Tests

Loads candidate configs and runs no-max backtest (MAX_STOP=999999, ASIA_TP_CAP=999999)
for each config. Writes results to orb_robustness_results table.

This is essentially the same backtest logic as backtest_orb_exec_5mhalfsl.py but:
- Runs programmatically (not CLI)
- No filters (MAX_STOP=999999, ASIA_TP_CAP=999999)
- Batch processes all candidate configs
"""

import duckdb
import json
import os
import sys
from datetime import date, timedelta, datetime
import time

DB_PATH = "gold.db"
SYMBOL = "MGC"
TICK_SIZE = 0.1

# NO FILTERS for robustness testing
MAX_STOP_TICKS = 999999
ASIA_TP_CAP_TICKS = 999999

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

def orb_scan_end_local(orb: str, d: date) -> str:
    if orb in ("0900", "1000", "1100"):
        return f"{d} 17:00:00"
    if orb == "1800":
        return f"{d} 23:00:00"
    if orb == "2300":
        return f"{d + timedelta(days=1)} 00:30:00"
    if orb == "0030":
        return f"{d + timedelta(days=1)} 02:00:00"
    return f"{d} 23:59:00"

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

def run_backtest_for_config(con, config, daily_features, bars_5m):
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

        # Get bars for this day
        scan_end_str = orb_scan_end_local(orb_code, date_local)
        # Filter bars: timestamp starts with date_local string (e.g., "2024-01-02")
        # We use string comparison since timestamps are already formatted correctly
        day_bars = [b for b in bars_5m
                    if str(b[0]).startswith(str(date_local)) and str(b[0]) <= scan_end_str]

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
            all_above = all(day_bars[i - j][4] > orb_high for j in range(close_confirmations))
            all_below = all(day_bars[i - j][4] < orb_low for j in range(close_confirmations))

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
        entry_ts = entry_bar[0]
        entry_price = entry_bar[4]  # close price

        # Calculate stop
        if sl_mode == 'half':
            orb_mid = (orb_high + orb_low) / 2.0
            if direction == "UP":
                stop_price = orb_mid - buffer_ticks * TICK_SIZE
            else:
                stop_price = orb_mid + buffer_ticks * TICK_SIZE
        else:  # full
            if direction == "UP":
                stop_price = orb_low - buffer_ticks * TICK_SIZE
            else:
                stop_price = orb_high + buffer_ticks * TICK_SIZE

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
            bar_high = bar[2]
            bar_low = bar[3]

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
    print("STEP 4: RUN ROBUSTNESS BATCH TESTS")
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

    # Load daily features and bars_5m once (for performance)
    print("Loading daily_features_v2...")
    daily_features_query = """
        SELECT date_local,
               orb_{orb}_high, orb_{orb}_low
        FROM daily_features_v2
        WHERE orb_{orb}_high IS NOT NULL
        ORDER BY date_local
    """

    print("Loading bars_5m...")
    bars_5m = con.execute("""
        SELECT ts_utc, open, high, low, close
        FROM bars_5m
        WHERE symbol = ?
        ORDER BY ts_utc
    """, [SYMBOL]).fetchall()

    print(f"[LOADED] {len(bars_5m):,} bars")
    print()

    # Process each config
    print("="*100)
    print("PROCESSING CONFIGS")
    print("="*100)
    print()

    start_time = time.time()

    for i, config in enumerate(candidates, 1):
        config_start = time.time()

        orb_code = config['orb']
        close_confirmations = config['close_confirmations']
        rr = config['rr']
        sl_mode = config['sl_mode'] if config['sl_mode'] else 'full'
        buffer_ticks = config['buffer_ticks']

        print(f"[{i}/{len(candidates)}] {orb_code} | RR={rr} | Confirm={close_confirmations} | SL={sl_mode} | Buffer={buffer_ticks}")

        # Load daily features for this ORB
        daily_features = con.execute(
            daily_features_query.format(orb=orb_code),
        ).fetchall()

        if len(daily_features) == 0:
            print(f"  [WARN] No daily features found for {orb_code}")
            continue

        # Run backtest
        trades = run_backtest_for_config(con, config, daily_features, bars_5m)

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

        # Stats
        actual_trades = len([t for t in trades if t['outcome'] in ['WIN', 'LOSS']])
        wins = len([t for t in trades if t['outcome'] == 'WIN'])
        total_r = sum(t['r_multiple'] for t in trades if t['outcome'] in ['WIN', 'LOSS'])

        config_time = time.time() - config_start

        print(f"  {actual_trades} trades | {wins}W | {total_r:+.1f}R | {config_time:.1f}s")

    elapsed = time.time() - start_time

    print()
    print("="*100)
    print("BATCH COMPLETE")
    print("="*100)
    print()
    print(f"Configs processed: {len(candidates)}")
    print(f"Total time: {elapsed:.1f}s ({elapsed/len(candidates):.1f}s/config)")
    print()
    print("[SUCCESS] All configs tested - results in orb_robustness_results table")
    print()
    print("="*100)

    con.close()

if __name__ == "__main__":
    run_robustness_batch()
