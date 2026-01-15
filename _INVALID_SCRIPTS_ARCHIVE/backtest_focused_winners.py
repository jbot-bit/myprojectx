"""
Focused Backtest - Winners Only

Based on initial 104-variant test results, this tests refined variations
of ONLY the profitable sessions with optimized parameters.

Focus Sessions:
- 10:00 ORB (+71R baseline)
- 18:00 ORB (+60R baseline)
- 11:00 ORB (+13R baseline)
- 00:30 ORB (+13R baseline)

NO FILTERS: Removed MAX_STOP and ASIA_TP_CAP to test full potential
"""

import duckdb
import argparse
from datetime import date, timedelta

DB_PATH = "gold.db"
SYMBOL = "MGC"
TICK_SIZE = 0.1

# NO FILTERS (testing full range)
MAX_STOP_TICKS = 999999
ASIA_TP_CAP_TICKS = 999999

# Focused sessions only
FOCUS_SESSIONS = {
    "1000": (10, 0),  # Best performer
    "1800": (18, 0),  # Second best
    "1100": (11, 0),  # Moderate
    "0030": (0, 30),  # Moderate
}

def is_asia(orb: str) -> bool:
    return orb in ("1000", "1100")

def orb_scan_end_local(orb: str, d: date) -> str:
    if orb in ("1000", "1100"):
        return f"{d} 17:00:00"
    if orb == "1800":
        return f"{d} 23:00:00"
    if orb == "0030":
        return f"{d + timedelta(days=1)} 02:00:00"
    return f"{d} 23:59:00"

def ensure_schema(con: duckdb.DuckDBPyConnection):
    con.execute("""
        CREATE TABLE IF NOT EXISTS orb_trades_focused (
            date_local DATE NOT NULL,
            orb VARCHAR NOT NULL,
            close_confirmations INTEGER NOT NULL,
            rr DOUBLE NOT NULL,
            exec_timeframe VARCHAR NOT NULL,  -- '1m' or '5m'
            sl_mode VARCHAR,                  -- 'full', 'half', or NULL
            buffer_ticks DOUBLE,

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

            PRIMARY KEY (date_local, orb, close_confirmations, rr, exec_timeframe, sl_mode, buffer_ticks)
        )
    """)

