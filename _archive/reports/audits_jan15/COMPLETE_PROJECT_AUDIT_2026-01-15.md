# COMPLETE PROJECT AUDIT - January 15, 2026

**Status:** READ-ONLY AUDIT (No files deleted or moved)
**Scope:** Root directory Python files (32 files analyzed)
**Archive Status:** _archive/ folder already contains 400+ archived files (not re-audited)

---

## PHASE 1: SOURCE OF TRUTH

### Database Schema (gold.db)

**Active Tables:**
- `bars_1m` - 1-minute OHLCV data (primary raw data)
- `bars_5m` - 5-minute aggregated bars (derived from bars_1m)
- `daily_features` - V1 legacy daily features (SESSION types, lookahead bias)
- `daily_features_v2` - V2 zero-lookahead features (PRE blocks, honest execution)
- `daily_features_v2_nq` - V2 features for NQ instrument
- `daily_features_v2_mpl` - V2 features for MPL instrument
- `bars_1m_mpl` - MPL 1-minute bars
- `bars_5m_mpl` - MPL 5-minute bars
- `orb_trades_1m_exec` - Backtest execution results (1-minute)
- `orb_exec_results` - General execution results table

**Schema Files:**
- `schema.sql` - Main schema (ACTIVE)
- `migrate_schema_v2.sql` - V2 migration script (HISTORICAL REFERENCE)
- `verify_schema_v2.sql` - V2 verification queries (UTILITY)
- `_unused_migrate_orbs.sql` - Unused migration (ORPHANED)

### Entry Points (Scripts Run Directly)

**Daily Workflow:**
1. `daily_update.py` - Morning routine (backfill + features + alerts)
2. `daily_alerts.py` - Generate high-probability setup alerts
3. `app_trading_hub.py` - Main Streamlit dashboard
4. `app_edge_research.py` - Edge research Streamlit dashboard

**Data Pipeline:**
5. `backfill_databento_continuous.py` - Primary MGC backfill
6. `backfill_databento_continuous_mpl.py` - MPL backfill
7. `backfill_range.py` - Alternative backfill (ProjectX API)
8. `build_daily_features_v2.py` - V2 zero-lookahead feature builder (PRODUCTION)
9. `build_daily_features.py` - V1 legacy feature builder (COMPARISON)
10. `build_5m.py` - Aggregate 5-minute bars

**Analysis & Export:**
11. `analyze_orb_v2.py` - V2 zero-lookahead ORB analyzer
12. `export_csv.py` - Export data to CSV
13. `export_v2_edges.py` - Export V2 validated edges
14. `query_features.py` - Feature query tool
15. `ai_query.py` - AI-powered natural language query
16. `journal.py` - Trading journal
17. `realtime_signals.py` - Real-time trading signals

**Database Maintenance:**
18. `init_db.py` - Initialize database schema
19. `check_db.py` - Inspect database contents
20. `wipe_mgc.py` - Wipe MGC data
21. `wipe_mpl.py` - Wipe MPL data
22. `validate_data.py` - Data validation system
23. `run_complete_audit.py` - Automated audit script

**Utilities:**
24. `inspect_dbn.py` - Inspect DBN files
25. `check_dbn_symbols.py` - Check symbols in DBN files
26. `start_ngrok.py` - Start ngrok tunnel for remote access

### Library/Module Files (Imported by Others)

**Core Libraries:**
- `query_engine.py` - Query interface (imported by both dashboards)
- `execution_engine.py` - Canonical execution engine (NOT CURRENTLY USED - see findings)
- `validated_strategies.py` - Strategy definitions (imported by app_trading_hub.py)

### DEPRECATED Files (Have Exit Guards)

These files have `sys.exit("DEPRECATED...")` at the top:
- `backtest_orb_exec_1m.py` - DEPRECATED (use build_daily_features_v2.py)
- `backtest_orb_exec_5m.py` - DEPRECATED (use build_daily_features_v2.py)
- `backtest_orb_exec_5mhalfsl.py` - DEPRECATED (use build_daily_features_v2.py)

**Reason:** These were redundant execution engines before V2 refactor. Execution logic now lives in `build_daily_features_v2.py` directly.

---

## PHASE 2: FILE CLASSIFICATION

