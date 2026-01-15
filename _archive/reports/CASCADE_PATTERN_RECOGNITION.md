# CASCADE PATTERN RECOGNITION - COMPLETE MECHANICS

**Date**: 2026-01-13
**Status**: Pattern fully mapped through systematic testing

---

## Executive Summary

Multi-liquidity cascades are **forced liquidation events** triggered by sequential sweeps of full-session liquidity pools that fail to hold. Edge requires precise timing (23:00), full session levels (8hr+ Asia, 5hr London), and acceptance failure confirmation.

**Core Edge**: +1.95R average, 9.3% frequency, 19-27% win rate
**Critical Multiplier**: Gap size >9.5pts = +5.36R vs ≤9.5pts = +0.36R (15× difference)

---

## What Makes Cascades Work (6 Mandatory Conditions)

### 1. Full Session Liquidity Pools (MANDATORY)

✅ **WORKS**: Asia (8hr: 09:00-17:00) + London (5hr: 18:00-23:00)
❌ **FAILS**: NY overnight (3hr: 23:00-02:00) → Asia
❌ **FAILS**: London → Next day Asia (overnight gap breaks chain)

**Rule**: Sessions must be ≥5 hours for sufficient positioning to accumulate.

**Test Results**:
- Asia → London → NY: +1.95R SHORT, +1.00R LONG ✅
- NY overnight → Asia: -0.01R SHORT, -0.04R LONG ❌
- London → Next Asia: -0.66R SHORT, -0.47R LONG ❌

**Why Full Sessions Matter**:
- Short sessions (3hr NY overnight) = normal price discovery, not forced positioning
- Overnight gaps break positioning chain (participants can adjust)
- Long sessions (8hr Asia) = participants trapped in stops, must liquidate

---

### 2. Sequential Multi-Level Sweeps (MANDATORY)

✅ **WORKS**: Asia high → London sweeps it → NY sweeps London high
❌ **FAILS**: Single level (London high only) = weaker edge
❌ **FAILS**: Two levels without third sweep timing = destroys edge

**Rule**: Minimum 2 levels required, but 3rd sweep at 23:00 is critical timing.

**Test Results**:
- Full cascade (Asia → London → NY at 23:00): +1.95R ✅
- Single liquidity reaction (London high only): +1.44R (weaker) ⚠️
- Asia → London early exit (before 23:00): **-1.78R** ❌

**Why Sequential Matters**:
- Each level = trapped participants
- Multiple levels = compounding forced liquidations
- Later participants trapped by earlier participants' stops

---

### 3. Acceptance Failure (MANDATORY)

✅ **WORKS**: Second sweep + close back through level within 3 bars
❌ **FAILS**: Structure only (London swept Asia) without failure confirmation

**Rule**: Close must break back through swept level within 3 bars (3 minutes).

**Test Results**:
- Full cascade (requires failure): +1.95R, 9.3% frequency ✅
- Structure only (no failure required): +0.94R, 62.9% frequency ❌

**Why Failure Matters**:
- Confirms participants are **trapped** (not just positioning adjustment)
- Cuts frequency 6.8× (from 63% to 9%) = selectivity filter
- **DOUBLES the edge** (from +0.94R to +1.95R)
- **Flips gap size predictor** from negative to positive

**Without failure confirmation**:
- Gap size relationship REVERSES (small > large)
- Edge exists (+0.94R) but is 50% weaker
- Too frequent (63% of days) = low selectivity

---

### 4. 23:00 Timing (CRITICAL)

✅ **WORKS**: Entry at 23:00 NY futures open (70% of cascades)
❌ **FAILS**: Early exit before 23:00 = -1.78R

**Rule**: Must wait for 23:00 third sweep window. Early exit destroys edge.

**Test Results**:
- Full cascade (waits for 23:00): +1.95R ✅
- Asia → London early exit (exits at 23:00): **-1.78R** ❌
- **3.73R difference!**

**Why 23:00 Matters**:
- NY futures open = liquidity surge + volatility spike
- During London session, price moves AGAINST you (avg % captured = -464%)
- Real cascade happens AFTER London closes at 23:00
- Median peak: 3-5 minutes after 23:00 entry

**Timing Distribution**:
- 70% of cascades enter at 23:00 (session open cluster)
- 30% enter during 23:01-23:30 window
- Must scan first 30 bars (30 minutes) for setup

---

### 5. Gap Size Multiplier (FORCE PREDICTOR)

✅ **WORKS**: Gap >9.5pts between swept levels
❌ **FAILS**: Gap ≤9.5pts = minimal edge

**Rule**: Gap = distance between swept levels (e.g., London high - Asia high). Larger gap = more trapped leverage.

