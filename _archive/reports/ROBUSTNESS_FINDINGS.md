# Robustness Test Findings & Strategic Recommendations

**Date:** 2026-01-12
**Test:** 69 candidate configs tested WITHOUT filters (MAX_STOP=999999, ASIA_TP_CAP=999999)

---

## Executive Summary

**CRITICAL FINDING:** Zero configs show positive expectancy when filters are removed.

- **Total trades:** 35,385 across 69 configs
- **Win rate:** 6.3% (2,216 wins / 33,169 losses)
- **Total R:** -28,895R
- **Average R per trade:** -0.82R

**All 69 configs lose money without filters applied.**

---

## Key Insights

### 1. ORB Session Performance
- **1800 ORB** performs significantly better than 1000 ORB
  - 1800: -2,368.5R total (avg -0.648R per trade)
  - 1000: -26,526.5R total (avg -0.836R per trade)
- Only 7 of 69 configs tested 1800 ORB
- 1800 deserves deeper investigation

### 2. R:R Ratio Impact
Lower R:R ratios perform progressively better:
- **1.0x R:R:** -649R total (avg -0.621R per trade) ← Best
- **1.5x R:R:** -6,348.5R total (avg -0.723R per trade)
- **2.0x R:R:** -2,758R total (avg -0.754R per trade)
- **2.5x R:R:** -9,179.5R total (avg -0.857R per trade)
- **3.0x R:R:** -9,960R total (avg -0.890R per trade) ← Worst

**High R:R ratios (2.5x-3.0x) are too aggressive for ORB breakouts.**

### 3. Close Confirmations
- **1 confirmation:** -13,750R (7.4% win rate)
- **2 confirmations:** -14,677.5R (5.2% win rate)
- **3 confirmations:** -467.5R (2.9% win rate)

More confirmations = worse performance (fewer trades, worse win rate).

### 4. Stop Loss Mode
- **Half SL:** -15,415R (7.7% win rate) ← Better
- **Full SL:** -13,480R (4.5% win rate combined)

Half SL performs better with higher win rate.

### 5. Best Config (Still Losing)
- **1800 | 1 confirm | 1.0x R:R | Half SL | 2 tick buffer**
  - 522 trades, 118 wins (22.6% win rate)
  - Total: -286R (avg -0.548R per trade)
  - **Still loses money**, but least bad

---

## What This Means

### The Filters Were Masking Reality

The candidate configs were extracted from filtered backtests that looked promising:
- Filters: MAX_STOP ≤ 60 ticks, ASIA_TP_CAP ≤ 100 ticks
- These filters excluded large losing trades
- **Without filters, the strategies have no edge**

This means either:
1. The filters are artificially creating "edge" through data selection bias
2. The strategies only work with strict risk management (filters)
3. The strategies fundamentally don't work

---

## Strategic Options

### Option A: Search for Unfiltered Edge (RECOMMENDED)

**Goal:** Find configs that are profitable WITHOUT needing filters.

**Action Plan:**
1. Run exhaustive parameter sweep on **1800 ORB** (best performer)
   - R:R ratios: 0.5x, 0.75x, 1.0x, 1.25x, 1.5x
   - Confirmations: 1 only (best performer)
   - SL modes: half (best performer)
   - Buffers: 0, 2, 5, 10, 15, 20

2. Test **other ORB sessions** (0900, 1100, 2300, 0030)
   - Use same low R:R ratios
   - Focus on sessions with directional bias

3. Look for **any positive expectancy** before applying filters

**Files needed:**
- `search_unfiltered_edge.py` - Sweep 1800 ORB with low R:R ratios
- Test 100-200 new configs focusing on what worked best

### Option B: Accept Filters as Part of Strategy

**Goal:** Use filters as legitimate risk management, not data selection.

**Action Plan:**
1. Re-run robustness test WITH filters (MAX_STOP=60, ASIA_TP_CAP=100)
2. Document that strategy REQUIRES these filters
3. Understand edge depends on consistent filter application
4. Backtests should always include filters

**Trade-off:** Edge depends on cutting losses short and capping wins.

### Option C: Investigate 1800 ORB Deeper

**Goal:** Focus on best-performing session (1800) with more parameters.

**Action Plan:**
1. Run dedicated 1800 sweep with 50+ configs
2. Lower R:R ratios (0.5x - 2.0x range)
3. Test different buffers and SL modes
4. Look for what makes 1800 different from 1000

**Why:** 1800 lost -2,368R vs 1000 lost -26,526R (10x better).

### Option D: Rethink Strategy Entirely

**Goal:** Pivot to fundamentally different approach.

**Ideas:**
1. **Mean reversion:** Fade ORB breaks instead of following them
2. **Different entry:** Use wicks, patterns, or levels instead of close confirmations
3. **Different ORB durations:** 10-minute, 15-minute, or 30-minute ORBs
4. **Time-based filters:** Only trade certain hours or weekdays
5. **Combine with other signals:** RSI, trend, session ranges

---

## Recommended Immediate Next Step

### Run 1800 ORB Low R:R Sweep

**Rationale:**
- 1800 performed 10x better than 1000
- Only 7 configs tested for 1800 (vs 62 for 1000)
- Lower R:R ratios showed best performance
- Half SL + 1 confirmation = best combo

**Parameters:**
- ORB: 1800 only
- R:R: 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0
- Confirmations: 1
- SL mode: half
- Buffers: 0, 2, 5, 10, 15, 20

**Total configs:** 7 × 6 = 42 configs

**Script:** `search_1800_low_rr.py`

Run this sweep WITHOUT filters to see if 1800 ORB has genuine unfiltered edge with tighter targets.

---

## Files Created

1. `run_robustness_batch_OPTIMIZED.py` - Fixed performance issue (completed)
2. `analyze_robustness_results.py` - Comprehensive analysis (completed)
3. `ROBUSTNESS_FINDINGS.md` - This summary document

---

## Next Script to Create

`search_1800_low_rr.py` - Sweep 1800 ORB with low R:R ratios to find unfiltered edge.
