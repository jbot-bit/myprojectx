"""
SIMPLE ORB TRADING DASHBOARD - PROFESSIONAL GRADE
Bloomberg-style clean interface. No complexity. Just what you need.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import duckdb

# Page config
st.set_page_config(page_title="ORB Dashboard", layout="wide")

# Timezone
TZ_LOCAL = ZoneInfo("Australia/Brisbane")

# ORB configs for MGC
ORB_CONFIGS = {
    "0900": {"rr": 1.5, "sl_mode": "HALF", "filter": None, "avg_r": 0.42, "win_rate": 57.2},
    "1000": {"rr": 3.0, "sl_mode": "FULL", "filter": "09:00 hit 1R MFE", "avg_r": 0.34, "win_rate": 55.0},
    "1100": {"rr": 1.0, "sl_mode": "FULL", "filter": None, "avg_r": 0.45, "win_rate": 56.8},
    "1800": {"rr": 1.0, "sl_mode": "HALF", "filter": None, "avg_r": 0.48, "win_rate": 58.1},
    "2300": {"rr": 1.0, "sl_mode": "HALF", "filter": None, "avg_r": 0.39, "win_rate": 55.3},
    "0030": {"rr": 1.0, "sl_mode": "HALF", "filter": "Pre-NY travel > 167 ticks", "avg_r": 0.31, "win_rate": 54.2},
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

def get_next_orb():
    """Find next ORB time"""
    now = datetime.now(TZ_LOCAL)

    for orb in ORB_TIMES:
        orb_time = now.replace(hour=orb["hour"], minute=orb["min"], second=0, microsecond=0)

        # Handle 00:30 (next day)
        if orb["hour"] == 0:
            if now.hour >= 23 or now.hour < 1:
                if now.hour >= 23:
                    orb_time = orb_time + timedelta(days=1)

        if orb_time > now:
            return orb["name"], orb_time

    # If past all ORBs, next is tomorrow's 0900
    tomorrow_0900 = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    return "0900", tomorrow_0900

def get_current_orb():
    """Check if we're IN an ORB window (forming now)"""
    now = datetime.now(TZ_LOCAL)

    for orb in ORB_TIMES:
        start_time = now.replace(hour=orb["hour"], minute=orb["min"], second=0, microsecond=0)

        if orb["hour"] == 0 and now.hour >= 23:
            start_time = start_time + timedelta(days=1)

        end_time = start_time + timedelta(minutes=5)

        if start_time <= now <= end_time:
            return orb["name"], start_time, end_time

    return None, None, None

# Title
st.markdown("""
<div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
    <h1 style="color: white; text-align: center; margin: 0; font-size: 42px;">📊 ORB TRADING DASHBOARD</h1>
    <p style="color: #ddd; text-align: center; margin: 5px 0 0 0; font-size: 16px;">MGC - Professional Grade - Validated Edge</p>
</div>
""", unsafe_allow_html=True)

# Current time
now = datetime.now(TZ_LOCAL)
st.markdown(f"<h2 style='text-align: center; color: #333;'>🕐 Current Time: {now.strftime('%H:%M:%S')}</h2>", unsafe_allow_html=True)

# Check if ORB is forming NOW
current_orb, orb_start, orb_end = get_current_orb()

