"""
LIVE TRADING HUB - Streamlit Application
Real-time decision support engine for trading.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import logging
import uuid
import os

from config import *
from data_loader import LiveDataLoader
from strategy_engine import StrategyEngine, ActionType, StrategyState
from utils import calculate_position_size, format_price, log_to_journal
from ai_memory import AIMemoryManager
from ai_assistant import TradingAIAssistant
from cloud_mode import is_cloud_deployment, show_cloud_setup_instructions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Trading Hub",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if "data_loader" not in st.session_state:
    st.session_state.data_loader = None
if "strategy_engine" not in st.session_state:
    st.session_state.strategy_engine = None
if "last_evaluation" not in st.session_state:
    st.session_state.last_evaluation = None
if "account_size" not in st.session_state:
    st.session_state.account_size = DEFAULT_ACCOUNT_SIZE
if "current_symbol" not in st.session_state:
    st.session_state.current_symbol = PRIMARY_INSTRUMENT
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "memory_manager" not in st.session_state:
    st.session_state.memory_manager = AIMemoryManager("trading_app.db")
if "ai_assistant" not in st.session_state:
    st.session_state.ai_assistant = TradingAIAssistant(st.session_state.memory_manager)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ============================================================================
# SIDEBAR - SETTINGS
# ============================================================================
with st.sidebar:
    st.title("⚙️ Settings")

    # Instrument selection
    symbol = st.selectbox(
        "Instrument",
        [PRIMARY_INSTRUMENT, SECONDARY_INSTRUMENT],
        index=0
    )

    if symbol != st.session_state.current_symbol:
        st.session_state.current_symbol = symbol
        st.session_state.data_loader = None  # Force reload

    # Account size
    account_size = st.number_input(
        "Account Size ($)",
        min_value=1000.0,
        max_value=10000000.0,
        value=st.session_state.account_size,
        step=1000.0
    )
    st.session_state.account_size = account_size

    st.divider()

    # Data status
    st.subheader("📊 Data Status")

    if st.button("Initialize/Refresh Data"):
        with st.spinner("Loading data..."):
            try:
                # Initialize data loader
                loader = LiveDataLoader(symbol)

                # Fetch data (cloud-aware)
                if is_cloud_deployment():
                    # In cloud: fetch live data from ProjectX API
                    if os.getenv("PROJECTX_API_KEY"):
                        loader.refresh()  # Fetches from ProjectX API automatically
                        st.success("Fetched live data from ProjectX API")
                    else:
                        st.error("No PROJECTX_API_KEY found. Add it in Streamlit Cloud secrets.")
                        st.stop()
                else:
                    # Local: backfill from gold.db then refresh
                    loader.backfill_from_gold_db("../gold.db", days=7)
                    loader.refresh()

                st.session_state.data_loader = loader
                st.session_state.strategy_engine = StrategyEngine(loader)

                st.success(f"Loaded data for {symbol}")
                logger.info(f"Data initialized for {symbol}")

            except Exception as e:
                st.error(f"Error loading data: {e}")
                logger.error(f"Data load error: {e}", exc_info=True)

    if st.session_state.data_loader:
        latest_bar = st.session_state.data_loader.get_latest_bar()
        if latest_bar:
            st.metric("Last Bar", latest_bar["ts_local"].strftime("%H:%M:%S"))
            st.metric("Last Price", f"${latest_bar['close']:.2f}")

    st.divider()

    # Instrument config display
    if st.session_state.strategy_engine:
        st.subheader(f"⚙️ {symbol} Config")
        engine = st.session_state.strategy_engine

        # Show instrument-specific settings
        st.caption(f"**CASCADE Gap:** {engine.cascade_min_gap:.1f}pts")

        # Show ORB configs
        with st.expander("📋 ORB Configurations", expanded=False):
            orb_data = []
            for orb_name, config in engine.orb_configs.items():
                if config.get("tier") == "SKIP":
                    orb_data.append({
                        "ORB": orb_name,
                        "Status": "⏭️ SKIP",
                        "RR": "-",
                        "SL": "-"
                    })
                else:
                    orb_data.append({
                        "ORB": orb_name,
                        "Status": "✅ Active",
                        "RR": f"{config['rr']}R",
                        "SL": config["sl_mode"]
                    })

            st.dataframe(
                pd.DataFrame(orb_data),
                use_container_width=True,
                hide_index=True
            )

        # Show active filters
        with st.expander("🔍 ORB Size Filters", expanded=False):
            filter_data = []
            for orb_name, threshold in engine.orb_size_filters.items():
                if threshold is None:
                    filter_data.append({"ORB": orb_name, "Filter": "None"})
                else:
                    filter_data.append({"ORB": orb_name, "Filter": f"< {threshold*100:.1f}% ATR"})

            st.dataframe(
                pd.DataFrame(filter_data),
                use_container_width=True,
                hide_index=True
            )

    st.divider()

    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    if auto_refresh:
        st.info(f"Refreshing every {DATA_REFRESH_SECONDS}s")

# ============================================================================
# MAIN TABS
# ============================================================================
tab_live, tab_levels, tab_trade_plan, tab_journal, tab_ai_chat = st.tabs([
    "🔴 LIVE",
    "📊 LEVELS",
    "📋 TRADE PLAN",
    "📓 JOURNAL",
    "🤖 AI CHAT"
])

# ============================================================================
# TAB 1: LIVE
# ============================================================================
with tab_live:
    st.title(f"🔴 LIVE - {symbol}")

    if not st.session_state.data_loader or not st.session_state.strategy_engine:
        if is_cloud_deployment():
            st.info("☁️ **Cloud Mode Detected**")
            st.markdown("""
            ### Welcome to your Trading Hub!

            Your app is running in the cloud!

            **What works right now:**
            - 🤖 **AI CHAT tab** - Ask strategy questions, get trade calculations

            **To enable live data & strategies:**
            1. Make sure `PROJECTX_API_KEY` is in your Streamlit Cloud secrets
            2. Click "Initialize/Refresh Data" in the sidebar
            3. App will fetch live data from ProjectX API

            **For now, try the AI CHAT tab!** →
            """)
        else:
            st.warning("⚠️ Click 'Initialize/Refresh Data' in sidebar to start")
        st.stop()

    # ========================================================================
    # NEXT ORB COUNTDOWN & SETUP DISPLAY
    # ========================================================================
    now = datetime.now(TZ_LOCAL)

    # Define ORB times (24-hour format)
    orb_times = {
        "0900": (9, 0, 5),   # 09:00-09:05
        "1000": (10, 0, 5),  # 10:00-10:05
        "1100": (11, 0, 5),  # 11:00-11:05
        "1800": (18, 0, 5),  # 18:00-18:05
        "2300": (23, 0, 5),  # 23:00-23:05
        "0030": (0, 30, 35), # 00:30-00:35
    }

    # Find next ORB
    next_orb_name = None
    next_orb_start = None
    next_orb_end = None
    min_delta = timedelta(days=1)

    for orb_name, (hour, minute, end_minute) in orb_times.items():
        orb_start = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        orb_end = now.replace(hour=hour, minute=end_minute, second=0, microsecond=0)

        # Handle midnight crossing (0030)
        if hour == 0 and now.hour >= 12:
            orb_start += timedelta(days=1)
            orb_end += timedelta(days=1)

        # If we're past this ORB today, check tomorrow
        if now > orb_end:
            orb_start += timedelta(days=1)
            orb_end += timedelta(days=1)

        delta = orb_start - now
        if delta < min_delta and delta > timedelta(0):
            min_delta = delta
            next_orb_name = orb_name
            next_orb_start = orb_start
            next_orb_end = orb_end

    # Check if we're IN an ORB window right now
    in_orb_window = False
    current_orb_name = None
    current_orb_end = None

    for orb_name, (hour, minute, end_minute) in orb_times.items():
        orb_start = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        orb_end = now.replace(hour=hour, minute=end_minute, second=0, microsecond=0)

        # Handle midnight crossing
        if hour == 0 and now.hour >= 12:
            orb_start += timedelta(days=1)
            orb_end += timedelta(days=1)

        if orb_start <= now <= orb_end:
            in_orb_window = True
            current_orb_name = orb_name
            current_orb_end = orb_end
            break

    # Display countdown or active ORB
    if in_orb_window:
        # ORB WINDOW IS ACTIVE RIGHT NOW
        time_remaining = (current_orb_end - now).total_seconds()
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)

        # Get current ORB high/low from live data
        orb_start_time = now.replace(hour=orb_times[current_orb_name][0], minute=orb_times[current_orb_name][1], second=0, microsecond=0)

        if st.session_state.data_loader:
            orb_bars = st.session_state.data_loader.get_bars_in_range(orb_start_time, now)
            if not orb_bars.empty:
                orb_high = orb_bars['high'].max()
                orb_low = orb_bars['low'].min()
                orb_size = orb_high - orb_low
            else:
                orb_high = orb_low = orb_size = None
        else:
            orb_high = orb_low = orb_size = None

        # Get filter threshold
        engine = st.session_state.strategy_engine
        if engine:
            filter_threshold = engine.orb_size_filters.get(current_orb_name)
            atr = st.session_state.data_loader.get_today_atr() if st.session_state.data_loader else None
        else:
            filter_threshold = None
            atr = None

        if filter_threshold and atr and orb_size:
            filter_passed = orb_size < (atr * filter_threshold)
            filter_text = f"< {filter_threshold*100:.1f}% ATR (~{atr * filter_threshold:.1f}pts)"
        else:
            filter_passed = True
            filter_text = "None"

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            border: 4px solid #ff4500;
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 8px 16px rgba(255,69,0,0.3);
            animation: pulse 2s infinite;
        ">
            <div style="text-align: center;">
                <div style="font-size: 24px; color: white; font-weight: bold; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 2px;">
                    🚨 {current_orb_name} ORB WINDOW ACTIVE 🚨
                </div>
                <div style="font-size: 64px; font-weight: bold; color: white; margin: 16px 0; text-shadow: 0 4px 8px rgba(0,0,0,0.3);">
                    {minutes:02d}:{seconds:02d}
                </div>
                <div style="font-size: 20px; color: white; margin-bottom: 24px;">
                    UNTIL WINDOW CLOSES
                </div>
            </div>

            <div style="background: rgba(255,255,255,0.95); border-radius: 12px; padding: 24px; margin-top: 16px;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 16px;">
                    <div style="text-align: center; padding: 16px; background: #f0f0f0; border-radius: 8px;">
                        <div style="font-size: 14px; color: #666; margin-bottom: 8px;">ORB HIGH</div>
                        <div style="font-size: 28px; font-weight: bold; color: #198754;">${orb_high:.2f if orb_high else 0:.2f}</div>
                    </div>
                    <div style="text-align: center; padding: 16px; background: #f0f0f0; border-radius: 8px;">
                        <div style="font-size: 14px; color: #666; margin-bottom: 8px;">ORB LOW</div>
                        <div style="font-size: 28px; font-weight: bold; color: #dc3545;">${orb_low:.2f if orb_low else 0:.2f}</div>
                    </div>
                    <div style="text-align: center; padding: 16px; background: #f0f0f0; border-radius: 8px;">
                        <div style="font-size: 14px; color: #666; margin-bottom: 8px;">ORB SIZE</div>
                        <div style="font-size: 28px; font-weight: bold; color: #0d6efd;">{orb_size:.2f if orb_size else 0:.2f}pts</div>
                    </div>
                </div>

                <div style="padding: 16px; background: {'#d1e7dd' if filter_passed else '#f8d7da'}; border-left: 4px solid {'#198754' if filter_passed else '#dc3545'}; border-radius: 8px; margin-top: 16px;">
                    <div style="font-size: 16px; font-weight: bold; color: #333; margin-bottom: 8px;">
                        {'✅ FILTER PASSED' if filter_passed else '❌ FILTER FAILED'}
                    </div>
                    <div style="font-size: 14px; color: #666;">
                        Filter: {filter_text}
                    </div>
                </div>

                <div style="margin-top: 16px; padding: 16px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 8px;">
                    <div style="font-size: 16px; font-weight: bold; color: #333; margin-bottom: 8px;">⏳ WAIT FOR BREAKOUT</div>
                    <div style="font-size: 14px; color: #666;">
                        Enter on first 5-min close OUTSIDE the range at {current_orb_end.strftime('%H:%M:%S')}
                    </div>
                </div>
            </div>
        </div>

        <style>
        @keyframes pulse {{
            0%, 100% {{ box-shadow: 0 8px 16px rgba(255,69,0,0.3); }}
            50% {{ box-shadow: 0 8px 32px rgba(255,69,0,0.6); }}
        }}
        </style>
        """, unsafe_allow_html=True)

    elif next_orb_name and next_orb_start:
        # COUNTDOWN TO NEXT ORB
        time_until = (next_orb_start - now).total_seconds()
        hours = int(time_until // 3600)
        minutes = int((time_until % 3600) // 60)
        seconds = int(time_until % 60)

        # Get config for this ORB (only if engine is initialized)
        engine = st.session_state.strategy_engine
        if engine:
            orb_config = engine.orb_configs.get(next_orb_name, {})
            filter_threshold = engine.orb_size_filters.get(next_orb_name)
            atr = st.session_state.data_loader.get_today_atr()
        else:
            orb_config = {}
            filter_threshold = None
            atr = None

        # Check if SKIP
        is_skip = orb_config.get("tier") == "SKIP"

        if is_skip:
            banner_color = "#6c757d"
            banner_text = f"⏭️ SKIPPING {next_orb_name} ORB"
        else:
            banner_color = "#0d6efd"
            banner_text = f"⏰ NEXT ORB: {next_orb_name}"

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {banner_color}20 0%, {banner_color}40 100%);
            border: 3px solid {banner_color};
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        ">
            <div style="text-align: center;">
                <div style="font-size: 20px; color: {banner_color}; font-weight: bold; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 2px;">
                    {banner_text}
                </div>
                <div style="font-size: 56px; font-weight: bold; color: {banner_color}; margin: 16px 0;">
                    {hours:02d}:{minutes:02d}:{seconds:02d}
                </div>
                <div style="font-size: 18px; color: #666; margin-bottom: 8px;">
                    Window Opens: {next_orb_start.strftime('%H:%M:%S')} - {next_orb_end.strftime('%H:%M:%S')}
                </div>
            </div>

            {"" if is_skip else f'''
            <div style="background: white; border-radius: 12px; padding: 24px; margin-top: 16px;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-bottom: 16px;">
                    <div style="text-align: center; padding: 12px; background: #f8f9fa; border-radius: 8px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 4px;">CONFIG</div>
                        <div style="font-size: 20px; font-weight: bold; color: #333;">{orb_config.get("rr", "?")}R</div>
                        <div style="font-size: 12px; color: #666;">{orb_config.get("sl_mode", "?")}</div>
                    </div>
                    <div style="text-align: center; padding: 12px; background: #f8f9fa; border-radius: 8px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 4px;">FILTER</div>
                        <div style="font-size: 16px; font-weight: bold; color: #333;">
                            {"< " + str(filter_threshold*100) + "% ATR" if filter_threshold else "None"}
                        </div>
                        <div style="font-size: 12px; color: #666;">
                            {"~" + str(round(atr * filter_threshold, 1)) + "pts" if (filter_threshold and atr) else "All sizes OK"}
                        </div>
                    </div>
                    <div style="text-align: center; padding: 12px; background: #f8f9fa; border-radius: 8px;">
                        <div style="font-size: 12px; color: #666; margin-bottom: 4px;">POSITION RISK</div>
                        <div style="font-size: 20px; font-weight: bold; color: #333;">
                            {orb_config.get("tier", "DAY") == "NIGHT" and "0.50%" or "0.25%"}
                        </div>
                    </div>
                </div>

                <div style="padding: 16px; background: #e7f3ff; border-left: 4px solid #0d6efd; border-radius: 8px;">
                    <div style="font-size: 16px; font-weight: bold; color: #0d6efd; margin-bottom: 8px;">📋 ENTRY CHECKLIST</div>
                    <div style="font-size: 14px; color: #333; line-height: 1.8;">
                        1️⃣ Watch {next_orb_start.strftime('%H:%M')}-{next_orb_end.strftime('%H:%M')} for range formation<br>
                        2️⃣ Note ORB high and low prices<br>
                        {"3️⃣ Check: ORB size < " + str(round(atr * filter_threshold, 1)) + "pts<br>" if (filter_threshold and atr) else ""}
                        {"4️⃣" if filter_threshold else "3️⃣"} Wait for 5-min close OUTSIDE range<br>
                        {"5️⃣" if filter_threshold else "4️⃣"} Enter with {"HALF" if orb_config.get("sl_mode") == "HALF" else "FULL"} stop at {"midpoint" if orb_config.get("sl_mode") == "HALF" else "opposite side"}
                    </div>
                </div>
            </div>
            '''}
        </div>
        """, unsafe_allow_html=True)

    # Evaluate strategies
    try:
        evaluation = st.session_state.strategy_engine.evaluate_all()
        st.session_state.last_evaluation = evaluation

        # Log state change
        log_to_journal(evaluation)

    except Exception as e:
        st.error(f"Strategy evaluation error: {e}")
        logger.error(f"Evaluation error: {e}", exc_info=True)
        st.stop()

    # ========================================================================
    # DECISION PANEL (WHAT TO DO NOW) - ENHANCED VISUAL DESIGN
    # ========================================================================

    # Color-code by action
    action_styles = {
        ActionType.STAND_DOWN: {"color": "#6c757d", "bg": "#f8f9fa", "emoji": "⏸️"},
        ActionType.PREPARE: {"color": "#0d6efd", "bg": "#cfe2ff", "emoji": "⚡"},
        ActionType.ENTER: {"color": "#198754", "bg": "#d1e7dd", "emoji": "🎯"},
        ActionType.MANAGE: {"color": "#fd7e14", "bg": "#ffe5d0", "emoji": "📊"},
        ActionType.EXIT: {"color": "#dc3545", "bg": "#f8d7da", "emoji": "🚪"},
    }

    style = action_styles.get(evaluation.action, action_styles[ActionType.STAND_DOWN])

    # Large prominent status banner
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {style['bg']} 0%, {style['bg']}dd 100%);
        border-left: 8px solid {style['color']};
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
            <span style="font-size: 48px;">{style['emoji']}</span>
            <div>
                <div style="font-size: 14px; color: #666; text-transform: uppercase; letter-spacing: 1px;">Status</div>
                <div style="font-size: 32px; font-weight: bold; color: {style['color']};">{evaluation.action.value}</div>
            </div>
        </div>
        <div style="font-size: 18px; color: #333; margin-bottom: 8px;">
            <strong>Strategy:</strong> {evaluation.strategy_name}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Reasons and action in clean cards
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 💡 WHY")
        reasons_html = ""
        for reason in evaluation.reasons[:3]:
            reasons_html += f'<div style="padding: 8px 0; border-left: 3px solid {style["color"]}; padding-left: 12px; margin: 4px 0;">• {reason}</div>'
        st.markdown(f'<div style="font-size: 16px;">{reasons_html}</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("### 🎯 NEXT ACTION")
        st.markdown(f"""
        <div style="
            background: {style['color']}22;
            border: 2px solid {style['color']};
            border-radius: 8px;
            padding: 16px;
            font-size: 18px;
            font-weight: bold;
            color: {style['color']};
            text-align: center;
        ">
            {evaluation.next_instruction}
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ========================================================================
    # LIVE CHART
    # ========================================================================
    st.subheader("📈 Live Chart")

    try:
        # Get recent bars
        bars_df = st.session_state.data_loader.fetch_latest_bars(
            lookback_minutes=CHART_LOOKBACK_BARS
        )

        if bars_df.empty:
            st.warning("No bar data available")
        else:
            # Create candlestick chart
            fig = go.Figure()

            fig.add_trace(go.Candlestick(
                x=bars_df["ts_local"],
                open=bars_df["open"],
                high=bars_df["high"],
                low=bars_df["low"],
                close=bars_df["close"],
                name="Price"
            ))

            # Overlay session levels
            now = datetime.now(TZ_LOCAL)

            # Asia levels
            asia_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
            asia_end = now.replace(hour=17, minute=0, second=0, microsecond=0)
            asia_hl = st.session_state.data_loader.get_session_high_low(asia_start, asia_end)

            if asia_hl:
                fig.add_hline(y=asia_hl["high"], line_dash="dash", line_color="green",
                              annotation_text="Asia High", annotation_position="right")
                fig.add_hline(y=asia_hl["low"], line_dash="dash", line_color="red",
                              annotation_text="Asia Low", annotation_position="right")

            # London levels
            london_start = now.replace(hour=18, minute=0, second=0, microsecond=0)
            london_end = now.replace(hour=23, minute=0, second=0, microsecond=0)
            london_hl = st.session_state.data_loader.get_session_high_low(london_start, london_end)

            if london_hl:
                fig.add_hline(y=london_hl["high"], line_dash="dot", line_color="blue",
                              annotation_text="London High", annotation_position="right")
                fig.add_hline(y=london_hl["low"], line_dash="dot", line_color="purple",
                              annotation_text="London Low", annotation_position="right")

            # VWAP
            vwap = st.session_state.data_loader.calculate_vwap(asia_start)
            if vwap:
                fig.add_hline(y=vwap, line_dash="solid", line_color="yellow", line_width=1,
                              annotation_text="VWAP", annotation_position="right")

            fig.update_layout(
                title=f"{symbol} - 1-Minute Chart",
                xaxis_title="Time",
                yaxis_title="Price",
                height=CHART_HEIGHT,
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Chart error: {e}")
        logger.error(f"Chart error: {e}", exc_info=True)

    # Entry details if READY or ACTIVE - ENHANCED VISUAL
    if evaluation.action in [ActionType.ENTER, ActionType.MANAGE]:
        st.divider()

        # Prominent trade details card
        st.markdown("### 📍 TRADE DETAILS")

        # Calculate all metrics
        entry_price = evaluation.entry_price or 0
        stop_price = evaluation.stop_price or 0
        target_price = evaluation.target_price or 0
        risk_pct = evaluation.risk_pct or 0
        risk_dollars = account_size * (risk_pct / 100)

        # Calculate R:R ratio
        if entry_price and stop_price and target_price:
            risk_points = abs(entry_price - stop_price)
            reward_points = abs(target_price - entry_price)
            rr_ratio = reward_points / risk_points if risk_points > 0 else 0
            direction = "LONG" if target_price > entry_price else "SHORT"
        else:
            rr_ratio = 0
            direction = "UNKNOWN"

        # Visual trade card with gradient
        trade_color = "#198754" if evaluation.action == ActionType.ENTER else "#fd7e14"

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {trade_color}15 0%, {trade_color}25 100%);
            border: 3px solid {trade_color};
            border-radius: 12px;
            padding: 24px;
            margin: 16px 0;
        ">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                <div style="text-align: center; padding: 16px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; color: #666; text-transform: uppercase; margin-bottom: 8px;">Direction</div>
                    <div style="font-size: 28px; font-weight: bold; color: {trade_color};">{direction}</div>
                </div>
                <div style="text-align: center; padding: 16px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; color: #666; text-transform: uppercase; margin-bottom: 8px;">Entry</div>
                    <div style="font-size: 28px; font-weight: bold; color: #333;">${entry_price:.2f}</div>
                </div>
                <div style="text-align: center; padding: 16px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; color: #666; text-transform: uppercase; margin-bottom: 8px;">Stop</div>
                    <div style="font-size: 28px; font-weight: bold; color: #dc3545;">${stop_price:.2f}</div>
                </div>
                <div style="text-align: center; padding: 16px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; color: #666; text-transform: uppercase; margin-bottom: 8px;">Target</div>
                    <div style="font-size: 28px; font-weight: bold; color: #198754;">${target_price:.2f}</div>
                </div>
                <div style="text-align: center; padding: 16px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; color: #666; text-transform: uppercase; margin-bottom: 8px;">R:R Ratio</div>
                    <div style="font-size: 28px; font-weight: bold; color: #0d6efd;">1:{rr_ratio:.1f}</div>
                </div>
                <div style="text-align: center; padding: 16px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; color: #666; text-transform: uppercase; margin-bottom: 8px;">Risk</div>
                    <div style="font-size: 24px; font-weight: bold; color: #fd7e14;">${risk_dollars:.0f}</div>
                    <div style="font-size: 14px; color: #666;">({risk_pct:.2f}%)</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# TAB 2: LEVELS
# ============================================================================
with tab_levels:
    st.title("📊 Session Levels")

    if not st.session_state.data_loader:
        if is_cloud_deployment():
            st.info("☁️ **Cloud Mode** - No data loaded yet")
            st.markdown("**Try the AI CHAT tab** to ask about strategies, levels, and trade setups!")
        else:
            st.warning("Initialize data first")
        st.stop()

    now = datetime.now(TZ_LOCAL)

    # Asia
    asia_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    asia_end = now.replace(hour=17, minute=0, second=0, microsecond=0)
    asia_hl = st.session_state.data_loader.get_session_high_low(asia_start, asia_end)

    # London
    london_start = now.replace(hour=18, minute=0, second=0, microsecond=0)
    london_end = now.replace(hour=23, minute=0, second=0, microsecond=0)
    london_hl = st.session_state.data_loader.get_session_high_low(london_start, london_end)

    # Display table
    levels_data = []

    if asia_hl:
        levels_data.append({
            "Session": "Asia (09:00-17:00)",
            "High": f"${asia_hl['high']:.2f}",
            "Low": f"${asia_hl['low']:.2f}",
            "Range": f"{asia_hl['range']:.2f}pts"
        })

    if london_hl:
        levels_data.append({
            "Session": "London (18:00-23:00)",
            "High": f"${london_hl['high']:.2f}",
            "Low": f"${london_hl['low']:.2f}",
            "Range": f"{london_hl['range']:.2f}pts"
        })

    if levels_data:
        st.table(pd.DataFrame(levels_data))

    # Gap analysis
    if asia_hl and london_hl:
        st.subheader("🔍 Gap Analysis")

        upside_gap = london_hl["high"] - asia_hl["high"]
        downside_gap = asia_hl["low"] - london_hl["low"]

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Upside Gap (London - Asia High)",
                f"{upside_gap:.2f}pts",
                delta="LARGE GAP" if upside_gap > CASCADE_MIN_GAP_POINTS else "small gap"
            )

        with col2:
            st.metric(
                "Downside Gap (Asia - London Low)",
                f"{downside_gap:.2f}pts",
                delta="LARGE GAP" if downside_gap > CASCADE_MIN_GAP_POINTS else "small gap"
            )

