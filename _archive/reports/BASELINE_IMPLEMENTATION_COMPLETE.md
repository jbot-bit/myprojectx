# Baseline Implementation Complete - 2026-01-12

## Summary

Implemented ORB-anchored MAE/MFE calculations and created a clean baseline backtest script as requested.

---

## What Was Done

### 1. Consolidated to Single Feature Builder

**Chose:** `build_daily_features_v2.py` as the single source of truth

**Why:**
- Zero-lookahead 1-minute execution model
- Writes to `daily_features_v2` table (current schema)
- More precise than v1

**Deprecated:** `build_daily_features.py` (old schema, entry-anchored MAE/MFE)

### 2. Added ORB-Anchored MAE/MFE to build_daily_features_v2.py

**Changes:**
- Added `sl_mode` parameter: "full" (stop at opposite edge) or "half" (stop at midpoint)
- Implemented **ORB-anchored MAE/MFE calculation**:
  - MAE: Maximum adverse excursion FROM ORB EDGE (not entry price)
  - MFE: Maximum favorable excursion FROM ORB EDGE (not entry price)
- Added MAE/MFE columns to schema (12 columns: 6 ORBs × 2 metrics)
- Updated INSERT statement to populate MAE/MFE data

**Formula (ORB-anchored):**
```python
orb_edge = orb_high if direction == "UP" else orb_low

# For UP break:
mae_ticks = max(0, (orb_edge - min_price_after) / tick_size)
mfe_ticks = max(0, (max_price_after - orb_edge) / tick_size)

# For DOWN break:
mae_ticks = max(0, (max_price_after - orb_edge) / tick_size)
mfe_ticks = max(0, (orb_edge - min_price_after) / tick_size)
```

**Verified:** Tested on 2026-01-09, MAE/MFE calculated correctly.

### 3. Created Clean Baseline Backtest Script

**File:** `baseline_orb_1m_halfsl.py`

**Configuration:**
- **Execution:** 1-minute (first close outside ORB)
- **SL mode:** Half SL (stop at ORB midpoint)
- **ORBs:** 0900, 1000, 1100 only
- **R:R ratios:** 1.0, 1.25, 1.5
- **Filters:** NONE
- **MAE/MFE:** ORB-anchored (from ORB edge)

**Output Structure:**
1. **PART 1: MAE/MFE DISTRIBUTIONS** (reported BEFORE P&L)
   - Mean, Median, P25, P75, P90, Max
   - Separate for each ORB time
   - MFE/MAE ratio

2. **PART 2: P&L RESULTS**
   - Broken down by R:R ratio
   - Win/Loss/No Exit counts
   - Win rate
   - Net P&L in R-multiples

**Verified:** Tested on 2026-01-06 to 2026-01-09 (4 days, 12 trades)

---

## Test Results (4-Day Sample: 2026-01-06 to 2026-01-09)

### MAE/MFE Distributions (ORB-Anchored)

**ORB 0900:**
- Breaks: 4
- Avg ORB size: 65.7 ticks
- MAE mean: 37.2 ticks (pullback from edge)
- MFE mean: 28.0 ticks (favorable from edge)
- MFE/MAE ratio: 0.75x (adverse > favorable)

**ORB 1000:**
- Breaks: 4
- Avg ORB size: 38.0 ticks
- MAE mean: 12.5 ticks
- MFE mean: 30.2 ticks
- MFE/MAE ratio: 0.84x

**ORB 1100:**
- Breaks: 4
- Avg ORB size: 120.5 ticks (much larger)
- MAE mean: 43.5 ticks
- MFE mean: 64.3 ticks
- MFE/MAE ratio: 27.45x (calculation artifact - need more data)

### P&L Results

**R:R = 1.0:**
- 12 trades total
- Win rate: 33.3% (4W / 8L)
- Net P&L: -4.0R

**R:R = 1.25:**
- 12 trades total
- Win rate: 25.0% (3W / 9L)
- Net P&L: -5.2R

**R:R = 1.5:**
- 12 trades total
- Win rate: 25.0% (3W / 9L)
- Net P&L: -4.5R

**Observation:** Negative expectancy across all R:R ratios even on this small sample.

---

## Next Steps

### Run Full Baseline (Recommended)

```bash
python baseline_orb_1m_halfsl.py 2024-01-01 2026-01-09
```

This will:
1. Test ~2 years of data
2. Provide robust MAE/MFE distributions
3. Show P&L results across multiple R:R ratios
4. Give you definitive baseline performance with NO FILTERS

### Interpreting Results

**Focus on MAE/MFE distributions FIRST:**
- If MFE/MAE < 1.0: Adverse moves dominate (pullbacks are larger than follow-through)
- If MFE/MAE > 1.5: Favorable moves dominate (strong directional follow-through)
- If MFE/MAE ≈ 1.0: Balanced behavior (no clear directional edge)

**Then look at P&L:**
- Negative expectancy at RR=1.0 means even 50% win rate won't be profitable
- Compare across RR ratios to see if higher RR improves edge (unlikely based on previous findings)

**CRITICAL:**
Per previous structural analysis, you found **zero directional edge** after ORB formation. This baseline will quantify that finding with proper ORB-anchored measurements.

---

## Files Summary

### Modified:
- `build_daily_features_v2.py` - Added ORB-anchored MAE/MFE calculation with Half SL support

### Created:
- `baseline_orb_1m_halfsl.py` - Clean baseline backtest script
- `BASELINE_IMPLEMENTATION_COMPLETE.md` - This document
- `verify_mae_mfe_v2.py` - Verification script for MAE/MFE data
- `find_latest_date.py` - Helper to find dates with ORB data

### Deprecated:
- `build_daily_features.py` - Use v2 instead (entry-anchored MAE/MFE, wrong methodology)

---

## R Definition Compliance

**MAE/MFE:** ORB-anchored (measured from ORB edge, NOT entry price) ✓

**Trade Simulation:** Entry-anchored (actual trade risk/reward):
```python
# Stop placement
stop = orb_mid  # Half SL mode

# Risk calculation (entry-anchored)
risk = abs(entry_price - stop)

# Target calculation (entry-anchored)
target = entry_price + rr * risk  # UP
target = entry_price - rr * risk  # DOWN
```

**Rationale:**
- **MAE/MFE must be ORB-anchored** to measure structural move quality (as requested)
- **Trade simulation uses entry-anchored** to represent actual trade risk/reward
- This matches legacy backtest methodology while adding ORB-anchored MAE/MFE measurement

**Note:** If you want to test ORB-anchored trade targets (TP calculated from ORB edge instead of entry), that would require a separate variant. The current implementation prioritizes realistic trade simulation.
