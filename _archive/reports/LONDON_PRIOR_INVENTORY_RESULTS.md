# London Prior Inventory Test Results

**Date:** 2026-01-12
**Test:** Engine A validation - Which prior session matters to London?
**Dataset:** 502 London ORB trades (2020-2026)

---

## Executive Summary

**KEY FINDING: Asia's resolution of PRIOR NY inventory creates the strongest London edge.**

- **NY_HIGH -> London LONG**: +0.281R avg, 43.3% WR, +25.3R total (90 trades) **[BEST PATTERN]**
- **NY_HIGH -> London SHORT**: -0.030R avg, 29.8% WR, -1.7R total (57 trades) **[TOXIC - AVOID]**
- **Continuation edge**: +0.310R vs fade (13.5% WR improvement)

**PROBLEM: NY_LOW continuation is BROKEN**
- **NY_LOW -> London DOWN**: -0.058R avg, 28.8% WR, -3.0R total **[FAILS]**
- **NY_LOW -> London UP** (fade): +0.150R avg, 37.0% WR, +6.9R total **[REVERSAL??]**

---

## Test Setup

### Labels Created:
1. **NY_HIGH**: Asia swept prior NY session high (not low)
2. **NY_LOW**: Asia swept prior NY session low (not high)
3. **BOTH_NY**: Asia swept both prior NY high and low
4. **LONDON_HIGH/LOW**: Asia swept only prior London levels (not NY)
5. **DAY_HIGH/LOW**: Asia swept only prior day levels (not NY/London)
6. **FAILED**: No prior inventory resolved

### Distribution:
- **BOTH_NY**: 266 days (51%)
- **NY_HIGH**: 152 days (29%)
- **NY_LOW**: 103 days (20%)

**Note:** Only 3 labels appeared with sufficient sample size. No LONDON_HIGH/LOW or DAY_HIGH/LOW labels met 20-trade minimum.

---

## Baseline Performance

**All London ORBs (no filters):**
- Total Trades: 502
- Win Rate: 36.1%
- Avg R: +0.109R
- Total R: +54.9R

---

## Results by Asia State

### 1. BOTH_NY (Asia swept both prior NY high and low)

**Overall:** 257 trades, 36.2% WR, +0.107R avg, +27.4R total

**By Direction:**
- **UP**: 126 trades, 38.9% WR, +0.181R avg, +22.9R total
- **DOWN**: 131 trades, 33.6% WR, +0.035R avg, +4.6R total

**Analysis:** Neutral vs baseline. When Asia sweeps both sides, no directional edge.

---

### 2. NY_HIGH (Asia resolved prior NY high only)

**Overall:** 147 trades, 38.1% WR, +0.160R avg, +23.6R total
- **Delta vs baseline:** +2.0% WR, +0.051R

**By Direction:**
- **UP (continuation)**: 90 trades, 43.3% WR, +0.281R avg, +25.3R total **[BEST]**
- **DOWN (fade)**: 57 trades, 29.8% WR, -0.030R avg, -1.7R total **[TOXIC]**

**Continuation vs Fade:**
- **Delta WR:** +13.5% (continuation > fade)
- **Delta Avg R:** +0.310R (continuation > fade)
- **Verdict:** **[YES] CONTINUATION EDGE** ✅

**This is the pattern. Asia resolves prior NY high -> London LONG.**

---

### 3. NY_LOW (Asia resolved prior NY low only)

**Overall:** 98 trades, 32.7% WR, +0.040R avg, +3.9R total
- **Delta vs baseline:** -3.4% WR, -0.070R (WORSE than baseline)

**By Direction:**
- **DOWN (continuation)**: 52 trades, 28.8% WR, -0.058R avg, -3.0R total **[FAILS]**
- **UP (fade)**: 46 trades, 37.0% WR, +0.150R avg, +6.9R total **[REVERSAL??]**

**Continuation vs Fade:**
- **Delta WR:** -8.1% (fade > continuation ??)
- **Delta Avg R:** -0.208R (fade > continuation ??)
- **Verdict:** **[WARN] FADE EDGE (unexpected)** ⚠️

**This is BROKEN. Continuation does NOT work for NY_LOW.**

---

## Continuation vs Fade Analysis

| Asia State | Continuation | Cont WR | Cont Avg R | Fade | Fade WR | Fade Avg R | Delta WR | Delta Avg R | Verdict |
|-----------|-------------|---------|------------|------|---------|------------|----------|-------------|---------|
| **NY_HIGH** | UP | 43.3% | +0.281R | DOWN | 29.8% | -0.030R | +13.5% | +0.310R | **[YES] EDGE** |
| **NY_LOW** | DOWN | 28.8% | -0.058R | UP | 37.0% | +0.150R | -8.1% | -0.208R | **[WARN] BROKEN** |

