#!/usr/bin/env python3
"""
Migrate persistent tables from gold.db to MotherDuck.
Safe, verified migration with row count validation.
"""

import os
import sys
import duckdb
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# Tables to migrate (persistent data only)
PERSISTENT_TABLES = [
    'bars_1m',
    'bars_5m',
    'daily_features_v2',
    'validated_setups',
]


def log(msg, indent=0):
    """Print and return log message."""
    prefix = "  " * indent
    full_msg = f"{prefix}{msg}"
    print(full_msg)
    return full_msg


def migrate_to_motherduck():
    """Migrate persistent tables to MotherDuck with verification."""

    # Check token
    token = os.getenv('MOTHERDUCK_TOKEN')
    if not token:
        print("\n[ERROR] MOTHERDUCK_TOKEN not set in .env file")
        print("\nTo get your token:")
        print("1. Go to https://motherduck.com/")
        print("2. Sign up or log in")
        print("3. Settings -> Access Tokens")
        print("4. Add to .env file: MOTHERDUCK_TOKEN=your_token_here")
        return False

    migration_report = {
        'started': datetime.now().isoformat(),
        'tables': {},
        'success': False
    }

    log_lines = []
    log_lines.append("=" * 70)
    log_lines.append("MOTHERDUCK MIGRATION")
    log_lines.append(f"Started: {migration_report['started']}")
    log_lines.append("=" * 70)
    log_lines.append("")

    try:
        # Connect to local
        print("\n" + "=" * 70)
        print("MOTHERDUCK MIGRATION")
        print("=" * 70)

        log("\n[1/5] Connecting to local gold.db...")
        local_conn = duckdb.connect('gold.db', read_only=True)
        log("  [OK] Connected to local database")
        log_lines.append("[1] Connected to local gold.db")

        # Connect to MotherDuck
        log("\n[2/5] Connecting to MotherDuck...")
        md_conn = duckdb.connect(f'md:?motherduck_token={token}')
        log("  [OK] Connected to MotherDuck")
        log_lines.append("[2] Connected to MotherDuck")

        # Attach local database
        log("\n[3/5] Attaching local gold.db...")
        local_db_path = os.path.abspath('gold.db')
        md_conn.execute(f"ATTACH '{local_db_path}' AS local_gold (READ_ONLY)")
        log(f"  [OK] Attached: {local_db_path}")
        log_lines.append(f"[3] Attached local gold.db")

        # Create or use database
        log("\n[4/5] Setting up projectx_prod database...")
        md_conn.execute("CREATE DATABASE IF NOT EXISTS projectx_prod")
        md_conn.execute("USE projectx_prod")
        log("  [OK] Database ready")
        log_lines.append("[4] Database projectx_prod ready")
        log_lines.append("")

        # Migrate each table
        log("\n[4/5] Migrating tables...")
        log_lines.append("[4] Migrating tables:")
        log_lines.append("-" * 70)

        for table in PERSISTENT_TABLES:
            log(f"\n  Migrating: {table}")

            # Get source info
            local_count = local_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            log(f"    Source rows: {local_count:,}", 2)

            # Get timestamp range if applicable
            ts_info = {}
            try:
                if 'bars_' in table:
                    ts_col = 'ts_utc'
                    ts_range = local_conn.execute(
                        f"SELECT MIN({ts_col}), MAX({ts_col}) FROM {table}"
                    ).fetchone()
                    ts_info = {'min_ts': str(ts_range[0]), 'max_ts': str(ts_range[1])}
                    log(f"    Time range: {ts_range[0]} to {ts_range[1]}", 2)
                elif table == 'daily_features':
                    date_range = local_conn.execute(
                        f"SELECT MIN(date_local), MAX(date_local) FROM {table}"
                    ).fetchone()
                    ts_info = {'min_date': str(date_range[0]), 'max_date': str(date_range[1])}
                    log(f"    Date range: {date_range[0]} to {date_range[1]}", 2)
            except:
                pass

            # Drop if exists in MotherDuck
            log(f"    Dropping existing table (if any)...", 2)
            md_conn.execute(f"DROP TABLE IF EXISTS {table}")

            # Create in MotherDuck from local
            log(f"    Creating and uploading...", 2)
            md_conn.execute(f"""
                CREATE TABLE {table} AS
                SELECT * FROM local_gold.{table}
            """)

            # Verify
            log(f"    Verifying...", 2)
            md_count = md_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            log(f"    MotherDuck rows: {md_count:,}", 2)

            if md_count != local_count:
                raise ValueError(f"Row count mismatch for {table}! Local={local_count:,}, MD={md_count:,}")

            log(f"    [OK] Verified", 2)

            # Record in report
            migration_report['tables'][table] = {
                'row_count': local_count,
                **ts_info,
                'verified': True
            }

            log_lines.append(f"  {table}: {local_count:,} rows (VERIFIED)")

        log_lines.append("-" * 70)
        log_lines.append("")

        # Create catalog table
        log("\n[5/5] Creating dataset catalog...")
        md_conn.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                asset VARCHAR,
                timeframe VARCHAR,
                table_name VARCHAR,
                start_ts TIMESTAMP,
                end_ts TIMESTAMP,
                row_count BIGINT,
                last_update_utc TIMESTAMP,
                PRIMARY KEY (asset, timeframe, table_name)
            )
        """)

        # Populate catalog
        for instrument in ['MGC', 'MPL', 'NQ']:
            # 1m bars
            bars_1m_info = md_conn.execute(f"""
                SELECT MIN(ts_utc), MAX(ts_utc), COUNT(*)
                FROM bars_1m
                WHERE symbol = '{instrument}'
            """).fetchone()

            if bars_1m_info[2] > 0:
                md_conn.execute("""
                    INSERT OR REPLACE INTO datasets VALUES (?, '1m', 'bars_1m', ?, ?, ?, CURRENT_TIMESTAMP)
                """, [instrument, bars_1m_info[0], bars_1m_info[1], bars_1m_info[2]])

            # 5m bars
            bars_5m_info = md_conn.execute(f"""
                SELECT MIN(ts_utc), MAX(ts_utc), COUNT(*)
                FROM bars_5m
                WHERE symbol = '{instrument}'
            """).fetchone()

            if bars_5m_info[2] > 0:
                md_conn.execute("""
                    INSERT OR REPLACE INTO datasets VALUES (?, '5m', 'bars_5m', ?, ?, ?, CURRENT_TIMESTAMP)
                """, [instrument, bars_5m_info[0], bars_5m_info[1], bars_5m_info[2]])

            # Daily features
            features_info = md_conn.execute(f"""
                SELECT MIN(date_local), MAX(date_local), COUNT(*)
                FROM daily_features_v2
                WHERE instrument = '{instrument}'
            """).fetchone()

            if features_info[2] > 0:
                md_conn.execute("""
                    INSERT OR REPLACE INTO datasets VALUES (?, 'daily', 'daily_features_v2', ?, ?, ?, CURRENT_TIMESTAMP)
                """, [instrument, features_info[0], features_info[1], features_info[2]])

        catalog_rows = md_conn.execute("SELECT COUNT(*) FROM datasets").fetchone()[0]
        log(f"  [OK] Catalog created with {catalog_rows} entries")
        log_lines.append(f"[5] Dataset catalog created ({catalog_rows} entries)")

        # Close connections
        local_conn.close()
        md_conn.close()

        # Success
        migration_report['success'] = True
        migration_report['finished'] = datetime.now().isoformat()

        # Write reports
        log_lines.append("")
        log_lines.append("=" * 70)
        log_lines.append("MIGRATION SUCCESSFUL")
        log_lines.append(f"Finished: {migration_report['finished']}")
        log_lines.append("=" * 70)

        with open('migration_report.json', 'w') as f:
            json.dump(migration_report, f, indent=2)

        with open('migration_report.txt', 'w') as f:
            f.write('\n'.join(log_lines))

        print("\n" + "=" * 70)
        print("MIGRATION SUCCESSFUL")
        print("=" * 70)
        print(f"\nMigrated {len(PERSISTENT_TABLES)} tables to MotherDuck:")
        for table, info in migration_report['tables'].items():
            print(f"  {table}: {info['row_count']:,} rows")
        print(f"\nReports:")
        print(f"  migration_report.json")
        print(f"  migration_report.txt")
        print("\n" + "=" * 70)

        return True

    except Exception as e:
        migration_report['success'] = False
        migration_report['error'] = str(e)
        migration_report['finished'] = datetime.now().isoformat()

        with open('migration_report.json', 'w') as f:
            json.dump(migration_report, f, indent=2)

        print(f"\n[ERROR] Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = migrate_to_motherduck()
    sys.exit(0 if success else 1)
