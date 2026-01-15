from __future__ import annotations

import os
import sys
import datetime as dt
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple

import duckdb
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import databento as db


# -----------------------------
# Config
# -----------------------------

@dataclass
class Cfg:
    db_path: str = "gold.db"
    symbol: str = "MGC"                 # logical symbol stored in DB
    tz_local: str = "Australia/Brisbane"

    # Databento
    api_key: str = ""
    dataset: str = "GLBX.MDP3"
    schema: str = "ohlcv-1m"
    stype_in: str = "parent"
    symbols: List[str] = None           # e.g. ["MGC.FUT"]

    # Behavior
    filter_spreads: bool = True         # remove symbols like MGCM4-MGCV4
    fill_missing_minutes: bool = True   # fill 1m gaps with last close, vol=0
    run_daily_features: bool = False    # optionally call build_daily_features.py per day


def env_cfg() -> Cfg:
    load_dotenv()
    cfg = Cfg()

    cfg.db_path = os.getenv("DUCKDB_PATH", cfg.db_path).strip()
    cfg.symbol = os.getenv("SYMBOL", cfg.symbol).strip()
    cfg.tz_local = os.getenv("TZ_LOCAL", cfg.tz_local).strip() or cfg.tz_local

    cfg.api_key = (os.getenv("DATABENTO_API_KEY") or "").strip()
    if not cfg.api_key:
        raise RuntimeError("Missing DATABENTO_API_KEY in .env")

    cfg.dataset = os.getenv("DATABENTO_DATASET", cfg.dataset).strip()
    cfg.schema = os.getenv("DATABENTO_SCHEMA", cfg.schema).strip()
    cfg.stype_in = os.getenv("DATABENTO_STYPE_IN", cfg.stype_in).strip()

    sym = os.getenv("DATABENTO_SYMBOLS", "MGC.FUT").strip()
    cfg.symbols = [s.strip() for s in sym.split(",") if s.strip()]

    cfg.filter_spreads = os.getenv("DATABENTO_FILTER_SPREADS", "true").strip().lower() in ("1", "true", "yes", "y")
    cfg.fill_missing_minutes = os.getenv("DATABENTO_FILL_MISSING_MINUTES", "true").strip().lower() in ("1", "true", "yes", "y")
    cfg.run_daily_features = os.getenv("RUN_DAILY_FEATURES", "false").strip().lower() in ("1", "true", "yes", "y")

    return cfg


# -----------------------------
# Date helpers
# -----------------------------

def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)

def daterange_inclusive(start: dt.date, end: dt.date):
    cur = start
    while cur <= end:
        yield cur
        cur += dt.timedelta(days=1)

def local_day_to_utc_window(d_local: dt.date, tz_name: str) -> Tuple[dt.datetime, dt.datetime]:
    """
    Trading day = 09:00 local -> next 09:00 local
    This aligns with ORB strategy (session starts at 09:00)
    """
    tz = ZoneInfo(tz_name)
    start_local = dt.datetime(d_local.year, d_local.month, d_local.day, 9, 0, tzinfo=tz)
    end_local = start_local + dt.timedelta(days=1)
    return start_local.astimezone(dt.timezone.utc), end_local.astimezone(dt.timezone.utc)


# -----------------------------
# DuckDB writes
# -----------------------------