| File | Category | Status | Referenced By | Safe to Delete |
|------|----------|--------|---------------|----------------|
| `ai_query.py` | ACTIVE | Entry point | None (standalone) | NO |
| `analyze_orb_v2.py` | ACTIVE | Library + Entry | app_trading_hub.py | NO |
| `app_edge_research.py` | ACTIVE | Entry point | None (Streamlit app) | NO |
| `app_trading_hub.py` | ACTIVE | Entry point | None (Streamlit app) | NO |
| `backfill_databento_continuous.py` | ACTIVE | Entry point | daily_update.py | NO |
| `backfill_databento_continuous_mpl.py` | ACTIVE | Entry point | None (standalone) | NO |
| `backfill_range.py` | ACTIVE | Entry point | None (standalone) | NO |
| `backtest_orb_exec_1m.py` | DEPRECATED | Exit guard | None | YES - ARCHIVE |
| `backtest_orb_exec_5m.py` | DEPRECATED | Exit guard | None | YES - ARCHIVE |
| `backtest_orb_exec_5mhalfsl.py` | DEPRECATED | Exit guard | None | YES - ARCHIVE |
| `build_5m.py` | ACTIVE | Entry point | backfill scripts | NO |
| `build_daily_features.py` | ACTIVE | Entry point | backfill scripts (legacy) | NO (keep for comparison) |
| `build_daily_features_v2.py` | ACTIVE | Entry point (PRIMARY) | daily_update.py | NO |
| `check_db.py` | ACTIVE | Utility | None (standalone) | NO |
| `check_dbn_symbols.py` | ACTIVE | Utility | None (standalone) | NO |
| `daily_alerts.py` | ACTIVE | Entry point | daily_update.py | NO |
| `daily_update.py` | ACTIVE | Entry point (PRIMARY) | None (user-run) | NO |
| `execution_engine.py` | ORPHANED | Library | _archive files only | YES - REVIEW |
| `export_csv.py` | ACTIVE | Entry point | None (standalone) | NO |
| `export_v2_edges.py` | ACTIVE | Entry point | None (standalone) | NO |
| `init_db.py` | ACTIVE | Entry point | None (setup) | NO |
| `inspect_dbn.py` | ACTIVE | Utility | None (standalone) | NO |
| `journal.py` | ACTIVE | Entry point | None (standalone) | NO |
| `query_engine.py` | ACTIVE | Library (CORE) | 2 apps | NO |
| `query_features.py` | ACTIVE | Entry point | None (standalone) | NO |
| `realtime_signals.py` | ACTIVE | Entry point | None (standalone) | NO |
| `run_complete_audit.py` | ACTIVE | Entry point | None (standalone) | NO |
| `start_ngrok.py` | ACTIVE | Utility | None (standalone) | NO |
| `validate_data.py` | ACTIVE | Entry point | None (standalone) | NO |
| `validated_strategies.py` | ACTIVE | Library | app_trading_hub.py | NO |
| `wipe_mgc.py` | ACTIVE | Utility | None (dangerous, keep) | NO |
| `wipe_mpl.py` | ACTIVE | Utility | None (dangerous, keep) | NO |

### Scripts Folder (11 files)

All scripts are **ACTIVE** and support NQ/MPL research:

| File | Purpose | Status |
|------|---------|--------|
| `scripts/audit_nq_data_integrity.py` | NQ data validation | ACTIVE |
| `scripts/backtest_baseline.py` | Baseline backtest (MGC/NQ) | ACTIVE |
| `scripts/build_daily_features_mpl.py` | MPL feature builder | ACTIVE |
| `scripts/build_daily_features_nq.py` | NQ feature builder | ACTIVE |
| `scripts/ingest_databento_dbn_mpl.py` | MPL DBN ingestion | ACTIVE |
| `scripts/ingest_databento_dbn_nq.py` | NQ DBN ingestion | ACTIVE |
| `scripts/optimize_rr.py` | RR optimization | ACTIVE |
| `scripts/research_1800_any_edges.py` | 1800 ORB research | ACTIVE |
| `scripts/research_nq_massive_moves.py` | NQ massive move research | ACTIVE |
| `scripts/research_nq_session_dependencies.py` | NQ session analysis | ACTIVE |
| `scripts/test_filters.py` | Filter testing | ACTIVE |

---

## PHASE 3: DUPLICATE DETECTION

### V1 vs V2 Pattern

**Legitimate V1/V2 Pairs (KEEP BOTH):**
- `build_daily_features.py` (V1 - legacy with lookahead bias)
- `build_daily_features_v2.py` (V2 - zero lookahead, PRODUCTION)
- **Reason:** V1 kept for comparison, V2 is production

**Legitimate V1/V2 Pairs (KEEP BOTH):**
- `analyze_orb_v2.py` (V2 analysis)
- **No V1 equivalent found** - V1 logic was archived

### Backfill Duplicates (NOT DUPLICATES - DIFFERENT DATA SOURCES)

