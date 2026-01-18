# SOURCE OF TRUTH - TRADING APP

**Date**: 2026-01-16
**Status**: ✅ SINGLE SOURCE OF TRUTH ESTABLISHED

---

## ⚠️ CRITICAL: TWO VALID APPS (Desktop + Mobile)

**DESKTOP APP (Tabs Interface):**
```
trading_app/app_trading_hub.py
```
- Launch: `START_TRADING_APP.bat` or `streamlit run trading_app/app_trading_hub.py`
- URL: http://localhost:8501
- Best for: Desktop/laptop screens

**MOBILE APP (Tinder Cards Interface):**
```
trading_app/app_mobile.py
```
- Launch: `START_MOBILE_APP.bat` or `streamlit run trading_app/app_mobile.py`
- URL: http://localhost:8501
- Best for: Phones (swipeable cards)
- Android APK: `app-debug.apk` (wraps this URL)

**Choose based on your device. Both apps access the same database and logic.**

---

## ❌ DO NOT USE THESE (ARCHIVED)

These apps are OLD and INCOMPLETE:
- ~~unified_trading_app.py~~ (archived to _archive/)
- ~~trading_app_decision_focused.py~~ (archived to _archive/)

**If you see any other .py files in the root claiming to be a "trading app", DO NOT USE THEM.**

---

## What's In The Production App

**trading_app/app_trading_hub.py** has EVERYTHING:

### Tabs:
1. **🔴 LIVE** - Real-time strategy evaluation with strategy engine
2. **📡 SETUP SCANNER** - All 17 setups (MGC/NQ/MPL) monitored simultaneously
3. **📍 LEVELS** - Key price levels and support/resistance
4. **📋 TRADE PLAN** - Entry/stop/target calculations
5. **📖 JOURNAL** - Trade logging and performance tracking
6. **🤖 AI CHAT** - Claude Sonnet 4.5 with memory

### Professional Features:
- ✅ **Alert System** - Audio + desktop notifications
- ✅ **Risk Manager** - Position sizing and daily loss limits
- ✅ **Position Tracker** - Open positions and P&L tracking
- ✅ **Data Quality Monitor** - Real-time data health checks
- ✅ **Market Hours Monitor** - Session timing and status
- ✅ **Directional Bias Detector** - ML-based direction prediction (1100 ORB)
- ✅ **Enhanced Charting** - ORB overlays and trade markers

### Data Source:
- ✅ **Uses validated_setups** table from gold.db
- ✅ **Synced with config.py** (verified by test_app_sync.py)
- ✅ **17 profitable setups** with correct RR, SL modes, and filters
- ✅ **Tier system** (S+, S, A, B, C) with automatic risk adjustment

### Critical Features:
- ✅ **Correct target calculation** - Uses actual RR from setup (not always 1R)
- ✅ **Tier-based risk** - S+=0.50%, A=0.50%, B/C=0.10-0.25%
- ✅ **Configurable account size** - Set your account size in sidebar
- ✅ **AI assistant with memory** - Remembers your trading history

---

## Why Only One App?

**Problems with multiple apps:**
1. ❌ Risk of using wrong version with bugs
2. ❌ Confusion about which one has latest fixes
3. ❌ Wasted time fixing same bug in multiple places
4. ❌ Data inconsistency between apps
5. ❌ Impossible to maintain quality

**Solution:**
- ✅ ONE app to rule them all
- ✅ All features in one place
- ✅ All fixes go to one place
- ✅ No confusion, no mistakes

---

## File Structure

```
myprojectx/
├── START_TRADING_APP.bat          ← USE THIS to launch app
├── SOURCE_OF_TRUTH.md             ← THIS FILE (read it!)
├── gold.db                         ← Database with validated_setups
├── test_app_sync.py               ← Verify database/config sync
├── trading_app/                    ← THE PRODUCTION CODE
│   ├── app_trading_hub.py         ← THE ONE TRUE APP ⭐
│   ├── config.py                  ← Setup configs (synced with DB)
│   ├── strategy_engine.py         ← Strategy evaluation logic
│   ├── setup_detector.py          ← Reads validated_setups from DB
│   ├── ai_assistant.py            ← AI chat functionality
│   ├── ai_memory.py               ← Conversation memory
│   ├── alert_system.py            ← Alerts & notifications
│   ├── risk_manager.py            ← Risk management
│   ├── position_tracker.py        ← Position tracking
│   ├── data_quality_monitor.py    ← Data health checks
│   ├── market_hours_monitor.py    ← Session timing
│   ├── directional_bias.py        ← Direction prediction
│   ├── enhanced_charting.py       ← Advanced charts
│   ├── setup_scanner.py           ← Multi-setup scanner
│   ├── data_loader.py             ← Live data loading
│   └── utils.py                   ← Helper functions
└── _archive/                       ← OLD STUFF (don't use!)
    ├── unified_trading_app.py.OLD
    └── trading_app_decision_focused.py.OLD
```

---

## Verification Checklist

Before trading with the app, verify:

1. ✅ Launch with START_TRADING_APP.bat
2. ✅ Opens at http://localhost:8501
3. ✅ See 6 tabs: LIVE, SCANNER, LEVELS, TRADE PLAN, JOURNAL, AI CHAT
4. ✅ Run `python test_app_sync.py` - ALL TESTS PASS
5. ✅ Check sidebar - can set account size
6. ✅ Check SCANNER tab - shows all 17 setups
7. ✅ Check AI CHAT tab - Claude Sonnet 4.5 ready

---

## When Making Changes

**ALWAYS:**
1. Edit `trading_app/app_trading_hub.py` (or its supporting modules in trading_app/)
2. Run `python test_app_sync.py` after any database/config changes
3. Test the changes in the running app
4. Document changes in ENHANCEMENTS_COMPLETE.md

**NEVER:**
1. Create new app files in root directory
2. Edit files in _archive/
3. Make copies of app_trading_hub.py
4. Skip running test_app_sync.py

---

## Emergency: If App Won't Start

1. Check if port 8501 is in use:
   ```bash
   netstat -ano | findstr :8501
   ```

2. Kill the process:
   ```bash
   taskkill /F /PID <pid_number>
   ```

3. Relaunch:
   ```bash
   START_TRADING_APP.bat
   ```

---

## Questions?

Ask the AI assistant in the app! (🤖 AI CHAT tab)

---

**Remember: ONE app. ONE source of truth. No confusion. No mistakes.**

**🎯 trading_app/app_trading_hub.py is THE ONLY WAY.**
