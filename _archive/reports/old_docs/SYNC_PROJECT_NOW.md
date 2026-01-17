# Project Root Synchronization - 2026-01-16

## Current State (OUT OF SYNC)

**Actual:**
- 39 Python files (target: 33)
- 49 Markdown files (target: 20)
- Various temp/status files

**Status:** ❌ NOT SYNCED - needs cleanup

---

## Files to Archive/Remove

### Python Files to Archive (6 files → move to _archive/):

1. **test_*.py** → `_archive/tests/`
   - `test_app_sync.py` - Keep in root (CRITICAL for validation)
   - `test_directional_app.py` → archive
   - `test_enhancements.py` → archive
   - `test_night_orbs_full_sl.py` - Keep in root (documented in PROJECT_STRUCTURE.md)
   - `test_safety_features.py` → archive

2. **Debug/Verification Scripts** → `_archive/scripts/`
   - `debug_app.py` → archive (was temporary debug tool)
   - `verify_app_integration.py` → archive

3. **Experimental/Prediction Scripts** → `_archive/experiments/`
   - `PREDICT_DIRECTION.py` → archive
   - `FIND_FREQUENT_HIGH_RR.py` → archive

4. **Execution Engine** (if still in root)
   - `execution_engine.py` - **KEEP IN ROOT** - This is CANONICAL with extended scan windows

### Markdown Files to Archive (29 files → move to _archive/reports/):

**Completion/Status Docs** (old completion reports):
- `AI_INTEGRATION_COMPLETE.md` → archive
- `APP_FIXED_AND_RUNNING.md` → archive
- `APP_ISSUES_FOUND.md` → archive
- `AUTOREFRESH_INTEGRATION.md` → archive
- `DIRECTIONAL_BIAS_INTEGRATION_COMPLETE.md` → archive
- `DISCOVERY_TOOL_COMPLETE.md` → archive
- `ENHANCEMENTS_COMPLETE.md` → archive
- `INTELLIGENT_COPILOT_COMPLETE.md` → archive
- `NEW_APP_DECISION_FOCUSED.md` → archive
- `PERSISTENT_MEMORY_COMPLETE.md` → archive
- `SAFETY_FEATURES_COMPLETE.md` → archive
- `SIMPLIFIED_APP_COMPLETE.md` → archive

**Feature Documentation** (superseded):
- `AI_CHAT_INTEGRATION_PLAN.md` → archive
- `ENHANCED_APP_INTEGRATION.md` → archive
- `TRADING_APP_ENHANCEMENT_PLAN.md` → archive

**Redesign Docs** (completed work):
- `APP_BEFORE_AFTER.md` → archive
- `APP_REDESIGN_PROPOSAL.md` → archive

**Audit Files** (old audits):
- `AUDIT_COVERAGE.md` → archive
- `AUDIT_GUIDE.md` → archive
- `AUDIT_REPORT_2026-01-15.md` → keep (recent)
- `AUDIT_SUMMARY_2026-01-15.md` → keep (recent)

**Deployment/Workflow** (duplicates):
- `CLEANUP_COMMANDS.md` → archive
- `DEPLOY_NOW_CHECKLIST.txt` → archive
- `QUICK_START_GUIDE.md` → archive (duplicate of QUICK_START.md)
- `WORKFLOW_GUIDE.md` → archive

**Test/Verification Reports**:
- `CRITICAL_MISSING_FEATURES.md` → archive
- `DEBUG_RESULTS.md` → archive
- `TEST_APP_SYNC_VERIFICATION.md` → archive

**Recent Bug Fix Docs** (keep):
- `BUG_FIX_SUMMARY.md` - Keep (just created today)
- `SCAN_WINDOW_BUG_FIX_SUMMARY.md` - Keep (critical doc)
- `UNICORN_SETUPS_CORRECTED.md` - Keep (current playbook)

### Data Files to Clean Up:

