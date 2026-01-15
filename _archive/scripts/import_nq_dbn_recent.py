"""
Import recent NQ data from DBN file (Nov 22, 2025 onwards)
Populates bars_1m_nq table with missing recent data
"""
import databento as db
import duckdb
from datetime import datetime, date
from zoneinfo import ZoneInfo
import pandas as pd

TZ_LOCAL = ZoneInfo("Australia/Brisbane")
DB_PATH = "gold.db"
DBN_PATH = "NQ/glbx-mdp3-20250112-20260111.ohlcv-1m.dbn.zst"

# Start from where existing data ends
# Use Nov 23 to avoid timezone overlap (existing data is to Nov 21)
START_DATE = date(2025, 11, 23)

print(f"Loading NQ data from {DBN_PATH}")
print(f"Filtering for data >= {START_DATE}")
print("=" * 80)

# Read DBN file
store = db.DBNStore.from_file(DBN_PATH)

# Convert to DataFrame
df = store.to_df()
print(f"Loaded {len(df):,} total bars from DBN file")

# Filter for NQ symbols only (exclude spreads and MGC)
nq_mask = df['symbol'].str.startswith('NQ') & ~df['symbol'].str.contains('-')
df_nq = df[nq_mask].copy()
print(f"Filtered to {len(df_nq):,} NQ bars (excluding spreads)")

# For each timestamp, keep only the contract with highest volume (most active)
# ts_event is the index, so reset it first
df_nq = df_nq.reset_index()
df_nq = df_nq.sort_values(['ts_event', 'volume'], ascending=[True, False])
df_nq = df_nq.drop_duplicates(subset=['ts_event'], keep='first')
print(f"After deduplication: {len(df_nq):,} bars (kept highest volume per timestamp)")

df_nq['ts_utc'] = pd.to_datetime(df_nq['ts_event'])
df_nq['date_local'] = df_nq['ts_utc'].dt.tz_convert(TZ_LOCAL).dt.date

# Filter for recent data only
df_recent = df_nq[df_nq['date_local'] >= START_DATE].copy()

print(f"Filtered to {len(df_recent):,} bars >= {START_DATE}")

if len(df_recent) == 0:
    print("No new data to import!")
    exit(0)

# Select columns to match bars_1m_nq schema
# Need: ts_utc, symbol, source_symbol, open, high, low, close, volume
bars_data = df_recent[['ts_utc', 'symbol', 'open', 'high', 'low', 'close', 'volume']].copy()
bars_data['nq_symbol'] = 'NQ'  # Logical symbol
bars_data = bars_data.rename(columns={'symbol': 'source_symbol', 'nq_symbol': 'symbol'})
bars_data = bars_data[['ts_utc', 'symbol', 'source_symbol', 'open', 'high', 'low', 'close', 'volume']]

print(f"\nInserting {len(bars_data):,} bars into bars_1m_nq...")

# Insert into database
con = duckdb.connect(DB_PATH)

# Create table if not exists (should already exist)
con.execute("""
    CREATE TABLE IF NOT EXISTS bars_1m_nq (
        ts_utc TIMESTAMPTZ NOT NULL,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume BIGINT,
        PRIMARY KEY (ts_utc)
    )
""")

# Delete existing data in this range first, then insert
min_ts = df_recent['ts_utc'].min()
print(f"Deleting existing data >= {min_ts}...")
con.execute("DELETE FROM bars_1m_nq WHERE symbol = 'NQ' AND ts_utc >= ?", [min_ts])

# Insert new data
con.execute("""
    INSERT INTO bars_1m_nq
    SELECT * FROM bars_data
""")

inserted = con.execute("SELECT COUNT(*) FROM bars_1m_nq WHERE ts_utc >= ?",
                       [df_recent['ts_utc'].min()]).fetchone()[0]

print(f"[OK] Inserted/updated {inserted:,} bars")

# Check date range
result = con.execute("""
    SELECT
        MIN(ts_utc) as first,
        MAX(ts_utc) as last,
        COUNT(*) as total
    FROM bars_1m_nq
""").fetchone()

print(f"\nBars_1m_nq table now contains:")
print(f"  Total bars: {result[2]:,}")
print(f"  Date range: {result[0]} to {result[1]}")

# Rebuild 5m bars
print("\nRebuilding bars_5m_nq...")
con.execute("""
    CREATE TABLE IF NOT EXISTS bars_5m_nq (
        ts_utc TIMESTAMPTZ NOT NULL,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume BIGINT,
        PRIMARY KEY (ts_utc)
    )
""")

con.execute("""
    DELETE FROM bars_5m_nq
    WHERE ts_utc >= (SELECT MIN(ts_utc) FROM bars_1m_nq WHERE ts_utc >= ?)
""", [df_recent['ts_utc'].min()])

con.execute("""
    INSERT INTO bars_5m_nq
    SELECT
        to_timestamp(CAST(epoch(ts_utc) AS BIGINT) / 300 * 300) as ts_utc,
        'NQ' as symbol,
        first(source_symbol ORDER BY ts_utc) as source_symbol,
        first(open ORDER BY ts_utc) as open,
        max(high) as high,
        min(low) as low,
        last(close ORDER BY ts_utc) as close,
        sum(volume) as volume
    FROM bars_1m_nq
    WHERE ts_utc >= ?
    GROUP BY 1
    ORDER BY 1
""", [df_recent['ts_utc'].min()])

bars_5m = con.execute("SELECT COUNT(*) FROM bars_5m_nq").fetchone()[0]
print(f"[OK] Built {bars_5m:,} 5-minute bars")

con.close()

print("\n" + "=" * 80)
print("[OK] NQ data import complete!")
print("Next step: Rebuild daily features")
print("  Command: python build_daily_features_v2.py --symbol NQ 2025-11-22")
print("=" * 80)
