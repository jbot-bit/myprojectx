"""
Debug Script - Check App Status
"""

import sys
from pathlib import Path

# Add trading_app to path
sys.path.insert(0, str(Path(__file__).parent / "trading_app"))

print("=" * 80)
print("APP DEBUG INFORMATION")
print("=" * 80)

# Test 1: Check imports
print("\n1. Testing Core Imports...")
try:
    from config import PRIMARY_INSTRUMENT, TZ_LOCAL, DB_PATH
    print(f"   ✓ config.py - Symbol: {PRIMARY_INSTRUMENT}, TZ: {TZ_LOCAL}")
except Exception as e:
    print(f"   ✗ config.py failed: {e}")
    sys.exit(1)

try:
    from data_loader import LiveDataLoader
    print("   ✓ data_loader.py")
except Exception as e:
    print(f"   ✗ data_loader.py failed: {e}")
    sys.exit(1)

try:
    from strategy_engine import StrategyEngine
    print("   ✓ strategy_engine.py")
except Exception as e:
    print(f"   ✗ strategy_engine.py failed: {e}")
    sys.exit(1)

try:
    from live_chart_builder import build_live_trading_chart, calculate_trade_levels
    print("   ✓ live_chart_builder.py")
except Exception as e:
    print(f"   ✗ live_chart_builder.py failed: {e}")
    sys.exit(1)

try:
    from professional_ui import inject_professional_css
    print("   ✓ professional_ui.py")
except Exception as e:
    print(f"   ✗ professional_ui.py failed: {e}")
    sys.exit(1)

try:
    from streamlit_autorefresh import st_autorefresh
    print("   ✓ streamlit_autorefresh")
except Exception as e:
    print(f"   ✗ streamlit_autorefresh failed: {e}")
    print("   → Run: pip install streamlit-autorefresh")

# Test 2: Check database files
print("\n2. Checking Database Files...")
import os

db_files = [
    ("../gold.db", "Main historical data"),
    ("live_data.db", "Live market data"),
    ("trading_app.db", "AI memory")
]

for db_file, description in db_files:
    db_path = Path(__file__).parent / "trading_app" / db_file
    if db_path.exists():
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"   ✓ {db_file} ({size_mb:.1f} MB) - {description}")
    else:
        print(f"   ✗ {db_file} NOT FOUND - {description}")

# Test 3: Check app files
print("\n3. Checking App Files...")
app_files = [
    "trading_app/app_simplified.py",
    "trading_app/app_trading_hub.py",
    "trading_app/config.py",
    "trading_app/data_loader.py",
    "trading_app/strategy_engine.py",
    "trading_app/live_chart_builder.py"
]

for app_file in app_files:
    file_path = Path(__file__).parent / app_file
    if file_path.exists():
        lines = len(open(file_path, 'r', encoding='utf-8').readlines())
        print(f"   ✓ {app_file} ({lines} lines)")
    else:
        print(f"   ✗ {app_file} NOT FOUND")

# Test 4: Check if Streamlit is running
print("\n4. Checking Streamlit Status...")
import socket

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

if check_port(8502):
    print("   ✓ Streamlit is running on port 8502")
    print("   → URL: http://localhost:8502")
else:
    print("   ✗ Streamlit NOT running on port 8502")
    print("   → Run: cd trading_app && streamlit run app_simplified.py")

# Test 5: Test data loader initialization (quick test)
print("\n5. Testing Data Loader (Quick)...")
try:
    # Don't actually load data, just check initialization
    print("   ℹ Skipping full data load (would take 10+ seconds)")
    print("   ℹ To test: Click 'Initialize/Refresh Data' in app")
except Exception as e:
    print(f"   ✗ Data loader test failed: {e}")

# Test 6: Check environment variables
print("\n6. Checking Environment Variables...")
import os
from dotenv import load_dotenv

# Try to load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print("   ✓ .env file found")

    # Check critical vars
    critical_vars = [
        "PROJECTX_API_KEY",
        "PROJECTX_USERNAME",
        "DUCKDB_PATH",
        "ANTHROPIC_API_KEY"
    ]

    for var in critical_vars:
        value = os.getenv(var)
        if value:
            # Mask API keys
            if "KEY" in var:
                masked = value[:8] + "..." if len(value) > 8 else "***"
                print(f"   ✓ {var} = {masked}")
            else:
                print(f"   ✓ {var} = {value}")
        else:
            print(f"   ✗ {var} NOT SET")
else:
    print("   ✗ .env file NOT FOUND")

# Summary
print("\n" + "=" * 80)
print("DEBUG SUMMARY")
print("=" * 80)

print("\nIf all checks passed:")
print("  1. Open: http://localhost:8502")
print("  2. Click 'Initialize/Refresh Data' in sidebar")
print("  3. Wait 5-10 seconds for data to load")
print("  4. You should see live price, signals, and chart")

print("\nIf app won't load:")
print("  1. Check .env has PROJECTX_API_KEY")
print("  2. Verify internet connection")
print("  3. Check app logs in browser console (F12)")
print("  4. Try: cd trading_app && streamlit run app_simplified.py")

print("\nCommon Issues:")
print("  • Database locked: Kill all python/streamlit processes")
print("  • No data: Click 'Initialize/Refresh Data' button")
print("  • Import errors: pip install -r requirements.txt")
print("  • Auto-refresh not working: Check it's enabled in sidebar")

print("\n" + "=" * 80)
