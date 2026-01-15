# Half SL Implementation Complete - 2026-01-12

## Summary

Successfully added **Half SL support** to `build_daily_features_v2.py` with **ORB-anchored R normalization** for MAE/MFE as requested.

---

## Implementation Details

### 1. SL Mode Configuration

**Added config parameter:**
```python
SL_MODE = "full"  # Options: "full" | "half" (default "full" for backward compatibility)
```

**Stop placement logic:**
```python
orb_mid = (orb_high + orb_low) / 2.0

if sl_mode == "full":
    # Full SL: stop at opposite ORB edge
    stop = orb_low if direction == "UP" else orb_high
else:  # half
    # Half SL: stop at ORB midpoint
    stop = orb_mid
```

### 2. ORB-Anchored R Calculation

**Formula:**
```python
# ORB edge (anchor point)
orb_edge = orb_high if direction == "UP" else orb_low

# ORB-anchored R: distance from edge to stop
r_orb = abs(orb_edge - stop)
risk_ticks = r_orb / 0.1
```

**Results:**
- **Full SL:** R = ORB size (e.g., 74 ticks)
- **Half SL:** R = 0.5 × ORB size (e.g., 37 ticks)

### 3. MAE/MFE Normalization

**Formula (normalized by ORB-anchored R):**
```python
# For UP break:
mae = (orb_edge - min_low_after_break) / r_orb  # R-multiples
mfe = (max_high_after_break - orb_edge) / r_orb  # R-multiples

# For DOWN break:
mae = (max_high_after_break - orb_edge) / r_orb  # R-multiples
mfe = (orb_edge - min_low_after_break) / r_orb  # R-multiples
```

**Before (incorrect):** MAE/MFE in ticks (e.g., 32.0 ticks, 88.0 ticks)
**After (correct):** MAE/MFE in R-multiples (e.g., 0.432R, 1.189R)

### 4. Debug Columns Added

**Per ORB (12 new columns total):**
- `orb_XXXX_stop_price`: Actual stop price used (DOUBLE)
- `orb_XXXX_risk_ticks`: ORB-anchored R in ticks (DOUBLE)

**Example:**
```
orb_0900_stop_price = 4493.70 (opposite edge for Full SL)
orb_0900_risk_ticks = 74.0 (ORB size for Full SL)
```

### 5. Guard for R <= 0

**Implementation:**
```python
if r_orb <= 0:
    return {
        "break_dir": break_dir,
        "outcome": "NO_TRADE",
        "mae": None, "mfe": None,
        "stop_price": stop,
        "risk_ticks": 0.0
    }
```

**Note:** This should never happen in practice, but guards against division by zero.

---

## Verification Results

### Full SL Mode (default)

**ORB 0900 (2026-01-09):**
- Range: 4493.70 - 4486.30 (74 ticks)
- Break: DOWN, Outcome: WIN
- **Stop: 4493.70** (opposite edge)
- **Risk: 74.0 ticks** (ORB size)
- **MAE: 0.432R** (= 32.0 ticks absolute)
- **MFE: 1.189R** (= 88.0 ticks absolute)
- MFE/MAE ratio: 2.75

**ORB 1000 (2026-01-09):**
- Range: 4486.80 - 4483.70 (31 ticks)
- Break: DOWN, Outcome: WIN
- **Stop: 4486.80** (opposite edge)
- **Risk: 31.0 ticks** (ORB size)
- **MAE: 0.000R** (no pullback)
- **MFE: 2.000R** (= 62.0 ticks absolute)

### Half SL Mode (tested)

**ORB 0900 (2026-01-09):**
- Range: 4493.70 - 4486.30 (74 ticks)
- Midpoint: 4490.00
- Break: DOWN, Outcome: WIN
- **Stop: 4490.00** ✓ (at midpoint)
- **Risk: 37.0 ticks** ✓ (0.5 × ORB size)
- **MAE: 0.865R** (= 32.0 ticks absolute)
- **MFE: 1.351R** (= 50.0 ticks absolute)
- MFE/MAE ratio: 1.56

---

## Schema Changes

### New Columns Added (via migration)

**Script:** `add_stop_risk_columns.py`

**Columns:**
```sql
ALTER TABLE daily_features_v2 ADD COLUMN orb_0900_stop_price DOUBLE;
ALTER TABLE daily_features_v2 ADD COLUMN orb_0900_risk_ticks DOUBLE;
-- (repeated for 1000, 1100, 1800, 2300, 0030)
```

**Total:** 12 new columns (6 ORBs × 2 debug fields)

---

## Files Modified/Created

### Modified:
1. **`build_daily_features_v2.py`**
   - Added `sl_mode` parameter (default 'full')
   - Implemented ORB-anchored R calculation
   - Normalized MAE/MFE by R
   - Added debug columns (stop_price, risk_ticks)
   - Updated schema to include new columns
   - Updated INSERT statement with 12 new fields

### Created:
1. **`add_stop_risk_columns.py`** - Migration script to add debug columns
2. **`verify_r_normalized_mae_mfe.py`** - Verification script for Full SL
3. **`verify_half_sl_mode.py`** - Verification script for Half SL
4. **`HALF_SL_IMPLEMENTATION_COMPLETE.md`** - This document

---

## Usage Examples

### Full SL Mode (default)

```python
# Default in build_daily_features_v2.py
SL_MODE = "full"

# Rebuild features
python build_daily_features_v2.py 2026-01-09
```

