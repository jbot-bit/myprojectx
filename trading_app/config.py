"""
TRADING APP CONFIGURATION
All constants, thresholds, and settings in one place.
"""

import os
from datetime import timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from dotenv import load_dotenv

# Load .env from parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# ============================================================================
# TIMEZONE & TIME CONSTANTS
# ============================================================================
TZ_LOCAL = ZoneInfo("Australia/Brisbane")  # UTC+10, no DST
TZ_UTC = ZoneInfo("UTC")

# ============================================================================
# INSTRUMENT CONFIGURATION
# ============================================================================
PRIMARY_INSTRUMENT = os.getenv("PRIMARY_INSTRUMENT", "MNQ")  # Default: Micro NQ
SECONDARY_INSTRUMENT = "MGC"  # Micro Gold (optional)
TERTIARY_INSTRUMENT = "MPL"  # Micro Platinum (optional)
ENABLE_SECONDARY = False  # Toggle via UI

# ============================================================================
# SESSION DEFINITIONS (LOCAL TIME UTC+10)
# ============================================================================
SESSIONS = {
    "ASIA": {"start_hour": 9, "start_min": 0, "end_hour": 17, "end_min": 0},
    "LONDON": {"start_hour": 18, "start_min": 0, "end_hour": 23, "end_min": 0},
    "NY_FUTURES": {"start_hour": 23, "start_min": 0, "end_hour": 2, "end_min": 0},  # Next day
}

# ORB times (local)
ORB_TIMES = [
    {"hour": 9, "min": 0, "name": "0900"},
    {"hour": 10, "min": 0, "name": "1000"},
    {"hour": 11, "min": 0, "name": "1100"},
    {"hour": 18, "min": 0, "name": "1800"},   # London open (Asia close)
    {"hour": 23, "min": 0, "name": "2300"},
    {"hour": 0, "min": 30, "name": "0030"},  # Next day
]

ORB_DURATION_MIN = 5  # 5-minute ORB window

# ============================================================================
# STRATEGY HIERARCHY (PRIORITY ORDER)
# ============================================================================
STRATEGY_PRIORITY = [
    "MULTI_LIQUIDITY_CASCADE",  # A+ tier
    # "PROXIMITY_PRESSURE",        # FAILED: -0.50R avg, 1.1% freq (DISABLED 2026-01-15)
    "NIGHT_ORB",                 # B tier (23:00, 00:30)
    "SINGLE_LIQUIDITY",          # B-Backup tier
    "DAY_ORB",                   # C tier (09:00, 10:00, 11:00)
]

# ============================================================================
# CASCADE STRATEGY PARAMETERS (From validation testing)
# ============================================================================
CASCADE_MIN_GAP_POINTS = 9.5  # Minimum gap between liquidity levels
CASCADE_ENTRY_TOLERANCE = 0.1  # Entry within 0.1 points of level
CASCADE_FAILURE_BARS = 3  # Check next 3 bars for acceptance failure
CASCADE_MAX_HOLD_MINUTES = 90  # Maximum hold time

# ============================================================================
# PROXIMITY PRESSURE PARAMETERS (DISABLED - FAILED TESTING)
# ============================================================================
# WARNING: This strategy tested at -0.50R avg, 1.1% frequency. FAILED.
# Disabled in STRATEGY_PRIORITY list above (2026-01-15).
# Kept for reference but not evaluated by strategy engine.
PROXIMITY_MAX_DISTANCE_POINTS = 5.0  # Levels within 5 points
PROXIMITY_ATR_MULTIPLIER = 0.3  # OR within 0.3 * ATR
PROXIMITY_TAG_WINDOW_MIN = 5  # Minutes to tag second level

# ============================================================================
# ORB STRATEGY PARAMETERS (INSTRUMENT-SPECIFIC)
# ============================================================================

# MGC (Micro Gold) - CANONICAL Configuration
# Source: Database verification (2026-01-14)
# Note: Win rates are per TRADE (excluding no-breakout days)
MGC_ORB_CONFIGS = {
    "0900": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"},  # 70.3% days break, 71.5% WR, +0.431R avg, ~+111R/yr
    "1000": {"rr": 3.0, "sl_mode": "FULL", "tier": "DAY"},  # 70.7% days break, 67.1% WR, +0.342R avg, ~+88R/yr
    "1100": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"},  # 70.7% days break, 72.5% WR, +0.449R avg, ~+116R/yr
    "1800": {"rr": 1.0, "sl_mode": "HALF", "tier": "DAY"},  # 70.5% days break, 71.3% WR, +0.425R avg, ~+110R/yr
    "2300": {"rr": 1.0, "sl_mode": "HALF", "tier": "NIGHT"},  # 70.5% days break, 69.3% WR, +0.387R avg, ~+100R/yr
    "0030": {"rr": 1.0, "sl_mode": "HALF", "tier": "NIGHT"},  # 70.7% days break, 61.6% WR, +0.231R avg, ~+60R/yr
}

MGC_ORB_SIZE_FILTERS = {
    "2300": 0.155,  # Skip if orb_size > 0.155 * ATR(20)
    "0030": 0.112,  # Skip if orb_size > 0.112 * ATR(20)
    "1100": 0.095,  # Skip if orb_size > 0.095 * ATR(20)
    "1000": 0.088,  # Skip if orb_size > 0.088 * ATR(20)
    "0900": None,   # No filter
    "1800": None,   # No filter (session open, not exhaustion)
}

