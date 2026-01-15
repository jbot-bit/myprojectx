"""
PROFESSIONAL MULTI-STRATEGY TRADING DASHBOARD
MGC + MNQ | All Validated Strategies | Bloomberg Grade
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Page config
st.set_page_config(page_title="Trading Dashboard Pro", layout="wide")

# Timezone
TZ_LOCAL = ZoneInfo("Australia/Brisbane")

# ============================================================================
# INSTRUMENT CONFIGS
# ============================================================================

MGC_ORB_CONFIGS = {
    "0900": {"rr": 1.5, "sl_mode": "HALF", "filter": None, "avg_r": 0.42, "win_rate": 57.2},
    "1000": {"rr": 3.0, "sl_mode": "FULL", "filter": "09:00 hit 1R MFE", "avg_r": 0.34, "win_rate": 55.0},
    "1100": {"rr": 1.0, "sl_mode": "FULL", "filter": None, "avg_r": 0.45, "win_rate": 56.8},
    "1800": {"rr": 1.0, "sl_mode": "HALF", "filter": None, "avg_r": 0.48, "win_rate": 58.1},
    "2300": {"rr": 1.0, "sl_mode": "HALF", "filter": None, "avg_r": 0.39, "win_rate": 55.3},
    "0030": {"rr": 1.0, "sl_mode": "HALF", "filter": "Pre-NY travel > 167 ticks", "avg_r": 0.31, "win_rate": 54.2},
}

MNQ_ORB_CONFIGS = {
    "0900": {"rr": 1.0, "sl_mode": "FULL", "filter": "ORB < 50 ticks (STRICT!)", "avg_r": 0.145, "win_rate": 53.0},
    "1000": {"rr": 1.5, "sl_mode": "FULL", "filter": "ORB < 50 ticks", "avg_r": 0.174, "win_rate": 54.5},
    "1100": {"rr": 1.5, "sl_mode": "FULL", "filter": "ORB < 50 ticks", "avg_r": 0.260, "win_rate": 56.0},
    "1800": {"rr": 1.5, "sl_mode": "HALF", "filter": "ORB < 60 ticks", "avg_r": 0.257, "win_rate": 55.8},
    "2300": {"rr": None, "sl_mode": "SKIP", "filter": "SKIP - Negative edge", "avg_r": -0.15, "win_rate": 48.0},
    "0030": {"rr": 1.0, "sl_mode": "HALF", "filter": None, "avg_r": 0.292, "win_rate": 57.5},
}

# ORB times
ORB_TIMES = [
    {"hour": 9, "min": 0, "name": "0900"},
    {"hour": 10, "min": 0, "name": "1000"},
    {"hour": 11, "min": 0, "name": "1100"},
    {"hour": 18, "min": 0, "name": "1800"},
    {"hour": 23, "min": 0, "name": "2300"},
    {"hour": 0, "min": 30, "name": "0030"},
]

# Strategy hierarchy
STRATEGIES = {
    "MULTI_LIQUIDITY_CASCADE": {
        "name": "Multi-Liquidity Cascade",
        "tier": "A+",
        "avg_r": 1.95,
        "frequency": "9.3%",
        "description": "London sweeps Asia level → 23:00 sweeps London level → Acceptance failure → Reaction trade",
        "mgc_only": True,
    },
    "NIGHT_ORB": {
        "name": "Night ORB (23:00, 00:30)",
        "tier": "B",
        "avg_r": 0.35,
        "frequency": "Daily",
        "description": "NY futures open ORBs - validated edge",
        "mgc_only": False,
    },
    "DAY_ORB": {
        "name": "Day ORB (09:00, 10:00, 11:00)",
        "tier": "B-C",
        "avg_r": 0.40,
        "frequency": "Daily",
        "description": "Asia session ORBs - mechanical edge",
        "mgc_only": False,
    },
    "LONDON_ORB": {
        "name": "London ORB (18:00)",
        "tier": "A-",
        "avg_r": 0.48,
        "frequency": "Daily",
        "description": "Session open - strongest ORB for MGC",
        "mgc_only": False,
    },
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_next_orb():
    """Find next ORB time"""
    now = datetime.now(TZ_LOCAL)

    for orb in ORB_TIMES:
        orb_time = now.replace(hour=orb["hour"], minute=orb["min"], second=0, microsecond=0)

        if orb["hour"] == 0:
            if now.hour >= 23 or now.hour < 1:
                if now.hour >= 23:
                    orb_time = orb_time + timedelta(days=1)

        if orb_time > now:
            return orb["name"], orb_time

    tomorrow_0900 = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    return "0900", tomorrow_0900

def get_current_orb():
    """Check if we're IN an ORB window"""
    now = datetime.now(TZ_LOCAL)

    for orb in ORB_TIMES:
        start_time = now.replace(hour=orb["hour"], minute=orb["min"], second=0, microsecond=0)

        if orb["hour"] == 0 and now.hour >= 23:
            start_time = start_time + timedelta(days=1)

        end_time = start_time + timedelta(minutes=5)

        if start_time <= now <= end_time:
            return orb["name"], start_time, end_time

    return None, None, None

