# Documentation Cleanup Plan

## Current Situation
- **65 MD files** in root directory (way too many!)
- Many are temporal status reports from Jan 16-17
- Duplicate content across multiple files
- Hard to find the actual source of truth

## Goal
- **Keep 29 essential files** that are actively used
- **Archive 36 redundant files** to `_archive/reports/`
- Clean, organized documentation structure

---

## ✅ KEEP (29 Files) - Active Use

### Core Documentation (5 files)
1. CLAUDE.md - Instructions for Claude Code
2. PROJECT_STRUCTURE.md - Codebase organization
3. TRADING_PLAYBOOK.md - All 17 validated strategies
4. DATABASE_SCHEMA_SOURCE_OF_TRUTH.md - Database schema
5. README.md - Project overview

### Strategy & Config (9 files)
6. SOURCE_OF_TRUTH.md - Which app to use
7. UNICORN_SETUPS_CORRECTED.md - Post-bugfix setups
8. SCAN_WINDOW_BUG_FIX_SUMMARY.md - Critical bug context
9. ZERO_LOOKAHEAD_RULES.md - Research methodology
10. TERMINOLOGY_EXPLAINED.md - Glossary
11. WHICH_APP_TO_USE.md - App selection guide
12. DOCUMENTATION_INDEX.md - Master index
13. CHATGPT_TRADING_GUIDE.md - Night ORB guide
14. rules.md - Global project rules

### ML Documentation (5 files)
15. ML_USER_GUIDE.md - How to use ML predictions
16. ML_FINAL_SUMMARY.md - ML project summary
17. ML_INTEGRATION_COMPLETE.md - Technical details
18. ML_PHASE1_COMPLETE.md - Phase 1 milestone
19. README_ML.md - ML technical overview

### Mobile App (2 files)
20. MOBILE_APP_README.md - Primary mobile guide
21. START_HERE.md - Quick start

### Setup & Deployment (8 files)
22. QUICK_START.md - Quick start guide
23. SETUP_TRADING_HUB.md - Dashboard setup
24. README_STREAMLIT.md - Streamlit docs
25. DEPLOY_TO_CLOUD.md - Cloud deployment
26. CLOUD_QUICK_START.md - Quick cloud setup
27. REMOTE_ACCESS_GUIDE.md - Remote access
28. QUICK_REMOTE_ACCESS.md - Quick remote
29. UPDATE_WORKFLOW.md - Dev workflow

---

## 📦 ARCHIVE (36 Files) - Move to _archive/reports/

### Completion Reports (21 files) → `_archive/reports/completion_docs_jan2026/`
**All temporal status reports from Jan 16-17:**
- FINAL_HONEST_STATUS_JAN17.md
- FINAL_STATUS_REPORT.md
- APP_READY_TO_START.md
- APP_STATUS_VERIFIED.md
- DEBUGGING_COMPLETE.md
- CLEANUP_COMPLETE_JAN16.md
- CLEANUP_COMPLETE_JAN16_v2.md
- DAILY_SUMMARY_JAN16.md
- PROJECT_STATUS_JAN16.md
- SYNC_VERIFICATION_JAN17.md
- SYSTEM_CLEANED.md
- SYSTEM_VERIFICATION_COMPLETE.md
- ARCHITECTURAL_IMPROVEMENTS_JAN16.md
- AI_DYNAMIC_LOADING_JAN16.md
- MOBILE_APP_COMPLETE.md
- MOBILE_APP_IMPLEMENTATION_COMPLETE.md
- MOBILE_APP_REAL_INTEGRATION.md
- MOBILE_APP_UPGRADE_COMPLETE.md
- BUG_FIX_JAN17_ML_INFERENCE.md
- BUG_FIX_SUMMARY.md
- SCAN_WINDOW_INVESTIGATION_COMPLETE.md

### Audit Reports (4 files) → `_archive/reports/audits_jan15/`
- AUDIT_INDEX.md
- AUDIT_REPORT_2026-01-15.md
- AUDIT_SUMMARY_2026-01-15.md
- COMPLETE_PROJECT_AUDIT_2026-01-15.md

### Duplicates/Superseded (7 files) → `_archive/reports/old_docs/`
- DATABASE_SCHEMA.md (superseded by SOURCE_OF_TRUTH version)
- MOBILE_APP_GUIDE.md (superseded by MOBILE_APP_README.md)
- APK_BUILD_FIXED.md (temporal fix, info in APK_BUILD_GUIDE)
- CLOUD_DEPLOYMENT_FIXED.md (temporal fix)
- SWITCH_TO_MOBILE_APP.md (covered in WHICH_APP_TO_USE)
- DATABASE_FIX_VERIFICATION.md (temporal fix)
- APK_BUILD_GUIDE.md (only if not using Android)

### NQ/MPL Analysis (3 files) → `_archive/reports/nq_mpl_analysis/`
- NQ_MPL_NOT_SUITABLE.md
- NQ_MPL_SCAN_WINDOW_STATUS.md
- CRITICAL_NQ_MPL_SHORT_SCANS_CONFIRMED.md

### Deployment Fixes (1 file) → `_archive/reports/old_docs/`
- CLOUD_DEPLOYMENT_FIXED.md

---

## ✅ Safety Checks Passed

### No Code References
✅ No BAT files reference MD docs
✅ No Python code references MD docs

### Essential File References
Checked CLAUDE.md, README.md, PROJECT_STRUCTURE.md:
✅ All referenced files are in KEEP list
✅ Old/missing references found (won't break anything):
   - APP_BEFORE_AFTER.md (doesn't exist)
   - SIMPLIFIED_APP_COMPLETE.md (doesn't exist)

---

## 🎯 Result After Cleanup

**Before:** 65 MD files (chaos!)
**After:** 29 MD files (organized!)

**Root Directory Structure:**
```
/
├── CLAUDE.md (instructions)
├── README.md (overview)
├── PROJECT_STRUCTURE.md (organization)
├── TRADING_PLAYBOOK.md (strategies)
├── DATABASE_SCHEMA_SOURCE_OF_TRUTH.md (schema)
├── [24 other essential docs]
└── _archive/
    └── reports/
        ├── completion_docs_jan2026/ (21 files)
        ├── audits_jan15/ (4 files)
        ├── nq_mpl_analysis/ (3 files)
        └── old_docs/ (8 files)
```

---

## 📋 Action Steps

1. Create archive folders:
   ```bash
   mkdir -p _archive/reports/completion_docs_jan2026
   mkdir -p _archive/reports/audits_jan15
   mkdir -p _archive/reports/nq_mpl_analysis
   ```

2. Move completion docs (21 files)
3. Move audit reports (4 files)
4. Move NQ/MPL analysis (3 files)
5. Move duplicates/old docs (8 files)
6. Verify 29 files remain in root
7. Update DOCUMENTATION_INDEX.md
8. Commit cleanup

---

## ⚠️ Important Notes

**APK_BUILD_GUIDE.md:**
- Keep if using Android mobile app
- Archive if mobile app not needed

**No content loss:**
- All files archived, not deleted
- Can retrieve from `_archive/reports/` if needed
- All important info already in source of truth docs

**References to archived docs:**
- If CLAUDE.md or other essential docs mention archived files
- They reference historical context only
- Won't break anything

---

**Ready to proceed?** This will reduce root MD files from 65 to 29.
