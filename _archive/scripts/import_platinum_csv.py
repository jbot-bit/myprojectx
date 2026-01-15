"""
Import Platinum from CSV - Flexible CSV Importer
================================================

This script handles various CSV formats for platinum data:
- TradingView exports
- ProjectX exports
- Custom CSV files
- Any OHLCV format

Usage:
  python import_platinum_csv.py <csv_file>

Example:
  python import_platinum_csv.py platinum_data.csv
"""

import sys
import csv
import duckdb
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

DB_PATH = "gold.db"
SYMBOL = "MPL"
TZ_LOCAL = ZoneInfo("Australia/Brisbane")


def detect_csv_format(file_path):
    """Auto-detect CSV format"""
    with open(file_path, 'r') as f:
        # Read first line (header)
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        # Try to detect format
        formats = {
            "tradingview": ["time", "open", "high", "low", "close", "Volume"],
            "projectx": ["timestamp", "open", "high", "low", "close", "volume"],
            "standard": ["datetime", "open", "high", "low", "close", "volume"],
            "simple": ["date", "time", "open", "high", "low", "close", "volume"]
        }

        for format_name, expected_headers in formats.items():
            # Case-insensitive match
            if all(any(h.lower() in [eh.lower() for eh in headers]) for h in expected_headers):
                return format_name

        return "custom"


def parse_timestamp(ts_str, fmt="auto"):
    """Parse timestamp string to UTC datetime"""
    # Common formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%m/%d/%Y %H:%M",
        "%d/%m/%Y %H:%M",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(ts_str, fmt)
            # If no timezone info, assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except:
            continue

    raise ValueError(f"Could not parse timestamp: {ts_str}")


def init_mpl_tables(con):
    """Create MPL tables if they don't exist"""
    con.execute("""
        CREATE TABLE IF NOT EXISTS bars_1m_mpl (
          ts_utc        TIMESTAMPTZ NOT NULL,
          symbol        TEXT NOT NULL,
          source_symbol TEXT,
          open          DOUBLE NOT NULL,
          high          DOUBLE NOT NULL,
          low           DOUBLE NOT NULL,
          close         DOUBLE NOT NULL,
          volume        BIGINT NOT NULL,
          PRIMARY KEY (symbol, ts_utc)
        );
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS bars_5m_mpl (
          ts_utc        TIMESTAMPTZ NOT NULL,
          symbol        TEXT NOT NULL,
          source_symbol TEXT,
          open          DOUBLE NOT NULL,
          high          DOUBLE NOT NULL,
          low           DOUBLE NOT NULL,
          close         DOUBLE NOT NULL,
          volume        BIGINT NOT NULL,
          PRIMARY KEY (symbol, ts_utc)
        );
    """)


