# Project Structure

**MGC (Micro Gold) Trading System - Clean Production Layout**

This document describes the current production-ready file structure after comprehensive cleanup (Jan 2026).

---

## Root Directory - Core Files Only (28 Python files, 11 Markdown docs)

### Data Pipeline (Core Production)

**Backfill Scripts:**
- `backfill_databento_continuous.py` - Primary backfill for MGC data from Databento
- `backfill_databento_continuous_mpl.py` - Backfill for MPL/NQ data
- `backfill_range.py` - Alternative backfill using ProjectX API

**Feature Building:**
- `build_daily_features_v2.py` - **V2 ZERO-LOOKAHEAD** feature builder (PRODUCTION)
- `build_daily_features.py` - V1 legacy feature builder (kept for comparison)
- `build_5m.py` - 5-minute bar aggregation from 1-minute data

**Database Management:**
- `init_db.py` - Initialize database schema
- `check_db.py` - Inspect database contents
- `wipe_mgc.py` - Wipe all MGC data
- `wipe_mpl.py` - Wipe all MPL/NQ data

### Query & Analysis (Production)

**Query Interface:**
- `query_engine.py` - Main query engine (used by dashboards)
- `query_features.py` - Feature query tool
- `analyze_orb_v2.py` - **V2 ZERO-LOOKAHEAD** ORB analyzer (PRODUCTION)

**Data Tools:**
- `export_csv.py` - Export data to CSV
- `export_v2_edges.py` - Export V2 validated edges
- `validate_data.py` - Data validation utilities
- `inspect_dbn.py` - Inspect DBN files
- `check_dbn_symbols.py` - Check symbols in DBN files

### Applications (User-Facing)

**Production App:**
- `trading_app/app_trading_hub.py` - **ULTIMATE TRADING APP** with:
  - Real-time strategy engine (5 strategies)
  - AI chat assistant (Claude Sonnet 4.5)
  - Persistent memory system
  - Live data & position calculator
  - Trade journal
  - 5 tabs: LIVE, LEVELS, TRADE PLAN, JOURNAL, AI CHAT

**Archived Apps:** (moved to `_archive/apps/`)
- `app_trading_hub_ai_version.py` - Original AI version (root)
- `app_edge_research.py` - Research tool
- `live_trading_dashboard.py` - Prototype
- `trading_dashboard_pro.py` - Prototype
- `orb_dashboard_simple.py` - Simple tool

**Daily Workflow:**
- `daily_update.py` - Morning routine: backfill + features + alerts
- `daily_alerts.py` - Generate high-probability setup alerts

**Interactive Tools:**
- `ai_query.py` - AI-powered natural language query interface
- `journal.py` - Trading journal (log trades, stats, compare to historical)
- `realtime_signals.py` - Live signal generation

### Strategy Library (Production)

**Validated Strategies:**
- `validated_strategies.py` - V2 zero-lookahead validated strategy definitions

**Note:** Legacy backtest execution models (1m/5m/5mhalfsl) archived on Jan 15, 2026. Strategy logic preserved in validated_strategies.py and build_daily_features_v2.py.

---

## Documentation (11 Essential Files)

**Primary Docs:**
- `README.md` - Main project overview and tool reference
- `CLAUDE.md` - Instructions for Claude AI (canonical commands)
- `TRADING_PLAYBOOK.md` - V2 zero-lookahead trading strategies
- `ZERO_LOOKAHEAD_RULES.md` - Methodology and data integrity rules

**Technical Reference:**
- `DATABASE_SCHEMA.md` - Schema documentation
- `TERMINOLOGY_EXPLAINED.md` - Glossary of terms

**User Guides:**
- `QUICK_START.md` - Quick start guide
- `QUICK_START_GUIDE.md` - Alternate quick start
- `WORKFLOW_GUIDE.md` - Daily workflow guide
- `SETUP_TRADING_HUB.md` - Dashboard setup instructions
- `README_STREAMLIT.md` - Streamlit-specific documentation

---

## Folders

### Core Folders (Keep)

