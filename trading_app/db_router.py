#!/usr/bin/env python3
"""
Database router - single source of truth for database connections.
Handles local vs cloud mode transparently.

CRITICAL: This is the ONLY file allowed to call duckdb.connect()
All other files must use get_connection() from this module.
"""

import os
import duckdb
from pathlib import Path
from dotenv import load_dotenv

# Load .env from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


# Configuration
CLOUD_MODE = os.getenv('CLOUD_MODE', '0') == '1'
MOTHERDUCK_TOKEN = os.getenv('MOTHERDUCK_TOKEN', '')
LOCAL_DB_PATH = os.getenv('DUCKDB_PATH', 'gold.db')
CACHE_DB_PATH = 'live_data.db'

# Persistent tables (stored in MotherDuck when CLOUD_MODE=1)
PERSISTENT_TABLES = {
    'bars_1m',
    'bars_5m',
    'daily_features_v2',
    'validated_setups',
}

# Cache-only tables (always local, even in cloud mode)
CACHE_TABLES = {
    'live_bars',
    'live_journal',
    'ml_predictions',
    'ml_performance',
}


def get_connection(purpose='read'):
    """
    Get database connection based on mode and purpose.

    Args:
        purpose: 'read' (read persistent data), 'write' (write persistent data),
                 'cache' (read/write cache), 'local' (force local)

    Returns:
        duckdb.Connection
    """

    if purpose == 'cache':
        # Cache DB - always local, self-healing
        return _get_cache_connection()

    elif purpose == 'local' or not CLOUD_MODE:
        # Local mode - use gold.db
        return duckdb.connect(LOCAL_DB_PATH)

    elif CLOUD_MODE:
        # Cloud mode - use MotherDuck for persistent data
        if not MOTHERDUCK_TOKEN:
            raise ValueError("CLOUD_MODE=1 but MOTHERDUCK_TOKEN not set")

        # Connect to MotherDuck
        conn = duckdb.connect(f'md:projectx_prod?motherduck_token={MOTHERDUCK_TOKEN}')

        # Attach local gold.db as fallback (if not already attached)
        try:
            conn.execute(f"ATTACH IF NOT EXISTS '{LOCAL_DB_PATH}' AS local_db (READ_ONLY)")
        except:
            # Database might already be attached, ignore error
            pass

        return conn

    else:
        raise ValueError(f"Invalid configuration: CLOUD_MODE={CLOUD_MODE}")


def _get_cache_connection():
    """
    Get cache database connection with self-healing.
    Cache DB stores ephemeral data (live bars, predictions, journal).
    """

    cache_path = Path(CACHE_DB_PATH)

    # Self-heal: Remove stale WAL files
    for wal_file in cache_path.parent.glob(f'{cache_path.name}.wal*'):
        try:
            wal_file.unlink()
        except:
            pass

    try:
        # Try to connect
        conn = duckdb.connect(str(cache_path))

        # Verify connection works
        conn.execute("SELECT 1").fetchone()

        return conn

    except Exception as e:
        # Cache DB corrupted - rebuild
        print(f"[WARN] Cache DB corrupted, rebuilding: {e}")

        # Delete corrupted cache
        if cache_path.exists():
            cache_path.unlink()

        # Create fresh cache DB
        conn = duckdb.connect(str(cache_path))

        # Initialize cache tables
        _initialize_cache_tables(conn)

        return conn


