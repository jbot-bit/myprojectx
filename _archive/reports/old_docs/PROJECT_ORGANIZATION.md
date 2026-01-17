# Project Organization & File Structure

## Database Files (Correct Locations)

### Root Directory
```
gold.db           (688 MB) - Main historical data (bars_1m, bars_5m, daily_features, validated_setups)
trades.db         (12 KB)  - Trade journal (used by ai_query.py, journal.py)
```

### trading_app/ Directory
```
live_data.db      (12 KB)  - Live market data from ProjectX API
trading_app.db    (268 KB) - AI assistant memory and conversation history
```

## Project Structure

### Root Directory (Production Code)
```
myprojectx/
├── gold.db                           # Main data
├── trades.db                         # Trade journal
├── audit_complete_accuracy.py        # NEW: Complete data audit
├── RUN_AUDIT.bat                     # NEW: Easy audit launcher
├── CLEAN_PROJECT.bat                 # NEW: Cleanup utility
├── backfill_databento_continuous.py  # Backfill from Databento
├── backfill_range.py                 # Backfill from ProjectX
├── build_daily_features.py           # Build ORB/session features
├── check_db.py                       # Database inspection
├── init_db.py                        # Database schema setup
├── query_features.py                 # Query daily features
├── validate_data.py                  # Data validation
├── validated_strategies.py           # Strategy definitions
├── test_app_sync.py                  # Config sync verification
├── verify_app_integration.py         # Component integration test
├── populate_validated_setups.py      # Populate database setups
└── ... (other production scripts)
```

### trading_app/ Directory (Streamlit Apps)
```
trading_app/
├── live_data.db                 # Live market data
├── trading_app.db               # AI memory
├── app_trading_hub.py           # Main trading app
├── config.py                    # Configuration
├── data_loader.py               # Data fetching
├── strategy_engine.py           # Strategy logic
├── setup_detector.py            # Setup detection
├── market_intelligence.py       # Market analysis
├── professional_ui.py           # UI components
├── live_chart_builder.py        # NEW: Trading charts
├── enhanced_charting.py         # Chart overlays
├── ai_assistant.py              # AI assistant
├── ai_memory.py                 # AI memory
├── alert_system.py              # Alerts
├── risk_manager.py              # Risk management
├── position_tracker.py          # Position tracking
├── setup_scanner.py             # Setup scanning
└── ... (other app modules)
```

### _archive/ Directory (Old/Experimental)
```
_archive/
├── bat_files/           # Old batch scripts
├── experiments/         # Experimental code
├── reports/             # Old reports and docs
└── ... (archived files)
```

### dbn/ Directory (Raw Data)
```
dbn/
└── *.dbn files         # Raw Databento market data
```

## Temporary Files (DELETED)

The following are automatically cleaned by `CLEAN_PROJECT.bat`:

### Python Cache
- `__pycache__/` directories (all levels)
- `*.pyc` files (compiled Python)

### SQLite Temporary
- `*.db-shm` (shared memory)
- `*.db-wal` (write-ahead log)

### Test Cache
- `.pytest_cache/` directories
- `.mypy_cache/` directories
- `.coverage` files

### General Temporary
- `*.tmp` files
- `*.log` files (generic)
- `*.bak` backup files
- `*~` editor backup files

## File Organization Rules

### ✅ Keep in Root
- Main production scripts
- Database files (gold.db, trades.db)
- Documentation (*.md files)
- Configuration (.env, *.bat)

### ✅ Keep in trading_app/
- Streamlit app modules
- App-specific databases (live_data.db, trading_app.db)
- UI components
- App configuration

### ✅ Keep in _archive/
- Old/experimental code
- Archived reports
- Deprecated scripts

### ❌ Delete (Temporary)
- Python cache files
- SQLite temp files
- Test cache
- Generic logs
- Backup files

## Maintenance Commands

### Clean Project
```cmd
CLEAN_PROJECT.bat
```
Removes all temporary files while keeping important data.

