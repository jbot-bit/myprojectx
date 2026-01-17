"""
MOBILE TRADING HUB - Streamlit Application
Card-based, swipeable, mobile-first trading interface
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
import uuid
import os
from pathlib import Path
from streamlit_autorefresh import st_autorefresh

from config import *
from data_loader import LiveDataLoader
from strategy_engine import StrategyEngine, ActionType, StrategyState
from utils import calculate_position_size, format_price, log_to_journal
from ai_memory import AIMemoryManager
from ai_assistant import TradingAIAssistant
from cloud_mode import is_cloud_deployment, show_cloud_setup_instructions
from alert_system import AlertSystem, render_alert_settings, render_audio_player, render_desktop_notification
from setup_scanner import SetupScanner, render_setup_scanner_tab
from enhanced_charting import EnhancedChart, ORBOverlay, TradeMarker, ChartTimeframe, resample_bars
from live_chart_builder import build_live_trading_chart, calculate_trade_levels
from data_quality_monitor import DataQualityMonitor, render_data_quality_panel
from market_hours_monitor import MarketHoursMonitor, render_market_hours_indicator
from risk_manager import RiskManager, RiskLimits, render_risk_dashboard
from position_tracker import PositionTracker, render_position_panel, render_empty_position_panel
from directional_bias import DirectionalBiasDetector, render_directional_bias_indicator
from strategy_discovery import StrategyDiscovery, DiscoveryConfig, add_setup_to_production, generate_config_snippet
# Removed MarketIntelligence - not used in mobile app (skeleton code)
# Removed render_intelligence_panel - not used in mobile app
from professional_ui import (
    inject_professional_css,
    render_pro_metric,
    render_status_badge,
    render_intelligence_card,
    render_countdown_timer,
    render_price_display
)
from mobile_ui import (
    inject_mobile_css,
    render_card_navigation,
    render_dashboard_card,
    render_chart_card,
    render_trade_entry_card,
    render_positions_card,
    render_ai_chat_card
)

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
# PAGE CONFIG - MOBILE OPTIMIZED
# ============================================================================
st.set_page_config(
    page_title="Trading Hub Mobile",
    page_icon="📱",
    layout="wide",  # Use wide for card layout
    initial_sidebar_state="collapsed"  # Hide sidebar on mobile
)

# Inject mobile CSS
inject_mobile_css()

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
    # Load persistent history from database
    try:
        loaded_history = st.session_state.memory_manager.load_session_history(
            session_id=st.session_state.session_id,
            limit=50
        )
        st.session_state.chat_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in loaded_history
        ]
        if loaded_history:
            logger.info(f"Loaded {len(loaded_history)} messages from persistent memory")
    except Exception as e:
        logger.warning(f"Could not load chat history: {e}")
        st.session_state.chat_history = []
if "alert_system" not in st.session_state:
    st.session_state.alert_system = AlertSystem()
if "data_quality_monitor" not in st.session_state:
    st.session_state.data_quality_monitor = DataQualityMonitor()
if "market_hours_monitor" not in st.session_state:
    st.session_state.market_hours_monitor = MarketHoursMonitor()
if "risk_manager" not in st.session_state:
    limits = RiskLimits(
        daily_loss_dollars=1000.0,
        daily_loss_r=10.0,
        weekly_loss_dollars=3000.0,
        weekly_loss_r=30.0,
        max_concurrent_positions=3,
        max_position_size_pct=2.0
    )
    st.session_state.risk_manager = RiskManager(DEFAULT_ACCOUNT_SIZE, limits)
if "position_tracker" not in st.session_state:
    st.session_state.position_tracker = PositionTracker()
if "setup_scanner" not in st.session_state:
    gold_db_path = str(Path(__file__).parent.parent / "gold.db")
    st.session_state.setup_scanner = SetupScanner(gold_db_path)
if "chart_timeframe" not in st.session_state:
    st.session_state.chart_timeframe = ChartTimeframe.M1
if "indicators_enabled" not in st.session_state:
    st.session_state.indicators_enabled = {
        "ema_9": False,
        "ema_20": False,
        "vwap": True,
        "rsi": False,
        "orb_overlays": True,
    }
if "directional_bias_detector" not in st.session_state:
    gold_db_path = str(Path(__file__).parent.parent / "gold.db")
    st.session_state.directional_bias_detector = DirectionalBiasDetector(gold_db_path)
if "strategy_discovery" not in st.session_state:
    gold_db_path = str(Path(__file__).parent.parent / "gold.db")
    st.session_state.strategy_discovery = StrategyDiscovery(gold_db_path)
# MarketIntelligence removed - was skeleton code (initialized but never used)
if "mobile_current_card" not in st.session_state:
    st.session_state.mobile_current_card = 0  # Start at Dashboard

# ============================================================================
# AUTO-REFRESH SETUP
# ============================================================================
now = datetime.now(TZ_LOCAL)
is_market_hours = 9 <= now.hour < 17

if 'auto_refresh_enabled' not in st.session_state:
    st.session_state.auto_refresh_enabled = is_market_hours

# Auto-refresh (faster during market hours)
if st.session_state.auto_refresh_enabled:
    refresh_interval = 10 if is_market_hours else 30
    count = st_autorefresh(interval=refresh_interval * 1000, key="mobile_refresh")

# ============================================================================
# DATA INITIALIZATION CHECK
# ============================================================================
if not st.session_state.data_loader or not st.session_state.strategy_engine:
    # Show initialization screen
    st.markdown("""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100vh;
        padding: 20px;
        text-align: center;
    ">
        <div style="font-size: 64px; margin-bottom: 24px;">📱</div>
        <div style="font-size: 28px; font-weight: 700; color: #f9fafb; margin-bottom: 16px;">
            Trading Hub Mobile
        </div>
        <div style="font-size: 16px; color: #9ca3af; margin-bottom: 32px;">
            Swipeable cards • Dark mode • Touch optimized
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Initialize Data")

    if st.button("🚀 Start Trading Hub", use_container_width=True, type="primary"):
        with st.spinner("Loading data..."):
            try:
                # Initialize data loader
                loader = LiveDataLoader(PRIMARY_INSTRUMENT)

                # Fetch data (cloud-aware)
                if is_cloud_deployment():
                    if os.getenv("PROJECTX_API_KEY"):
                        loader.refresh()
                        st.success("Fetched live data from ProjectX API")
                    else:
                        st.error("No PROJECTX_API_KEY found. Add it in Streamlit Cloud secrets.")
                        st.stop()
                else:
                    # Local: check if we need to backfill
                    latest_bar = loader.get_latest_bar()
                    needs_backfill = True

                    if latest_bar:
                        latest_time = latest_bar['ts_utc']
                        time_since_last = datetime.now(TZ_UTC) - latest_time
                        if time_since_last.total_seconds() < 6 * 3600:
                            needs_backfill = False

                    if needs_backfill:
                        gold_db_path = str(Path(__file__).parent.parent / "gold.db")
                        loader.backfill_from_gold_db(gold_db_path, days=2)

                    loader.refresh()

                st.session_state.data_loader = loader

                # Initialize ML engine if enabled
                ml_engine = None
                if ML_ENABLED:
                    try:
                        import sys
                        sys.path.insert(0, str(Path(__file__).parent.parent))
                        from ml_inference.inference_engine import MLInferenceEngine
                        ml_engine = MLInferenceEngine()
                        logger.info("ML engine initialized successfully")
                    except Exception as e:
                        logger.warning(f"ML engine initialization failed: {e}")

                st.session_state.strategy_engine = StrategyEngine(loader, ml_engine=ml_engine)

                st.success(f"Loaded data for {PRIMARY_INSTRUMENT}")
                logger.info(f"Data initialized for {PRIMARY_INSTRUMENT}")

                st.rerun()

            except Exception as e:
                st.error(f"Error loading data: {e}")
                logger.error(f"Data load error: {e}", exc_info=True)

    st.info("☁️ Cloud Mode: Data will be fetched from ProjectX API" if is_cloud_deployment() else "💻 Local Mode: Data loaded from local database")

    st.stop()

