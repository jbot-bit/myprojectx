# CLEANUP COMMANDS - Ready to Execute

**Date:** January 15, 2026
**Based On:** Complete Project Audit

---

## ⚠️ IMPORTANT: DO NOT RUN THESE COMMANDS YET

**Review the audit reports first:**
1. `COMPLETE_PROJECT_AUDIT_2026-01-15.md` (detailed analysis)
2. `AUDIT_SUMMARY_2026-01-15.md` (executive summary)
3. `file_classification_audit.csv` (spreadsheet view)

**Then answer the decision questions below before proceeding.**

---

## 🎯 DECISION QUESTIONS

### Question 1: execution_engine.py

**Context:** This file is a well-documented canonical execution engine but is NOT imported by any active production code. Execution logic is duplicated in `build_daily_features_v2.py`.

**Choose one:**
- [ ] **A. ARCHIVE** - Move to `_archive/legacy/` (recommended)
- [ ] **B. REFACTOR** - Update build_daily_features_v2.py to use it
- [ ] **C. KEEP** - Leave in root as reference/template

**Your choice:** _____________

---

### Question 2: Deprecated Backtest Files

**Context:** 3 files have `sys.exit("DEPRECATED...")` guards and cannot execute.

**Files:**
- `backtest_orb_exec_1m.py`
- `backtest_orb_exec_5m.py`
- `backtest_orb_exec_5mhalfsl.py`

**Action:** Move to `_archive/backtest_old/`?

- [ ] **YES** - Archive them (recommended)
- [ ] **NO** - Keep in root
- [ ] **REVIEW** - Need more information

**Your choice:** _____________

---

### Question 3: Unused SQL Migration

**Context:** `_unused_migrate_orbs.sql` is in root but unused.

**Action:** Move to `_archive/scripts/`?

- [ ] **YES** - Archive it (recommended)
- [ ] **NO** - Keep in root

**Your choice:** _____________

---

## 📋 CLEANUP COMMANDS

### STEP 1: Create Backup (RECOMMENDED)

```bash
# Create backup of current state before any moves
git add -A
git commit -m "Backup before audit cleanup (Jan 15 2026)"

# Or create a backup folder
mkdir backup_pre_cleanup_jan15
cp backtest_orb_exec_1m.py backup_pre_cleanup_jan15/
cp backtest_orb_exec_5m.py backup_pre_cleanup_jan15/
cp backtest_orb_exec_5mhalfsl.py backup_pre_cleanup_jan15/
cp execution_engine.py backup_pre_cleanup_jan15/
cp _unused_migrate_orbs.sql backup_pre_cleanup_jan15/
```

---

### STEP 2: Archive Deprecated Backtest Files (if YES to Question 2)

**Destination:** `_archive/backtest_old/` (folder already exists)

```bash
# Windows (Git Bash)
git mv backtest_orb_exec_1m.py _archive/backtest_old/
git mv backtest_orb_exec_5m.py _archive/backtest_old/
git mv backtest_orb_exec_5mhalfsl.py _archive/backtest_old/

# Or without Git
mv backtest_orb_exec_1m.py _archive/backtest_old/
mv backtest_orb_exec_5m.py _archive/backtest_old/
mv backtest_orb_exec_5mhalfsl.py _archive/backtest_old/
```

**Verify:**
```bash
ls _archive/backtest_old/backtest_orb_exec_*.py
# Should show 3 files now moved
```

---

### STEP 3: Archive execution_engine.py (if A - ARCHIVE chosen)

**Destination:** `_archive/legacy/`

```bash
# Windows (Git Bash)
git mv execution_engine.py _archive/legacy/

# Or without Git
mv execution_engine.py _archive/legacy/
```

**Verify:**
```bash
ls _archive/legacy/execution_engine.py
# Should exist
```

**Note:** If you chose **B. REFACTOR**, skip this step and instead:
1. Update `build_daily_features_v2.py` to import from execution_engine
2. Remove duplicated execution logic from v2
3. Test thoroughly

**Note:** If you chose **C. KEEP**, skip this step and instead:
1. Add clear header comment to execution_engine.py
2. Update CLAUDE.md to explain its purpose

---

### STEP 4: Archive Unused SQL Migration (if YES to Question 3)

**Destination:** `_archive/scripts/`

```bash
# Windows (Git Bash)
git mv _unused_migrate_orbs.sql _archive/scripts/

# Or without Git
mv _unused_migrate_orbs.sql _archive/scripts/
```

**Verify:**
```bash
ls _archive/scripts/_unused_migrate_orbs.sql
# Should exist
```

---

### STEP 5: Update Documentation

**Update PROJECT_STRUCTURE.md:**