# NQ (Micro Nasdaq) - Optimized configuration
NQ_ORB_CONFIGS = {
    "0900": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"},     # +0.145R avg (with filter)
    "1000": {"rr": 1.5, "sl_mode": "FULL", "tier": "DAY"},     # +0.174R avg
    "1100": {"rr": 1.5, "sl_mode": "FULL", "tier": "DAY"},     # +0.260R avg
    "1800": {"rr": 1.5, "sl_mode": "HALF", "tier": "DAY"},     # +0.257R avg
    "2300": {"rr": None, "sl_mode": None, "tier": "SKIP"},     # SKIP (negative)
    "0030": {"rr": 1.0, "sl_mode": "HALF", "tier": "NIGHT"},   # +0.292R avg
}

NQ_ORB_SIZE_FILTERS = {
    "0900": 0.050,  # Small ORBs only (+233% improvement!)
    "1000": 0.100,  # Filter large ORBs
    "1100": 0.100,  # Filter large ORBs
    "1800": 0.120,  # Filter large ORBs
    "2300": None,   # SKIP this ORB entirely
    "0030": None,   # No filter (baseline best)
}

# MPL (Platinum) - VALIDATED CONFIGURATION (2026-01-15)
# Backtest: 365 days (2025-01-13 to 2026-01-12), ALL 6 ORBs profitable
# Total: +288R, Win rates: 55-67%, GREEN LIGHT for live trading
# Note: Full-size PL contracts ($50/point), excellent diversification with MGC/NQ
MPL_ORB_CONFIGS = {
    "0900": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"},      # 57.6% WR, +55R (Tier B)
    "1000": {"rr": 1.0, "sl_mode": "FULL", "tier": "SWING"},    # 56.1% WR, +31R (Tier C)
    "1100": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"},      # 67.1% WR, +88R (Tier A - BEST)
    "1800": {"rr": 1.0, "sl_mode": "FULL", "tier": "SWING"},    # 55.1% WR, +27R (Tier C)
    "2300": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"},      # 62.9% WR, +77R (Tier A - EXCELLENT)
    "0030": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"},      # 58.0% WR, +52R (Tier B)
}

MPL_ORB_SIZE_FILTERS = {
    "2300": None,  # No filter (strong baseline)
    "0030": None,  # No filter (strong baseline)
    "1100": None,  # No filter (BEST ORB - 67.1% WR)
    "1000": None,  # No filter (baseline sufficient)
    "0900": None,  # No filter (strong baseline)
    "1800": None,  # No filter (baseline sufficient)
}

# Dynamic configs (loaded based on selected instrument)
ORB_CONFIGS = MGC_ORB_CONFIGS  # Default to MGC
ORB_SIZE_FILTERS = MGC_ORB_SIZE_FILTERS

# Enable/disable filters globally
ENABLE_ORB_SIZE_FILTERS = True

# ============================================================================
# SINGLE LIQUIDITY PARAMETERS
# ============================================================================
SINGLE_LIQ_ENTRY_TOLERANCE = 0.1
SINGLE_LIQ_FAILURE_BARS = 3

# ============================================================================
# DATA INGESTION
# ============================================================================
DATA_WINDOW_HOURS = 48  # Keep 48 hours of rolling data
DATA_REFRESH_SECONDS = 5  # Refresh every 5 seconds

# ProjectX API (for live data)
PROJECTX_USERNAME = os.getenv("PROJECTX_USERNAME", "")
PROJECTX_API_KEY = os.getenv("PROJECTX_API_KEY", "")
PROJECTX_BASE_URL = os.getenv("PROJECTX_BASE_URL", "https://api.topstepx.com")
PROJECTX_LIVE = os.getenv("PROJECTX_LIVE", "false").lower() == "true"

# Databento API (backup/alternative)
DATABENTO_API_KEY = os.getenv("DATABENTO_API_KEY", "")

# ============================================================================
# RISK MANAGEMENT
# ============================================================================
DEFAULT_ACCOUNT_SIZE = 100000.0  # $100k default
RISK_LIMITS = {
    "CASCADE": {"min": 0.10, "max": 0.25, "default": 0.25},  # % of account
    "PROXIMITY": {"min": 0.10, "max": 0.50, "default": 0.25},
    "NIGHT_ORB": {"min": 0.25, "max": 0.50, "default": 0.50},
    "SINGLE_LIQ": {"min": 0.25, "max": 0.50, "default": 0.25},
    "DAY_ORB": {"min": 0.10, "max": 0.25, "default": 0.10},
}

# ============================================================================
# DATABASE
# ============================================================================
DB_PATH = "trading_app.db"  # Separate from backtest DB
JOURNAL_TABLE = "live_journal"

# ============================================================================
# UI SETTINGS
# ============================================================================
CHART_HEIGHT = 600
CHART_LOOKBACK_BARS = 200
UPDATE_INTERVAL_MS = 5000  # 5 seconds

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL = "INFO"
LOG_FILE = "trading_app.log"