**Test Results**:
- Large gap (>9.5pts): **+5.36R** average, 43% frequency ✅
- Small gap (≤9.5pts): +0.36R average, 57% frequency ⚠️
- **15× difference in payoff**

**Why Gap Size Matters**:
- Gap = trapped participant density
- Larger gap = more stops accumulated between levels
- Forced liquidations compound as price cascades through stops
- Small gaps = participants can adjust, no forced moves

**Gap Size Distribution**:
- Median gap: 9.5 points
- Use >median as large gap threshold
- Gap size only predictive AFTER acceptance failure confirmed

---

### 6. Entry at Swept Level (PRECISION)

✅ **WORKS**: Entry within ±0.1pts of swept level (after failure confirmed)
❌ **FAILS**: Random entry without level alignment

**Rule**: Wait for retrace to swept level after acceptance failure, enter within 1 tick (0.1pts).

**Entry Logic**:
1. Second sweep confirmed (close above/below level)
2. Acceptance failure within 3 bars (close back through)
3. Wait for retrace to level (wicks touching within 0.1pts)
4. Enter SHORT at level (if swept upside) or LONG at level (if swept downside)

**Stop Placement**:
- SHORT: Stop = sweep high (the peak of second sweep)
- LONG: Stop = sweep low (the bottom of second sweep)
- Risk = distance from entry to stop

---

## Pattern Recognition Rules Summary

### Entry Checklist (ALL must be true):

1. ✅ **Full session levels**: Asia (8hr) + London (5hr) both complete
2. ✅ **First sweep**: London high > Asia high (or London low < Asia low)
3. ✅ **Gap size**: london_high - asia_high > 9.5pts (or asia_low - london_low > 9.5pts)
4. ✅ **Second sweep**: At 23:00 window, close > london_high (or < london_low)
5. ✅ **Acceptance failure**: Within 3 bars, close back < london_high (or > london_low)
6. ✅ **Entry opportunity**: Price retraces to london_high (within 0.1pts)

### Exit Rules:

**Phase 1: Breakeven Protection (first 10 min)**:
- If +1R achieved within 10 minutes, move stop to breakeven (entry price)
- Protects against whipsaw after initial move

**Phase 2: Structure Trail (after 15 min)**:
- Trail stop behind structural pivots:
  - SHORT: Trail behind lower highs (pivot highs that are lower than previous)
  - LONG: Trail behind higher lows (pivot lows that are higher than previous)
- Look back 10 bars to identify pivots

**Time Limit**:
- Max hold: 90 minutes from entry
- Median peak: 3-5 minutes
- Average peak: 13-21 minutes
- Fixed-time exits DESTROY edge (capture only 4-54% of max R)

**Target**:
- First target: Opposite Asia level (full range)
- Cascade target: Entry - Risk (1:1 R) or more depending on displacement

---

## What Destroys Edge (Tested Failures)

### ❌ Time-Based Entries
- ORB breakouts: No edge (-0.10R)
- Fixed-time entries: Timing is price-based (acceptance failure), not clock-based

### ❌ Partial Sessions
- NY overnight (3hr) → Asia: Too short, -0.01R
- London → Next day Asia: Overnight gap breaks chain, -0.66R

### ❌ Early Exits
- Exiting before 23:00: **-1.78R** vs +1.95R (3.73R difference!)
- Fixed-time exits (15min, 30min): Capture only 4-54% of max R
- Must trail structure to capture tail events

### ❌ No Acceptance Failure Filter
- Structure only (London swept Asia): +0.94R vs +1.95R with failure
- Frequency too high (63% vs 9%) = no selectivity
- Gap size relationship reverses without failure

### ❌ Small Gaps
- Gap ≤9.5pts: +0.36R (15× weaker than large gaps)
- Small gaps = minimal trapped positioning

---

## Edge Validation (Systematic Testing)

### Test 1: Single Liquidity Reaction
- **Pattern**: London high sweep → failure → reaction
- **Result**: +1.44R average, 16% frequency, 33.7% win rate
- **Conclusion**: Edge exists but weaker than multi-level

### Test 2: Multi-Liquidity Cascade (Full Pattern)
- **Pattern**: Asia high → London high → NY sweep → failure → cascade
- **Result**: +1.95R average, 9.3% frequency, 19-27% win rate
- **Conclusion**: ✅ PRIMARY EDGE

### Test 3: Bidirectional Validation
- **SHORT** (swept Asia high): +1.95R, 69 setups
- **LONG** (swept Asia low): +1.00R, 37 setups
- **Conclusion**: ✅ Edge valid both directions (structural, not directional bias)