def calculate_orb_setup(orb_high, orb_low, config, instrument):
    """Calculate entry, stop, target for both directions"""
    if orb_high <= orb_low or orb_high == 0:
        return None

    orb_size = orb_high - orb_low
    midpoint = (orb_high + orb_low) / 2

    # Tick value
    tick_value = 0.10 if instrument == "MGC" else 0.20
    ticks_per_point = 10 if instrument == "MGC" else 4

    # Calculate for LONG
    if config["sl_mode"] == "HALF":
        risk_long = orb_size / 2
        stop_long = midpoint
    else:
        risk_long = orb_size
        stop_long = orb_low

    target_distance_long = risk_long * config["rr"]
    target_long = orb_high + target_distance_long

    # Calculate for SHORT
    if config["sl_mode"] == "HALF":
        risk_short = orb_size / 2
        stop_short = midpoint
    else:
        risk_short = orb_size
        stop_short = orb_high

    target_distance_short = risk_short * config["rr"]
    target_short = orb_low - target_distance_short

    return {
        "orb_size": orb_size,
        "orb_size_ticks": orb_size * ticks_per_point,
        "midpoint": midpoint,
        "long": {
            "entry": orb_high,
            "stop": stop_long,
            "target": target_long,
            "risk_pts": risk_long,
            "risk_ticks": risk_long * ticks_per_point,
            "risk_dollars": risk_long * ticks_per_point * tick_value,
        },
        "short": {
            "entry": orb_low,
            "stop": stop_short,
            "target": target_short,
            "risk_pts": risk_short,
            "risk_ticks": risk_short * ticks_per_point,
            "risk_dollars": risk_short * ticks_per_point * tick_value,
        }
    }

# ============================================================================
# MAIN APP
# ============================================================================

# Sidebar - Instrument selector
with st.sidebar:
    st.markdown("### 📊 INSTRUMENT")
    instrument = st.radio("Select:", ["MGC", "MNQ"], horizontal=True)

    st.markdown("---")
    st.markdown("### 📈 STRATEGY HIERARCHY")

    for strat_key, strat in STRATEGIES.items():
        if strat["mgc_only"] and instrument != "MGC":
            continue

        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 5px 0;">
            <strong style="color: #0066cc;">{strat['tier']}: {strat['name']}</strong><br>
            <span style="font-size: 12px;">Avg R: +{strat['avg_r']}R | {strat['frequency']}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚙️ ACCOUNT")
    account_size = st.number_input("Account Size ($)", value=100000, step=10000)
    default_risk_pct = st.slider("Risk per Trade (%)", 0.1, 2.0, 0.5, 0.1)

# Header
color = "#FFD700" if instrument == "MGC" else "#00CED1"
st.markdown(f"""
<div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
     padding: 25px; border-radius: 12px; margin-bottom: 20px; border-left: 8px solid {color};">
    <h1 style="color: white; margin: 0; font-size: 48px;">
        {'🥇' if instrument == 'MGC' else '📊'} {instrument} TRADING DASHBOARD
    </h1>
    <p style="color: #ddd; margin: 5px 0 0 0; font-size: 18px;">
        {'Micro Gold - All Strategies' if instrument == 'MGC' else 'Micro Nasdaq - Validated Setups'}
    </p>
</div>
""", unsafe_allow_html=True)

# Current time
now = datetime.now(TZ_LOCAL)
st.markdown(f"<h2 style='text-align: center; color: #333;'>🕐 {now.strftime('%H:%M:%S')} Brisbane Time</h2>", unsafe_allow_html=True)