### Audit Data
```cmd
RUN_AUDIT.bat
```
Verifies all calculations and data integrity.

### Verify Sync
```cmd
python test_app_sync.py
```
Checks config.py matches validated_setups database.

### Verify Integration
```cmd
python verify_app_integration.py
```
Tests all app components work together.

## Database Migration Rules

### Never Store in Root
- live_data.db → Must be in trading_app/
- trading_app.db → Must be in trading_app/

### Always in Root
- gold.db → Main historical data
- trades.db → Trade journal

### Why This Matters
Misplaced database files cause:
- File locking issues
- Import errors
- Path confusion
- Duplicate data

## Backup Strategy

### Critical Files (Backup Daily)
```
gold.db           # Main data
trades.db         # Trade journal
.env              # API keys
validated_strategies.py  # Strategy definitions
```

### Important Files (Backup Weekly)
```
trading_app/*.py  # App code
*.md              # Documentation
```

### No Backup Needed
```
__pycache__/      # Regenerated
*.pyc             # Regenerated
*.db-shm          # Temporary
*.db-wal          # Temporary
```

## Disk Space Management

### Large Files (Monitor)
- `gold.db` (688 MB) - Grows with backfill
- `dbn/*.dbn` - Raw market data files

### Cleanup Opportunities
- Old `dbn/*.dbn` files (if backfill complete)
- `_archive/` files (review and delete if not needed)
- Test output files in root (if any)

### Space Recommendations
- Keep 10+ GB free for database growth
- Archive old DBN files after backfill
- Periodically review _archive/ folder

## File Naming Conventions

### Python Scripts
- `snake_case.py` for all Python files
- Descriptive names (e.g., `audit_complete_accuracy.py`)
- No spaces or special characters

### Batch Files
- `UPPERCASE_WITH_UNDERSCORES.bat`
- Clear purpose (e.g., `RUN_AUDIT.bat`, `CLEAN_PROJECT.bat`)

### Documentation
- `UPPERCASE.md` for important docs
- `lowercase.md` for supporting docs
- Clear, descriptive names

### Databases
- `lowercase.db` for all database files
- Descriptive names (e.g., `gold.db`, `trades.db`, `live_data.db`)

## Current Status (After Cleanup)

✅ **CLEAN PROJECT STRUCTURE**

### Root Directory
- ✅ 2 database files (gold.db, trades.db)
- ✅ 29 production Python scripts
- ✅ 11+ markdown documentation files
- ✅ 3 batch utility files
- ✅ No duplicate database files
- ✅ No Python cache files
- ✅ No temporary files

### trading_app/ Directory
- ✅ 2 database files (live_data.db, trading_app.db)
- ✅ All app modules organized
- ✅ No cache files
- ✅ Clean structure

### _archive/ Directory
- ✅ All old files archived
- ✅ Organized by type (bat_files/, experiments/, reports/)

## Regular Maintenance

### Daily
- Run app and verify data loads
- Check for error logs

### Weekly
- Run `CLEAN_PROJECT.bat`
- Run `RUN_AUDIT.bat`
- Run `test_app_sync.py`
- Backup gold.db and trades.db

### Monthly
- Review _archive/ folder
- Archive old DBN files
- Check disk space
- Update documentation

## Troubleshooting

### "Cannot open database" Error
**Cause:** Duplicate database files or wrong locations
**Fix:** Run `CLEAN_PROJECT.bat` then check file locations

### "File is already open" Error
**Cause:** Multiple processes accessing same database
**Fix:** Kill all Python/Streamlit processes, delete *.db-shm and *.db-wal files

### Import Errors
**Cause:** Misplaced files or wrong paths
**Fix:** Verify file locations match this structure

### Disk Space Issues
**Cause:** Too many temporary files or old backups
**Fix:** Run `CLEAN_PROJECT.bat`, review _archive/ folder

---

**Last Updated:** 2026-01-16
**Project:** Gold (MGC) Trading System
**Status:** Clean and Organized ✅