# ============================================================================
# EVALUATE STRATEGIES
# ============================================================================
try:
    evaluation = st.session_state.strategy_engine.evaluate_all()
    st.session_state.last_evaluation = evaluation
    log_to_journal(evaluation)
except Exception as e:
    st.error(f"Strategy evaluation error: {e}")
    logger.error(f"Evaluation error: {e}", exc_info=True)
    evaluation = None

# ============================================================================
# CARD-BASED NAVIGATION
# ============================================================================

# Card definitions
CARDS = [
    {"name": "Dashboard", "icon": "📊", "render": render_dashboard_card},
    {"name": "Chart", "icon": "📈", "render": render_chart_card},
    {"name": "Trade", "icon": "🎯", "render": render_trade_entry_card},
    {"name": "Positions", "icon": "💼", "render": render_positions_card},
    {"name": "AI Chat", "icon": "🤖", "render": render_ai_chat_card},
]

card_names = [f"{card['icon']} {card['name']}" for card in CARDS]
current_card = st.session_state.mobile_current_card

# Navigation
render_card_navigation(current_card, len(CARDS), card_names)

# Render current card
st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)  # Spacer

try:
    if current_card == 0:
        # Dashboard
        render_dashboard_card(
            st.session_state.data_loader,
            st.session_state.strategy_engine,
            evaluation,
            st.session_state.current_symbol
        )
    elif current_card == 1:
        # Chart
        render_chart_card(
            st.session_state.data_loader,
            st.session_state.strategy_engine,
            evaluation
        )
    elif current_card == 2:
        # Trade Entry
        render_trade_entry_card(
            st.session_state.data_loader,
            st.session_state.strategy_engine
        )
    elif current_card == 3:
        # Positions
        render_positions_card(
            st.session_state.risk_manager,
            st.session_state.data_loader
        )
    elif current_card == 4:
        # AI Chat
        render_ai_chat_card(
            st.session_state.ai_assistant,
            st.session_state.chat_history,
            st.session_state.current_symbol,
            st.session_state.data_loader
        )