- `backfill_databento_continuous.py` - MGC via Databento
- `backfill_databento_continuous_mpl.py` - MPL via Databento
- `backfill_range.py` - MGC via ProjectX API (alternative source)
- **Reason:** Each serves different purpose/data source

### Wipe Duplicates (NOT DUPLICATES - DIFFERENT INSTRUMENTS)

- `wipe_mgc.py` - Wipe MGC data
- `wipe_mpl.py` - Wipe MPL data
- **Reason:** Different instruments, intentional separation

### True Duplicates - DEPRECATED BACKTEST FILES

These 3 files are **redundant execution engines** that duplicate logic in `build_daily_features_v2.py`:
1. `backtest_orb_exec_1m.py` - Has exit guard
2. `backtest_orb_exec_5m.py` - Has exit guard
3. `backtest_orb_exec_5mhalfsl.py` - Has exit guard

**Status:** Already have `sys.exit("DEPRECATED...")` guards preventing execution

---

## PHASE 4: CLEANUP PLAN

### Files to ARCHIVE (Move to _archive/)

**Category: Deprecated Execution Engines (3 files)**
- `backtest_orb_exec_1m.py`
- `backtest_orb_exec_5m.py`
- `backtest_orb_exec_5mhalfsl.py`

**Reason:** These were standalone execution engines before V2 refactor. Execution logic now lives in `build_daily_features_v2.py` directly. They have exit guards preventing use.

**Destination:** `_archive/backtest_old/` (folder already exists with similar files)

### Files to REVIEW (Potential Orphans)

**Category: Unused Library (1 file)**
- `execution_engine.py`

**Status:** This is a well-documented canonical execution engine, but:
- NOT imported by any active root file
- Only imported by `_archive/backtest_old/example_backtest_using_engine.py`
- Execution logic duplicated in `build_daily_features_v2.py`

**Question for Human:**
> Was `execution_engine.py` intended to be used going forward? Or was it superseded by the direct implementation in `build_daily_features_v2.py`?
>
> Options:
> 1. ARCHIVE it (logic is duplicated in build_daily_features_v2.py)
> 2. REFACTOR build_daily_features_v2.py to use it (DRY principle)
> 3. KEEP it as reference/library for future backtest variations

### SQL Files to ARCHIVE (1 file)

- `_unused_migrate_orbs.sql` - Unused migration script

**Destination:** `_archive/scripts/`

### Files to KEEP (29 files)

**All other root Python files are ACTIVE and form the production system.**

---

## PHASE 5: SAFETY CHECK

### Import Dependency Analysis

**Core Libraries (must not break):**
- `query_engine.py` → imported by 2 apps ✅
- `validated_strategies.py` → imported by 1 app ✅
- `analyze_orb_v2.py` → imported by 1 app ✅
- `execution_engine.py` → NOT imported by any active file ⚠️

**Entry Points (no imports from root):**
- All 26 entry point scripts are standalone ✅

**Deprecated Files (have exit guards):**
- 3 backtest files prevent execution at runtime ✅

### Database Table Usage

**Active Writers (files that INSERT/UPDATE/DELETE):**
- `backfill_databento_continuous.py` → bars_1m, bars_5m ✅
- `backfill_databento_continuous_mpl.py` → bars_1m_mpl, bars_5m_mpl ✅
- `backfill_range.py` → bars_1m, bars_5m ✅
- `build_daily_features_v2.py` → daily_features_v2 ✅
- `build_daily_features.py` → daily_features ✅
- `build_5m.py` → bars_5m ✅
- `journal.py` → trades (SQLite, separate DB) ✅
- `wipe_mgc.py` → DELETE from bars_1m, bars_5m, daily_features ✅
- `wipe_mpl.py` → DELETE from bars_1m_mpl, bars_5m_mpl, daily_features_v2_mpl ✅

**No orphaned writers detected** ✅

---

## CRITICAL FINDINGS

### Finding 1: Deprecated Backtest Files

**Issue:** 3 backtest execution files are deprecated but still in root directory.

**Files:**
- `backtest_orb_exec_1m.py`
- `backtest_orb_exec_5m.py`
- `backtest_orb_exec_5mhalfsl.py`

**Evidence:** Each has `sys.exit("DEPRECATED: This script is a redundant execution engine. Use build_daily_features_v2.py instead...")` at line 1.

**Impact:** Low (cannot execute due to guards)

**Recommendation:** Move to `_archive/backtest_old/`

---

### Finding 2: Orphaned Execution Engine

**Issue:** `execution_engine.py` is a well-documented canonical execution engine but is not imported by any active production code.

**Evidence:**
- Only import found: `_archive/backtest_old/example_backtest_using_engine.py`
- NOT imported by `build_daily_features_v2.py` (which implements execution directly)
- File header says "All backtest scripts MUST call this engine instead of reimplementing execution logic"