# ============================================================================
# TAB 3: TRADE PLAN
# ============================================================================
with tab_trade_plan:
    st.title("📋 Trade Plan Calculator")

    if not st.session_state.last_evaluation:
        if is_cloud_deployment():
            st.info("☁️ **Cloud Mode** - No active trade setup yet")
            st.markdown("""
            **This calculator works once you have data loaded.**

            For now, try the **AI CHAT tab** to:
            - Calculate position sizes manually
            - Ask about risk management
            - Get trade setup explanations
            """)
        else:
            st.warning("No active evaluation")
        st.stop()

    eval = st.session_state.last_evaluation

    if eval.entry_price and eval.stop_price and eval.risk_pct:
        st.subheader("Position Size Calculator")

        # Calculate
        risk_points = abs(eval.entry_price - eval.stop_price)
        risk_dollars = account_size * (eval.risk_pct / 100)

        # Determine contract size (depends on instrument)
        if symbol == "MNQ":
            tick_value = 2.0  # $2 per tick
            tick_size = 0.25
        elif symbol == "MGC":
            tick_value = 10.0  # $10 per point
            tick_size = 0.1
        else:
            tick_value = 1.0
            tick_size = 0.01

        risk_per_contract = risk_points * tick_value
        contracts = int(risk_dollars / risk_per_contract) if risk_per_contract > 0 else 0

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Risk Points", f"{risk_points:.2f}pts")
        with col2:
            st.metric("Risk $", f"${risk_dollars:.0f}")
        with col3:
            st.metric("Contracts", contracts)

        st.divider()

        st.subheader("Trade Summary")

        st.code(f"""
STRATEGY: {eval.strategy_name}
DIRECTION: {"LONG" if eval.entry_price < eval.stop_price else "SHORT"}

ENTRY:    ${eval.entry_price:.2f}
STOP:     ${eval.stop_price:.2f}
TARGET:   ${eval.target_price:.2f if eval.target_price else 0.0}

RISK:     {risk_points:.2f}pts = ${risk_dollars:.0f} ({eval.risk_pct:.2f}%)
SIZE:     {contracts} contracts

MANAGEMENT:
- Phase 1: Move stop to BE at +1R (within 10 min)
- Phase 2: Trail structure (after 15 min)
- Max hold: 90 minutes (cascades)
        """)

    else:
        st.info("No active trade plan. Wait for ENTER signal.")

