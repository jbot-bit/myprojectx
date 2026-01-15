from datetime import datetime
from pathlib import Path

import duckdb

from app.data.projectx_client import ProjectXClient

DB_PATH = Path("gold.db")
SYMBOL = "MGC"


def parse_ts(ts: str) -> datetime:
    # ProjectX gives ISO like "2026-01-08T23:59:00+00:00"
    return datetime.fromisoformat(ts)


def main(start_utc: str, end_utc: str) -> None:
    client = ProjectXClient()
    client.login()

    info = client.get_active_mgc_contract_info()
    contract_id = info["contract_id"]
    source_symbol = info["source_symbol"]

    bars = client.retrieve_1m_bars(contract_id, start_utc, end_utc)

    rows = []
    for b in bars:
        rows.append(
            (
                parse_ts(b["t"]),
                SYMBOL,
                source_symbol,
                float(b["o"]),
                float(b["h"]),
                float(b["l"]),
                float(b["c"]),
                int(b["v"]),
            )
        )

    con = duckdb.connect(str(DB_PATH))
    try:
        # Idempotent: primary key (symbol, ts_utc) => reruns overwrite
        con.executemany(
            """
            INSERT OR REPLACE INTO bars_1m
            (ts_utc, symbol, source_symbol, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        print(f"OK: inserted/replaced {len(rows)} rows into bars_1m")
    finally:
        con.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        raise SystemExit("Usage: python ingest_1m.py <start_utc> <end_utc>")

    main(sys.argv[1], sys.argv[2])