**Key Insight:**
- NY_HIGH continuation = STRONG edge
- NY_LOW continuation = FAILS (reversal instead??)

---

## Resolution Depth Analysis

**Question:** Does depth of sweep matter?

All resolutions were classified as "deep" (>=10 ticks beyond level). No shallow resolutions (<10 ticks) in the dataset with this labeling approach.

**Conclusion:** Depth analysis not conclusive with current data. May need finer bins.

---

## KEY FINDINGS

### ✅ CONFIRMED PATTERNS

1. **Asia resolved prior NY HIGH -> London LONG**
   - 90 trades, 43.3% WR, +0.281R avg
   - +13.5% WR vs fade
   - +0.310R avg vs fade
   - **This is the edge.**

2. **Asia resolved prior NY HIGH -> AVOID London SHORT**
   - 57 trades, 29.8% WR, -0.030R avg
   - **Toxic pattern - DO NOT FADE**

### ❌ BROKEN PATTERNS

3. **Asia resolved prior NY LOW -> London DOWN FAILS**
   - 52 trades, 28.8% WR, -0.058R avg (LOSES money)
   - Expected continuation does NOT work
   - **Do NOT trade London DOWN after Asia sweeps NY low**

### ⚠️ UNEXPECTED PATTERNS

4. **Asia resolved prior NY LOW -> London UP (reversal?)**
   - 46 trades, 37.0% WR, +0.150R avg, +6.9R total
   - Fade outperforms continuation
   - **Requires investigation - why does reversal work here?**

---

## WHY IS NY_LOW BROKEN?

**Hypothesis 1: Liquidity asymmetry**
- Sweeping highs vs lows may have different market structure
- Longs trapped above -> harder to continue down?
- Shorts trapped below -> easier to squeeze up?

**Hypothesis 2: Session timing**
- NY_LOW might resolve at different times than NY_HIGH
- Late Asia resolution vs early resolution - different outcomes?

**Hypothesis 3: Depth/quality of resolution**
- Maybe NY_LOW resolutions are shallower (tags only)
- NY_HIGH resolutions might be deeper (acceptance)

**Hypothesis 4: Sample size**
- NY_LOW only has 98 trades (vs 147 for NY_HIGH)
- Could be noise / insufficient data

**NEEDS FURTHER TESTING:**
1. Split by resolution timing (early vs late Asia)
2. Split by resolution depth (shallow vs deep)
3. Check if NY_LOW + other conditions fixes it

---

## RECOMMENDED TRADING RULES (Preliminary)

### Rule 1: NY_HIGH -> London LONG (STRONG EDGE)

