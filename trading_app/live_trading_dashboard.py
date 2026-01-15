"""
LIVE TRADING DASHBOARD - Real Market Data Integration
Reads current market conditions, tracks ORB outcomes, applies filters dynamically
"""

import streamlit as st
import pandas as pd
import duckdb
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from strategy_recommender import recommend_strategy

# Page config
st.set_page_config(
    page_title="Live Trading Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
    }

    /* Headers */
    h1, h2, h3 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        font-size: 16px;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 12px 24px;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }

    .stButton>button:hover {
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }

    /* Number inputs */
    [data-testid="stNumberInput"] input {
        font-size: 18px;
        font-weight: 600;
        border-radius: 8px;
        border: 2px solid #667eea;
    }

    /* Radio buttons */
    [data-testid="stRadio"] {
        background: rgba(255,255,255,0.05);
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Timezone
TZ_LOCAL = ZoneInfo("Australia/Brisbane")
TZ_UTC = ZoneInfo("UTC")

# ============================================================================
# CONFIGS
# ============================================================================

MGC_ORB_CONFIGS = {
    "0900": {"rr": 1.0, "sl_mode": "FULL", "avg_r": 0.431, "win_rate": 71.5, "filter_fn": None, "reason": "High WR baseline (70% days, ~+111R/yr)", "tier": "A"},
    "1000": {"rr": 3.0, "sl_mode": "FULL", "avg_r": 0.342, "win_rate": 67.1, "filter_fn": "check_max_stop", "max_ticks": 100, "reason": "Best Asia ORB (~+88R/yr)", "tier": "A"},
    "1100": {"rr": 1.0, "sl_mode": "FULL", "avg_r": 0.449, "win_rate": 72.5, "filter_fn": None, "reason": "SAFEST - 72.5% WR (~+116R/yr)", "tier": "A"},
    "1800": {"rr": 1.0, "sl_mode": "HALF", "avg_r": 0.425, "win_rate": 71.3, "filter_fn": None, "reason": "London Open - 71.3% WR (~+110R/yr)", "tier": "A", "warning": "PAPER TRADE FIRST"},
    "2300": {"rr": 1.0, "sl_mode": "HALF", "avg_r": 0.387, "win_rate": 69.3, "filter_fn": None, "reason": "Night session (71% days, ~+100R/yr)", "tier": "A"},
    "0030": {"rr": 1.0, "sl_mode": "HALF", "avg_r": 0.231, "win_rate": 61.6, "filter_fn": None, "reason": "Late night (71% days, ~+60R/yr)", "tier": "A"},
}

MNQ_ORB_CONFIGS = {
    "0900": {"rr": 1.0, "sl_mode": "FULL", "avg_r": 0.145, "win_rate": 53.0, "filter_fn": "check_orb_size", "max_ticks": 50, "tier": "A"},
    "1000": {"rr": 1.5, "sl_mode": "FULL", "avg_r": 0.174, "win_rate": 54.5, "filter_fn": "check_orb_size", "max_ticks": 50, "tier": "A"},
    "1100": {"rr": 1.5, "sl_mode": "FULL", "avg_r": 0.260, "win_rate": 56.0, "filter_fn": "check_orb_size", "max_ticks": 50, "tier": "A"},
    "1800": {"rr": 1.5, "sl_mode": "HALF", "avg_r": 0.257, "win_rate": 55.8, "filter_fn": "check_orb_size", "max_ticks": 60, "tier": "A"},
    "2300": {"rr": None, "sl_mode": "SKIP", "avg_r": -0.15, "win_rate": 48.0, "filter_fn": None, "tier": "SKIP"},
    "0030": {"rr": 1.0, "sl_mode": "HALF", "avg_r": 0.292, "win_rate": 57.5, "filter_fn": None, "tier": "A"},
}

ORB_TIMES = [
    {"hour": 9, "min": 0, "name": "0900"},
    {"hour": 10, "min": 0, "name": "1000"},
    {"hour": 11, "min": 0, "name": "1100"},
    {"hour": 18, "min": 0, "name": "1800"},
    {"hour": 23, "min": 0, "name": "2300"},
    {"hour": 0, "min": 30, "name": "0030"},
]

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

@st.cache_resource
def get_db_connection():
    """Connect to gold.db"""
    try:
        return duckdb.connect("../gold.db", read_only=True)
    except:
        return None

# ============================================================================
# MARKET DATA FUNCTIONS
# ============================================================================

def get_current_price(con, instrument):
    """Get most recent price from database"""
    if not con:
        return None

    try:
        table = "bars_1m" if instrument == "MGC" else "bars_1m_nq"
        symbol_filter = "WHERE symbol = 'MGC'" if instrument == "MGC" else ""

        query = f"""
            SELECT ts_utc, close, high, low
            FROM {table}
            {symbol_filter}
            ORDER BY ts_utc DESC
            LIMIT 1
        """

        result = con.execute(query).fetchone()
        if result:
            return {
                "time": result[0],
                "price": result[1],
                "high": result[2],
                "low": result[3]
            }
    except:
        pass

    return None

def get_orb_from_db(con, instrument, orb_name, date_local):
    """Get ORB high/low from database for a specific day"""
    if not con:
        return None

    try:
        table = "daily_features_v2" if instrument == "MGC" else "daily_features_v2_nq"

        query = f"""
            SELECT
                orb_{orb_name}_high,
                orb_{orb_name}_low,
                orb_{orb_name}_break_dir
            FROM {table}
            WHERE date_local = ?
        """

        result = con.execute(query, [date_local]).fetchone()
        if result and result[0] is not None:
            return {
                "high": result[0],
                "low": result[1],
                "break_dir": result[2],
                "size": result[0] - result[1] if result[0] and result[1] else 0
            }
    except:
        pass

    return None

def get_session_high_low(con, instrument, start_time, end_time):
    """Get session high/low between times"""
    if not con:
        return None

    try:
        table = "bars_1m" if instrument == "MGC" else "bars_1m_nq"
        symbol_filter = "AND symbol = 'MGC'" if instrument == "MGC" else ""

        query = f"""
            SELECT MAX(high), MIN(low)
            FROM {table}
            WHERE ts_utc >= ? AND ts_utc < ? {symbol_filter}
        """

        result = con.execute(query, [start_time, end_time]).fetchone()
        if result and result[0]:
            return {"high": result[0], "low": result[1]}
    except:
        pass

    return None

def check_orb_mfe(con, instrument, orb_name, date_local):
    """Check if prior ORB hit 1R MFE"""
    if not con:
        return False

    try:
        table = "daily_features_v2" if instrument == "MGC" else "daily_features_v2_nq"

        query = f"""
            SELECT orb_{orb_name}_mfe
            FROM {table}
            WHERE date_local = ?
        """

        result = con.execute(query, [date_local]).fetchone()
        if result and result[0]:
            return result[0] >= 1.0  # Hit 1R MFE
    except:
        pass

    return False

def get_pre_ny_travel(con, instrument, date_local):
    """Get pre-NY travel for 00:30 filter"""
    if not con:
        return None

    try:
        table = "daily_features_v2" if instrument == "MGC" else "daily_features_v2_nq"

        query = f"""
            SELECT pre_ny_travel
            FROM {table}
            WHERE date_local = ?
        """

        result = con.execute(query, [date_local]).fetchone()
        if result and result[0]:
            return result[0]
    except:
        pass

    return None

# ============================================================================
# FILTER LOGIC
# ============================================================================

def apply_filters(con, instrument, orb_name, config, orb_data, now_local):
    """Apply filters and return trade decision"""

    filter_fn = config.get("filter_fn")

    if not filter_fn:
        return {"allow_trade": True, "reason": "No filter required"}

    # MGC MAX_STOP filter (for 1000 ORB only)
    if filter_fn == "check_max_stop" and orb_data:
        ticks_per_point = 10
        orb_size_ticks = orb_data["size"] * ticks_per_point
        max_ticks = config.get("max_ticks", 100)

        if orb_size_ticks > max_ticks:
            return {
                "allow_trade": False,
                "reason": f"ORB too wide: {orb_size_ticks:.0f} ticks > {max_ticks} - Skip (outlier volatility)"
            }
        else:
            return {
                "allow_trade": True,
                "reason": f"✓ Normal range: {orb_size_ticks:.0f} ticks ≤ {max_ticks}"
            }

    # MNQ ORB size filter
    if filter_fn == "check_orb_size" and orb_data:
        ticks_per_point = 4
        orb_size_ticks = orb_data["size"] * ticks_per_point
        max_ticks = config.get("max_ticks", 50)

        if orb_size_ticks > max_ticks:
            return {
                "allow_trade": False,
                "reason": f"ORB too large: {orb_size_ticks:.0f} ticks > {max_ticks} ticks limit"
            }
        else:
            return {
                "allow_trade": True,
                "reason": f"✓ ORB compressed: {orb_size_ticks:.0f} ticks < {max_ticks} ticks"
            }

    # MGC 10:00 - Check if 09:00 hit 1R MFE
    if filter_fn == "check_0900_mfe":
        date_str = now_local.strftime("%Y-%m-%d")
        hit_1r = check_orb_mfe(con, instrument, "0900", date_str)

        if hit_1r:
            return {
                "allow_trade": True,
                "reason": "✓ 09:00 hit 1R MFE - Momentum confirmed (+13.8% edge)"
            }
        else:
            return {
                "allow_trade": True,
                "reason": "⚠️ 09:00 didn't hit 1R - Baseline edge only"
            }

    # MGC 00:30 - Check pre-NY travel
    if filter_fn == "check_pre_ny_travel":
        date_str = now_local.strftime("%Y-%m-%d")
        pre_ny_travel = get_pre_ny_travel(con, instrument, date_str)

        if pre_ny_travel and pre_ny_travel > 167:
            return {
                "allow_trade": True,
                "reason": f"✓ Pre-NY travel {pre_ny_travel:.0f} ticks > 167 (+33% edge)"
            }
        else:
            travel = pre_ny_travel if pre_ny_travel else 0
            return {
                "allow_trade": False,
                "reason": f"Pre-NY travel {travel:.0f} ticks < 167 ticks - SKIP"
            }

    return {"allow_trade": True, "reason": "Filter check passed"}

# ============================================================================
# MAIN APP
# ============================================================================

# Connect to database
con = get_db_connection()

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
         padding: 20px; border-radius: 12px; margin-bottom: 20px; text-align: center;">
        <h2 style="color: white; margin: 0; font-size: 28px; font-weight: 900;">⚙️ CONTROLS</h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 INSTRUMENT")
    instrument = st.radio("Select:", ["MGC", "MNQ"], horizontal=True, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("### 🔄 DATA STATUS")

    if con:
        current_price_data = get_current_price(con, instrument)
        if current_price_data:
            st.success("✓ Database connected")
            st.info(f"📅 Last bar: {current_price_data['time'].strftime('%Y-%m-%d %H:%M')}")
            st.metric("💵 Last Close", f"{current_price_data['price']:.2f}")
        else:
            st.warning("⚠️ No recent data")
    else:
        st.error("❌ Database not connected")
        st.caption("Run: backfill data first")

    st.markdown("---")
    st.markdown("""
    <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-top: 20px;">
        <p style="margin: 0; font-size: 12px; color: #aaa; text-align: center;">
            📍 Brisbane Time (UTC+10)<br>
            🔄 Auto-refresh: 1s
        </p>
    </div>
    """, unsafe_allow_html=True)

# Header
now = datetime.now(TZ_LOCAL)
color = "#FFD700" if instrument == "MGC" else "#00CED1"
gradient = "linear-gradient(135deg, #f09819 0%, #edde5d 100%)" if instrument == "MGC" else "linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%)"

st.markdown(f"""
<div style="background: {gradient};
     padding: 35px; border-radius: 16px; margin-bottom: 25px;
     box-shadow: 0 10px 30px rgba(0,0,0,0.3); border: 3px solid {color};">
    <h1 style="color: #1a1a1a; margin: 0; font-size: 56px; text-shadow: 2px 2px 4px rgba(255,255,255,0.3); font-weight: 900; letter-spacing: 1px;">
        {'🥇' if instrument == 'MGC' else '📊'} {instrument} LIVE TRADING
    </h1>
    <p style="color: #2a2a2a; margin: 8px 0 0 0; font-size: 20px; font-weight: 600;">
        Real-Time Analysis • Validated Edges • Smart Recommendations
    </p>
</div>
""", unsafe_allow_html=True)

# Current time and price
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"### 🕐 {now.strftime('%H:%M:%S')}")
    st.caption("Brisbane Time")

with col2:
    if con and current_price_data:
        st.markdown(f"### 💵 {current_price_data['price']:.2f}")
        st.caption("Current Price")
    else:
        st.markdown("### ⚠️ No Data")
        st.caption("Connect to live feed")

with col3:
    date_str = now.strftime("%Y-%m-%d")
    st.markdown(f"### 📅 {date_str}")
    st.caption("Trading Day")

st.markdown("---")

# ============================================================================
# STRATEGY RECOMMENDATIONS
# ============================================================================

st.markdown("### 🎯 UPCOMING OPPORTUNITIES")

# Get ORB configs
orb_configs = MGC_ORB_CONFIGS if instrument == "MGC" else MNQ_ORB_CONFIGS

# Get recommendations for UPCOMING ORBs and recent ORBs (within last hour)
recommendations = []
for orb_def in ORB_TIMES:
    orb_name = orb_def["name"]
    orb_hour = orb_def["hour"]
    orb_min = orb_def["min"]
    config = orb_configs[orb_name]

    # Calculate when this ORB ends
    orb_start = now.replace(hour=orb_hour, minute=orb_min, second=0, microsecond=0)
    if orb_hour == 0 and now.hour >= 23:
        orb_start = orb_start + timedelta(days=1)
    orb_end = orb_start + timedelta(minutes=5)
    orb_trade_window_end = orb_end + timedelta(hours=1)  # Keep visible for 1 hour after close

    # Include if: (1) not finished yet, OR (2) finished within last hour (still tradeable)
    if now < orb_trade_window_end:
        # Get ORB data if available
        orb_data = get_orb_from_db(con, instrument, orb_name, date_str) if con else None

        # Get recommendation
        rec = recommend_strategy(con, instrument, now, orb_name, config, orb_data)
        rec["orb_name"] = orb_name
        rec["orb_end"] = orb_end
        recommendations.append(rec)

# Sort by priority (1=highest)
recommendations.sort(key=lambda x: x['priority'])

# Display upcoming recommendations (up to 3, or all if fewer)
if len(recommendations) == 0:
    st.info("📅 No more ORBs today - Trading day complete!")
else:
    num_to_show = min(3, len(recommendations))
    cols = st.columns(num_to_show)
    for i, rec in enumerate(recommendations[:num_to_show]):
        with cols[i]:
            # Check if ORB just closed (ready to trade)
            orb_finished = now > rec.get('orb_end', now)

            # Color based on confidence
            if rec['recommendation'] == 'SKIP':
                bg_color = "#dc3545"  # Red
                icon = "🚫"
            elif rec['confidence'] == 'HIGH':
                bg_color = "#28a745"  # Green
                icon = "✅"
            elif rec['confidence'] == 'MEDIUM':
                bg_color = "#ffc107"  # Yellow
                icon = "⚠️"
            else:
                bg_color = "#6c757d"  # Gray
                icon = "❌"

            # Status badge and tier badge
            status_html = ""
            tier = config.get('tier', 'A')
            tier_badge = f"<div style='background: rgba(0,0,0,0.3); padding: 3px 8px; border-radius: 4px; display: inline-block; font-size: 10px; font-weight: 700; margin-bottom: 6px;'>TIER {tier}</div>"

            if orb_finished and rec['recommendation'] == 'TRADE':
                status_html = f"<div style='background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; margin-bottom: 6px; font-size: 11px; font-weight: 700;'>⏰ WATCH FOR ENTRY</div>{tier_badge}"
            else:
                status_html = tier_badge

            # Add directional bias if available
            bias_html = ""
            if rec['bias'] and rec['bias'] != 'NEUTRAL':
                bias_arrow = "📈" if rec['bias'] == 'UP' else "📉"
                bias_html = f"<div style='margin: 5px 0; font-size: 14px; font-weight: 600;'>{bias_arrow} {rec['bias']}</div>"

            st.markdown(f"""
            <div style="background: {bg_color}; border-radius: 12px; padding: 18px;
                 color: white; text-align: center;
                 box-shadow: 0 6px 20px rgba(0,0,0,0.3);
                 border: 2px solid rgba(255,255,255,0.15);">
                {status_html}
                <div style="font-size: 42px; margin-bottom: 8px;">{icon}</div>
                <div style="font-size: 32px; font-weight: 900; margin: 0;">{rec['orb_name']}</div>
                <div style="height: 2px; background: rgba(255,255,255,0.3); margin: 10px auto; width: 50%;"></div>
                <div style="font-size: 14px; font-weight: 700; margin: 6px 0; text-transform: uppercase; letter-spacing: 0.5px;">{rec['confidence']}</div>
                {bias_html}
                <div style="font-size: 12px; line-height: 1.5; margin: 10px 0; min-height: 40px;">{rec['reason']}</div>
                <div style="background: rgba(0,0,0,0.25); border-radius: 6px; padding: 6px; margin-top: 8px;">
                    <div style="font-size: 11px; font-weight: 600;">PRIORITY #{rec['priority']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# Find current/next ORB
current_orb = None
next_orb = None
recent_orb = None

for orb_def in ORB_TIMES:
    orb_hour = orb_def["hour"]
    orb_min = orb_def["min"]
    orb_name = orb_def["name"]

    orb_start = now.replace(hour=orb_hour, minute=orb_min, second=0, microsecond=0)
    if orb_hour == 0 and now.hour >= 23:
        orb_start = orb_start + timedelta(days=1)

    orb_end = orb_start + timedelta(minutes=5)
    orb_trade_window_end = orb_end + timedelta(hours=1)

    # Check if forming now
    if orb_start <= now <= orb_end:
        current_orb = {"name": orb_name, "start": orb_start, "end": orb_end}
        break

    # Check if just finished (within last hour - still tradeable)
    if orb_end < now < orb_trade_window_end:
        recent_orb = {"name": orb_name, "start": orb_start, "end": orb_end}
        # Keep looking for next upcoming one

    # Check if upcoming
    if orb_start > now and not next_orb:
        next_orb = {"name": orb_name, "start": orb_start}

# If no ORB forming now, but we have a recent one, use that
if not current_orb and recent_orb:
    current_orb = recent_orb
    current_orb["recently_closed"] = True

# If no upcoming today, next is tomorrow 0900
if not next_orb and not current_orb:
    tomorrow_0900 = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    next_orb = {"name": "0900", "start": tomorrow_0900}

# Display current ORB or countdown
if current_orb:
    orb_name = current_orb["name"]
    config = orb_configs[orb_name]

    # Get strategy recommendation
    orb_data_current = get_orb_from_db(con, instrument, orb_name, date_str) if con else None
    recommendation = recommend_strategy(con, instrument, now, orb_name, config, orb_data_current)

    # Display recommendation prominently
    if recommendation['recommendation'] == 'SKIP':
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
             border: 3px solid #bd2130; border-radius: 12px; padding: 20px; margin-bottom: 15px;
             box-shadow: 0 6px 14px rgba(220,53,69,0.3);">
            <div style="color: white; text-align: center;">
                <div style="font-size: 36px; margin-bottom: 8px;">🚫</div>
                <div style="font-size: 32px; font-weight: 900; margin: 0;">SKIP {orb_name}</div>
                <div style="font-size: 14px; margin: 8px 0;">{recommendation['reason']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif recommendation['confidence'] == 'HIGH':
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
             border: 3px solid #1e7e34; border-radius: 12px; padding: 20px; margin-bottom: 15px;
             box-shadow: 0 6px 14px rgba(40,167,69,0.3);">
            <div style="color: white; text-align: center;">
                <div style="font-size: 36px; margin-bottom: 8px;">✅</div>
                <div style="font-size: 32px; font-weight: 900; margin: 0;">{orb_name} HIGH CONFIDENCE</div>
                <div style="font-size: 14px; margin: 8px 0;">{recommendation['reason']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif recommendation['confidence'] == 'MEDIUM':
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ffc107 0%, #ffca2c 100%);
             border: 3px solid #d39e00; border-radius: 12px; padding: 20px; margin-bottom: 15px;
             box-shadow: 0 6px 14px rgba(255,193,7,0.3);">
            <div style="color: #856404; text-align: center;">
                <div style="font-size: 36px; margin-bottom: 8px;">⚠️</div>
                <div style="font-size: 32px; font-weight: 900; margin: 0;">{orb_name} MEDIUM CONFIDENCE</div>
                <div style="font-size: 14px; margin: 8px 0;">{recommendation['reason']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if config["sl_mode"] == "SKIP":
        pass  # Already displayed above
    else:
        # Check if ORB recently closed or still forming
        if current_orb.get("recently_closed"):
            # ORB just closed - watch for breakout
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                 border: 4px solid #5a67d8; border-radius: 15px; padding: 30px;
                 box-shadow: 0 8px 16px rgba(102,126,234,0.4);">
                <h1 style="color: white; text-align: center; font-size: 44px; margin: 0;">
                    ⏰ {orb_name} ORB CLOSED
                </h1>
                <div style="text-align: center; color: white; font-size: 24px; margin: 15px 0; font-weight: 600;">
                    WATCH FOR 1-MINUTE BREAKOUT
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # ORB still forming - show countdown
            remaining = (current_orb["end"] - now).total_seconds()
            mins = int(remaining // 60)
            secs = int(remaining % 60)

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
                 border: 5px solid #ff0000; border-radius: 15px; padding: 40px;
                 box-shadow: 0 8px 16px rgba(255,0,0,0.3);">
                <h1 style="color: white; text-align: center; font-size: 52px; margin: 0;">
                    🔴 {orb_name} ORB FORMING NOW!
                </h1>
                <div style="text-align: center; color: white; font-size: 72px; font-weight: bold; margin: 20px 0;">
                    {mins:02d}:{secs:02d}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Try to get ORB from database (if already computed)
        orb_data = get_orb_from_db(con, instrument, orb_name, date_str) if con else None

        if orb_data and orb_data["high"] > 0:
            st.success(f"✓ ORB detected in database: High={orb_data['high']:.2f}, Low={orb_data['low']:.2f}")

            # Apply filters
            filter_result = apply_filters(con, instrument, orb_name, config, orb_data, now)

            if filter_result["allow_trade"]:
                st.success(f"✅ **TRADE ALLOWED**: {filter_result['reason']}")
            else:
                st.warning(f"⚠️ **FILTER BLOCKED**: {filter_result['reason']}")
        else:
            st.info("📊 Mark ORB high/low from your chart after window closes")

        # Entry method instructions
        st.markdown("---")
        st.markdown(f"""
        <div style="background: #fff3cd; border-left: 6px solid #ffc107; padding: 20px; border-radius: 8px; margin: 10px 0;">
            <h3 style="color: #856404; margin: 0 0 10px 0;">📋 ENTRY METHOD FOR {orb_name}:</h3>
            <ol style="color: #856404; font-size: 16px; line-height: 2;">
                <li><strong>{orb_start.strftime('%H:%M')}-{orb_end.strftime('%H:%M')}</strong> - ORB window forming, mark HIGH and LOW</li>
                <li><strong>After {orb_end.strftime('%H:%M')}</strong> - Wait for <strong>FIRST 1-MINUTE BAR</strong> to close outside ORB range</li>
                <li><strong>Entry trigger:</strong> 1-min close above HIGH → LONG | 1-min close below LOW → SHORT</li>
                <li><strong>Entry price:</strong> AT THE ORB BOUNDARY (HIGH for long, LOW for short) - DO NOT CHASE</li>
                <li><strong>Stop placement:</strong> {('MIDPOINT of ORB (HALF SL)' if config['sl_mode'] == 'HALF' else 'OPPOSITE BOUNDARY (FULL SL)')}</li>
                <li><strong>Target:</strong> {config['rr']}R from ORB edge (NOT from your entry price)</li>
                <li><strong>This is 1-minute bar execution</strong> - Fastest entry, validated edge</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

        # Manual input
        st.markdown("---")
        st.markdown("### 📝 ENTER ORB LEVELS:")

        col1, col2 = st.columns(2)
        with col1:
            manual_high = st.number_input("ORB High", value=0.0, format="%.2f", key="manual_high")
        with col2:
            manual_low = st.number_input("ORB Low", value=0.0, format="%.2f", key="manual_low")

        if manual_high > manual_low and manual_high > 0:
            orb_size = manual_high - manual_low
            ticks_per_point = 10 if instrument == "MGC" else 4
            orb_size_ticks = orb_size * ticks_per_point

            st.metric("ORB Size", f"{orb_size:.2f} pts", f"{orb_size_ticks:.0f} ticks")

            # Apply filters to manual ORB
            manual_orb_data = {"high": manual_high, "low": manual_low, "size": orb_size}
            filter_result = apply_filters(con, instrument, orb_name, config, manual_orb_data, now)

            if filter_result["allow_trade"]:
                st.success(f"✅ {filter_result['reason']}")

                # Show setups
                st.markdown("---")
                st.markdown("## 🎯 ENTRY SETUPS:")

                midpoint = (manual_high + manual_low) / 2

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                         border-radius: 12px; padding: 20px; color: white;">
                        <h2 style="margin: 0 0 15px 0;">📈 LONG SETUP</h2>
                    """, unsafe_allow_html=True)

                    if config["sl_mode"] == "HALF":
                        risk = orb_size / 2
                        stop = midpoint
                        stop_label = "MIDPOINT (HALF SL)"
                    else:
                        risk = orb_size
                        stop = manual_low
                        stop_label = "ORB LOW (FULL SL)"

                    target_distance = risk * config["rr"]
                    target = manual_high + target_distance

                    st.markdown(f"""
                        <div style="font-size: 18px; line-height: 2; background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                            <strong>1️⃣ WAIT FOR:</strong> 1-min bar close ABOVE {manual_high:.2f}<br>
                            <strong>2️⃣ ENTER AT:</strong> {manual_high:.2f} (ORB High)<br>
                            <strong>3️⃣ STOP AT:</strong> {stop:.2f} ({stop_label})<br>
                            <strong>4️⃣ TARGET AT:</strong> {target:.2f} ({config['rr']}R from ORB edge)<br>
                            <strong>5️⃣ RISK:</strong> {risk:.2f} pts = {risk * ticks_per_point:.0f} ticks = ${risk * ticks_per_point * (0.10 if instrument == 'MGC' else 0.20):.2f}/contract
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div style="background: #e7f3ff; border-left: 4px solid #0066cc; padding: 15px; border-radius: 5px; margin-top: 10px;">
                        <strong style="color: #0066cc;">📐 HOW TARGET IS CALCULATED:</strong><br>
                        <span style="color: #0066cc;">Risk = {risk:.2f} pts (distance from entry to stop)</span><br>
                        <span style="color: #0066cc;">Target = Entry + ({config['rr']} × Risk) = {manual_high:.2f} + {target_distance:.2f} = {target:.2f}</span><br>
                        <em style="color: #666;">This is ORB-anchored: measured from ORB edge, not your fill price</em>
                    </div>
                    """, unsafe_allow_html=True)

                    # Position sizing
                    st.markdown("#### 💰 Position Sizing")
                    risk_dollars = risk * ticks_per_point * (0.10 if instrument == "MGC" else 0.20)
                    default_risk = 150 if instrument == "MGC" else 200
                    risk_amount = st.number_input("$ Risk:", value=default_risk, step=50, key="risk_long_manual")
                    contracts = int(risk_amount / risk_dollars) if risk_dollars > 0 else 0
                    potential_profit = contracts * target_distance * ticks_per_point * (0.10 if instrument == "MGC" else 0.20)

                    st.success(f"**Trade {contracts} contracts**")
                    st.info(f"Potential profit: ${potential_profit:.0f} if target hit")

                with col2:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                         border-radius: 12px; padding: 20px; color: white;">
                        <h2 style="margin: 0 0 15px 0;">📉 SHORT SETUP</h2>
                    """, unsafe_allow_html=True)

                    if config["sl_mode"] == "HALF":
                        risk = orb_size / 2
                        stop = midpoint
                        stop_label = "MIDPOINT (HALF SL)"
                    else:
                        risk = orb_size
                        stop = manual_high
                        stop_label = "ORB HIGH (FULL SL)"

                    target_distance = risk * config["rr"]
                    target = manual_low - target_distance

                    st.markdown(f"""
                        <div style="font-size: 18px; line-height: 2; background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                            <strong>1️⃣ WAIT FOR:</strong> 1-min bar close BELOW {manual_low:.2f}<br>
                            <strong>2️⃣ ENTER AT:</strong> {manual_low:.2f} (ORB Low)<br>
                            <strong>3️⃣ STOP AT:</strong> {stop:.2f} ({stop_label})<br>
                            <strong>4️⃣ TARGET AT:</strong> {target:.2f} ({config['rr']}R from ORB edge)<br>
                            <strong>5️⃣ RISK:</strong> {risk:.2f} pts = {risk * ticks_per_point:.0f} ticks = ${risk * ticks_per_point * (0.10 if instrument == 'MGC' else 0.20):.2f}/contract
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div style="background: #ffe7e7; border-left: 4px solid #cc0000; padding: 15px; border-radius: 5px; margin-top: 10px;">
                        <strong style="color: #cc0000;">📐 HOW TARGET IS CALCULATED:</strong><br>
                        <span style="color: #cc0000;">Risk = {risk:.2f} pts (distance from entry to stop)</span><br>
                        <span style="color: #cc0000;">Target = Entry - ({config['rr']} × Risk) = {manual_low:.2f} - {target_distance:.2f} = {target:.2f}</span><br>
                        <em style="color: #666;">This is ORB-anchored: measured from ORB edge, not your fill price</em>
                    </div>
                    """, unsafe_allow_html=True)

                    # Position sizing
                    st.markdown("#### 💰 Position Sizing")
                    risk_dollars = risk * ticks_per_point * (0.10 if instrument == "MGC" else 0.20)
                    default_risk = 150 if instrument == "MGC" else 200
                    risk_amount = st.number_input("$ Risk:", value=default_risk, step=50, key="risk_short_manual")
                    contracts = int(risk_amount / risk_dollars) if risk_dollars > 0 else 0
                    potential_profit = contracts * target_distance * ticks_per_point * (0.10 if instrument == "MGC" else 0.20)

                    st.success(f"**Trade {contracts} contracts**")
                    st.info(f"Potential profit: ${potential_profit:.0f} if target hit")
            else:
                st.error(f"🚫 {filter_result['reason']}")

elif next_orb:
    orb_name = next_orb["name"]
    config = orb_configs[orb_name]

    # Get strategy recommendation for next ORB
    orb_data_next = get_orb_from_db(con, instrument, orb_name, date_str) if con else None
    recommendation_next = recommend_strategy(con, instrument, now, orb_name, config, orb_data_next)

    time_until = (next_orb["start"] - now).total_seconds()
    hours = int(time_until // 3600)
    mins = int((time_until % 3600) // 60)
    secs = int(time_until % 60)

    # Display recommendation banner
    if recommendation_next['recommendation'] == 'SKIP':
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);
             border: 3px solid #545b62; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <h2 style="color: white; text-align: center; margin: 0;">
                🚫 NEXT ORB: {orb_name} - WILL SKIP
            </h2>
            <p style="color: white; text-align: center; font-size: 14px; margin: 5px 0;">
                {recommendation_next['reason']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    elif recommendation_next['confidence'] == 'HIGH':
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
             border: 3px solid #1e7e34; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <h2 style="color: white; text-align: center; margin: 0;">
                ✅ NEXT ORB: {orb_name} - HIGH CONFIDENCE
            </h2>
            <p style="color: white; text-align: center; font-size: 14px; margin: 5px 0;">
                {recommendation_next['reason']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    if config["sl_mode"] == "SKIP":
        pass  # Already displayed above
    else:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
             border-radius: 15px; padding: 50px;">
            <h1 style="color: white; text-align: center; font-size: 40px;">
                ⏰ NEXT: {orb_name}
            </h1>
            <div style="text-align: center; color: white; font-size: 80px; font-weight: bold; margin: 30px 0;">
                {hours:02d}:{mins:02d}:{secs:02d}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Show config
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        rr_display = f"{config['rr']}:1" if config['rr'] is not None else "N/A"
        col1.metric("RR", rr_display)
        col2.metric("Stop", config['sl_mode'])
        col3.metric("Win Rate", f"{config['win_rate']}%")
        avg_r_sign = "+" if config['avg_r'] >= 0 else ""
        col4.metric("Avg R", f"{avg_r_sign}{config['avg_r']:.3f}R")

        # Check filters for next ORB
        if config.get("filter_fn"):
            st.markdown("---")
            st.markdown("### 🔍 FILTER STATUS:")

            # Pre-check filters if possible
            if config["filter_fn"] == "check_0900_mfe" and orb_name == "1000":
                hit_1r = check_orb_mfe(con, instrument, "0900", date_str) if con else False
                if hit_1r:
                    st.success("✓ 09:00 hit 1R MFE - **STRONGER SETUP FOR 10:00**")
                else:
                    st.info("⚠️ 09:00 didn't hit 1R - Baseline edge for 10:00")

            elif config["filter_fn"] == "check_pre_ny_travel" and orb_name == "0030":
                pre_ny = get_pre_ny_travel(con, instrument, date_str) if con else None
                if pre_ny and pre_ny > 167:
                    st.success(f"✓ Pre-NY travel {pre_ny:.0f} ticks > 167 - **TRADE 00:30**")
                else:
                    travel = pre_ny if pre_ny else "N/A"
                    st.warning(f"⚠️ Pre-NY travel {travel} < 167 - Will likely SKIP 00:30")

# Auto-refresh
st.markdown("""
<script>
setTimeout(function() {
    window.location.reload();
}, 1000);
</script>
""", unsafe_allow_html=True)

# Summary table at bottom
st.markdown("---")
st.markdown(f"### 📊 {instrument} ORB SUMMARY:")

df = pd.DataFrame(orb_configs).T.reset_index()
# Rename columns based on what we have
df = df.rename(columns={
    "index": "ORB",
    "rr": "RR",
    "sl_mode": "Stop",
    "avg_r": "Avg R",
    "win_rate": "Win %",
    "filter_fn": "Filter",
    "reason": "Reason"
})

# Select only relevant columns for display
display_cols = ["ORB", "RR", "Stop", "Avg R", "Win %", "Reason"]
df_display = df[display_cols].copy()

st.dataframe(df_display, use_container_width=True, hide_index=True)
