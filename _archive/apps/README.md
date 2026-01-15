# Archived Trading Apps

These apps were archived on 2026-01-15 after consolidating all features into the ultimate production app.

## Archived Apps

### app_trading_hub_ai_version.py
**Original Location:** Root directory
**Description:** Original AI chat version with basic trading features
**Reason for Archiving:** AI chat functionality now integrated into production app with enhanced strategy engine

### app_edge_research.py
**Original Location:** Root directory
**Description:** Research tool for edge analysis and backtest exploration
**Reason for Archiving:** Research features available in production app; kept for specialized backtesting analysis

### live_trading_dashboard.py
**Original Location:** trading_app/
**Description:** Early prototype of live trading dashboard
**Reason for Archiving:** Superseded by main production app with full strategy engine

### trading_dashboard_pro.py
**Original Location:** trading_app/
**Description:** Prototype with enhanced features
**Reason for Archiving:** All features now in production app

### orb_dashboard_simple.py
**Original Location:** trading_app/
**Description:** Simple ORB visualization tool
**Reason for Archiving:** ORB features integrated into main app with better UI

## Production App

**Use only:** `trading_app/app_trading_hub.py`

This app has everything:
- ✅ Full StrategyEngine (5 strategies: CASCADE, NIGHT_ORB, SINGLE_LIQUIDITY, DAY_ORB, UNIFIED)
- ✅ AI Chat Assistant with Claude Sonnet 4.5
- ✅ Persistent memory system (DuckDB)
- ✅ Real-time decision support
- ✅ Position calculator
- ✅ Trade journal
- ✅ Live data integration
- ✅ Session levels tracking

## How to Launch Production App

```bash
cd trading_app
streamlit run app_trading_hub.py
```

## Recovery Instructions

If you need to restore an archived app temporarily:

```bash
# Copy (don't move) from archive
cp _archive/apps/app_edge_research.py .

# Use it
streamlit run app_edge_research.py

# Remove when done
rm app_edge_research.py
```

**Note:** Do not permanently restore these apps. The production app is the canonical version.

---

**Archive Date:** January 15, 2026
**By:** AI Integration Project
**Status:** Complete - Production app fully functional with all features
