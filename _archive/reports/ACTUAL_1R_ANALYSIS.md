# Actual 1R Analysis - Trade Tables

**Date:** 2026-01-12
**Analysis:** Measured actual 1R values from executed trades

---

## Executive Summary

**NO, 1R ≠ ORB size.**

### Key Findings:

**1-Minute Execution:**
- **Average 1R = 1.3-1.35x ORB size**
- Entries happen ~0.3 ORB sizes away from boundary

**5-Minute Execution:**
- **Average 1R = 1.45-1.58x ORB size**
- Entries happen ~0.5 ORB sizes away from boundary
- Full SL: 1R = 1.58-1.69x ORB
- Half SL: 1R = 1.29-1.45x ORB

**This explains why 3R targets fail:**
- 3R target = 3 × 1.5 × ORB = **4.5x ORB size** (unrealistic)

---

## 1-Minute Execution Results

**Sample:** 37,348 trades across 6 ORBs

| ORB  | Trades | Avg ORB Size | Avg 1R (Entry) | 1R/ORB Ratio | Median 1R | P90 1R | Max 1R |
|------|--------|--------------|----------------|--------------|-----------|--------|--------|
| 0900 | 6,328  | 21.7 ticks   | 27.2 ticks     | **1.34x**    | 20.0      | 63.0   | 100.0  |
| 1000 | 6,503  | 23.9 ticks   | 30.7 ticks     | **1.34x**    | 22.0      | 65.0   | 100.0  |
| 1100 | 5,882  | 33.3 ticks   | 41.9 ticks     | **1.30x**    | 37.0      | 79.0   | 100.0  |
| 1800 | 6,551  | 26.9 ticks   | 35.1 ticks     | **1.35x**    | 31.0      | 61.0   | 100.0  |
| 2300 | 6,165  | 38.4 ticks   | 48.6 ticks     | **1.31x**    | 46.0      | 82.0   | 100.0  |
| 0030 | 5,919  | 38.5 ticks   | 49.8 ticks     | **1.33x**    | 46.0      | 79.0   | 100.0  |

### Interpretation:

**1R consistently 1.3-1.35x ORB size** across all sessions.

**Why?**
- Entries occur ~0.3 ORB sizes away from ORB boundary on average
- Stop is at ORB edge (Full SL mode in 1m execution)
- Therefore: 1R = Entry distance + ORB size to opposite edge

**Example:**
- ORB size = 20 ticks
- Entry at ORB high + 6 ticks
- Stop at ORB low
- **1R = 26 ticks = 1.3x ORB size** ✓

---

## 5-Minute Execution Results

**Sample:** 263,724 trades across 6 ORBs

### Overall Stats:

| ORB  | Trades | Avg ORB Size | Avg 1R (Entry) | 1R/ORB Ratio | Median 1R | P90 1R | Max 1R |
|------|--------|--------------|----------------|--------------|-----------|--------|--------|
| 0900 | 45,612 | 21.7 ticks   | 28.6 ticks     | **1.53x**    | 22.0      | 61.0   | 100.0  |
| 1000 | 46,141 | 23.4 ticks   | 32.0 ticks     | **1.55x**    | 25.0      | 66.0   | 100.0  |
| 1100 | 41,989 | 33.9 ticks   | 43.9 ticks     | **1.45x**    | 39.0      | 81.0   | 100.0  |
| 1800 | 46,676 | 26.4 ticks   | 38.4 ticks     | **1.58x**    | 34.0      | 67.0   | 100.0  |
| 2300 | 42,304 | 37.9 ticks   | 51.7 ticks     | **1.51x**    | 50.0      | 84.0   | 100.0  |
| 0030 | 41,002 | 39.1 ticks   | 52.0 ticks     | **1.45x**    | 49.5      | 83.0   | 100.0  |

### By Stop Loss Mode:

| ORB  | SL Mode | Trades | Avg ORB | Avg 1R (Entry) | 1R/ORB Ratio | Avg 1R (Edge) | Edge/ORB Ratio |
|------|---------|--------|---------|----------------|--------------|---------------|----------------|
| 0900 | Full    | 24,444 | 20.3    | 29.8           | **1.64x**    | 20.3          | **1.00x**      |
| 0900 | Half    | 21,168 | 23.3    | 27.2           | **1.41x**    | 17.3          | **0.82x**      |
| 1000 | Full    | 24,692 | 22.2    | 33.6           | **1.66x**    | 22.2          | **1.00x**      |
| 1000 | Half    | 21,449 | 24.8    | 30.3           | **1.43x**    | 18.5          | **0.81x**      |
| 1100 | Full    | 21,808 | 31.0    | 45.7           | **1.58x**    | 31.0          | **1.00x**      |
| 1100 | Half    | 20,181 | 37.1    | 41.9           | **1.30x**    | 26.0          | **0.76x**      |
| 1800 | Full    | 25,196 | 25.7    | 40.7           | **1.69x**    | 25.7          | **1.00x**      |
| 1800 | Half    | 21,480 | 27.1    | 35.7           | **1.45x**    | 20.6          | **0.80x**      |
| 2300 | Full    | 21,908 | 36.0    | 55.0           | **1.65x**    | 36.0          | **1.00x**      |
| 2300 | Half    | 20,396 | 40.1    | 48.3           | **1.35x**    | 28.2          | **0.74x**      |
| 0030 | Full    | 21,448 | 37.1    | 55.7           | **1.58x**    | 37.1          | **1.00x**      |
| 0030 | Half    | 19,554 | 41.2    | 48.0           | **1.29x**    | 29.0          | **0.74x**      |

