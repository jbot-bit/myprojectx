#!/usr/bin/env python3
"""
Consolidate multi-instrument tables into unified schema.
Part of MotherDuck migration - clean architecture before upload.
"""

import duckdb
from datetime import datetime
import json


def log_step(msg, indent=0):
    """Print and log a step."""
    prefix = "  " * indent
    print(f"{prefix}{msg}")
    return msg


def consolidate_schema():
    """Consolidate fragmented tables into clean multi-instrument schema."""

    log_file = []
    log_file.append("=" * 70)
    log_file.append("SCHEMA CONSOLIDATION REPORT")
    log_file.append(f"Started: {datetime.now().isoformat()}")
    log_file.append("=" * 70)
    log_file.append("")

    conn = duckdb.connect('gold.db')

    print("\n" + "=" * 70)
    print("SCHEMA CONSOLIDATION - Multi-Instrument Unification")
    print("=" * 70)

    # ===================================================================
    # STEP 1: Consolidate bars_1m
    # ===================================================================
    print("\n[STEP 1] Consolidating bars_1m tables...")
    log_file.append("[STEP 1] Consolidating bars_1m")
    log_file.append("-" * 70)

    # Count existing rows
    mgc_1m = conn.execute("SELECT COUNT(*) FROM bars_1m").fetchone()[0]
    mpl_1m = conn.execute("SELECT COUNT(*) FROM bars_1m_mpl").fetchone()[0]
    nq_1m = conn.execute("SELECT COUNT(*) FROM bars_1m_nq").fetchone()[0]
    expected_total_1m = mgc_1m + mpl_1m + nq_1m

    log_step(f"Source row counts:")
    log_step(f"  bars_1m (MGC): {mgc_1m:,}", 1)
    log_step(f"  bars_1m_mpl: {mpl_1m:,}", 1)
    log_step(f"  bars_1m_nq: {nq_1m:,}", 1)
    log_step(f"  Expected total: {expected_total_1m:,}", 1)

    log_file.append(f"Source bars_1m (MGC): {mgc_1m:,}")
    log_file.append(f"Source bars_1m_mpl: {mpl_1m:,}")
    log_file.append(f"Source bars_1m_nq: {nq_1m:,}")

    # Create consolidated table
    log_step("Creating bars_1m_consolidated...")
    conn.execute("""
        CREATE TABLE bars_1m_consolidated AS
        SELECT
            ts_utc,
            symbol,
            source_symbol,
            open,
            high,
            low,
            close,
            volume
        FROM bars_1m
        UNION ALL
        SELECT
            ts_utc,
            symbol,
            source_symbol,
            open,
            high,
            low,
            close,
            volume
        FROM bars_1m_mpl
        UNION ALL
        SELECT
            ts_utc,
            symbol,
            source_symbol,
            open,
            high,
            low,
            close,
            volume
        FROM bars_1m_nq
    """)

    # Validate
    actual_total_1m = conn.execute("SELECT COUNT(*) FROM bars_1m_consolidated").fetchone()[0]
    log_step(f"Consolidated rows: {actual_total_1m:,}")

    if actual_total_1m != expected_total_1m:
        raise ValueError(f"bars_1m row count mismatch! Expected {expected_total_1m:,}, got {actual_total_1m:,}")

    log_step("[OK] bars_1m consolidation verified")
    log_file.append(f"Consolidated bars_1m: {actual_total_1m:,} rows (VERIFIED)")
    log_file.append("")

    # ===================================================================
    # STEP 2: Consolidate bars_5m
    # ===================================================================
    print("\n[STEP 2] Consolidating bars_5m tables...")
    log_file.append("[STEP 2] Consolidating bars_5m")
    log_file.append("-" * 70)

    # Count existing rows
    mgc_5m = conn.execute("SELECT COUNT(*) FROM bars_5m").fetchone()[0]
    mpl_5m = conn.execute("SELECT COUNT(*) FROM bars_5m_mpl").fetchone()[0]
    nq_5m = conn.execute("SELECT COUNT(*) FROM bars_5m_nq").fetchone()[0]
    expected_total_5m = mgc_5m + mpl_5m + nq_5m

    log_step(f"Source row counts:")
    log_step(f"  bars_5m (MGC): {mgc_5m:,}", 1)
    log_step(f"  bars_5m_mpl: {mpl_5m:,}", 1)
    log_step(f"  bars_5m_nq: {nq_5m:,}", 1)
    log_step(f"  Expected total: {expected_total_5m:,}", 1)

    log_file.append(f"Source bars_5m (MGC): {mgc_5m:,}")
    log_file.append(f"Source bars_5m_mpl: {mpl_5m:,}")
    log_file.append(f"Source bars_5m_nq: {nq_5m:,}")

    # Create consolidated table
    log_step("Creating bars_5m_consolidated...")
    conn.execute("""
        CREATE TABLE bars_5m_consolidated AS
        SELECT
            ts_utc,
            symbol,
            source_symbol,
            open,
            high,
            low,
            close,
            volume
        FROM bars_5m
        UNION ALL
        SELECT
            ts_utc,
            symbol,
            source_symbol,
            open,
            high,
            low,
            close,
            volume
        FROM bars_5m_mpl
        UNION ALL
        SELECT
            ts_utc,
            symbol,
            source_symbol,
            open,
            high,
            low,
            close,
            volume
        FROM bars_5m_nq
    """)

    # Validate
    actual_total_5m = conn.execute("SELECT COUNT(*) FROM bars_5m_consolidated").fetchone()[0]
    log_step(f"Consolidated rows: {actual_total_5m:,}")

    if actual_total_5m != expected_total_5m:
        raise ValueError(f"bars_5m row count mismatch! Expected {expected_total_5m:,}, got {actual_total_5m:,}")

    log_step("[OK] bars_5m consolidation verified")
    log_file.append(f"Consolidated bars_5m: {actual_total_5m:,} rows (VERIFIED)")
    log_file.append("")

    # ===================================================================
    # STEP 3: Consolidate daily_features_v2
    # ===================================================================
    print("\n[STEP 3] Consolidating daily_features_v2 tables...")
    log_file.append("[STEP 3] Consolidating daily_features_v2")
    log_file.append("-" * 70)

    # Count existing rows
    mgc_features = conn.execute("SELECT COUNT(*) FROM daily_features_v2").fetchone()[0]
    mpl_features = conn.execute("SELECT COUNT(*) FROM daily_features_v2_mpl").fetchone()[0]
    nq_features = conn.execute("SELECT COUNT(*) FROM daily_features_v2_nq").fetchone()[0]
    expected_total_features = mgc_features + mpl_features + nq_features

    log_step(f"Source row counts:")
    log_step(f"  daily_features_v2 (MGC): {mgc_features:,}", 1)
    log_step(f"  daily_features_v2_mpl: {mpl_features:,}", 1)
    log_step(f"  daily_features_v2_nq: {nq_features:,}", 1)
    log_step(f"  Expected total: {expected_total_features:,}", 1)

    log_file.append(f"Source daily_features_v2 (MGC): {mgc_features:,}")
    log_file.append(f"Source daily_features_v2_mpl: {mpl_features:,}")
    log_file.append(f"Source daily_features_v2_nq: {nq_features:,}")

    # Create consolidated table - use MGC schema as base (86 columns)
    log_step("Creating daily_features_v2_consolidated...")
    conn.execute("""
        CREATE TABLE daily_features_v2_consolidated AS
        SELECT * FROM daily_features_v2
        UNION ALL
        SELECT * FROM daily_features_v2_mpl
        UNION ALL
        -- NQ has 85 columns, need to add rsi_at_orb if missing
        SELECT
            date_local, instrument, pre_asia_high, pre_asia_low, pre_asia_range,
            pre_london_high, pre_london_low, pre_london_range, pre_ny_high, pre_ny_low, pre_ny_range,
            asia_high, asia_low, asia_range, london_high, london_low, london_range,
            ny_high, ny_low, ny_range, asia_type_code, london_type_code, pre_ny_type_code,
            orb_0900_high, orb_0900_low, orb_0900_size, orb_0900_break_dir, orb_0900_outcome, orb_0900_r_multiple,
            orb_1000_high, orb_1000_low, orb_1000_size, orb_1000_break_dir, orb_1000_outcome, orb_1000_r_multiple,
            orb_1100_high, orb_1100_low, orb_1100_size, orb_1100_break_dir, orb_1100_outcome, orb_1100_r_multiple,
            orb_1800_high, orb_1800_low, orb_1800_size, orb_1800_break_dir, orb_1800_outcome, orb_1800_r_multiple,
            orb_2300_high, orb_2300_low, orb_2300_size, orb_2300_break_dir, orb_2300_outcome, orb_2300_r_multiple,
            orb_0030_high, orb_0030_low, orb_0030_size, orb_0030_break_dir, orb_0030_outcome, orb_0030_r_multiple,
            rsi_at_0030, atr_20,
            orb_0900_mae, orb_0900_mfe, orb_0900_stop_price, orb_0900_risk_ticks,
            orb_1000_mae, orb_1000_mfe, orb_1000_stop_price, orb_1000_risk_ticks,
            orb_1100_mae, orb_1100_mfe, orb_1100_stop_price, orb_1100_risk_ticks,
            orb_1800_mae, orb_1800_mfe, orb_1800_stop_price, orb_1800_risk_ticks,
            orb_2300_mae, orb_2300_mfe, orb_2300_stop_price, orb_2300_risk_ticks,
            orb_0030_mae, orb_0030_mfe, orb_0030_stop_price, orb_0030_risk_ticks,
            NULL as rsi_at_orb  -- NQ missing this column
        FROM daily_features_v2_nq
    """)

    # Validate
    actual_total_features = conn.execute("SELECT COUNT(*) FROM daily_features_v2_consolidated").fetchone()[0]
    log_step(f"Consolidated rows: {actual_total_features:,}")

    if actual_total_features != expected_total_features:
        raise ValueError(f"daily_features_v2 row count mismatch! Expected {expected_total_features:,}, got {actual_total_features:,}")

    log_step("[OK] daily_features_v2 consolidation verified")
    log_file.append(f"Consolidated daily_features_v2: {actual_total_features:,} rows (VERIFIED)")
    log_file.append("")

    # ===================================================================
    # STEP 4: Archive old tables
    # ===================================================================
    print("\n[STEP 4] Archiving old tables...")
    log_file.append("[STEP 4] Archiving old tables")
    log_file.append("-" * 70)

    tables_to_archive = [
        'bars_1m',
        'bars_1m_mpl',
        'bars_1m_nq',
        'bars_5m',
        'bars_5m_mpl',
        'bars_5m_nq',
        'daily_features',  # Old version
        'daily_features_v2',
        'daily_features_v2_half',  # Experimental
        'daily_features_v2_mpl',
        'daily_features_v2_nq',
    ]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    for table in tables_to_archive:
        new_name = f"_archive_{timestamp}_{table}"
        log_step(f"Archiving {table} -> {new_name}")
        conn.execute(f"ALTER TABLE {table} RENAME TO {new_name}")
        log_file.append(f"Archived: {table} -> {new_name}")

    log_file.append("")

    # ===================================================================
    # STEP 5: Rename consolidated tables to production names
    # ===================================================================
    print("\n[STEP 5] Promoting consolidated tables to production...")
    log_file.append("[STEP 5] Promoting consolidated tables")
    log_file.append("-" * 70)

    renames = [
        ('bars_1m_consolidated', 'bars_1m'),
        ('bars_5m_consolidated', 'bars_5m'),
        ('daily_features_v2_consolidated', 'daily_features_v2'),
    ]

    for old, new in renames:
        log_step(f"Renaming {old} -> {new}")
        conn.execute(f"ALTER TABLE {old} RENAME TO {new}")
        log_file.append(f"Promoted: {old} -> {new}")

    log_file.append("")

    # ===================================================================
    # STEP 6: Verify final state
    # ===================================================================
    print("\n[STEP 6] Verifying final state...")
    log_file.append("[STEP 6] Final verification")
    log_file.append("-" * 70)

    # Check bars_1m
    bars_1m_final = conn.execute("SELECT COUNT(*) FROM bars_1m").fetchone()[0]
    bars_1m_symbols = conn.execute("SELECT symbol, COUNT(*) FROM bars_1m GROUP BY symbol ORDER BY symbol").fetchall()

    log_step(f"bars_1m: {bars_1m_final:,} total rows")
    log_file.append(f"bars_1m total: {bars_1m_final:,}")
    for symbol, count in bars_1m_symbols:
        log_step(f"  {symbol}: {count:,}", 1)
        log_file.append(f"  {symbol}: {count:,}")

    # Check bars_5m
    bars_5m_final = conn.execute("SELECT COUNT(*) FROM bars_5m").fetchone()[0]
    bars_5m_symbols = conn.execute("SELECT symbol, COUNT(*) FROM bars_5m GROUP BY symbol ORDER BY symbol").fetchall()

    log_step(f"bars_5m: {bars_5m_final:,} total rows")
    log_file.append(f"bars_5m total: {bars_5m_final:,}")
    for symbol, count in bars_5m_symbols:
        log_step(f"  {symbol}: {count:,}", 1)
        log_file.append(f"  {symbol}: {count:,}")

    # Check daily_features_v2
    features_final = conn.execute("SELECT COUNT(*) FROM daily_features_v2").fetchone()[0]
    features_instruments = conn.execute("SELECT instrument, COUNT(*) FROM daily_features_v2 GROUP BY instrument ORDER BY instrument").fetchall()

    log_step(f"daily_features_v2: {features_final:,} total rows")
    log_file.append(f"daily_features_v2 total: {features_final:,}")
    for inst, count in features_instruments:
        log_step(f"  {inst}: {count:,}", 1)
        log_file.append(f"  {inst}: {count:,}")

    log_file.append("")

    conn.close()

    # ===================================================================
    # STEP 7: Write report
    # ===================================================================
    log_file.append("=" * 70)
    log_file.append("CONSOLIDATION COMPLETE")
    log_file.append(f"Finished: {datetime.now().isoformat()}")
    log_file.append("=" * 70)
    log_file.append("")
    log_file.append("SUMMARY:")
    log_file.append(f"  bars_1m: {bars_1m_final:,} rows (3 instruments)")
    log_file.append(f"  bars_5m: {bars_5m_final:,} rows (3 instruments)")
    log_file.append(f"  daily_features_v2: {features_final:,} rows (3 instruments)")
    log_file.append(f"  Archived tables: {len(tables_to_archive)}")
    log_file.append("")
    log_file.append("Next step: Run audit_master.py to verify data integrity")

    # Write to file
    with open('consolidation_report.txt', 'w') as f:
        f.write('\n'.join(log_file))

    print("\n" + "=" * 70)
    print("CONSOLIDATION SUCCESSFUL!")
    print("=" * 70)
    print(f"\nReport written to: consolidation_report.txt")
    print(f"\nFinal state:")
    print(f"  bars_1m: {bars_1m_final:,} rows (MGC, MPL, NQ)")
    print(f"  bars_5m: {bars_5m_final:,} rows (MGC, MPL, NQ)")
    print(f"  daily_features_v2: {features_final:,} rows (MGC, MPL, NQ)")
    print(f"\nOld tables archived with timestamp: {timestamp}")
    print("\n" + "=" * 70)

    return True


if __name__ == "__main__":
    try:
        success = consolidate_schema()
        if success:
            print("\n[OK] Ready for MotherDuck migration")
            exit(0)
    except Exception as e:
        print(f"\n[ERROR] Consolidation failed: {e}")
        print("\n[RESTORE] To restore, rename _archive tables back to original names")
        exit(1)
