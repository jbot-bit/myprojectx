# Schema Migration Complete - 2026-01-12

## Summary

Schema inconsistencies have been fixed to make `daily_features_v2` + `v_orb_trades` internally consistent for structural analysis.

---

## Changes Made

### 1. ✅ RSI Column Standardization

**Added:** `rsi_at_orb` column to `daily_features_v2`

**Backfilled:** 739 rows from `rsi_at_0030` → `rsi_at_orb`

**Result:** RSI is now accessible via standardized `rsi_at_orb` name

**Note:** `rsi_at_0030` retained for backward compatibility

---

### 2. ✅ MAE/MFE Columns Added

**Added 12 columns to `daily_features_v2`:**
- `orb_0900_mae`, `orb_0900_mfe`
- `orb_1000_mae`, `orb_1000_mfe`
- `orb_1100_mae`, `orb_1100_mfe`
- `orb_1800_mae`, `orb_1800_mfe`
- `orb_2300_mae`, `orb_2300_mfe`
- `orb_0030_mae`, `orb_0030_mfe`

**Status:** Columns exist but NOT yet backfilled (all NULL currently)

**Next step:** Update `build_daily_features.py` to calculate and populate MAE/MFE

---

### 3. ✅ v_orb_trades View Updated

**New columns in view:**
- `mae` - Maximum adverse excursion (NULL until backfill)
- `mfe` - Maximum favorable excursion (NULL until backfill)
- `rsi_at_orb` - RSI value (populated for 0030 only, NULL for others by design)

**Also includes:**
- `outcome` - Trade outcome (UP/DOWN/NONE)
- `r_multiple` - R-multiple for the break
- `break_dir` - Break direction

**View now has:** 4,434 rows (6 ORBs × 739 days)

---

### 4. ⏭️ instrument Column (Optional - Not Done)

**Reason:** `orb_trades_1m_exec` schema was not modified to avoid breaking existing code

**If needed later:** Add `instrument VARCHAR DEFAULT 'MGC'` column and update PK to include it

---

## Verification Results

```
RSI Columns:
  ✓ rsi_at_0030: DOUBLE (original)
  ✓ rsi_at_orb: DOUBLE (standardized, backfilled 100%)

MAE/MFE Columns:
  ✓ 12 columns added (all ORBs)
  ⚠ Data: 0% populated (backfill needed)

v_orb_trades View:
  ✓ View exists
  ✓ mae, mfe, rsi_at_orb columns present
  ✓ 4,434 rows accessible
  ✓ RSI populated for 0030 ORB (739 rows)
```

---

## What Works Now

### ✅ Can Query RSI Consistently
```sql
-- Query RSI for 0030 ORB
SELECT date_local, rsi_at_orb
FROM daily_features_v2
WHERE rsi_at_orb IS NOT NULL;

-- Or via view
SELECT date_local, orb_time, rsi_at_orb
FROM v_orb_trades
WHERE orb_time = '0030' AND rsi_at_orb IS NOT NULL;
```

### ✅ Schema Ready for MAE/MFE Analysis
```sql
-- Once backfilled, can query MAE/MFE
SELECT orb_time, AVG(mae) as avg_mae, AVG(mfe) as avg_mfe
FROM v_orb_trades
WHERE mae IS NOT NULL
GROUP BY orb_time;
```

### ✅ No More Column Name Mismatches
- All structural analysis scripts can reference `rsi_at_orb`
- All ORBs have consistent MAE/MFE column naming
- View unifies all ORBs into single queryable structure

---

## What Needs To Be Done Next

### 1. Backfill MAE/MFE Data

**Current state:** MAE/MFE columns exist but contain NULL

**Required:** Update `build_daily_features.py` to calculate MAE/MFE:

**For each ORB:**
1. Get all 1-minute bars from ORB close until scan end
2. Track maximum adverse move (MAE) in ticks
3. Track maximum favorable move (MFE) in ticks
4. Store in appropriate `orb_XXXX_mae` and `orb_XXXX_mfe` columns

**Run after update:**
```bash
# Backfill all dates
python build_daily_features.py 2020-12-20 2026-01-10
```

---

### 2. Update Structural Analysis Scripts

**Scripts that can now use MAE/MFE:**
- `orb_structure_analysis_impl.py` - Add MAE/MFE to break behavior analysis
- Any scripts analyzing trade quality
- Risk/reward analysis scripts

**Example usage after backfill:**
```sql
-- Analyze MAE/MFE by break type
SELECT
    orb_time,
    break_dir,
    AVG(mae) as avg_mae_ticks,
    AVG(mfe) as avg_mfe_ticks,
    AVG(mfe / NULLIF(mae, 0)) as mfe_mae_ratio
FROM v_orb_trades
WHERE break_dir IS NOT NULL
  AND mae IS NOT NULL
GROUP BY orb_time, break_dir;
```

---

## Files Created

1. ✅ `migrate_schema_v2.sql` - Migration script
2. ✅ `verify_schema_v2.sql` - Verification script
3. ✅ `SCHEMA_MIGRATION_COMPLETE.md` - This document

---

## Migration Details

**Approach:** Safe ALTER TABLE (no DROP/CREATE)

**Backward compatible:** Old column names retained

**Verified:** All checks pass

**Time to complete:** ~1 second

**Data loss:** None

**Breaking changes:** None

---

## Quick Reference

### Query RSI
```sql
SELECT date_local, rsi_at_orb
FROM daily_features_v2
WHERE rsi_at_orb > 70;  -- Overbought
```

### Check MAE/MFE Status
```sql
SELECT
    COUNT(*) as total_rows,
    COUNT(orb_0900_mae) as mae_populated,
    COUNT(orb_0900_mfe) as mfe_populated
FROM daily_features_v2;
-- Currently: total_rows=739, mae_populated=0, mfe_populated=0
```

### Query View with All Fields
```sql
SELECT *
FROM v_orb_trades
WHERE date_local = '2026-01-10'
ORDER BY orb_time;
```

---

## Schema Status

| Feature | Status | Notes |
|---------|--------|-------|
| RSI standardization | ✅ Complete | 100% backfilled |
| MAE/MFE columns | ✅ Added | Backfill needed |
| v_orb_trades view | ✅ Updated | Includes new columns |
| instrument column | ⏭️ Skipped | Optional, not needed yet |
| Backward compatibility | ✅ Maintained | Old names retained |
| Data integrity | ✅ Verified | All checks pass |

---

## Next Action Required

**Update `build_daily_features.py` to calculate MAE/MFE for all ORBs.**

Once complete, run full backfill to populate the 12 MAE/MFE columns.

Then all structural analysis can use MAE/MFE via `daily_features_v2` or `v_orb_trades` view.