**Impact:** Medium (duplication of execution logic, DRY violation)

**Possible Causes:**
1. It was superseded by direct implementation in v2
2. It was intended to be used but wasn't integrated
3. It's kept as reference/template for future variations

**Recommendation:** Human decision needed (see Questions section)

---

### Finding 3: V1 vs V2 System Coexistence

**Issue:** Two parallel feature systems exist:
- V1: `build_daily_features.py` → `daily_features` table (has lookahead bias)
- V2: `build_daily_features_v2.py` → `daily_features_v2` table (zero lookahead)

**Status:** This is INTENTIONAL per project docs (V1 kept for comparison)

**Evidence:**
- CLAUDE.md mentions V2 zero-lookahead system
- PROJECT_STRUCTURE.md shows both as active
- Both tables exist in schema.sql

**Impact:** None (intentional)

**Recommendation:** Keep both, ensure documentation is clear about which to use

---

### Finding 4: Multi-Instrument Support

**Issue:** Project has expanded beyond MGC to include MPL and NQ with separate:
- Backfill scripts (3 instruments)
- Feature builders (3 instruments)
- Database tables (separate tables per instrument)

**Status:** This is ACTIVE DEVELOPMENT

**Evidence:**
- `scripts/` folder dedicated to NQ/MPL research
- Separate backfill/feature scripts
- Separate tables: daily_features_v2_nq, daily_features_v2_mpl

**Impact:** None (intentional expansion)

**Recommendation:** Consider future consolidation into instrument-parameterized functions

---

## QUESTIONS FOR HUMAN REVIEW

### Question 1: execution_engine.py Purpose

**Context:** `execution_engine.py` is not imported by any active production code, but appears to be a well-designed canonical execution engine.

**Options:**
1. **ARCHIVE** - Logic is duplicated in build_daily_features_v2.py, no longer needed
2. **REFACTOR** - Update build_daily_features_v2.py to import and use execution_engine.py (DRY)
3. **KEEP AS REFERENCE** - Document as template/library for future backtest variations

**Your Answer:** _______________

---

### Question 2: Deprecated Backtest Files

**Context:** 3 backtest files have exit guards preventing execution and are documented as deprecated.

**Action:** Move `backtest_orb_exec_{1m,5m,5mhalfsl}.py` to `_archive/backtest_old/`?

**Your Answer:** YES / NO / REVIEW

---

### Question 3: _unused_migrate_orbs.sql

**Context:** SQL file named `_unused_migrate_orbs.sql` exists in root.

**Action:** Move to `_archive/scripts/`?

**Your Answer:** YES / NO / REVIEW

---

### Question 4: Future Multi-Instrument Architecture

**Context:** Currently each instrument (MGC/MPL/NQ) has separate scripts and tables.

**Consider:** Consolidating into parameterized functions with instrument config files?

**Priority:** LOW / MEDIUM / HIGH / NOT_NOW

**Your Answer:** _______________

---

## SUMMARY STATISTICS

**Root Directory Python Files:** 32
- Active Entry Points: 23
- Active Libraries: 3
- Deprecated (with guards): 3
- Orphaned: 1 (execution_engine.py - needs review)
- Utilities: 6

**Scripts Folder:** 11 files (all ACTIVE for NQ/MPL research)

**Files to Archive:** 3-4 (depending on human decisions)

**Import Dependencies:** Clean (no breaking changes detected)

**Database Writers:** 9 active, all verified

**Overall Status:** 🟢 HEALTHY
- Core production system is clean and well-documented
- Deprecated files have safety guards
- Only 1 orphaned file requiring human decision
- _archive/ folder already contains 400+ historical files

---

## RECOMMENDED ACTIONS

**Immediate (Low Risk):**
1. ✅ Move 3 deprecated backtest files to `_archive/backtest_old/`
2. ✅ Move `_unused_migrate_orbs.sql` to `_archive/scripts/`

**Requires Human Decision:**
1. ⚠️ Decide fate of `execution_engine.py` (ARCHIVE / REFACTOR / KEEP)

**Documentation Updates:**
1. ✅ Update PROJECT_STRUCTURE.md after moves
2. ✅ Clarify V1 vs V2 system usage in CLAUDE.md

**Future Considerations:**
1. 🔵 Consider multi-instrument architecture consolidation
2. 🔵 Consider refactoring build_daily_features_v2.py to use execution_engine.py (DRY)

---

**Audit Completed:** 2026-01-15
**Auditor:** Claude Code (Sonnet 4.5)
**Methodology:** Static analysis, import tracing, schema verification, documentation review