**JSON files** → move to data/ or archive:
- `available_contracts.json` → archive
- `contracts.json` → archive
- `condition.json` → archive
- `manifest.json` → archive
- `metadata.json` → archive
- `symbology.json` → archive
- `backfill_progress.json` → keep (active tracking)

**CSV files** → move to exports/ or archive:
- `ALL_ORBS_EXTENDED_WINDOWS.csv` → `exports/` (or archive)
- `DIRECTION_PREDICTION.csv` → `exports/` (or archive)
- `file_classification_audit.csv` → `_archive/results/`
- `FREQUENT_HIGH_RR.csv` → `exports/` (or archive)
- `MASSIVE_MOVERS.csv` → `exports/` (or archive)

**Text/Backup Files**:
- `audit.txt` → archive
- `audit_results.txt` → archive
- `audit_results_final.txt` → archive
- `notepad.txt.env` → DELETE (looks like accident)
- `nul` → DELETE (null file)
- `-Tail` → DELETE (temp file)
- `validated_strategies.py.backup` → `_archive/backup/`

**DBN files in root**:
- `glbx-mdp3-20250112-20260111.ohlcv-1m.dbn.zst` → move to `dbn/` folder

---

## Target State (SYNCED)

### Python Files in Root (33 files):

**Backfill Scripts (3):**
- backfill_databento_continuous.py
- backfill_databento_continuous_mpl.py
- backfill_range.py

**Feature Building (3):**
- build_daily_features_v2.py
- build_daily_features.py
- build_5m.py

**Database Management (4):**
- init_db.py
- check_db.py
- wipe_mgc.py
- wipe_mpl.py

**Query & Analysis (10):**
- query_engine.py
- query_features.py
- analyze_orb_v2.py
- export_csv.py
- export_v2_edges.py
- validate_data.py
- inspect_dbn.py
- check_dbn_symbols.py
- test_app_sync.py (CRITICAL)
- test_night_orbs_full_sl.py

**Applications (4):**
- daily_update.py
- daily_alerts.py
- ai_query.py
- journal.py
- realtime_signals.py

**Strategy Library (5):**
- validated_strategies.py
- execution_engine.py (CANONICAL)
- populate_validated_setups.py
- MGC_NOW.py
- run_complete_audit.py
- audit_complete_accuracy.py

**Scripts (1):**
- start_ngrok.py

### Markdown Files in Root (20 files):

**Primary Docs (5):**
- README.md
- CLAUDE.md
- TRADING_PLAYBOOK.md
- UNICORN_SETUPS_CORRECTED.md
- SCAN_WINDOW_BUG_FIX_SUMMARY.md

**Technical Reference (4):**
- DATABASE_SCHEMA.md
- DATABASE_SCHEMA_SOURCE_OF_TRUTH.md
- TERMINOLOGY_EXPLAINED.md
- PROJECT_STRUCTURE.md

**User Guides (6):**
- QUICK_START.md
- SETUP_TRADING_HUB.md
- README_STREAMLIT.md
- DEPLOY_TO_STREAMLIT_CLOUD.md
- REMOTE_ACCESS_GUIDE.md
- SOURCE_OF_TRUTH.md

**Audit & Reports (5):**
- AUDIT_INDEX.md
- AUDIT_REPORT_2026-01-15.md
- AUDIT_SUMMARY_2026-01-15.md
- COMPLETE_PROJECT_AUDIT_2026-01-15.md
- BUG_FIX_SUMMARY.md

**Other**:
- ZERO_LOOKAHEAD_RULES.md

---

## Cleanup Commands