### Interpretation:

**Full SL Mode:**
- 1R (entry) = **1.58-1.69x ORB**
- 1R (edge) = **1.00x ORB** (stop exactly at ORB edge)
- Entry happens ~0.6 ORB sizes away from boundary

**Half SL Mode:**
- 1R (entry) = **1.29-1.45x ORB**
- 1R (edge) = **0.74-0.82x ORB** (stop at midpoint)
- Entry happens ~0.5 ORB sizes away, but stop is closer

---

## What This Means for R:R Ratios

### Actual Target Sizes:

If **ORB size = 20 ticks**, and **1R = 30 ticks** (1.5x ORB):

| R:R Ratio | Target Distance | Target/ORB Ratio |
|-----------|-----------------|------------------|
| 1.0x      | 30 ticks        | **1.5x ORB**     |
| 1.5x      | 45 ticks        | **2.25x ORB**    |
| 2.0x      | 60 ticks        | **3.0x ORB**     |
| 2.5x      | 75 ticks        | **3.75x ORB**    |
| 3.0x      | 90 ticks        | **4.5x ORB**     |

### Why High R:R Ratios Failed:

Your backtests used **2.5x-3.0x R:R ratios**, which means:
- **3R target = 4.5x ORB size**
- For a 20-tick ORB, target = 90 ticks away
- This is **unrealistically large** for intraday moves

**No wonder win rates were 2-3%** - you were targeting moves that almost never happen.

---

## 1R Definitions Explained

### Entry-Anchored 1R (What Backtests Use):
```
1R = |Entry Price - Stop Price|
```
- **Variable per trade** (depends on entry distance)
- **What you actually risk** when you enter
- **1.3-1.7x ORB size** on average

### Edge-Anchored 1R (Structural Reference):
```
1R = |ORB Edge - Stop Price|
```
- **More stable** (independent of entry timing)
- **Full SL: 1R = ORB size exactly**
- **Half SL: 1R = 0.5 ORB size** (stop at midpoint)

---

## Key Takeaways

1. ❌ **1R ≠ ORB size** (common misconception)

2. ✅ **1R = 1.3-1.7x ORB size** (depending on execution method)

3. 🎯 **1-minute execution has tighter 1R** (1.3x vs 1.5x for 5-minute)
   - Entries closer to ORB boundary
   - Less slippage/drift

4. 📊 **Full SL = larger 1R** (1.6x vs 1.3x for half SL)
   - Stop at edge vs midpoint
   - More risk per trade

5. ⚠️ **3R target = 4.5x ORB size** (unrealistic for most ORBs)
   - Explains 2-3% win rates
   - Targets almost never hit

---

## Implications for Strategy Design

### If You Want Higher Win Rates:

**Lower R:R ratios:**
- 1.0x R:R = 1.5x ORB target (more achievable)
- 1.5x R:R = 2.25x ORB target (still difficult)

**Tighter entries:**
- Enter closer to ORB boundary
- Reduces 1R size
- But may increase false signals

**Smaller stops:**
- Half SL mode reduces 1R by ~20-30%
- But may get stopped out more

### If You Accept Lower Win Rates:

**Keep higher R:R ratios:**
- 2.0x-3.0x R:R
- But accept 5-10% win rates
- Requires **positive expectancy** (which you don't have)

---

## 1-Minute vs 5-Minute Execution

**Why 1-minute is better:**

| Metric | 1-Minute | 5-Minute | Winner |
|--------|----------|----------|--------|
| Avg 1R/ORB | 1.33x | 1.52x | **1-min** (tighter) |
| Entry drift | 0.33 ORB | 0.52 ORB | **1-min** (closer) |
| Total loss | -1,940R | -17,041R | **1-min** (8.8x better) |

**1-minute execution enters closer to ORB boundary**, resulting in:
- Smaller 1R (less risk per trade)
- More realistic targets for same R:R ratio
- Better overall performance

---

## Recommended Actions

1. **Stop using 2.5x-3.0x R:R ratios** (targets are 4x+ ORB size)

2. **Test 1.0x-1.5x R:R ratios** (targets are 1.5x-2.25x ORB size)

3. **Focus on 1-minute execution** (tighter 1R, better results)

4. **Consider Half SL mode** (reduces 1R by 20-30%)

5. **Accept reality:** Even with realistic targets, **you have no structural edge** (per earlier analysis)

---

## Bottom Line

**Your 1R averages 1.5x ORB size.**

**Your 3R targets were 4.5x ORB size.**

**This explains the 2-3% win rates** - you were targeting unrealistic moves.

**But even with realistic targets (1R-1.5R)**, the structural analysis showed **no directional edge exists** after ORB formation.

**Conclusion:** Lower R:R ratios might improve win rate, but won't create profitability without underlying structural edge.
