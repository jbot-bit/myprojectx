# POLICE.TXT STEP 1: DISCOVERY REPORT (READ-ONLY)

**Generated**: 2026-01-18
**Purpose**: Identify all database files, entry points, connection points, and duplications before implementing canonical enforcement system.

---

## 1. CURRENT ENTRYPOINTS

### Active Apps (Production)
- **`trading_app/app_mobile.py`** - Mobile-optimized Tinder-style card interface
  - Cloud-aware, MotherDuck enabled
  - Primary mobile entry point

- **`trading_app/app_trading_hub.py`** - Desktop tabs interface
  - Multi-tab dashboard with AI assistant
  - Primary desktop entry point

### Archived Apps (Not Production)
- `_archive/apps/app_trading_hub_ai_version.py` - Old AI version (superseded)
- `_archive/apps/live_trading_dashboard.py` - Legacy dashboard (superseded)

**FINDING**: 2 active entry points, 2 archived duplicates (correctly archived)

---

## 2. ALL DATABASE FILES FOUND

### Root Directory (Production)
```
gold.db              690 MB   (Main historical data - MGC/NQ/MPL)
live_data.db         3.1 MB   (Live bars cache)
trades.db            12 KB    (Trade journal)
trading_app.db       268 KB   (App state/config)
```

### trading_app/ Directory (DUPLICATES)
```
trading_app/live_data.db      1.6 MB   (DUPLICATE of root live_data.db)
trading_app/trading_app.db    524 KB   (DUPLICATE of root trading_app.db)
```

### scripts/ Directory (DUPLICATE)
```
scripts/gold.db              12 KB    (OLD/DUPLICATE - likely test artifact)
```

### backups/ Directory (Archived - OK)
```
backups/20260118_0106/
  - gold.db
  - live_data.db
  - trades.db
  - trading_app.db
```

**TOTAL**: 11 database files
- **4 canonical** (root directory)
- **3 duplicates** (trading_app/ and scripts/)
- **4 backups** (correctly archived in backups/)

**CRITICAL FINDING**: 3 shadow/duplicate database files exist outside canonical locations

---

## 3. SCHEMA AND RULES DOCUMENTATION

### Canonical Documents (Current)
- **`DATABASE_SCHEMA_SOURCE_OF_TRUTH.md`** - Database schema authority
- **`TRADING_PLAYBOOK.md`** - Trading rules and strategies authority
- **`ZERO_LOOKAHEAD_RULES.md`** - Temporal validation rules

### Archived Documents (Old Versions)
- `_archive/reports/old_docs/DATABASE_SCHEMA.md` - Archived old schema doc
- `_archive/reports/TRADING_RULESET_CANONICAL.md` - Archived old ruleset
- Multiple outdated playbook versions in `_archive/reports/`

**FINDING**: Clean separation - 3 canonical docs in root, old versions correctly archived

---

## 4. DATABASE CONNECTION POINTS

### Module 1: cloud_mode.py (ACTIVE - USED BY 7 FILES)
**Location**: `trading_app/cloud_mode.py`
**Status**: ✅ Currently in use
**Functions**:
- `get_motherduck_connection()` - MotherDuck cloud connection
- `get_database_connection()` - Auto-detect cloud vs local
- `get_database_path()` - Return appropriate path/connection string
- `is_cloud_deployment()` - Check if running in cloud

**Imported by**:
1. `trading_app/ai_assistant.py` - AI chat context loading
2. `trading_app/setup_detector.py` - Setup detection
3. `trading_app/directional_bias.py` - ML predictions
4. `trading_app/data_loader.py` - Live data fetching
5. `trading_app/app_mobile.py` - Mobile app
6. `trading_app/app_trading_hub.py` - Desktop app
7. `trading_app/strategy_discovery.py` - Strategy analysis

### Module 2: db_router.py (INACTIVE - USED BY 0 FILES)
**Location**: `trading_app/db_router.py`
**Status**: ⚠️ NOT imported by any files (DUPLICATE/DEAD CODE)
**Functions**:
- `get_connection(purpose='read')` - Connection routing
- `_get_cache_connection()` - Cache DB with self-healing
- `_initialize_cache_tables()` - Cache table schemas
- `health_check()` - Database health status

**Features**:
- 296 lines of sophisticated connection logic
- Persistent vs cache table routing
- Self-healing cache database
- Health check functionality
- ZERO imports found in codebase

**CRITICAL FINDING**: db_router.py duplicates functionality of cloud_mode.py but is completely unused

### Raw duckdb.connect() Calls
**Total files with direct duckdb.connect()**: 274 files
**Breakdown**:
- Root scripts: ~30 files (backfills, feature building, analysis)
- trading_app/: ~10 files (various modules)
- _archive/: ~230 files (experiments, old scripts, legacy code)

**Active files with hardcoded connections** (outside cloud_mode.py):
1. `config_generator.py` - ✅ Fixed (now cloud-aware)
2. `trading_app/data_loader.py` - ✅ Fixed (cloud-aware, skips writes)
3. `test_app_sync.py` - OK (test file, needs direct access)
4. `populate_validated_setups.py` - OK (admin script)
5. `build_daily_features*.py` - OK (data pipeline scripts)
6. Various backfill scripts - OK (data ingestion)

**FINDING**: Most hardcoded connections are in legitimate data pipeline scripts. Core app now routes through cloud_mode.py.

---

## 5. DUPLICATE APPS AND DASHBOARDS

### Active Apps (No Duplication)
- `trading_app/app_mobile.py` - Mobile interface
- `trading_app/app_trading_hub.py` - Desktop interface
- Clear separation of concerns, no overlap