### Archive Old Status/Completion Docs:
```bash
mkdir -p _archive/reports/completion_docs
mv AI_INTEGRATION_COMPLETE.md _archive/reports/completion_docs/
mv APP_FIXED_AND_RUNNING.md _archive/reports/completion_docs/
mv APP_ISSUES_FOUND.md _archive/reports/completion_docs/
mv AUTOREFRESH_INTEGRATION.md _archive/reports/completion_docs/
mv DIRECTIONAL_BIAS_INTEGRATION_COMPLETE.md _archive/reports/completion_docs/
mv DISCOVERY_TOOL_COMPLETE.md _archive/reports/completion_docs/
mv ENHANCEMENTS_COMPLETE.md _archive/reports/completion_docs/
mv INTELLIGENT_COPILOT_COMPLETE.md _archive/reports/completion_docs/
mv NEW_APP_DECISION_FOCUSED.md _archive/reports/completion_docs/
mv PERSISTENT_MEMORY_COMPLETE.md _archive/reports/completion_docs/
mv SAFETY_FEATURES_COMPLETE.md _archive/reports/completion_docs/
mv SIMPLIFIED_APP_COMPLETE.md _archive/reports/completion_docs/
```

### Archive Test Files:
```bash
mv test_directional_app.py _archive/tests/
mv test_enhancements.py _archive/tests/
mv test_safety_features.py _archive/tests/
mv debug_app.py _archive/scripts/
mv verify_app_integration.py _archive/scripts/
```

### Archive Experiments:
```bash
mv PREDICT_DIRECTION.py _archive/experiments/
mv FIND_FREQUENT_HIGH_RR.py _archive/experiments/
```

### Archive Old Docs:
```bash
mkdir -p _archive/reports/old_docs
mv AI_CHAT_INTEGRATION_PLAN.md _archive/reports/old_docs/
mv ENHANCED_APP_INTEGRATION.md _archive/reports/old_docs/
mv TRADING_APP_ENHANCEMENT_PLAN.md _archive/reports/old_docs/
mv APP_BEFORE_AFTER.md _archive/reports/old_docs/
mv APP_REDESIGN_PROPOSAL.md _archive/reports/old_docs/
mv AUDIT_COVERAGE.md _archive/reports/old_docs/
mv AUDIT_GUIDE.md _archive/reports/old_docs/
mv CLEANUP_COMMANDS.md _archive/reports/old_docs/
mv DEPLOY_NOW_CHECKLIST.txt _archive/reports/old_docs/
mv QUICK_START_GUIDE.md _archive/reports/old_docs/
mv WORKFLOW_GUIDE.md _archive/reports/old_docs/
mv CRITICAL_MISSING_FEATURES.md _archive/reports/old_docs/
mv DEBUG_RESULTS.md _archive/reports/old_docs/
mv TEST_APP_SYNC_VERIFICATION.md _archive/reports/old_docs/
```

### Move Data Files:
```bash
mkdir -p _archive/data
mv available_contracts.json _archive/data/
mv contracts.json _archive/data/
mv condition.json _archive/data/
mv manifest.json _archive/data/
mv metadata.json _archive/data/
mv symbology.json _archive/data/

mv ALL_ORBS_EXTENDED_WINDOWS.csv exports/
mv DIRECTION_PREDICTION.csv exports/
mv FREQUENT_HIGH_RR.csv exports/
mv MASSIVE_MOVERS.csv exports/
mv file_classification_audit.csv _archive/results/

mv audit.txt _archive/reports/
mv audit_results.txt _archive/reports/
mv audit_results_final.txt _archive/reports/

mv validated_strategies.py.backup _archive/backup/

mv glbx-mdp3-20250112-20260111.ohlcv-1m.dbn.zst dbn/
```

### Delete Junk Files:
```bash
rm -f notepad.txt.env nul "-Tail"
```

---

## After Cleanup, Verify:

```bash
# Count files
echo "Python files:" && ls -1 *.py 2>/dev/null | wc -l
echo "Markdown files:" && ls -1 *.md 2>/dev/null | wc -l

# Expected:
# Python files: 33
# Markdown files: 20
```

---

## Status

**Before:**
- ❌ 39 Python files (6 extra)
- ❌ 49 Markdown files (29 extra)
- ❌ Many temp files

**After (Target):**
- ✅ 33 Python files
- ✅ 20 Markdown files
- ✅ Clean root directory
- ✅ Everything archived systematically

---

**Created:** 2026-01-16
**Purpose:** Sync project root with PROJECT_STRUCTURE.md
**Status:** READY TO EXECUTE