**exports/** - CSV exports from tools
- `daily_features_last_30d.csv`
- `orb_performance_summary.csv`
- `v2_edges_20260111_191502.csv`
- `v2_edges_summary_20260111_191502.md`

**logs/** - Recent log files only
- `backfill_*.log` (recent only)

**trading_app/** - Production trading application
- `app_trading_hub.py` - Main production app (with AI chat)
- `ai_memory.py` - AI memory management system
- `ai_assistant.py` - Claude AI assistant
- `config.py` - Configuration
- `data_loader.py` - Live data loading
- `strategy_engine.py` - Strategy engine
- `utils.py` - Utility functions
- `requirements.txt` - Python dependencies
- `trading_app.db` - DuckDB database (includes ai_chat_history)
- `trading_app.log` - Application logs

**configs/** - Configuration files (if any)

**scripts/** - Helper scripts (if needed)

**outputs/** - NQ/MGC analysis outputs

**NQ/** - NQ-specific data/analysis

### Archive Folder Structure

**_archive/** - All non-production files
```
_archive/
├── apps/                  # 5 archived dashboard apps (Jan 15, 2026)
├── tests/                  # 90+ test_*.py, verify_*.py, validate_*.py files
├── experiments/            # 50+ analyze_*.py, compare_*.py experimental scripts
├── scripts/                # 60+ one-off utility scripts
├── backtest_old/          # 13+ old backtest variants
├── bat_files/             # 7 archived .bat scripts
├── reports/               # 100+ outdated markdown reports
├── results/               # 70+ CSV result files
├── jobs/                  # Batch files and overnight job logs
├── legacy/                # Old/unused production code (execution_engine.py)
└── notes/                 # Text files and notes
```

**_INVALID_SCRIPTS_ARCHIVE/** - Previously archived invalid scripts

---

## Configuration Files

- `.env` - Environment variables (DATABENTO_API_KEY, etc.)
- `.gitignore` - Git ignore rules
- `requirements.txt` - Python dependencies

---

## Key Changes from Previous Structure

**January 15, 2026 Audit Cleanup:**
- Archived 3 deprecated backtest files → `_archive/backtest_old/`
- Archived execution_engine.py → `_archive/legacy/` (logic duplicated in V2)
- Archived _unused_migrate_orbs.sql → `_archive/scripts/`
- Result: 28 Python files in root (down from 32)
- All imports verified, no breaking changes

**Removed from Root (200+ files → 28 files):**
- 90+ test files → `_archive/tests/`
- 50+ analysis experiments → `_archive/experiments/`
- 60+ one-off scripts → `_archive/scripts/`
- 100+ outdated reports → `_archive/reports/`
- 70+ CSV files → `_archive/results/`
- 300+ tmpclaude-* temp directories → DELETED
- Batch files and logs → `_archive/jobs/`
- Text notes → `_archive/notes/`

**Focus on Production:**
- Core data pipeline (backfill, features, database)
- Production query and analysis tools (V2 zero-lookahead)
- User-facing applications (dashboards, AI query, journal)
- Current backtest execution models
- Essential documentation only

**Result:**
- Clean, navigable root directory
- Clear separation of production vs. experimental code
- Nothing lost - everything archived systematically
- Easy to find core functionality

---

## Usage After Cleanup

### Core Daily Workflow

```bash
# 1. Morning update
python daily_update.py

# 2. Launch dashboard
streamlit run app_trading_hub.py

# 3. Ask questions
python ai_query.py "What was win rate for 1000 UP?"

# 4. Log trades
python journal.py add
```

### Data Management

```bash
# Backfill new data
python backfill_databento_continuous.py 2026-01-01 2026-01-10

# Rebuild features (V2 zero-lookahead)
python build_daily_features_v2.py 2026-01-10

# Check database
python check_db.py

# Export data
python export_csv.py
```

### Analysis & Research

```bash
# Analyze ORBs (V2 zero-lookahead)
python analyze_orb_v2.py

# Query features
python query_features.py

# Launch research dashboard
streamlit run app_edge_research.py
```

### Finding Archived Files

Need an old test or experiment? Check `_archive/`:

```bash
# Find old test
ls _archive/tests/test_*.py

# Find old analysis
ls _archive/experiments/analyze_*.py

# Find old reports
ls _archive/reports/*.md

# Find old results
ls _archive/results/*.csv
```

---

## Maintenance

**When Adding New Files:**
- Production scripts → root directory
- Test scripts → `_archive/tests/`
- Experiments → `_archive/experiments/`
- One-off utilities → `_archive/scripts/`
- Reports/findings → `_archive/reports/`

**When Documenting:**
- Core documentation → root `.md` files
- Session findings → `_archive/reports/`
- Implementation logs → `_archive/reports/`

**Keep Root Clean:**
- Only production-ready, validated code in root
- Archive experiments and tests immediately
- Delete temp files regularly
- Move old logs to archive

---

## Status

**Latest Update:** January 15, 2026 - Audit Cleanup Completed

**Files Reduced:**
- Python files: 200+ → 28 (86% reduction)
- Markdown files: 130+ → 11 (92% reduction)
- SQL files: 4 → 3 (1 archived)
- CSV files: 80+ → ~5 in root (94% reduction)
- Temp directories: 300+ → 0 (100% removed)

**Total Archived:** 400+ files moved to systematic archive structure
**Total Deleted:** 300+ temporary directories

**Recent Updates (Jan 15, 2026):**

**Morning Cleanup:**
- 508 temp files deleted (492 tmpclaude-*, 4 .backup, 7 status files, 7 .bat archived)
- 5 files archived (3 deprecated backtests, 1 orphaned engine, 1 unused SQL)
- Files reduced: 581 → 73 in root (87% reduction)

**Afternoon AI Integration:**
- Added AI chat assistant with Claude Sonnet 4.5
- Created persistent memory system (DuckDB)
- Archived 5 redundant dashboard apps
- Production app now has 5 tabs: LIVE, LEVELS, TRADE PLAN, JOURNAL, AI CHAT
- New files: `trading_app/ai_memory.py`, `trading_app/ai_assistant.py`
- Updated: `trading_app/app_trading_hub.py` (+152 lines)

**All imports verified and working**
**No breaking changes**
**Git history preserved for rollback if needed**

**System Status:** Production-ready, clean, maintainable, AI-powered