if current_orb:
    # ORB IS FORMING RIGHT NOW
    config = ORB_CONFIGS[current_orb]
    remaining = (orb_end - now).total_seconds()
    minutes = int(remaining // 60)
    seconds = int(remaining % 60)

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
         border: 5px solid #ff0000; border-radius: 15px; padding: 40px; margin: 20px 0;
         box-shadow: 0 8px 16px rgba(255,0,0,0.3); animation: pulse 2s infinite;">
        <h1 style="color: white; text-align: center; font-size: 48px; margin: 0;">
            🔴 {current_orb} ORB FORMING NOW!
        </h1>
        <div style="text-align: center; color: white; font-size: 64px; font-weight: bold; margin: 20px 0;">
            {minutes:02d}:{seconds:02d}
        </div>
        <div style="text-align: center; color: white; font-size: 24px;">
            WATCH THE RANGE - MARK HIGH AND LOW
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Instructions
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: #fff3cd; border-left: 6px solid #ffc107; padding: 20px; border-radius: 8px;">
            <h3 style="color: #856404; margin-top: 0;">📝 RIGHT NOW:</h3>
            <ul style="font-size: 18px; color: #856404; line-height: 2;">
                <li><strong>WATCH PRICE ACTION</strong></li>
                <li><strong>Track the HIGHEST price</strong></li>
                <li><strong>Track the LOWEST price</strong></li>
                <li><strong>DO NOT TRADE YET</strong></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: #d1ecf1; border-left: 6px solid #0c5460; padding: 20px; border-radius: 8px;">
            <h3 style="color: #0c5460; margin-top: 0;">⚙️ CONFIG:</h3>
            <div style="font-size: 18px; color: #0c5460; line-height: 2;">
                <strong>RR:</strong> {config['rr']}:1<br>
                <strong>Stop:</strong> {config['sl_mode']}<br>
                <strong>Win Rate:</strong> {config['win_rate']}%<br>
                <strong>Avg R:</strong> +{config['avg_r']:.2f}R
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Manual input for ORB
    st.markdown("---")
    st.markdown("### 📊 ENTER ORB LEVELS (After 5-min window closes):")

    col1, col2, col3 = st.columns(3)

    with col1:
        orb_high = st.number_input("ORB HIGH", value=0.0, format="%.1f", key="orb_high")

    with col2:
        orb_low = st.number_input("ORB LOW", value=0.0, format="%.1f", key="orb_low")

    with col3:
        if orb_high > 0 and orb_low > 0:
            orb_size = orb_high - orb_low
            st.metric("ORB SIZE", f"{orb_size:.1f} pts", f"{orb_size * 10:.0f} ticks")

    # Calculate entry levels
    if orb_high > orb_low and orb_high > 0:
        orb_size = orb_high - orb_low
        midpoint = (orb_high + orb_low) / 2

        st.markdown("---")
        st.markdown("## 🎯 ENTRY SETUP:")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                 border-radius: 12px; padding: 30px; color: white;">
                <h2 style="margin: 0 0 20px 0;">📈 LONG SETUP (Upside Break)</h2>
            """, unsafe_allow_html=True)

            if config["sl_mode"] == "HALF":
                risk = orb_size / 2
                stop = midpoint
            else:
                risk = orb_size
                stop = orb_low

            target_distance = risk * config["rr"]
            target = orb_high + target_distance

            st.markdown(f"""
                <div style="font-size: 20px; line-height: 2;">
                    <strong>Entry:</strong> {orb_high:.1f} (ORB High)<br>
                    <strong>Stop:</strong> {stop:.1f} ({config['sl_mode']})<br>
                    <strong>Target:</strong> {target:.1f} ({config['rr']}R)<br>
                    <strong>Risk:</strong> {risk:.1f} pts = {risk*10:.0f} ticks
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Position sizing
            st.markdown("#### 💰 Position Sizing:")
            risk_per_contract = risk
            st.write(f"**Risk per contract:** ${risk_per_contract:.2f}")

            desired_risk = st.number_input("$ Risk per trade:", value=100, step=50, key="risk_long")
            contracts = int(desired_risk / risk_per_contract)
            potential_profit = contracts * target_distance

            st.success(f"**Trade {contracts} contracts**")
            st.info(f"Potential profit: ${potential_profit:.0f}")

        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                 border-radius: 12px; padding: 30px; color: white;">
                <h2 style="margin: 0 0 20px 0;">📉 SHORT SETUP (Downside Break)</h2>
            """, unsafe_allow_html=True)

            if config["sl_mode"] == "HALF":
                risk = orb_size / 2
                stop = midpoint
            else:
                risk = orb_size
                stop = orb_high

            target_distance = risk * config["rr"]
            target = orb_low - target_distance

            st.markdown(f"""
                <div style="font-size: 20px; line-height: 2;">
                    <strong>Entry:</strong> {orb_low:.1f} (ORB Low)<br>
                    <strong>Stop:</strong> {stop:.1f} ({config['sl_mode']})<br>
                    <strong>Target:</strong> {target:.1f} ({config['rr']}R)<br>
                    <strong>Risk:</strong> {risk:.1f} pts = {risk*10:.0f} ticks
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Position sizing
            st.markdown("#### 💰 Position Sizing:")
            risk_per_contract = risk
            st.write(f"**Risk per contract:** ${risk_per_contract:.2f}")

            desired_risk = st.number_input("$ Risk per trade:", value=100, step=50, key="risk_short")
            contracts = int(desired_risk / risk_per_contract)
            potential_profit = contracts * target_distance

            st.success(f"**Trade {contracts} contracts**")
            st.info(f"Potential profit: ${potential_profit:.0f}")

else:
    # COUNTDOWN TO NEXT ORB
    next_orb_name, next_orb_time = get_next_orb()
    config = ORB_CONFIGS[next_orb_name]

    time_until = (next_orb_time - now).total_seconds()
    hours = int(time_until // 3600)
    minutes = int((time_until % 3600) // 60)
    seconds = int(time_until % 60)

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
         border: 3px solid #5a67d8; border-radius: 15px; padding: 50px;
         box-shadow: 0 8px 16px rgba(0,0,0,0.2);">
        <h1 style="color: white; text-align: center; font-size: 36px; margin-bottom: 20px;">
            ⏰ NEXT ORB: {next_orb_name}
        </h1>
        <div style="text-align: center; color: white; font-size: 72px; font-weight: bold; margin: 30px 0;">
            {hours:02d}:{minutes:02d}:{seconds:02d}
        </div>
        <div style="text-align: center; color: white; font-size: 20px;">
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

    st.markdown("---")
    st.markdown("### 📋 SETUP CHECKLIST:")
    st.markdown(f"""
    1. **{next_orb_time.strftime('%H:%M')}-{(next_orb_time + timedelta(minutes=5)).strftime('%H:%M')}** - ORB window, mark HIGH and LOW
    2. **After {(next_orb_time + timedelta(minutes=5)).strftime('%H:%M')}** - Wait for **1-minute close** outside range
    3. **Entry** - Long at HIGH or Short at LOW
    4. **Stop** - {'Midpoint' if config['sl_mode'] == 'HALF' else 'Opposite boundary'}
    5. **Target** - {config['rr']}R from ORB edge
    """)

# Auto-refresh every 1 second
st.markdown("""
<script>
setTimeout(function() {
    window.location.reload();
}, 1000);
</script>
""", unsafe_allow_html=True)

# All ORBs summary at bottom
st.markdown("---")
st.markdown("### 📊 ALL ORB CONFIGS (MGC):")

df_orbs = pd.DataFrame(ORB_CONFIGS).T
df_orbs = df_orbs.reset_index()
df_orbs.columns = ["ORB", "RR", "Stop Mode", "Filter", "Avg R", "Win Rate %"]
st.dataframe(df_orbs, use_container_width=True, hide_index=True)