except Exception as e:
    st.error(f"Error rendering card: {e}")
    logger.error(f"Card render error: {e}", exc_info=True)

# ============================================================================
# SETTINGS MODAL (OPTIONAL - ACCESSIBLE VIA BOTTOM BUTTON)
# ============================================================================

# Small settings button at bottom
st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

with st.expander("⚙️ Settings", expanded=False):
    st.markdown("### App Settings")

    # Account size
    account_size = st.number_input(
        "Account Size ($)",
        min_value=1000.0,
        max_value=10000000.0,
        value=st.session_state.account_size,
        step=1000.0,
        key="mobile_account_size"
    )
    st.session_state.account_size = account_size

    # Auto-refresh toggle
    auto_refresh = st.checkbox(
        "Auto-refresh",
        value=st.session_state.auto_refresh_enabled,
        key="mobile_auto_refresh"
    )
    st.session_state.auto_refresh_enabled = auto_refresh

    if auto_refresh:
        st.info(f"Refreshing every {refresh_interval}s")

    # Refresh data button
    if st.button("🔄 Refresh Data Now", use_container_width=True):
        with st.spinner("Refreshing..."):
            try:
                st.session_state.data_loader.refresh()
                st.success("Data refreshed!")
                st.rerun()
            except Exception as e:
                st.error(f"Refresh error: {e}")

    # Reset button
    if st.button("🔄 Reset App", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.success("App reset! Reloading...")
        st.rerun()

# Footer
st.markdown("""
<div style="
    text-align: center;
    padding: 20px;
    color: #6b7280;
    font-size: 12px;
">
    Trading Hub Mobile v2.0 • Swipe to navigate • {time}
</div>
""".format(time=datetime.now(TZ_LOCAL).strftime('%H:%M:%S')), unsafe_allow_html=True)
