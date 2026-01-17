"""
Mobile Trading App Entry Point
This file exists so Streamlit Cloud auto-detects and runs the mobile app.
"""

# Import and run the mobile app
import sys
from pathlib import Path

# Ensure trading_app is in path
sys.path.insert(0, str(Path(__file__).parent / "trading_app"))

# Run mobile app
from trading_app import app_mobile
