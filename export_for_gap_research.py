"""Export MGC data for gap analysis (quick export, then close connection)"""

import duckdb
import pandas as pd

print("Exporting MGC 1-minute bars for gap research...")

try:
    conn = duckdb.connect(r"C:\Users\sydne\OneDrive\myprojectx\gold.db", read_only=True)

    # Quick export
    df = conn.execute("""
        SELECT ts_utc, open, high, low, close, volume
        FROM bars_1m
        WHERE symbol = 'MGC'
            AND ts_utc >= '2024-01-01'
        ORDER BY ts_utc
    """).fetchdf()

    # Close immediately
    conn.close()

    print(f"Exported {len(df):,} bars")

    # Save
    output_path = r"C:\Users\sydne\OneDrive\myprojectx\mgc_1m_export.parquet"
    df.to_parquet(output_path)

    print(f"Saved to: {output_path}")
    print(f"Size: {len(df):,} rows, {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

except Exception as e:
    print(f"Error: {e}")
    print("\nThe database is locked by another process.")
    print("Waiting for the background research to complete...")
