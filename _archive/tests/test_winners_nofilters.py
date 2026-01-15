"""
Minimal No-Filter Test - Winners Only

Tests ONLY your proven winning configs with filters removed.
Answers: "Do MAX_STOP and ASIA_TP_CAP filters help or hurt my edge?"

Compares:
- WITH filters (already done, in existing tables)
- WITHOUT filters (this test, writes to _nofilters tables)

Total runtime: ~10-15 minutes (5 configs vs 2+ hours for 104)
"""

import duckdb
from datetime import date, timedelta

DB_PATH = "gold.db"
SYMBOL = "MGC"
TICK_SIZE = 0.1

# NO FILTERS
MAX_STOP_TICKS = 999999
ASIA_TP_CAP_TICKS = 999999

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

ORB_TIMES = {
    "0900": (9, 0),
    "1000": (10, 0),
    "1100": (11, 0),
    "1800": (18, 0),
    "2300": (23, 0),
    "0030": (0, 30),
}

def ensure_schema_5m(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS orb_trades_5m_exec_nofilters (
            date_local DATE NOT NULL,
            orb VARCHAR NOT NULL,
            close_confirmations INTEGER NOT NULL,
            rr DOUBLE NOT NULL,
            sl_mode VARCHAR,
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
            PRIMARY KEY (date_local, orb, close_confirmations, rr, sl_mode, buffer_ticks)
        )
    """)

def test_5m_winner(orb, rr, confirm, sl_mode=None, buffer_ticks=0):
    """Test a 5m winner config without filters"""
    con = duckdb.connect(DB_PATH)
    ensure_schema_5m(con)

    orb_time = ORB_TIMES[orb]
    orb_hour = orb_time[0]
    orb_min = orb_time[1]

    orb_col_high = f"orb_{orb}_high"
    orb_col_low = f"orb_{orb}_low"
    orb_col_dir = f"orb_{orb}_break_dir"

    # Get all days, then exclude first and last (incomplete data)
    all_days = con.execute(f"""
        SELECT date_local
        FROM daily_features_v2
        WHERE {orb_col_dir} IS NOT NULL
        ORDER BY date_local
    """).fetchall()

    # Exclude first and last day
    if len(all_days) > 2:
        days = all_days[1:-1]
    else:
        days = all_days

    inserted = 0
    skipped_no_orb = 0
    skipped_no_bars = 0
    skipped_no_entry = 0

    config = f"{orb} | 5m | RR={rr} | confirm={confirm}"
    if sl_mode:
        config += f" | SL={sl_mode} | buffer={buffer_ticks}"
    config += " | NO FILTERS"

    print(f"\n{'='*80}")
    print(f"Testing: {config}")
    print(f"Days: {len(days)} (excluding first/last)")
    print(f"{'='*80}")

    for idx, (d,) in enumerate(days, start=1):
        orb_data = con.execute(f"""
            SELECT {orb_col_high}, {orb_col_low}, {orb_col_dir}
            FROM daily_features_v2
            WHERE date_local = ?
        """, [d]).fetchone()

        if not orb_data or orb_data[0] is None:
            skipped_no_orb += 1
            continue

        orb_high, orb_low, orb_dir = orb_data
        if orb_dir not in ("UP", "DOWN"):
            skipped_no_orb += 1
            continue

        direction = orb_dir
        entry_price = orb_high if direction == "UP" else orb_low

        if buffer_ticks > 0:
            buf_price = buffer_ticks * TICK_SIZE
            entry_price = entry_price + buf_price if direction == "UP" else entry_price - buf_price

        # ORB ends 5 minutes after open
        orb_end = f"{str(d)} {orb_hour:02d}:{orb_min+5:02d}:00"
        scan_end = orb_scan_end_local(orb, d)

        bars = con.execute("""
            SELECT ts_utc, open, high, low, close
            FROM bars_5m
            WHERE symbol = ? AND ts_utc > ?::TIMESTAMP AND ts_utc <= ?::TIMESTAMP
            ORDER BY ts_utc
        """, [SYMBOL, orb_end, scan_end]).fetchall()

        if not bars:
            skipped_no_bars += 1
            continue

        entry_idx = None
        confirms = 0
        for i, (ts, o, h, l, c) in enumerate(bars):
            triggered = (c > entry_price) if direction == "UP" else (c < entry_price)
            if triggered:
                confirms += 1
                if confirms >= confirm:
                    entry_idx = i
                    entry_ts = ts
                    break
            else:
                confirms = 0

        if entry_idx is None:
            skipped_no_entry += 1
            continue

        stop_price = orb_low if direction == "UP" else orb_high
        stop_ticks = abs(entry_price - stop_price) / TICK_SIZE

        # NO MAX_STOP FILTER - accept all stops

        if sl_mode == "half":
            stop_price = (entry_price + stop_price) / 2
            stop_ticks = abs(entry_price - stop_price) / TICK_SIZE

        risk = abs(entry_price - stop_price)
        target_price = entry_price + rr * risk if direction == "UP" else entry_price - rr * risk

        # NO ASIA_TP_CAP - let targets run full distance

        outcome = None
        max_adv_ticks = 0
        max_fav_ticks = 0

        for ts, o, h, l, c in bars[entry_idx+1:]:
            if direction == "UP":
                adv = (stop_price - l) / TICK_SIZE
                fav = (h - entry_price) / TICK_SIZE
            else:
                adv = (h - stop_price) / TICK_SIZE
                fav = (entry_price - l) / TICK_SIZE

            max_adv_ticks = max(max_adv_ticks, adv)
            max_fav_ticks = max(max_fav_ticks, fav)

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

        r_mult = rr if outcome == "WIN" else (-1.0 if outcome == "LOSS" else 0.0)
        mae_r = (max_adv_ticks / stop_ticks) if stop_ticks > 0 else None
        mfe_r = (max_fav_ticks / stop_ticks) if stop_ticks > 0 else None

        con.execute("""
            INSERT OR REPLACE INTO orb_trades_5m_exec_nofilters
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            d, orb, confirm, rr,
            sl_mode or '', buffer_ticks,
            direction, entry_ts,
            entry_price, stop_price, target_price, stop_ticks,
            outcome, r_mult, entry_idx + 1,
            mae_r, mfe_r
        ])

        inserted += 1

        if idx % 100 == 0:
            con.commit()
            print(f"  [{idx}/{len(days)}] Inserted: {inserted}")

    con.commit()
    print(f"DONE: {inserted} trades | Skipped: no_orb={skipped_no_orb} no_entry={skipped_no_entry}\n")
    con.close()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("MINIMAL NO-FILTER TEST - WINNERS ONLY")
    print("="*80)
    print("Testing your proven winners WITHOUT max_stop and asia_tp_cap filters")
    print("Total: 5 configs (~10-15 minutes)")
    print()

    # Test exact winning configs without filters
    configs = [
        # 1. 10:00 winner (+71R with filters)
        ("1000", 3.0, 2, None, 0),

        # 2. 18:00 winner (+60R with filters)
        ("1800", 2.0, 1, "half", 0),

        # 3. 11:00 winner (+13R with filters)
        ("1100", 3.0, 1, "half", 0),

        # 4. 00:30 winner (+13R with filters)
        ("0030", 1.5, 2, "half", 0),

        # 5. 09:00 winner (+8R with filters)
        ("0900", 3.0, 2, None, 0),
    ]

    for i, (orb, rr, confirm, sl_mode, buffer) in enumerate(configs, 1):
        print(f"\n[{i}/5] Testing variant...")
        test_5m_winner(orb, rr, confirm, sl_mode, buffer)

    print("="*80)
    print("TEST COMPLETE - Now run: python compare_winners_filters.py")
    print("="*80)