# Get ORB configs based on instrument
orb_configs = MGC_ORB_CONFIGS if instrument == "MGC" else MNQ_ORB_CONFIGS

# Check current ORB
current_orb, orb_start, orb_end = get_current_orb()

if current_orb:
    # ORB IS FORMING NOW
    config = orb_configs[current_orb]

    # Check if SKIP
    if config["sl_mode"] == "SKIP":
        st.error(f"⏭️ **SKIP {current_orb} ORB** - {config['filter']}")
        st.info("Wait for next ORB")
    else:
        remaining = (orb_end - now).total_seconds()
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
             border: 5px solid #ff0000; border-radius: 15px; padding: 40px; margin: 20px 0;
             box-shadow: 0 8px 16px rgba(255,0,0,0.3);">
            <h1 style="color: white; text-align: center; font-size: 52px; margin: 0;">
                🔴 {current_orb} ORB FORMING NOW!
            </h1>
            <div style="text-align: center; color: white; font-size: 72px; font-weight: bold; margin: 20px 0;">
                {minutes:02d}:{seconds:02d}
            </div>
            <div style="text-align: center; color: white; font-size: 26px;">
                WATCH THE RANGE - MARK HIGH AND LOW
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Config display
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("RR Target", f"{config['rr']}:1")
        col2.metric("Stop Mode", config['sl_mode'])
        col3.metric("Win Rate", f"{config['win_rate']}%")
        col4.metric("Avg R", f"+{config['avg_r']:.2f}R")

        if config["filter"]:
            st.warning(f"⚠️ **FILTER:** {config['filter']}")

        st.markdown("---")

        # Manual ORB input
        st.markdown("### 📊 ENTER ORB LEVELS (After window closes):")

        col1, col2, col3 = st.columns(3)

        with col1:
            orb_high = st.number_input("ORB HIGH", value=0.0, format="%.2f", key=f"orb_high_{current_orb}")

        with col2:
            orb_low = st.number_input("ORB LOW", value=0.0, format="%.2f", key=f"orb_low_{current_orb}")

        with col3:
            if orb_high > 0 and orb_low > 0:
                ticks_per_point = 10 if instrument == "MGC" else 4
                orb_size = orb_high - orb_low
                st.metric("ORB SIZE", f"{orb_size:.2f} pts", f"{orb_size * ticks_per_point:.0f} ticks")

        # Calculate setups if ORB entered
        if orb_high > orb_low and orb_high > 0:
            setup = calculate_orb_setup(orb_high, orb_low, config, instrument)

            if setup:
                st.markdown("---")
                st.markdown("## 🎯 ENTRY SETUPS:")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                         border-radius: 12px; padding: 25px; color: white;">
                        <h2 style="margin: 0 0 15px 0;">📈 LONG (Upside Break)</h2>
                    """, unsafe_allow_html=True)

                    long = setup["long"]

                    st.markdown(f"""
                        <div style="font-size: 20px; line-height: 2;">
                            <strong>Entry:</strong> {long['entry']:.2f}<br>
                            <strong>Stop:</strong> {long['stop']:.2f}<br>
                            <strong>Target:</strong> {long['target']:.2f}<br>
                            <strong>Risk:</strong> {long['risk_pts']:.2f} pts = {long['risk_ticks']:.0f} ticks = ${long['risk_dollars']:.2f}/contract
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("#### 💰 Position Sizing")
                    risk_amount = st.number_input("$ Risk:", value=int(account_size * default_risk_pct / 100), step=50, key="risk_long")
                    contracts = int(risk_amount / long['risk_dollars']) if long['risk_dollars'] > 0 else 0
                    potential_profit = contracts * (long['target'] - long['entry']) * (10 if instrument == "MGC" else 4) * (0.10 if instrument == "MGC" else 0.20)

                    st.success(f"**Trade {contracts} contracts**")
                    st.info(f"Potential profit: ${potential_profit:.0f}")

                with col2:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                         border-radius: 12px; padding: 25px; color: white;">
                        <h2 style="margin: 0 0 15px 0;">📉 SHORT (Downside Break)</h2>
                    """, unsafe_allow_html=True)

                    short = setup["short"]

                    st.markdown(f"""
                        <div style="font-size: 20px; line-height: 2;">
                            <strong>Entry:</strong> {short['entry']:.2f}<br>
                            <strong>Stop:</strong> {short['stop']:.2f}<br>
                            <strong>Target:</strong> {short['target']:.2f}<br>
                            <strong>Risk:</strong> {short['risk_pts']:.2f} pts = {short['risk_ticks']:.0f} ticks = ${short['risk_dollars']:.2f}/contract
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("#### 💰 Position Sizing")
                    risk_amount = st.number_input("$ Risk:", value=int(account_size * default_risk_pct / 100), step=50, key="risk_short")
                    contracts = int(risk_amount / short['risk_dollars']) if short['risk_dollars'] > 0 else 0
                    potential_profit = contracts * (short['entry'] - short['target']) * (10 if instrument == "MGC" else 4) * (0.10 if instrument == "MGC" else 0.20)

                    st.success(f"**Trade {contracts} contracts**")
                    st.info(f"Potential profit: ${potential_profit:.0f}")