**Result:**
- Stop = opposite ORB edge
- R = ORB size (e.g., 74 ticks)
- MAE/MFE normalized by R

### Half SL Mode

```python
# Change in build_daily_features_v2.py
SL_MODE = "half"

# Rebuild features
python build_daily_features_v2.py 2026-01-09
```

**Result:**
- Stop = ORB midpoint
- R = 0.5 × ORB size (e.g., 37 ticks)
- MAE/MFE normalized by R

### Query Results

```sql
SELECT
    date_local,
    orb_0900_high, orb_0900_low, orb_0900_size,
    orb_0900_break_dir, orb_0900_outcome,
    orb_0900_stop_price,  -- Debug: actual stop price
    orb_0900_risk_ticks,  -- Debug: ORB-anchored R in ticks
    orb_0900_mae,         -- Normalized by R (R-multiples)
    orb_0900_mfe          -- Normalized by R (R-multiples)
FROM daily_features_v2
WHERE date_local = '2026-01-09'
  AND orb_0900_break_dir IS NOT NULL;
```

---

## Key Benefits

### 1. Proper R Normalization
**Before:** MAE/MFE in absolute ticks (not comparable across ORBs)
**After:** MAE/MFE in R-multiples (comparable across all ORBs/modes)

**Example:**
- ORB A: MAE = 32 ticks, R = 74 ticks → MAE = 0.43R
- ORB B: MAE = 32 ticks, R = 37 ticks → MAE = 0.86R
- Now comparable: ORB B has 2x the adverse excursion relative to risk

### 2. Debug Transparency
**stop_price** and **risk_ticks** allow verification of:
- Correct stop placement (opposite edge vs midpoint)
- Correct R calculation (ORB size vs 0.5 × ORB size)
- MAE/MFE normalization accuracy

### 3. Mode Flexibility
- **Full SL:** Traditional ORB with wider stops (R = ORB size)
- **Half SL:** Tighter stops with reduced risk (R = 0.5 × ORB size)
- **Backward compatible:** Default 'full' preserves existing behavior

### 4. Structural Measurement
**ORB-anchored MAE/MFE** measures move quality from structure, not entry:
- Independent of entry timing/slippage
- Reveals true directional follow-through
- Enables structural analysis as requested

---

## Validation Checklist

- [x] sl_mode parameter added (full/half)
- [x] Midpoint defined: `orb_mid = (orb_high + orb_low) / 2.0`
- [x] Stop placement correct for both modes
- [x] ORB-anchored R calculated: `R = abs(edge - stop)`
- [x] Guard for R <= 0 implemented
- [x] MAE/MFE normalized by R (not in ticks)
- [x] Debug columns added (stop_price, risk_ticks)
- [x] Schema migration successful
- [x] Full SL mode verified (R = ORB size)
- [x] Half SL mode verified (R = 0.5 × ORB size)
- [x] Default = 'full' for backward compatibility

---

## Next Steps

### Rebuild Historical Data (Optional)

**If you want to backfill with new format:**

1. **Choose SL mode** (edit `build_daily_features_v2.py`):
   ```python
   SL_MODE = "full"  # or "half"
   ```

2. **Rebuild features:**
   ```bash
   python build_daily_features_v2.py 2024-01-01 2026-01-09
   ```

3. **Result:**
   - MAE/MFE in R-multiples
   - stop_price and risk_ticks populated
   - Consistent with chosen SL mode

### Use in Analysis

**Query MAE/MFE by ORB:**
```sql
SELECT
    orb_time,
    AVG(mae) as avg_mae_r,  -- In R-multiples
    AVG(mfe) as avg_mfe_r,  -- In R-multiples
    AVG(mfe / NULLIF(mae, 0)) as mfe_mae_ratio
FROM v_orb_trades
WHERE break_dir IS NOT NULL
  AND mae IS NOT NULL
GROUP BY orb_time
ORDER BY orb_time;
```

**Compare Full vs Half SL:**
- Rebuild twice (once with each mode)
- Compare MAE/MFE distributions
- Analyze which mode has better risk-adjusted performance

---

## Technical Notes

### Why Normalize by ORB-Anchored R?

**User requirement:**
> "Compute MAE/MFE (edge-referenced, normalized by R)"

**Rationale:**
- **ORB-anchored R** is the structural reference (fixed per ORB)
- **Entry-anchored R** varies by entry timing (not structural)
- Normalization makes MAE/MFE comparable across:
  - Different ORB sizes
  - Different SL modes (Full vs Half)
  - Different ORBs (0900 vs 1000 vs 1100, etc.)

**Example:**
Without normalization, MAE = 32 ticks means nothing without context.
With normalization, MAE = 0.43R means 43% pullback relative to structural risk.

### Guard for R <= 0

**When could this happen?**
- Theoretically never (ORB edge ≠ stop by design)
- Included as defensive programming

**What happens:**
- Skip metrics (set NULL)
- Log count (none observed in testing)
- Prevents division by zero

---

## Conclusion

**Implementation complete and verified.**

All requirements met:
1. ✓ Half SL support added
2. ✓ ORB-anchored R used everywhere for MAE/MFE
3. ✓ MAE/MFE normalized by R
4. ✓ Debug columns added (stop_price, risk_ticks)
5. ✓ Guard for R <= 0
6. ✓ Full SL unchanged (backward compatible)
7. ✓ Default = 'full' for backward compatibility

**Ready for production use.**