def upsert_bars_1m(
    con: duckdb.DuckDBPyConnection,
    cfg: Cfg,
    rows: List[Tuple[dt.datetime, str, Optional[str], float, float, float, float, int]],
) -> int:
    if not rows:
        return 0

    con.executemany(
        """
        INSERT OR REPLACE INTO bars_1m
        (ts_utc, symbol, source_symbol, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)

def rebuild_5m_from_1m(con: duckdb.DuckDBPyConnection, cfg: Cfg, start_utc: dt.datetime, end_utc: dt.datetime) -> None:
    con.execute(
        """
        DELETE FROM bars_5m
        WHERE symbol = ?
          AND ts_utc >= CAST(? AS TIMESTAMPTZ)
          AND ts_utc <  CAST(? AS TIMESTAMPTZ)
        """,
        [cfg.symbol, start_utc, end_utc],
    )

    con.execute(
        """
        INSERT INTO bars_5m (ts_utc, symbol, source_symbol, open, high, low, close, volume)
        SELECT
            CAST(to_timestamp(floor(epoch(ts_utc) / 300) * 300) AS TIMESTAMPTZ) AS ts_5m,
            symbol,
            NULL AS source_symbol,
            arg_min(open, ts_utc)  AS open,
            max(high)              AS high,
            min(low)               AS low,
            arg_max(close, ts_utc) AS close,
            sum(volume)            AS volume
        FROM bars_1m
        WHERE symbol = ?
          AND ts_utc >= CAST(? AS TIMESTAMPTZ)
          AND ts_utc <  CAST(? AS TIMESTAMPTZ)
        GROUP BY 1, 2
        ORDER BY 1
        """,
        [cfg.symbol, start_utc, end_utc],
    )


# -----------------------------
# Optional: Fill missing minutes
# -----------------------------

def fill_missing_1m(rows: List[Tuple[dt.datetime, str, Optional[str], float, float, float, float, int]]) -> List[Tuple[dt.datetime, str, Optional[str], float, float, float, float, int]]:
    if not rows:
        return rows

    rows.sort(key=lambda r: r[0])
    out = [rows[0]]
    minute = dt.timedelta(minutes=1)

    prev_ts, sym, src, o, h, l, c, v = rows[0]
    last_close = c

    for ts, sym, src, o, h, l, c, v in rows[1:]:
        expected = prev_ts + minute
        while expected < ts:
            out.append((expected, sym, src, last_close, last_close, last_close, last_close, 0))
            expected += minute

        out.append((ts, sym, src, o, h, l, c, v))
        prev_ts = ts
        last_close = c

    return out


# -----------------------------
# Main
# -----------------------------

def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python backfill_databento_range.py YYYY-MM-DD YYYY-MM-DD  (local Brisbane dates)")

    cfg = env_cfg()
    start_day = parse_date(sys.argv[1])
    end_day = parse_date(sys.argv[2])

    client = db.Historical(cfg.api_key)
    con = duckdb.connect(cfg.db_path)

    try:
        total = 0

        for d in daterange_inclusive(start_day, end_day):
            start_utc, end_utc = local_day_to_utc_window(d, cfg.tz_local)

            store = client.timeseries.get_range(
                dataset=cfg.dataset,
                schema=cfg.schema,
                stype_in=cfg.stype_in,
                symbols=cfg.symbols,
                start=start_utc.isoformat(),
                end=end_utc.isoformat(),
            )

            df = store.to_df()
            if df.empty:
                print(f"{d} (local) [{start_utc.isoformat()} -> {end_utc.isoformat()}] -> inserted/replaced 0 rows")
                continue

            df = df.reset_index()  # ts_event becomes column

            rows: List[Tuple[dt.datetime, str, Optional[str], float, float, float, float, int]] = []
            for _, r in df.iterrows():
                src_symbol = str(r.get("symbol") or "")

                # filter calendar spreads / combos
                if cfg.filter_spreads and "-" in src_symbol:
                    continue

                ts = r["ts_event"]
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=dt.timezone.utc)
                ts_utc = ts.astimezone(dt.timezone.utc)

                rows.append((
                    ts_utc,
                    cfg.symbol,
                    src_symbol or None,
                    float(r["open"]),
                    float(r["high"]),
                    float(r["low"]),
                    float(r["close"]),
                    int(r["volume"]),
                ))

            if cfg.fill_missing_minutes:
                rows = fill_missing_1m(rows)

            inserted = upsert_bars_1m(con, cfg, rows)
            total += inserted

            print(f"{d} (local) [{start_utc.isoformat()} -> {end_utc.isoformat()}] -> inserted/replaced {inserted} rows")

        # rebuild 5m for the full range
        range_start_utc, _ = local_day_to_utc_window(start_day, cfg.tz_local)
        _, range_end_utc = local_day_to_utc_window(end_day, cfg.tz_local)

        rebuild_5m_from_1m(con, cfg, range_start_utc, range_end_utc)
        print("OK: rebuilt 5m bars for range")
        print(f"OK: bars_1m upsert total = {total}")

    finally:
        con.close()

    # optionally build daily_features
    if cfg.run_daily_features:
        for d in daterange_inclusive(start_day, end_day):
            cmd = [sys.executable, "build_daily_features.py", d.isoformat()]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"FAIL daily_features {d}:")
                print(r.stdout)
                print(r.stderr)
                raise SystemExit(r.returncode)
            print(f"OK: daily_features built for {d}")

    print("DONE")


if __name__ == "__main__":
    main()