# ============================================================================
# TAB 4: JOURNAL
# ============================================================================
with tab_journal:
    st.title("📓 Trade Journal")

    st.info("Journal entries are automatically logged on state changes.")

    # Query recent journal entries
    try:
        from utils import get_recent_journal_entries

        journal_df = get_recent_journal_entries(limit=50)

        if journal_df is not None and not journal_df.empty:
            # Display as table with formatted columns
            display_df = journal_df.copy()
            display_df["ts_local"] = pd.to_datetime(display_df["ts_local"]).dt.strftime("%Y-%m-%d %H:%M:%S")

            # Format prices
            if "entry_price" in display_df.columns:
                display_df["entry_price"] = display_df["entry_price"].apply(
                    lambda x: f"${x:.2f}" if pd.notna(x) else ""
                )
            if "stop_price" in display_df.columns:
                display_df["stop_price"] = display_df["stop_price"].apply(
                    lambda x: f"${x:.2f}" if pd.notna(x) else ""
                )
            if "target_price" in display_df.columns:
                display_df["target_price"] = display_df["target_price"].apply(
                    lambda x: f"${x:.2f}" if pd.notna(x) else ""
                )
            if "risk_pct" in display_df.columns:
                display_df["risk_pct"] = display_df["risk_pct"].apply(
                    lambda x: f"{x:.2f}%" if pd.notna(x) else ""
                )

            # Rename columns for display
            display_df.columns = [
                "Time", "Strategy", "State", "Action", "Reasons",
                "Next Instruction", "Entry", "Stop", "Target", "Risk %"
            ]

            # Show most recent first
            st.dataframe(
                display_df,
                use_container_width=True,
                height=600
            )

            # Summary stats
            st.divider()
            st.subheader("📊 Journal Summary")

            col1, col2, col3 = st.columns(3)

            with col1:
                total_entries = len(journal_df)
                st.metric("Total Entries", total_entries)

            with col2:
                enter_actions = len(journal_df[journal_df["action"] == "ENTER"])
                st.metric("Entry Signals", enter_actions)

            with col3:
                if "strategy_name" in journal_df.columns:
                    unique_strategies = journal_df["strategy_name"].nunique()
                    st.metric("Strategies Active", unique_strategies)

            # Strategy breakdown
            if "strategy_name" in journal_df.columns and "action" in journal_df.columns:
                st.subheader("Strategy Breakdown")
                strategy_counts = journal_df.groupby(["strategy_name", "action"]).size().reset_index(name="count")
                st.dataframe(strategy_counts, use_container_width=True)

        else:
            st.warning("No journal entries found. Entries will appear as strategies are evaluated.")

    except Exception as e:
        st.error(f"Error loading journal: {e}")
        logger.error(f"Journal display error: {e}", exc_info=True)

