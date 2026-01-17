# Enhanced Trading App - Integration Guide

**Date**: 2026-01-16
**Purpose**: Document integration of professional-grade features into app_trading_hub.py

---

## New Modules Created

1. **alert_system.py** - Multi-channel alerts (audio, desktop, price levels)
2. **setup_scanner.py** - Multi-instrument setup scanner (all 17 setups)
3. **enhanced_charting.py** - Professional charting with indicators and overlays

---

## Integration Steps

### 1. Add New Imports (Line 20)

```python
from alert_system import AlertSystem, render_alert_settings, render_audio_player, render_desktop_notification
from setup_scanner import SetupScanner, render_setup_scanner_tab
from enhanced_charting import EnhancedChart, ORBOverlay, TradeMarker, ChartTimeframe, resample_bars
```

### 2. Add New Session State Variables (Line 64)

```python
if "alert_system" not in st.session_state:
    st.session_state.alert_system = AlertSystem()
if "setup_scanner" not in st.session_state:
    st.session_state.setup_scanner = SetupScanner("gold.db")
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
```

### 3. Add Alert Settings in Sidebar (Line 183)

```python
# Alert system integration
render_alert_settings()
```

### 4. Change Tab Structure (Line 194)

**OLD**:
```python
tab_live, tab_levels, tab_trade_plan, tab_journal, tab_ai_chat = st.tabs([
    "🔴 LIVE",
    "📊 LEVELS",
    "📋 TRADE PLAN",
    "📓 JOURNAL",
    "🤖 AI CHAT"
])
```

**NEW**:
```python
tab_live, tab_scanner, tab_levels, tab_trade_plan, tab_journal, tab_ai_chat = st.tabs([
    "🔴 LIVE",
    "🔍 SCANNER",
    "📊 LEVELS",
    "📋 TRADE PLAN",
    "📓 JOURNAL",
    "🤖 AI CHAT"
])
```

### 5. Add Setup Scanner Tab (After LIVE tab, around line 697)

```python
# ============================================================================
# TAB 2: SETUP SCANNER
# ============================================================================
with tab_scanner:
    st.title("🔍 Setup Scanner")

    # Get current prices and ATRs for all instruments
    current_prices = {}
    current_atrs = {}

    # For now, use manual input (can be enhanced with live data later)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("MGC")
        current_prices["MGC"] = st.number_input("MGC Price", value=2650.0, step=0.1, key="scanner_mgc_price")
        current_atrs["MGC"] = st.number_input("MGC ATR", value=40.0, step=0.1, key="scanner_mgc_atr")

    with col2:
        st.subheader("NQ")
        current_prices["NQ"] = st.number_input("NQ Price", value=21000.0, step=1.0, key="scanner_nq_price")
        current_atrs["NQ"] = st.number_input("NQ ATR", value=400.0, step=1.0, key="scanner_nq_atr")

    with col3:
        st.subheader("MPL")
        current_prices["MPL"] = st.number_input("MPL Price", value=1000.0, step=0.1, key="scanner_mpl_price")
        current_atrs["MPL"] = st.number_input("MPL ATR", value=20.0, step=0.1, key="scanner_mpl_atr")

    st.divider()

    # Render scanner
    render_setup_scanner_tab(
        st.session_state.setup_scanner,
        current_prices,
        current_atrs,
        orb_data=None  # TODO: Pass actual ORB data from live data loader
    )
```

### 6. Enhance LIVE Tab Chart (Replace chart section around line 565)

**Add Chart Settings Before Chart**:
```python
# Chart settings
st.subheader("📈 Live Chart")

col1, col2, col3, col4 = st.columns(4)

with col1:
    timeframe = st.selectbox(
        "Timeframe",
        [ChartTimeframe.M1, ChartTimeframe.M5, ChartTimeframe.M15, ChartTimeframe.H1],
        key="chart_timeframe_selector"
    )
    st.session_state.chart_timeframe = timeframe

with col2:
    show_ema = st.checkbox("EMA (9, 20)", value=st.session_state.indicators_enabled["ema_9"], key="show_ema")
    st.session_state.indicators_enabled["ema_9"] = show_ema
    st.session_state.indicators_enabled["ema_20"] = show_ema

with col3:
    show_vwap = st.checkbox("VWAP", value=st.session_state.indicators_enabled["vwap"], key="show_vwap")
    st.session_state.indicators_enabled["vwap"] = show_vwap

with col4:
    show_orbs = st.checkbox("ORB Overlays", value=st.session_state.indicators_enabled["orb_overlays"], key="show_orbs")
    st.session_state.indicators_enabled["orb_overlays"] = show_orbs

st.divider()
```

**Replace Chart Creation Code**:
```python
try:
    # Get recent bars
    bars_df = st.session_state.data_loader.fetch_latest_bars(
        lookback_minutes=CHART_LOOKBACK_BARS
    )

    if bars_df.empty:
        st.warning("No bar data available")
    else:
        # Resample if needed
        if timeframe != ChartTimeframe.M1:
            bars_df = resample_bars(bars_df, timeframe)

        # Create enhanced chart
        chart = EnhancedChart(timeframe)
        fig = chart.create_chart(
            bars_df,
            title=f"{symbol} - {timeframe.upper()} Chart",
            height=CHART_HEIGHT,
            show_volume=False
        )

        # Add indicators
        if st.session_state.indicators_enabled["ema_9"]:
            chart.add_ema(bars_df, 9, color='blue')
            chart.add_ema(bars_df, 20, color='purple')

        if st.session_state.indicators_enabled["vwap"]:
            chart.add_vwap(bars_df)

        # Add session levels
        now = datetime.now(TZ_LOCAL)
        asia_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        asia_end = now.replace(hour=17, minute=0, second=0, microsecond=0)
        asia_hl = st.session_state.data_loader.get_session_high_low(asia_start, asia_end)

        if asia_hl:
            chart.add_session_levels(
                asia_hl["high"],
                asia_hl["low"],
                "Asia",
                color="green"
            )

        # Add ORB overlays if enabled
        if st.session_state.indicators_enabled["orb_overlays"]:
            # Example: Add current ORB if active
            # TODO: Get actual ORB data from data loader
            pass

        # Display chart
        st.plotly_chart(chart.get_figure(), use_container_width=True)

except Exception as e:
    st.error(f"Chart error: {e}")
    logger.error(f"Chart error: {e}", exc_info=True)
```