else:
    # COUNTDOWN TO NEXT ORB
    next_orb_name, next_orb_time = get_next_orb()
    config = orb_configs[next_orb_name]

    time_until = (next_orb_time - now).total_seconds()
    hours = int(time_until // 3600)
    minutes = int((time_until % 3600) // 60)
    seconds = int(time_until % 60)

    # Check if SKIP
    if config["sl_mode"] == "SKIP":
        st.markdown(f"""
        <div style="background: #6c757d; border-radius: 15px; padding: 40px; text-align: center;">
            <h2 style="color: white;">⏭️ NEXT ORB: {next_orb_name} (SKIPPING)</h2>
            <p style="color: white; font-size: 18px;">{config['filter']}</p>
            <p style="color: white;">Looking ahead...</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
             border: 3px solid #5a67d8; border-radius: 15px; padding: 50px;
             box-shadow: 0 8px 16px rgba(0,0,0,0.2);">
            <h1 style="color: white; text-align: center; font-size: 40px; margin-bottom: 20px;">
                ⏰ NEXT ORB: {next_orb_name}
            </h1>
            <div style="text-align: center; color: white; font-size: 80px; font-weight: bold; margin: 30px 0;">
                {hours:02d}:{minutes:02d}:{seconds:02d}
            </div>
            <div style="text-align: center; color: white; font-size: 22px;">
                Opens at {next_orb_time.strftime('%H:%M:%S')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Config for next ORB
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("RR Target", f"{config['rr']}:1")
        col2.metric("Stop Mode", config['sl_mode'])
        col3.metric("Win Rate", f"{config['win_rate']}%")
        col4.metric("Avg R", f"+{config['avg_r']:.2f}R")

        if config["filter"]:
            st.warning(f"⚠️ **FILTER:** {config['filter']}")

# Strategy summary at bottom
st.markdown("---")
st.markdown(f"### 📊 ALL {instrument} ORB CONFIGS:")

df_orbs = pd.DataFrame(orb_configs).T
df_orbs = df_orbs.reset_index()
df_orbs.columns = ["ORB", "RR", "Stop Mode", "Filter", "Avg R", "Win Rate %"]
st.dataframe(df_orbs, use_container_width=True, hide_index=True)

# Additional strategies (MGC only)
if instrument == "MGC":
    st.markdown("---")
    st.markdown("### 🚀 ADDITIONAL MGC STRATEGIES:")

    st.markdown("""
    <div style="background: #fff3cd; border-left: 6px solid #ffc107; padding: 20px; border-radius: 8px; margin: 10px 0;">
        <h4 style="color: #856404; margin: 0;">⭐ Multi-Liquidity Cascade (A+ Tier)</h4>
        <p style="color: #856404; margin: 5px 0;"><strong>Avg R:</strong> +1.95R | <strong>Frequency:</strong> 9.3%</p>
        <p style="color: #856404; margin: 5px 0;">London sweeps Asia → 23:00 sweeps London → Acceptance failure → Trade reaction</p>
        <p style="color: #856404; margin: 5px 0;"><em>Watch for multi-level sweeps into session transitions</em></p>
    </div>
    """, unsafe_allow_html=True)

# Auto-refresh
st.markdown("""
<script>
setTimeout(function() {
    window.location.reload();
}, 1000);
</script>
""", unsafe_allow_html=True)