def import_csv(file_path):
    """Import CSV file"""
    print(f"Importing: {file_path}")

    # Detect format
    csv_format = detect_csv_format(file_path)
    print(f"Detected format: {csv_format}")

    # Connect to database
    con = duckdb.connect(DB_PATH)
    init_mpl_tables(con)

    rows_imported = 0
    errors = 0

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)

        rows_to_insert = []

        for row in reader:
            try:
                # Extract timestamp
                if 'time' in row:
                    ts_str = row['time']
                elif 'timestamp' in row:
                    ts_str = row['timestamp']
                elif 'datetime' in row:
                    ts_str = row['datetime']
                elif 'date' in row and 'time' in row:
                    ts_str = f"{row['date']} {row['time']}"
                else:
                    print(f"ERROR: No timestamp column found")
                    print(f"Available columns: {', '.join(row.keys())}")
                    return False

                ts_utc = parse_timestamp(ts_str)

                # Extract OHLCV (case-insensitive)
                def get_value(key):
                    for k in row.keys():
                        if k.lower() == key.lower():
                            return row[k]
                    raise KeyError(f"Column '{key}' not found")

                open_price = float(get_value('open'))
                high_price = float(get_value('high'))
                low_price = float(get_value('low'))
                close_price = float(get_value('close'))
                volume = int(float(get_value('volume')))

                # Validate
                if high_price < low_price:
                    print(f"WARNING: Invalid bar at {ts_utc}: high < low")
                    errors += 1
                    continue

                if close_price < low_price or close_price > high_price:
                    print(f"WARNING: Invalid bar at {ts_utc}: close outside range")
                    errors += 1
                    continue

                rows_to_insert.append((
                    ts_utc.isoformat(),
                    SYMBOL,
                    None,  # source_symbol (unknown for CSV)
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume
                ))

                rows_imported += 1

                if rows_imported % 1000 == 0:
                    print(f"  Processed {rows_imported:,} rows...")

            except Exception as e:
                print(f"ERROR parsing row: {e}")
                errors += 1
                if errors > 100:
                    print("Too many errors - stopping")
                    return False
                continue

    # Bulk insert
    print(f"\nInserting {len(rows_to_insert):,} rows into database...")

    con.executemany(
        """
        INSERT OR REPLACE INTO bars_1m_mpl
        (ts_utc, symbol, source_symbol, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows_to_insert
    )

    print(f"OK: Imported {rows_imported:,} bars ({errors} errors)")

    # Build 5m bars
    print("\nBuilding 5-minute bars...")

    con.execute("""
        INSERT OR REPLACE INTO bars_5m_mpl (ts_utc, symbol, source_symbol, open, high, low, close, volume)
        SELECT
            CAST(to_timestamp(floor(epoch(ts_utc) / 300) * 300) AS TIMESTAMPTZ) AS ts_5m,
            symbol,
            NULL AS source_symbol,
            arg_min(open, ts_utc)  AS open,
            max(high)              AS high,
            min(low)               AS low,
            arg_max(close, ts_utc) AS close,
            sum(volume)            AS volume
        FROM bars_1m_mpl
        WHERE symbol = 'MPL'
        GROUP BY 1, 2
        ORDER BY 1
    """)

    result = con.execute("SELECT COUNT(*) FROM bars_5m_mpl WHERE symbol = 'MPL'").fetchone()
    print(f"OK: Built {result[0]:,} 5m bars")

    con.close()

    # Now build features
    print("\nBuilding daily features...")
    import subprocess

    # Get date range
    con = duckdb.connect(DB_PATH)
    result = con.execute("""
        SELECT
            DATE(ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'Australia/Brisbane') as date_local
        FROM bars_1m_mpl
        WHERE symbol = 'MPL'
        GROUP BY 1
        ORDER BY 1
    """).fetchall()
    con.close()

    dates = [row[0] for row in result]

    print(f"Found {len(dates)} trading days")

    for date in dates:
        cmd = [sys.executable, "scripts/build_daily_features_mpl.py", str(date)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  WARNING: Feature building failed for {date}")
        else:
            if len(dates) <= 10:  # Only print for small datasets
                print(f"  OK: {date}")

    print(f"\nOK: Features built for {len(dates)} days")

    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_platinum_csv.py <csv_file>")
        print("\nExample:")
        print("  python import_platinum_csv.py platinum_data.csv")
        print("\nSupported formats:")
        print("  - TradingView exports")
        print("  - ProjectX exports")
        print("  - Any CSV with: timestamp, open, high, low, close, volume")
        sys.exit(1)

    csv_file = Path(sys.argv[1])

    if not csv_file.exists():
        print(f"ERROR: File not found: {csv_file}")
        sys.exit(1)

    print("="*80)
    print("PLATINUM CSV IMPORT")
    print("="*80)

    success = import_csv(csv_file)

    if success:
        print("\n" + "="*80)
        print("SUCCESS")
        print("="*80)
        print("\nNext step: Run analysis")
        print("  python CHECK_AND_ANALYZE_MPL.py")
    else:
        print("\n" + "="*80)
        print("FAILED")
        print("="*80)
        print("\nCheck errors above and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()