### Archived Apps (Correctly Archived)
- `_archive/apps/app_trading_hub_ai_version.py` - Old version before AI integration
- `_archive/apps/live_trading_dashboard.py` - Legacy pre-refactor dashboard

**FINDING**: No active duplicate apps. Archived versions correctly separated.

---

## 6. CRITICAL ISSUES IDENTIFIED

### Issue 1: Duplicate Database Connection Module ⚠️
**Problem**: Two modules provide database connections:
- `cloud_mode.py` - 7 imports, actively used
- `db_router.py` - 0 imports, completely unused

**Risk**: Violates police.txt Rule #2 "Single source of truth for DB path"

**Recommendation**:
- Option A: Delete db_router.py (unused code)
- Option B: Merge db_router.py features into cloud_mode.py (if cache routing/health check needed)
- Option C: Deprecate cloud_mode.py, migrate all imports to db_router.py (major refactor)

### Issue 2: Shadow Database Files ⚠️
**Problem**: 3 duplicate database files outside canonical root directory:
- `trading_app/live_data.db` (1.6 MB)
- `trading_app/trading_app.db` (524 KB)
- `scripts/gold.db` (12 KB)

**Risk**: Violates police.txt "NO OLD DB" guard - multiple sources of truth

**Recommendation**:
1. Verify these are not actively used by any scripts
2. Delete or move to backups/
3. Add to .gitignore to prevent recreation
4. Implement `check_no_shadow_dbs.py` guard to prevent future occurrence

### Issue 3: Hardcoded Connection Strings
**Problem**: 274 files have direct `duckdb.connect()` calls

**Status**: MOSTLY OK - breakdown:
- ~230 files in `_archive/` (legacy, ignored)
- ~30 files are data pipeline scripts (legitimate use)
- ~10 files in trading_app/ (mix of legitimate and problematic)

**Risk**: Medium - Core app now routes through cloud_mode.py, but some edge cases remain

**Recommendation**:
1. Audit the ~10 trading_app/ files with duckdb.connect()
2. Create test: `test_no_hardcoded_db_paths.py` to grep/AST scan
3. Allow exceptions for data pipeline scripts (backfill, feature building)

---

## 7. PROPOSED CANONICAL STRUCTURE

Based on discovery, recommend this canonical structure:

### CANONICAL.json (to be created)
```json
{
  "canon_db_path": "gold.db",
  "canon_cache_db_path": "live_data.db",
  "canon_schema_doc": "DATABASE_SCHEMA_SOURCE_OF_TRUTH.md",
  "canon_ruleset_doc": "TRADING_PLAYBOOK.md",
  "canon_zero_lookahead_doc": "ZERO_LOOKAHEAD_RULES.md",
  "canon_app_mobile": "trading_app/app_mobile.py",
  "canon_app_desktop": "trading_app/app_trading_hub.py",
  "canon_connection_module": "trading_app/cloud_mode.py",
  "allowed_tables": [
    "bars_1m",
    "bars_5m",
    "daily_features_v2",
    "validated_setups",
    "live_bars",
    "live_journal",
    "ml_predictions",
    "ml_performance"
  ],
  "allowed_db_locations": [
    "gold.db",
    "live_data.db",
    "trades.db",
    "trading_app.db"
  ],
  "ignore_patterns": [
    "_archive/**",
    "backups/**",
    "*.db.wal",
    "*.db-shm"
  ]
}
```

### trading_app/canonical.py (to be created)
Functions to implement:
- `get_canon_db_path()` - Return canonical database path
- `get_canon_docs()` - Return dict of canonical doc paths
- `assert_canonical_environment()` - Runtime validation
- `get_canon_app_entry(platform='mobile'|'desktop')` - Return entry point

---

## 8. NEXT STEPS (READY FOR IMPLEMENTATION)

Per police.txt workflow, **STOP HERE** for user approval before proceeding to Step 2.

**If approved, implement in this order:**

### Step 2: Create CANONICAL.json + canonical.py
- Create CANONICAL.json with paths above
- Create trading_app/canonical.py with enforcement functions
- Update db connection points to use canonical.py

### Step 3: Create tools/build_working_set.py
- AST-based dependency discovery
- Runtime file dependency scanning (duckdb.connect, open, Path, pandas reads)
- Copy to _WORKING_SET/ with inventory
- Fail on missing dependencies

### Step 4: Create guards + tests
- `tools/check_no_shadow_dbs.py` - Fail if >4 *.db files in root/trading_app
- `tests/test_canonical_env.py` - Test canonical file loads, DB connects
- `tests/test_no_hardcoded_db_paths.py` - AST scan for rogue duckdb.connect()

### Step 5: CI/CD integration
- Add pre-commit hooks (if .pre-commit-config.yaml exists)
- Add GitHub Actions workflow
- Run guards on every commit

---

## 9. SUMMARY

**Database Files**: 11 total (4 canonical, 3 duplicates, 4 backups)
**Entry Points**: 2 active apps (mobile + desktop)
**Connection Modules**: 2 modules (cloud_mode.py used, db_router.py unused)
**Schema Docs**: 3 canonical docs (clean separation from archives)
**Shadow DBs**: 3 duplicate database files (requires cleanup)

**Risk Level**: 🟡 MEDIUM
- No duplicate apps ✅
- Clean canonical docs ✅
- Shadow databases exist ⚠️
- Duplicate connection module exists ⚠️
- Most hardcoded connections OK (data pipeline) ✅

**Ready for Step 2**: ✅ YES (pending user approval)

---

**Report Complete**. Awaiting user confirmation to proceed with implementation phases.