**Condition:**
- Asia swept prior NY session high (from previous day)
- Asia did NOT sweep prior NY low (or it's a BOTH_NY case)

**Action:**
- ONLY trade London UP breaks
- Skip London DOWN breaks (toxic)

**Expected:**
- 43.3% WR
- +0.281R avg
- Sample: 90 trades

**Confidence: HIGH** ✅

### Rule 2: NY_LOW -> SKIP LONDON (BROKEN)

**Condition:**
- Asia swept prior NY session low (from previous day)
- Asia did NOT sweep prior NY high

**Action:**
- **SKIP London entirely** (both directions broken or unclear)
- Continuation DOWN = -0.058R (loses)
- Reversal UP = +0.150R (works but counterintuitive)

**Confidence: SKIP until investigated** ⚠️

### Rule 3: BOTH_NY -> Baseline

**Condition:**
- Asia swept BOTH prior NY high and low

**Action:**
- Trade London normally (no directional edge)
- 36.2% WR, +0.107R avg (same as baseline)

**Confidence: NEUTRAL**

---

## NEXT TESTS (Priority Order)

### TEST 1: Resolution Timing (Early vs Late Asia) **[HIGH PRIORITY]**

**Question:** Does the TIME of resolution matter?

**Labels:**
- **Early resolution**: Prior inventory swept during 09:00-10:00
- **Late resolution**: Prior inventory swept during 10:00-11:00

**Hypothesis:**
- Late resolution (closer to London) = stronger continuation
- Early resolution = weaker signal by London open

**Why this matters:**
- Could explain NY_LOW failure (if it resolves early)
- Could strengthen NY_HIGH edge (if late resolution even better)

---

### TEST 2: Resolution Quality/Depth **[MEDIUM PRIORITY]**

**Question:** Does HOW FAR Asia goes beyond the level matter?

**Labels:**
- **Shallow**: Sweeps level by < 5 ticks (tag only)
- **Medium**: 5-15 ticks beyond
- **Deep**: > 15 ticks beyond (strong acceptance)

**Hypothesis:**
- Deep resolutions = stronger London continuation
- Shallow resolutions = false breaks, reversal risk

**Why this matters:**
- Could filter out weak NY_LOW resolutions
- Could strengthen NY_HIGH edge

---

### TEST 3: Prior LONDON vs Prior NY **[LOW PRIORITY - Insufficient Data]**

**Current status:**
- No LONDON_HIGH or LONDON_LOW labels appeared with >20 trades
- Asia almost always resolves NY inventory, not London inventory

**Conclusion:**
- Prior NY dominates (as hypothesized)
- Prior London may not matter much (too far back)
- **Skip this test for now**

---

### TEST 4: NY_LOW Reversal Investigation **[MEDIUM PRIORITY]**

**Question:** Why does NY_LOW -> London UP work better than continuation?

**Investigate:**
1. Is it a liquidity squeeze? (shorts trapped)
2. Is it session-specific? (London reverses Asia lows)
3. Is it related to ORB size? (small ORB = reversal)
4. Is it just noise? (98 trades, could be luck)

**Approach:**
- Break down NY_LOW -> London UP by:
  - ORB size (small vs large)
  - Asia travel (how far past NY low)
  - Time of resolution (early vs late)

---

## IMPLEMENTATION NOTES

### Data Required for Live Trading:

1. **Prior NY high/low**: From PREVIOUS trading day
   - NY 2300 ORB high/low
   - NY 0030 ORB high/low
   - Take max(2300_high, 0030_high) and min(2300_low, 0030_low)

2. **Asia session high/low**: From CURRENT trading day
   - Measure at 11:00 (end of Asia session)
   - Check: Did asia_high >= prior_ny_high?
   - Check: Did asia_low <= prior_ny_low?

3. **Classify state**:
   - If both: BOTH_NY -> no filter
   - If high only: NY_HIGH -> London LONG only
   - If low only: NY_LOW -> **SKIP London**
   - If neither: FAILED -> no filter

### Code Checklist:

- [ ] Add prior_ny_high/low calculation to daily_features_v2
- [ ] Add asia_resolved_state column (NY_HIGH, NY_LOW, BOTH_NY, FAILED)
- [ ] Create London direction filter based on state
- [ ] Backtest with filters applied
- [ ] Validate expected +0.310R edge for NY_HIGH continuation

---

## HONEST ASSESSMENT

### What We Know (HIGH CONFIDENCE):

1. **Asia resolves prior NY high -> London LONG works** (+0.281R avg, 43.3% WR)
2. **Asia resolves prior NY high -> London SHORT fails** (-0.030R avg, 29.8% WR)
3. **Prior NY inventory matters more than prior London** (no London-only patterns found)

### What We DON'T Know (NEEDS TESTING):

1. **Why does NY_LOW continuation fail?** (-0.058R avg)
2. **Why does NY_LOW reversal work?** (+0.150R avg fade)
3. **Does resolution timing matter?** (early vs late Asia)
4. **Does resolution depth matter?** (shallow vs deep sweep)

### Risks:

1. **In-sample optimization**: These rules came from looking at outcomes
2. **Small samples**: NY_LOW only 98 trades, NY_HIGH 147 trades
3. **Asymmetric pattern**: Only one direction works (suspicious?)
4. **Unexplained reversal**: NY_LOW fade edge needs explanation

### Recommendation:

**PHASE 1: Implement NY_HIGH -> London LONG filter ONLY**
- Clear edge: +0.310R vs fade
- Logical: Continuation makes sense
- Sample: 90 trades (adequate)
- **Paper trade this first**

**PHASE 2: Investigate NY_LOW**
- Run timing/depth tests
- Understand reversal pattern
- Only implement if explanation makes sense
- **Do NOT trade until understood**

**PHASE 3: Refine with timing/depth**
- Add early vs late resolution
- Add shallow vs deep resolution
- Improve edge from +0.281R to potentially higher

---

## CONCLUSION

**Engine A validation: PARTIAL SUCCESS**

✅ **Confirmed:** Prior NY inventory resolution matters to London
✅ **Confirmed:** NY_HIGH -> London LONG is a real edge (+0.310R vs fade)
❌ **Broken:** NY_LOW continuation does not work as expected
⚠️ **Unexpected:** NY_LOW reversal works (needs investigation)

**Next Step:** Run TEST 1 (resolution timing) to understand why NY_LOW fails.

---

## REFERENCES

- Test script: `test_london_prior_inventory.py`
- Framework doc: `ASIA_LONDON_FRAMEWORK.md`
- Data source: `daily_features_v2`, `orb_trades_5m_exec_orbr`
- Sample size: 502 London ORB trades, 2020-2026