```bash
# Edit PROJECT_STRUCTURE.md to reflect new structure
# Remove archived files from "Root Directory" section
# Add note about execution_engine.py decision
```

**Update CLAUDE.md (if needed):**

```bash
# Add clarification about execution_engine.py status
# Update backtest section if files were archived
```

---

### STEP 6: Verify No Broken Imports

**Run verification:**

```bash
# Test that apps still work
python check_db.py
python query_features.py
python -c "import query_engine; import validated_strategies; import analyze_orb_v2; print('✅ All imports OK')"

# Test dashboards (dry run - just import check)
python -c "import app_trading_hub; print('✅ Trading hub imports OK')"
python -c "import app_edge_research; print('✅ Edge research imports OK')"
```

**Expected Result:** All imports should succeed with no errors

---

### STEP 7: Commit Changes

```bash
# Stage all changes
git add -A

# Commit with descriptive message
git commit -m "Cleanup: Archive deprecated files (audit Jan 15 2026)

- Moved 3 deprecated backtest files to _archive/backtest_old/
- Moved execution_engine.py to _archive/legacy/
- Moved _unused_migrate_orbs.sql to _archive/scripts/
- Updated PROJECT_STRUCTURE.md

Based on comprehensive audit findings.
No breaking changes - all imports verified."

# Push to remote (optional)
git push origin main
```

---

## 🧪 POST-CLEANUP VERIFICATION

**Run these tests after cleanup:**

### Test 1: Daily Workflow
```bash
python daily_update.py --dry-run
# Should complete without errors
```

### Test 2: Dashboard Launch
```bash
streamlit run app_trading_hub.py
# Should launch without import errors (Ctrl+C to stop)
```

### Test 3: Query Engine
```bash
python query_features.py
# Should show features without errors
```

### Test 4: Build Features
```bash
python build_daily_features_v2.py 2026-01-14
# Should rebuild features for that date
```

### Test 5: Check Database
```bash
python check_db.py
# Should show database contents
```

**Expected Result:** All tests pass ✅

---

## 📊 EXPECTED RESULTS

### Before Cleanup
```
Root Python files: 32
├── Active: 26
├── Deprecated: 3
├── Orphaned: 1
└── Libraries: 2
```

### After Cleanup (if all archived)
```
Root Python files: 28
├── Active: 26
└── Libraries: 2

Archived: 4 files
├── _archive/backtest_old/: 3 files
├── _archive/legacy/: 1 file
└── _archive/scripts/: 1 SQL file
```

### File Count Reduction
- **Before:** 32 Python files + 4 SQL files = 36 files
- **After:** 28 Python files + 3 SQL files = 31 files
- **Reduction:** 5 files (14% cleaner)

---

## 🔄 ROLLBACK PROCEDURE (if needed)

**If something breaks after cleanup:**

```bash
# Option 1: Git revert
git revert HEAD
git push

# Option 2: Restore from backup
cp backup_pre_cleanup_jan15/*.py .
cp backup_pre_cleanup_jan15/*.sql .

# Option 3: Move back from archive
mv _archive/backtest_old/backtest_orb_exec_*.py .
mv _archive/legacy/execution_engine.py .
mv _archive/scripts/_unused_migrate_orbs.sql .
```

---

## ✅ CHECKLIST

**Before Running Commands:**
- [ ] Read complete audit report
- [ ] Answer all decision questions
- [ ] Create backup (git commit or folder)
- [ ] Understand what each command does

**During Cleanup:**
- [ ] Run commands one step at a time
- [ ] Verify each move completed successfully
- [ ] Check for errors after each step

**After Cleanup:**
- [ ] Run all verification tests
- [ ] Update documentation
- [ ] Commit changes with clear message
- [ ] Test main workflow (daily_update.py)
- [ ] Test both dashboards

**Final Steps:**
- [ ] Delete backup_pre_cleanup_jan15/ (optional, keep for a week)
- [ ] Update team (if applicable)
- [ ] Mark audit as completed

---

## 📝 NOTES

**What This Cleanup Does:**
- ✅ Removes 3-4 files from root directory
- ✅ Moves them to organized _archive/ folders
- ✅ No code deletion (everything preserved)
- ✅ No functional changes (deprecated files already can't execute)
- ✅ Cleaner root directory for development

**What This Cleanup Does NOT Do:**
- ❌ Delete any code
- ❌ Break any imports
- ❌ Modify active production files
- ❌ Change any database tables
- ❌ Affect daily operations

**Risk Level:** 🟢 LOW
- Deprecated files already have exit guards
- execution_engine.py not imported by active code
- All changes are reversible
- Backup procedure included

---

**Created:** January 15, 2026
**Ready to Execute:** After answering decision questions
**Estimated Time:** 5-10 minutes
**Risk:** Low (with backup)
