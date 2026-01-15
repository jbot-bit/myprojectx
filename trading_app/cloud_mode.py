"""
Cloud Mode Handler - Makes app work in Streamlit Cloud without local database
"""

import os
from pathlib import Path


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
        return "trading_app.db"
    else:
        # Locally, use parent directory's gold.db
        return "../gold.db"


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
