"""
Cloud Mode Handler - Makes app work in Streamlit Cloud without local database
"""

import os
from pathlib import Path
import duckdb
import logging

logger = logging.getLogger(__name__)


def is_cloud_deployment() -> bool:
    """Detect if running in Streamlit Cloud"""
    # Streamlit Cloud sets STREAMLIT_SHARING_MODE or has specific paths
    return (
        os.getenv("STREAMLIT_SHARING_MODE") is not None
        or os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud"
        or not Path("../gold.db").exists()  # No local database
    )


def get_database_path() -> str:
    """Get database path appropriate for environment"""
    if is_cloud_deployment():
        # In cloud, use local trading_app.db (will be empty initially)
        # Use absolute path to ensure it's in the app directory
        app_dir = Path(__file__).parent
        db_path = app_dir / "trading_app.db"
        db_path_str = str(db_path)
        
        # Initialize schema if database is newly created
        _ensure_schema_initialized(db_path_str)
        
        return db_path_str
    else:
        # Locally, use parent directory's gold.db
        app_dir = Path(__file__).parent
        db_path = app_dir.parent / "gold.db"
        return str(db_path)


def _ensure_schema_initialized(db_path: str):
    """Initialize database schema if database is newly created or missing tables"""
    try:
        db_path_obj = Path(db_path)
        
        # Check if database exists
        db_exists = db_path_obj.exists()
        
        # Connect to database
        con = duckdb.connect(db_path)
        
        try:
            # Check if daily_features_v2 table exists
            tables = con.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'main'
            """).fetchall()
            
            table_names = [t[0] for t in tables]
            
            # Initialize schema if needed
            needs_init = False
            
            if 'daily_features_v2' not in table_names:
                logger.info(f"Initializing daily_features_v2 table in {db_path}")
                _init_daily_features_v2(con)
                needs_init = True
            
            if 'validated_setups' not in table_names:
                logger.info(f"Initializing validated_setups table in {db_path}")
                _init_validated_setups(con)
                needs_init = True
            
            if needs_init:
                logger.info(f"Schema initialized for {db_path}")
        
        finally:
            con.close()
    
    except Exception as e:
        logger.warning(f"Could not initialize schema for {db_path}: {e}")


def _init_daily_features_v2(con: duckdb.DuckDBPyConnection):
    """Create daily_features_v2 table"""
    con.execute("""
        CREATE TABLE IF NOT EXISTS daily_features_v2 (
            date_local DATE NOT NULL,
            instrument VARCHAR NOT NULL,
            
            pre_asia_high DOUBLE,
            pre_asia_low DOUBLE,
            pre_asia_range DOUBLE,
            pre_london_high DOUBLE,
            pre_london_low DOUBLE,
            pre_london_range DOUBLE,
            pre_ny_high DOUBLE,
            pre_ny_low DOUBLE,
            pre_ny_range DOUBLE,
            
            asia_high DOUBLE,
            asia_low DOUBLE,
            asia_range DOUBLE,
            london_high DOUBLE,
            london_low DOUBLE,
            london_range DOUBLE,
            ny_high DOUBLE,
            ny_low DOUBLE,
            ny_range DOUBLE,
            asia_type_code VARCHAR,
            london_type_code VARCHAR,
            pre_ny_type_code VARCHAR,
            
            orb_0900_high DOUBLE,
            orb_0900_low DOUBLE,
            orb_0900_size DOUBLE,
            orb_0900_break_dir VARCHAR,
            orb_0900_outcome VARCHAR,
            orb_0900_r_multiple DOUBLE,
            
            orb_1000_high DOUBLE,
            orb_1000_low DOUBLE,
            orb_1000_size DOUBLE,
            orb_1000_break_dir VARCHAR,
            orb_1000_outcome VARCHAR,
            orb_1000_r_multiple DOUBLE,
            
            orb_1100_high DOUBLE,
            orb_1100_low DOUBLE,
            orb_1100_size DOUBLE,
            orb_1100_break_dir VARCHAR,
            orb_1100_outcome VARCHAR,
            orb_1100_r_multiple DOUBLE,
            
            orb_1800_high DOUBLE,
            orb_1800_low DOUBLE,
            orb_1800_size DOUBLE,
            orb_1800_break_dir VARCHAR,
            orb_1800_outcome VARCHAR,
            orb_1800_r_multiple DOUBLE,
            
            orb_2300_high DOUBLE,
            orb_2300_low DOUBLE,
            orb_2300_size DOUBLE,
            orb_2300_break_dir VARCHAR,
            orb_2300_outcome VARCHAR,
            orb_2300_r_multiple DOUBLE,
            
            orb_0030_high DOUBLE,
            orb_0030_low DOUBLE,
            orb_0030_size DOUBLE,
            orb_0030_break_dir VARCHAR,
            orb_0030_outcome VARCHAR,
            orb_0030_r_multiple DOUBLE,
            
            rsi_at_0030 DOUBLE,
            atr_20 DOUBLE,
            
            PRIMARY KEY (date_local, instrument)
        )
    """)


def _init_validated_setups(con: duckdb.DuckDBPyConnection):
    """Create validated_setups table"""
    con.execute("""
        CREATE TABLE IF NOT EXISTS validated_setups (
            setup_id VARCHAR NOT NULL,
            instrument VARCHAR NOT NULL,
            orb_time VARCHAR NOT NULL,
            rr DOUBLE NOT NULL,
            sl_mode VARCHAR NOT NULL,
            close_confirmations INTEGER,
            buffer_ticks DOUBLE,
            orb_size_filter DOUBLE,
            atr_filter DOUBLE,
            min_gap_filter DOUBLE,
            trades INTEGER,
            win_rate DOUBLE,
            avg_r DOUBLE,
            annual_trades INTEGER,
            tier VARCHAR,
            notes VARCHAR,
            validated_date DATE,
            data_source VARCHAR,
            
            PRIMARY KEY (setup_id)
        )
    """)


def show_cloud_setup_instructions():
    """Display instructions for setting up data in cloud"""
    import streamlit as st

    st.warning("⚠️ Cloud Deployment Detected - Database Not Found")

    st.info("""
    **Your app is running in the cloud!**

    The local `gold.db` database is not available here. You have two options:

    **Option 1: Demo Mode (Recommended for testing)**
    - The app will work with AI chat and strategy explanations
    - No live data or backtesting available yet
    - Perfect for exploring the interface on mobile

    **Option 2: Backfill Data in Cloud**
    1. Add your `DATABENTO_API_KEY` to Streamlit Cloud secrets
    2. Click "Initialize/Refresh Data" to backfill from Databento
    3. This will download and store data in the cloud

    **To use Demo Mode now:**
    - AI Chat tab works immediately
    - Ask strategy questions, get calculations
    - Test the interface on your phone

    **To backfill data:**
    - Go to https://share.streamlit.io/
    - Open your app settings → Secrets
    - Add: `ANTHROPIC_API_KEY`, `DATABENTO_API_KEY`, etc.
    - Restart the app and click "Initialize/Refresh Data"
    """)


def get_demo_data():
    """Return demo/placeholder data for cloud mode"""
    from datetime import datetime, timedelta
    import pandas as pd

    # Generate some demo bars for visualization
    now = datetime.now()
    demo_bars = []

    for i in range(100):
        ts = now - timedelta(minutes=100-i)
        price = 2700 + (i % 20) - 10  # Oscillating around 2700
        demo_bars.append({
            "ts_local": ts,
            "open": price,
            "high": price + 2,
            "low": price - 2,
            "close": price + 1,
            "volume": 1000
        })

    return pd.DataFrame(demo_bars)


def get_demo_strategy_result():
    """Return demo strategy evaluation"""
    return {
        "strategy_name": "DEMO_MODE",
        "action": "STAND_DOWN",
        "state": "DEMO",
        "reasons": [
            "Cloud deployment detected",
            "No database connected",
            "Add API keys to enable live data"
        ],
        "next_action": "Set up Databento API in Streamlit Cloud secrets",
        "entry_price": None,
        "stop_price": None,
        "target_price": None,
        "risk_pct": None
    }