# ============================================================================
# TAB 5: AI CHAT
# ============================================================================
with tab_ai_chat:
    st.title("🤖 AI Trading Assistant")

    # Check if AI is available
    if not st.session_state.ai_assistant.is_available():
        st.error("⚠️ AI Assistant not available. Add ANTHROPIC_API_KEY to .env file.")
        st.info("Get your API key from: https://console.anthropic.com/")
        st.code("ANTHROPIC_API_KEY=sk-ant-your-key-here", language="bash")
    else:
        st.success("✅ AI Assistant ready! Claude Sonnet 4.5 - Ask about strategies, calculations, or trade decisions.")

        # Display chat history
        st.subheader("💬 Conversation")

        chat_container = st.container()
        with chat_container:
            if not st.session_state.chat_history:
                st.info("Start a conversation! Ask me about strategies, risk calculations, or trade setups.")
            else:
                for msg in st.session_state.chat_history:
                    if msg["role"] == "user":
                        st.markdown(f"**You:** {msg['content']}")
                    else:
                        st.markdown(f"**AI:** {msg['content']}")
                        st.divider()

        # Chat input
        st.subheader("Ask a Question")

        user_input = st.text_area(
            "Your question:",
            key="ai_chat_input",
            placeholder="Example: ORB is 2700-2706, I want to go LONG, what's my stop and target?",
            height=100
        )

        col1, col2, col3 = st.columns([1, 1, 3])

        with col1:
            if st.button("Send", type="primary", use_container_width=True):
                if user_input.strip():
                    with st.spinner("Thinking..."):
                        # Get current context
                        strategy_state = None
                        if st.session_state.get('last_evaluation'):
                            result = st.session_state.last_evaluation
                            strategy_state = {
                                'strategy': result.get('strategy_name', 'None'),
                                'action': result.get('action', 'STAND_DOWN'),
                                'reasons': result.get('reasons', []),
                                'next_action': result.get('next_action', 'Wait'),
                                'current_session': 'Unknown'
                            }

                        # Get session levels (if available)
                        session_levels = {}
                        # TODO: Extract from data_loader if needed

                        # Get ORB data (if available)
                        orb_data = {}
                        # TODO: Extract from data_loader if needed

                        # Get backtest stats
                        backtest_stats = {
                            'total_r': 1153.0,
                            'win_rate': 57.2,
                            'avg_r': 0.43,
                            'total_trades': 2682,
                            'best_orb': '1100',
                            'best_orb_r': 0.49
                        }

                        # Get current price
                        current_price = 0
                        if st.session_state.data_loader:
                            latest = st.session_state.data_loader.get_latest_bar()
                            if latest:
                                current_price = latest.get('close', 0)

                        # Call AI
                        response = st.session_state.ai_assistant.chat(
                            user_message=user_input,
                            conversation_history=st.session_state.chat_history,
                            session_id=st.session_state.session_id,
                            instrument=st.session_state.current_symbol,
                            current_price=current_price,
                            strategy_state=strategy_state,
                            session_levels=session_levels,
                            orb_data=orb_data,
                            backtest_stats=backtest_stats
                        )

                        # Update history
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        st.session_state.chat_history.append({"role": "assistant", "content": response})

                    # Rerun to show new messages
                    st.rerun()

        with col2:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        # Quick examples
        st.subheader("💡 Example Questions")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **Trade Calculations:**
            - "ORB is 2700-2706, direction LONG, calculate my stop and target"
            - "I'm in a trade at 2705, ORB was 2700-2706, am I close to stop?"
            - "What's the risk in dollars for a $10k account?"
            """)

        with col2:
            st.markdown("""
            **Strategy Questions:**
            - "Why is 00:30 ORB good?"
            - "What's the best strategy right now?"
            - "Should I trade 09:00 or 10:00 ORB?"
            """)

        # Show recent trade discussions from memory
        st.divider()
        st.subheader("📚 Recent Trade Discussions")

        recent_trades = st.session_state.memory_manager.get_recent_trades(
            session_id=st.session_state.session_id,
            days=7
        )

        if recent_trades:
            for trade in recent_trades[:5]:
                with st.expander(f"{trade['timestamp'].strftime('%Y-%m-%d %H:%M')} - {trade['role']}"):
                    st.write(trade['content'])
        else:
            st.info("No recent trade discussions found. Start asking questions to build your memory!")

# ============================================================================
# AUTO-REFRESH
# ============================================================================
if auto_refresh and st.session_state.data_loader:
    time.sleep(DATA_REFRESH_SECONDS)
    st.rerun()