### 7. Add Alert Triggers in ORB Monitoring (Around line 290)

**In ORB ACTIVE section**:
```python
# Trigger alert when ORB opens
if in_orb_window:
    # Check if we should alert
    alert_system = st.session_state.alert_system

    # Alert that ORB is active
    if st.session_state.get('desktop_alerts_enabled', True):
        alert = alert_system.trigger_orb_window_open(
            current_orb_name,
            orb_high if orb_high else 0,
            orb_low if orb_low else 0,
            filter_passed,
            symbol
        )

        if alert:
            # Play audio
            if st.session_state.get('audio_alerts_enabled', True):
                st.components.v1.html(
                    render_audio_player(alert['sound']),
                    height=0
                )

            # Show desktop notification
            if st.session_state.get('desktop_alerts_enabled', True):
                st.components.v1.html(
                    render_desktop_notification(alert['title'], alert['message'], alert['priority']),
                    height=0
                )
```

**In COUNTDOWN section (5 minutes before ORB)**:
```python
# Alert 5 minutes before ORB opens
if next_orb_name and next_orb_start:
    time_until = (next_orb_start - now).total_seconds()
    minutes_until = int(time_until // 60)

    # Trigger 5-minute warning
    if 4 <= minutes_until <= 5:
        alert_system = st.session_state.alert_system
        alert = alert_system.trigger_orb_opening_soon(
            next_orb_name,
            minutes_until,
            symbol
        )

        if alert and st.session_state.get('audio_alerts_enabled', True):
            st.components.v1.html(
                render_audio_player(alert['sound']),
                height=0
            )
```

### 8. Add Price Alert Management (New section in Sidebar)

```python
# Price Alerts (in sidebar, after alert settings)
with st.sidebar.expander("💰 Price Alerts", expanded=False):
    alert_system = st.session_state.alert_system

    # Add new alert
    st.subheader("Add Price Alert")
    alert_name = st.text_input("Alert Name", key="new_alert_name")
    alert_price = st.number_input("Price", value=2700.0, step=0.1, key="new_alert_price")
    alert_condition = st.selectbox(
        "Condition",
        ["above", "below", "cross_above", "cross_below"],
        key="new_alert_condition"
    )

    if st.button("Add Alert", key="add_price_alert"):
        if alert_name:
            alert_system.add_price_alert(
                alert_name,
                alert_price,
                alert_condition,
                st.session_state.current_symbol
            )
            st.success(f"Alert added: {alert_name}")

    # Show active alerts
    st.subheader("Active Alerts")
    active_alerts = alert_system.get_active_price_alerts(st.session_state.current_symbol)

    if active_alerts:
        for alert in active_alerts:
            col1, col2 = st.columns([3, 1])
            with col1:
                status = "🔔" if not alert.triggered else "✅"
                st.caption(f"{status} {alert.name}: {alert.condition} {alert.price:.1f}")
            with col2:
                if st.button("×", key=f"remove_alert_{alert.alert_id}"):
                    alert_system.remove_price_alert(alert.alert_id)
                    st.rerun()
    else:
        st.caption("No active alerts")
```

---

## Features Added

### ✅ Alert System
- Audio alerts for ORB windows and setups
- Desktop notifications
- Price level alerts (user-configurable)
- Alert cooldowns to prevent spam

### ✅ Setup Scanner
- Monitors all 17 setups across MGC, NQ, MPL
- Real-time status tracking
- Filter by tier, status, instrument
- Sortable table with color coding
- Detailed setup information

### ✅ Enhanced Charting
- Multiple timeframes (1m, 5m, 15m, 1h)
- Technical indicators (EMA, SMA, VWAP, RSI, ATR, Bollinger Bands)
- ORB visual overlays (rectangles + levels)
- Trade markers (entry, stop, target)
- Session level overlays
- Previous day/week levels

### ✅ Professional Polish
- Color-coded statuses
- Gradient designs
- Responsive layout
- Clean typography
- Institutional-grade UX

---

## Testing Checklist

- [ ] Audio alerts play when ORB opens
- [ ] Desktop notifications appear
- [ ] Price alerts trigger correctly
- [ ] Setup scanner shows all 17 setups
- [ ] Scanner filters work (elite, active, instrument)
- [ ] Chart timeframe selector works
- [ ] Indicators display correctly
- [ ] ORB overlays appear on chart
- [ ] Session levels display
- [ ] All tabs load without errors
- [ ] Auto-refresh works

---

## Future Enhancements

1. **WebSocket Integration** - Real-time price streaming
2. **Trade Execution** - One-click order entry (if broker API available)
3. **Position Monitoring** - Active position display with P&L
4. **Advanced Backtesting** - Click "Backtest This Setup" button
5. **Risk Dashboard** - Comprehensive risk monitoring across all positions

---

**Status**: Ready for integration
**Estimated Integration Time**: 2-3 hours
**Test Time**: 1 hour