### Test 4: Gap Size Multiplier
- **Large gap** (>9.5pts): +5.36R, 43% of cascades
- **Small gap** (≤9.5pts): +0.36R, 57% of cascades
- **Conclusion**: ✅ Gap size = force multiplier (15× difference)

### Test 5: Timing Analysis
- **Entry timing**: 70% at 23:00 session open
- **Median peak**: 3-5 minutes
- **Average peak**: 13-21 minutes
- **Conclusion**: ✅ 23:00 critical, must hold through tail events

### Test 6: Exit Strategy
- **Structure-based**: Captures 62-71% of max R
- **Fixed 15min**: Captures 4% of max R
- **Fixed 30min**: Captures 18-54% of max R
- **Conclusion**: ✅ Structure-based superior

### Test 7: NY Overnight → Asia
- **Pattern**: NY overnight (3hr) → Asia sweep → failure
- **Result**: -0.01R SHORT, -0.04R LONG, 29% frequency
- **Conclusion**: ❌ FAILED - partial sessions don't work

### Test 8: London → Next Day Asia
- **Pattern**: Previous day London → next day Asia
- **Result**: -0.66R SHORT, -0.47R LONG
- **Conclusion**: ❌ FAILED - overnight gap breaks chain

### Test 9: Asia → London Early Exit
- **Pattern**: Enter during London, exit at 23:00 (no third sweep)
- **Result**: **-1.78R** average (vs +1.95R for full cascade)
- **Conclusion**: ❌ FAILED - 23:00 timing CRITICAL, early exit destroys edge

### Test 10: Structure Only (No Failure)
- **Pattern**: London swept Asia → enter at 23:00 (no second sweep required)
- **Result**: +0.94R average, 62.9% frequency
- **Conclusion**: ❌ WEAKENS EDGE - acceptance failure doubles edge, mandatory filter

---

## Risk and Deployment

### Position Sizing (NON-NEGOTIABLE)
- **Risk per attempt**: 0.10% - 0.25% of capital
- **Max drawdown tested**: -43.4R (43 consecutive losses)
- **Max historical string**: 14 consecutive losses
- **Why small**: Low frequency (9.3%), low win rate (19-27%), tail-based edge

### Expected Performance
- **Frequency**: 2-3 valid setups per month
- **Win rate**: 19-27%
- **Median R**: -1R (most trades lose)
- **Max R observed**: +129R (single trade)
- **Average R**: +1.95R (driven by tail events)

### Mental Model
- **Portfolio-style intraday campaign trader**
- Expect strings of losses (up to 14 consecutive)
- Edge comes from occasional massive payoffs (>10R)
- Not a "high win rate" strategy
- Requires discipline to hold through -1R strings

### Filters Before Entry (All Required)
1. Gap >9.5pts (large gaps only)
2. Acceptance failure within 3 bars (confirmation)
3. 23:00 entry window (timing precision)
4. Entry at level (within 0.1pts)
5. Full session levels (Asia 8hr + London 5hr)
6. Displacement after failure (price moving away from level)

---

## Next Steps

### Deployment Phase
1. ✅ **Build monitoring system**: `monitor_cascade_live.py` (COMPLETE)
2. ✅ **Build exit tracker**: `track_cascade_exits.py` (COMPLETE)
3. ⏭️ **Paper trade**: 20-40 trading days to validate execution
4. ⏭️ **Size validation**: Confirm 0.10-0.25% risk per attempt
5. ⏭️ **Edge decay monitoring**: Quarterly review for edge persistence

### Paper Trading Validation
- Validate entry timing (expect 70% at 23:00)
- Validate gap-size correlation (large > small)
- Validate bidirectional (SHORT and LONG work)
- Practice emotional discipline (holding through -1R strings)
- Measure frequency (expect ~2-3 per month)
- Measure R distribution (expect median -1R, occasional huge R)

### Edge Decay Monitoring
- Track quarterly: frequency, average R, gap-size correlation
- Threshold: If average R drops below +1.0R, re-evaluate
- If frequency increases >15%, edge may be degrading (selectivity loss)
- Gap-size correlation must hold (large > small by 5×+ margin)

---

## Conclusion

Cascades are **forced liquidation events**, not prediction patterns. Edge requires:
- Full session levels (8hr+ positioning)
- Acceptance failure (trapped confirmation)
- 23:00 timing (liquidity surge)
- Gap size >9.5pts (force multiplier)
- Structure-based exits (capture tail)

Remove any one condition → edge degrades or disappears completely.

**This is not discretionary interpretation** - it's a precise mechanical pattern with strict entry rules and testable edge validated across 741 days.