def _initialize_cache_tables(conn):
    """Initialize cache database tables."""

    # live_bars - recent bars for live trading
    conn.execute("""
        CREATE TABLE IF NOT EXISTS live_bars (
            ts_utc TIMESTAMPTZ,
            symbol VARCHAR,
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume BIGINT,
            PRIMARY KEY (ts_utc, symbol)
        )
    """)

    # live_journal - trading decisions log
    conn.execute("""
        CREATE TABLE IF NOT EXISTS live_journal (
            ts_local TIMESTAMPTZ,
            strategy_name VARCHAR,
            state VARCHAR,
            action VARCHAR,
            reasons VARCHAR,
            next_instruction VARCHAR,
            entry_price DOUBLE,
            stop_price DOUBLE,
            target_price DOUBLE,
            risk_pct DOUBLE
        )
    """)

    # ml_predictions - ML model predictions
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ml_predictions (
            prediction_id VARCHAR PRIMARY KEY,
            timestamp_utc TIMESTAMP,
            instrument VARCHAR,
            orb_time VARCHAR,
            strategy_name VARCHAR,
            predicted_direction VARCHAR,
            confidence FLOAT,
            confidence_level VARCHAR,
            prob_up FLOAT,
            prob_down FLOAT,
            prob_none FLOAT,
            risk_adjustment FLOAT,
            orb_size FLOAT,
            atr_14 FLOAT,
            rsi_14 FLOAT,
            actual_direction VARCHAR,
            actual_r_multiple FLOAT,
            win BOOLEAN,
            outcome_logged_at TIMESTAMP
        )
    """)

    # ml_performance - ML model performance tracking
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ml_performance (
            date_local DATE,
            instrument VARCHAR,
            model_version VARCHAR,
            total_predictions INTEGER,
            correct_predictions INTEGER,
            directional_accuracy FLOAT,
            avg_confidence FLOAT,
            wins INTEGER,
            losses INTEGER,
            win_rate FLOAT,
            avg_r_multiple FLOAT,
            created_at TIMESTAMP,
            PRIMARY KEY (date_local, instrument, model_version)
        )
    """)


def health_check():
    """
    Check database health and return status.

    Returns:
        dict with status, data_source, and table_info
    """

    try:
        conn = get_connection(purpose='read')

        # Check persistent tables
        table_info = {}
        for table in PERSISTENT_TABLES:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

                # Get latest timestamp
                if 'bars_' in table:
                    max_ts = conn.execute(f"SELECT MAX(ts_utc) FROM {table}").fetchone()[0]
                    table_info[table] = {'count': count, 'max_ts': str(max_ts)}
                elif table == 'daily_features_v2':
                    max_date = conn.execute(f"SELECT MAX(date_local) FROM {table}").fetchone()[0]
                    table_info[table] = {'count': count, 'max_date': str(max_date)}
                else:
                    table_info[table] = {'count': count}

            except Exception as e:
                table_info[table] = {'error': str(e)}

        conn.close()

        return {
            'status': 'healthy',
            'data_source': 'MotherDuck' if CLOUD_MODE else 'Local',
            'cloud_mode': CLOUD_MODE,
            'tables': table_info
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'data_source': 'MotherDuck' if CLOUD_MODE else 'Local',
            'cloud_mode': CLOUD_MODE
        }


if __name__ == "__main__":
    # Test connections
    print("=" * 70)
    print("DATABASE ROUTER TEST")
    print("=" * 70)

    print(f"\nConfiguration:")
    print(f"  CLOUD_MODE: {CLOUD_MODE}")
    print(f"  LOCAL_DB_PATH: {LOCAL_DB_PATH}")
    print(f"  CACHE_DB_PATH: {CACHE_DB_PATH}")

    print(f"\n[1/3] Testing read connection...")
    try:
        conn = get_connection(purpose='read')
        version = conn.execute("SELECT version()").fetchone()[0]
        print(f"  [OK] Connected: {version}")
        conn.close()
    except Exception as e:
        print(f"  [ERROR] {e}")

    print(f"\n[2/3] Testing cache connection...")
    try:
        conn = get_connection(purpose='cache')
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"  [OK] Cache DB has {len(tables)} tables")
        conn.close()
    except Exception as e:
        print(f"  [ERROR] {e}")

    print(f"\n[3/3] Running health check...")
    health = health_check()
    print(f"  Status: {health['status']}")
    print(f"  Data source: {health['data_source']}")
    if 'error' in health:
        print(f"  [ERROR] {health['error']}")
    if 'tables' in health:
        print(f"  Tables checked: {len(health['tables'])}")
        for table, info in health['tables'].items():
            if 'error' in info:
                print(f"    - {table}: ERROR - {info['error']}")
            elif 'count' in info:
                print(f"    - {table}: {info['count']:,} rows")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
