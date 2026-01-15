from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import List, Optional, Tuple

import duckdb


DB_PATH = Path("gold.db")
SYMBOL = "MGC"
TZ_LOCAL = ZoneInfo("Australia/Brisbane")  # UTC+10 (Brisbane)


@dataclass
class Bar1m:
    ts_utc: datetime
    o: float
    h: float
    l: float
    c: float
    v: int


def local_window_to_utc(for_local_date: date, start_local: time, end_local: time) -> Tuple[datetime, datetime]:
    """
    Build a UTC window from local times.
    If end_local <= start_local, end is on the next day.
    """
    start_dt_local = datetime.combine(for_local_date, start_local, tzinfo=TZ_LOCAL)
    end_dt_local = datetime.combine(for_local_date, end_local, tzinfo=TZ_LOCAL)
    if end_dt_local <= start_dt_local:
        end_dt_local += timedelta(days=1)
    return start_dt_local.astimezone(timezone.utc), end_dt_local.astimezone(timezone.utc)


def fetch_bars_1m(con: duckdb.DuckDBPyConnection, start_utc: datetime, end_utc: datetime) -> List[Bar1m]:
    rows = con.execute(
        """
        SELECT ts_utc, open, high, low, close, volume
        FROM bars_1m
        WHERE symbol = ?
          AND ts_utc >= ?
          AND ts_utc < ?
        ORDER BY ts_utc ASC
        """,
        [SYMBOL, start_utc, end_utc],
    ).fetchall()

    out: List[Bar1m] = []
    for ts_utc, o, h, l, c, v in rows:
        if ts_utc.tzinfo is None:
            ts_utc = ts_utc.replace(tzinfo=timezone.utc)
        out.append(Bar1m(ts_utc=ts_utc, o=float(o), h=float(h), l=float(l), c=float(c), v=int(v)))
    return out


def high_low_1m(bars: List[Bar1m]) -> Tuple[Optional[float], Optional[float]]:
    if not bars:
        return None, None
    return max(b.h for b in bars), min(b.l for b in bars)


def travel_range_1m(bars: List[Bar1m]) -> Optional[float]:
    hi, lo = high_low_1m(bars)
    if hi is None or lo is None:
        return None
    return float(hi - lo)


def orb_break_dir(orb_hi: float, orb_lo: float, bars_after_orb: List[Bar1m]) -> str:
    # break = CLOSE outside range; wicks ignored
    for b in bars_after_orb:
        if b.c > orb_hi:
            return "UP"
        if b.c < orb_lo:
            return "DOWN"
    return "NONE"


def main(date_local_str: str) -> None:
    d = date.fromisoformat(date_local_str)

    # Sessions (local Brisbane)
    asia_start_utc, asia_end_utc = local_window_to_utc(d, time(9, 0), time(17, 0))
    london_start_utc, london_end_utc = local_window_to_utc(d, time(18, 0), time(23, 0))
    ny_start_utc, ny_end_utc = local_window_to_utc(d, time(23, 0), time(2, 0))  # crosses midnight

    # ORB fixed local: 00:30–00:35
    orb_start_utc, orb_end_utc = local_window_to_utc(d, time(0, 30), time(0, 35))

    # After-ORB check window: 00:35 -> 02:00 local
    break_start_utc = orb_end_utc
    _, break_end_utc = local_window_to_utc(d, time(0, 0), time(2, 0))  # returns end at 02:00 local in UTC

    # Pre windows
    pre_ny_start_utc, pre_ny_end_utc = london_start_utc, london_end_utc     # 18:00–23:00
    pre_orb_start_utc, _ = ny_start_utc, ny_end_utc                         # 23:00–02:00
    # pre_orb is 23:00 -> 00:30
    pre_orb_end_utc = orb_start_utc

    con = duckdb.connect(str(DB_PATH))
    try:
        asia_bars = fetch_bars_1m(con, asia_start_utc, asia_end_utc)
        london_bars = fetch_bars_1m(con, london_start_utc, london_end_utc)
        ny_bars = fetch_bars_1m(con, ny_start_utc, ny_end_utc)

        pre_ny_bars = fetch_bars_1m(con, pre_ny_start_utc, pre_ny_end_utc)
        pre_orb_bars = fetch_bars_1m(con, pre_orb_start_utc, pre_orb_end_utc)

        orb_bars = fetch_bars_1m(con, orb_start_utc, orb_end_utc)
        after_orb_bars = fetch_bars_1m(con, break_start_utc, break_end_utc)

        asia_hi, asia_lo = high_low_1m(asia_bars)
        lon_hi, lon_lo = high_low_1m(london_bars)
        ny_hi, ny_lo = high_low_1m(ny_bars)

        orb_hi, orb_lo = high_low_1m(orb_bars)
        if orb_hi is None or orb_lo is None:
            raise RuntimeError(
                f"ORB bars missing for {d.isoformat()} "
                f"(need 1m data in local 00:30–00:35 window)."
            )

        orb_first5m = float(orb_hi - orb_lo)
        ob_dir = orb_break_dir(float(orb_hi), float(orb_lo), after_orb_bars)

        pre_ny = travel_range_1m(pre_ny_bars)
        pre_orb = travel_range_1m(pre_orb_bars)

        con.execute(
            """
            INSERT OR REPLACE INTO daily_features
            (date_local, asia_high, asia_low, london_high, london_low, ny_high, ny_low,
             pre_ny_travel, pre_orb_travel, orb_high, orb_low, orb_first5m, orb_break_dir, rsi_at_orb)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            [
                d,
                asia_hi, asia_lo,
                lon_hi, lon_lo,
                ny_hi, ny_lo,
                pre_ny,
                pre_orb,
                float(orb_hi),
                float(orb_lo),
                orb_first5m,
                ob_dir,
            ],
        )

        print("OK: daily_features built for", d.isoformat())
        print("  ORB local:", "00:30–00:35", "| ORB start UTC:", orb_start_utc.isoformat())
        print("  ORB dir:", ob_dir, "| ORB size:", orb_first5m)

    finally:
        con.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python build_daily_features.py YYYY-MM-DD  (local Brisbane date)")
    main(sys.argv[1])