def run_backtest(
    orb: str,
    close_confirmations: int,
    rr: float,
    exec_timeframe: str = "5m",  # '1m' or '5m'
    sl_mode: str = None,          # 'full', 'half', or None
    buffer_ticks: float = 0,
    commit_every_days: int = 50
):
    con = duckdb.connect(DB_PATH)
    ensure_schema(con)

    # Get ORB data
    h, m = FOCUS_SESSIONS[orb]
    orb_col_high = f"orb_{orb}_high"
    orb_col_low = f"orb_{orb}_low"
    orb_col_dir = f"orb_{orb}_break_dir"

    days = con.execute(f"""
        SELECT date_local
        FROM daily_features_v2
        WHERE {orb_col_dir} IS NOT NULL
        ORDER BY date_local
    """).fetchall()

    total_days = len(days)
    inserted = 0
    skipped_no_orb = 0
    skipped_no_bars = 0
    skipped_no_entry = 0
    skipped_big_stop = 0

    config_str = f"{orb} | {exec_timeframe} | confirm={close_confirmations} | RR={rr}"
    if sl_mode:
        config_str += f" | SL={sl_mode} | buffer={buffer_ticks}"

    print(f"\n{'='*80}")
    print(f"CONFIG: {config_str}")
    print(f"Days: {total_days} | NO FILTERS")
    print(f"{'='*80}\n")

    for idx, (d,) in enumerate(days, start=1):
        # Get ORB range
        orb_data = con.execute(f"""
            SELECT {orb_col_high}, {orb_col_low}, {orb_col_dir}
            FROM daily_features_v2
            WHERE date_local = ?
        """, [d]).fetchone()

        if not orb_data or orb_data[0] is None or orb_data[1] is None:
            skipped_no_orb += 1
            continue

        orb_high, orb_low, orb_dir = orb_data

        if orb_dir not in ("UP", "DOWN"):
            skipped_no_orb += 1
            continue

        direction = orb_dir
        entry_price = orb_high if direction == "UP" else orb_low

        # Apply buffer
        if buffer_ticks > 0:
            buffer_price = buffer_ticks * TICK_SIZE
            if direction == "UP":
                entry_price += buffer_price
            else:
                entry_price -= buffer_price

        # Get bars for execution
        timeframe_table = "bars_1m" if exec_timeframe == "1m" else "bars_5m"
        orb_end = f"{d} {h:02d}:{m+5:02d}:00"
        scan_end = orb_scan_end_local(orb, d)

        bars = con.execute(f"""
            SELECT ts_utc, open, high, low, close
            FROM {timeframe_table}
            WHERE symbol = ?
              AND ts_utc > ?::TIMESTAMP
              AND ts_utc <= ?::TIMESTAMP
            ORDER BY ts_utc
        """, [SYMBOL, orb_end, scan_end]).fetchall()

        if not bars:
            skipped_no_bars += 1
            continue

        # Find entry
        entry_idx = None
        confirms = 0

        for i, (ts, o, h, l, c) in enumerate(bars):
            triggered = (c > entry_price) if direction == "UP" else (c < entry_price)
            if triggered:
                confirms += 1
                if confirms >= close_confirmations:
                    entry_idx = i
                    entry_ts = ts
                    break
            else:
                confirms = 0

        if entry_idx is None:
            skipped_no_entry += 1
            continue

        # Calculate stop
        stop_price = orb_low if direction == "UP" else orb_high
        stop_ticks = abs(entry_price - stop_price) / TICK_SIZE

        if stop_ticks > MAX_STOP_TICKS:
            skipped_big_stop += 1
            continue

        # Adjust stop for half-SL mode
        if sl_mode == "half":
            half_stop = (entry_price + stop_price) / 2
            stop_price = half_stop
            stop_ticks = abs(entry_price - stop_price) / TICK_SIZE

        # Calculate target
        risk = abs(entry_price - stop_price)
        target_price = entry_price + rr * risk if direction == "UP" else entry_price - rr * risk

        # Apply Asia TP cap
        if is_asia(orb):
            cap = ASIA_TP_CAP_TICKS * TICK_SIZE
            if direction == "UP":
                target_price = min(target_price, entry_price + cap)
            else:
                target_price = max(target_price, entry_price - cap)

        # Simulate outcome
        outcome = None
        max_adv_ticks = 0
        max_fav_ticks = 0

        for ts, o, h, l, c in bars[entry_idx+1:]:
            # Track MAE/MFE
            if direction == "UP":
                adv = (stop_price - l) / TICK_SIZE
                fav = (h - entry_price) / TICK_SIZE
            else:
                adv = (h - stop_price) / TICK_SIZE
                fav = (entry_price - l) / TICK_SIZE

            max_adv_ticks = max(max_adv_ticks, adv)
            max_fav_ticks = max(max_fav_ticks, fav)

            # Check SL/TP
            if direction == "UP":
                if l <= stop_price:
                    outcome = "LOSS"
                    break
                if h >= target_price:
                    outcome = "WIN"
                    break
            else:
                if h >= stop_price:
                    outcome = "LOSS"
                    break
                if l <= target_price:
                    outcome = "WIN"
                    break

        if outcome is None:
            outcome = "OPEN"

        # Calculate R
        r_mult = rr if outcome == "WIN" else (-1.0 if outcome == "LOSS" else 0.0)
        mae_r = (max_adv_ticks / stop_ticks) if stop_ticks > 0 else None
        mfe_r = (max_fav_ticks / stop_ticks) if stop_ticks > 0 else None
        entry_delay_bars = entry_idx + 1

        # Insert
        con.execute("""
            INSERT OR REPLACE INTO orb_trades_focused
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            d, orb, close_confirmations, rr,
            exec_timeframe, sl_mode or '', buffer_ticks,
            direction, entry_ts,
            entry_price, stop_price, target_price, stop_ticks,
            outcome, r_mult, entry_delay_bars,
            mae_r, mfe_r
        ])

        inserted += 1

        if idx % commit_every_days == 0:
            con.commit()
            print(f"[{idx:>4}/{total_days}] {d} | inserted={inserted} | "
                  f"skip: no_orb={skipped_no_orb} no_bars={skipped_no_bars} "
                  f"no_entry={skipped_no_entry} big_stop={skipped_big_stop}")

    con.commit()
    print(f"\nDONE: {config_str}")
    print(f"Inserted: {inserted} | Skipped: no_orb={skipped_no_orb} no_bars={skipped_no_bars} "
          f"no_entry={skipped_no_entry} big_stop={skipped_big_stop}\n")

    con.close()

if __name__ == "__main__":
    # Run focused grid - optimized around winners
    print("\n" + "="*80)
    print("FOCUSED BACKTEST - WINNERS ONLY (NO FILTERS)")
    print("="*80)

    configs = [
        # 10:00 ORB - Best performer, test variations around RR 3.0
        ("1000", 5, "5m", 2, 2.5, None, 0),   # Baseline: lower RR
        ("1000", 5, "5m", 2, 3.0, None, 0),   # Original winner
        ("1000", 5, "5m", 2, 3.5, None, 0),   # Higher RR
        ("1000", 5, "5m", 1, 3.0, None, 0),   # Less confirmation
        ("1000", 5, "5m", 3, 3.0, None, 0),   # More confirmation
        ("1000", 1, "1m", 2, 3.0, None, 0),   # Try 1m exec

        # 18:00 ORB - Test half-SL variations
        ("1800", 5, "5m", 1, 2.0, "half", 0),    # Original winner
        ("1800", 5, "5m", 1, 2.5, "half", 0),    # Higher RR
        ("1800", 5, "5m", 1, 1.5, "half", 0),    # Lower RR
        ("1800", 5, "5m", 2, 2.0, "half", 0),    # More confirmation
        ("1800", 5, "5m", 1, 2.0, "full", 0),    # Full SL instead
        ("1800", 5, "5m", 1, 2.0, "half", 5),    # Add buffer

        # 11:00 ORB - Test variations
        ("1100", 5, "5m", 1, 3.0, "half", 0),    # Original winner
        ("1100", 5, "5m", 1, 2.5, "half", 0),    # Lower RR
        ("1100", 5, "5m", 2, 3.0, "half", 0),    # More confirmation

        # 00:30 ORB - Test variations
        ("0030", 5, "5m", 2, 1.5, "half", 0),    # Original winner
        ("0030", 5, "5m", 1, 1.5, "half", 0),    # Less confirmation
        ("0030", 5, "5m", 2, 2.0, "half", 0),    # Higher RR
    ]

    total_configs = len(configs)

    for i, (orb, timeframe_mins, timeframe_str, confirm, rr, sl, buf) in enumerate(configs, 1):
        print(f"\n[{i}/{total_configs}] Testing variant...")
        run_backtest(
            orb=orb,
            close_confirmations=confirm,
            rr=rr,
            exec_timeframe=timeframe_str,
            sl_mode=sl,
            buffer_ticks=buf
        )

    print("\n" + "="*80)
    print("FOCUSED BACKTEST COMPLETE")
    print("="*80)
    print(f"Total configs tested: {total_configs}")
    print("\nNext step: python analyze_focused_results.py")
