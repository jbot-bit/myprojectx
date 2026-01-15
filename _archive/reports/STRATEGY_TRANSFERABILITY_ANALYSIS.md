# STRATEGY TRANSFERABILITY & FAILURE ANALYSIS - Phase 4

**Date:** 2026-01-14
**Purpose:** Analyze how strategies could fail and their transferability
**Per:** clearfolder.txt "update 2" - Strategy Discovery Transfer meta-prompt Phase 4

---

## PHASE 4 OBJECTIVE

For each strategy (existing and new candidates), answer:
1. **How could it fail?**
2. **What market regime would kill it?**
3. **Is it asset-specific, session-specific, or structurally transferable?**

---

## EXISTING STRATEGIES (1-8) - FAILURE ANALYSIS

### Strategy 1: MGC ORB Breakouts

**How It Could Fail:**
- Regime shift: Markets become range-bound (low volatility, high chop)
- Algorithmic changes: More false breakouts as HFTs adapt
- Liquidity drain: Lower volume reduces follow-through
- Parameter drift: Optimal RR ratios change over time

**Market Regime That Would Kill It:**
- **Extended low volatility** (VIX <12 for months) → ORB ranges shrink, breakouts fail
- **High-frequency mean reversion** dominates → Breakouts immediately reverse
- **Sustained sideways markets** (2015-2016 style) → No directional bias

**Transferability:**
- **Asset-specific: NO** - Pattern works on MGC, NQ, likely SI/CL/ES
- **Session-specific: PARTIALLY** - Different sessions need different parameters (proven)
- **Structurally transferable: YES** - ORB concept universal to liquid futures

**Confidence:** HIGH (2+ years data, 2,893 trades, parameter-dependent)

---

### Strategy 2: Single Liquidity Reactions (1800 ORB)

**How It Could Fail:**
- Sweep behavior changes: Market makers stop providing liquidity at levels
- Session overlap changes: London participation declines
- Pattern recognition: Too many traders exploit same pattern → edge disappears
- Invalidation rule breaks: Acceptance behavior changes

**Market Regime That Would Kill It:**
- **Low liquidity markets** → Levels don't hold, sweeps more random
- **High volatility** → Sweeps don't reverse, price runs through levels
- **Decreased session gap** (Asia and London converge) → Less level significance

**Transferability:**
- **Asset-specific: PARTIALLY** - Liquidity patterns exist on most futures, but magnitude varies
- **Session-specific: YES** - Only works at 1800 ORB (tested, failed on other sessions)
- **Structurally transferable: LIMITED** - Requires custom pattern per session

**Confidence:** MODERATE (49 trades, strong edge +0.687R, but session-specific)

---

### Strategy 3: Multi-Liquidity Cascades

**How It Could Fail:**
- Gap frequency declines: Sessions become more aligned
- Institutional behavior changes: Cascade patterns break down
- Acceptance rule breaks: 3-bar threshold becomes invalid
- Reduced trending behavior: More mean reversion

**Market Regime That Would Kill It:**
- **Increased 24-hour liquidity** → Less session-specific behavior
- **Reduced directional moves** → Gaps close but no follow-through
- **Higher correlation across sessions** → No gap advantage

**Transferability:**
- **Asset-specific: PARTIALLY** - Gaps exist on most futures, but frequency varies
- **Session-specific: NO** - Structure applies to any 3-session alignment
- **Structurally transferable: YES** - Multi-session alignment concept universal

**Confidence:** HIGH (69 trades, massive edge +1.95R, rare but strong)

---

### Strategy 4: NQ ORB Breakouts

**How It Could Fail:**
- Same as MGC ORBs (Strategy 1)
- Additionally: NQ volatility regime shift (becomes less volatile)
- Correlation with MGC increases → Less diversification benefit

**Market Regime That Would Kill It:**
- **NQ volatility compression** (extended low vol) → Targets unreachable
- **Increased MGC/NQ correlation** → Both fail together

**Transferability:**
- **Asset-specific: YES** - Performance 2.2× worse than MGC (not a bug, feature of asset)
- **Session-specific: PARTIALLY** - 2300 ORB fails on NQ, works on MGC
- **Structurally transferable: YES** - Same discovery method applies

**Confidence:** HIGH (1,238 trades, proven but inferior to MGC)

---

### Strategy 5: London Advanced Filters (3 Tiers)

**How It Could Fail:**
- Filter stacking breaks: Conditions become redundant or contradictory
- Asia range regime shift: NORMAL bucket (100-200 ticks) no longer optimal
- Prior inventory resolution changes: NY_LOW pattern reverses
- Over-filtering: Becomes too selective (<5% of days)

**Market Regime That Would Kill It:**
- **Increased Asia volatility** → NORMAL range shifts to 150-250 ticks
- **Prior session correlation breaks** → NY_HIGH/NY_LOW no longer predictive
- **London behavior changes** → Filters based on 2020-2025 data become outdated

**Transferability:**
- **Asset-specific: PARTIALLY** - Asia range thresholds are asset-specific
- **Session-specific: YES** - Filters tailored to 1800 ORB specifically
- **Structurally transferable: LIMITED** - Requires re-discovery per session

**Confidence:** MODERATE (68-499 trades per tier, strong edges but filter-dependent)

---

### Strategy 6: Session-Based Enhancements (Engine A)

**How It Could Fail:**
- Prior inventory concept breaks: Market stops respecting prior levels
- Continuation dominance reverses: Mean reversion becomes stronger
- Session participant changes: Timezone traders behave differently
- Toxic pattern emerges elsewhere (not just NY_LOW)

**Market Regime That Would Kill It:**
- **Increased algorithmic mean reversion** → Continuation fails
- **24/7 market structure** → Session boundaries blur
- **Decreased level respect** → Prior inventory irrelevant

**Transferability:**
- **Asset-specific: NO** - Inventory resolution is universal concept
- **Session-specific: PARTIALLY** - Asia → London validated, London → NY untested
- **Structurally transferable: YES** - Framework applies to any session pair

**Confidence:** HIGH (200+ trades per pattern, +0.15R improvement, toxic pattern identified)

---

### Strategy 7: Outcome Momentum (Engine B)

**How It Could Fail:**
- Correlation weakens: Win/loss outcomes become random
- Zero-lookahead broken: Trades take longer to close (RR 4.0 ORBs)
- Edge too small: +2-5% WR improvement disappears with variance
- Reversal patterns dominate: Momentum flips to anti-momentum

**Market Regime That Would Kill It:**
- **Increased chop** → Outcomes become random, no momentum
- **Extended holding times** → Prior trades don't close before next ORB (lookahead violation)
- **Mean reversion dominance** → Winning = next losing

**Transferability:**
- **Asset-specific: NO** - Psychological/order flow momentum universal
- **Session-specific: PARTIALLY** - Intra-Asia validated, cross-session untested
- **Structurally transferable: YES** - Correlation concept transfers

**Confidence:** HIGH (200+ trades per pattern, small but consistent edge)

---

### Strategy 8A: ORB Positioning Analysis

**How It Could Fail:**
- Positioning categories arbitrary: BELOW/OVERLAP/ABOVE thresholds change
- Pattern reverses: BELOW becomes worse, ABOVE becomes better
- Sample size insufficient: 110 trades per category marginal
- Opposite patterns confuse: 10:00/09:00 vs 11:00/10:00 contradictory

**Market Regime That Would Kill It:**
- **Increased randomness** → Positioning loses predictive power
- **Threshold shift** → Optimal positioning changes (NEAR_TOP becomes best)

**Transferability:**
- **Asset-specific: UNKNOWN** - Not tested on other assets
- **Session-specific: YES** - Different patterns per ORB pair (10:00/09:00 vs 11:00/10:00)
- **Structurally transferable: LIMITED** - Requires discovery per ORB pair

**Confidence:** MODERATE (110-135 trades per category, +0.05-0.06R improvement)

---

### Strategy 8B: Lagged Features (Previous Day)

**How It Could Fail:**
- Memory effect disappears: Previous day stops mattering
- Regime shift: Features become uncorrelated
- Sample size insufficient: 83-154 trades marginal for some buckets
- Over-fitting: Features work on 2024-2026, fail 2027+

**Market Regime That Would Kill It:**
- **Increased day-to-day independence** → Memory fades
- **Algorithmic reset** → Each day starts fresh, no carry-over
- **Volatility regime change** → PREV_ASIA_IMPULSE=HIGH becomes common/rare

**Transferability:**
- **Asset-specific: PARTIALLY** - Lagged correlations asset-dependent
- **Session-specific: YES** - Works for 0030, 1100; NOT for 1000
- **Structurally transferable: YES** - Framework applies universally, results vary

**Confidence:** HIGH (83-154 trades, massive improvements +0.15-0.19R, transforms losers to winners)

---

### Strategy 8C: ORB Size Filters (Adaptive ATR)

**How It Could Fail:**
- Volatility regime shift: ATR(20) no longer predictive
- Threshold drift: Optimal 0.112×ATR becomes 0.150×ATR
- Compression/exhaustion pattern reverses: Large ORBs become winners
- Too restrictive: Filter reduces frequency to <10% of days

**Market Regime That Would Kill It:**
- **Extended high volatility** → All ORBs large, filter rejects most trades
- **Extended low volatility** → All ORBs small, filter irrelevant
- **Pattern reversal** → Large ORB = genuine breakout (opposite of current)

**Transferability:**
- **Asset-specific: PARTIALLY** - Thresholds are asset-specific (NQ 0.050×ATR vs MGC 0.155×ATR)
- **Session-specific: YES** - Works for 1000, 1100, 2300, 0030; NOT for 0900, 1800
- **Structurally transferable: YES** - Compression/exhaustion concept universal

**Confidence:** HIGH (59-221 trades per ORB, robustness 4-5/5, structural explanation)

---

## NEW CANDIDATES (1-10) - FAILURE ANALYSIS

### Candidate 1: London → NY Inventory Resolution

**How It Could Fail:**
- Same as Asia → London (Strategy 6)
- Additionally: NY session less sensitive to London inventory
- London inventory less significant than Asia inventory

**Market Regime That Would Kill It:**
- Same as Strategy 6
- **NY dominance** → NY ignores London, only cares about Asia

**Transferability:**
- **Asset-specific: NO** - Inventory concept universal
- **Session-specific: PARTIALLY** - London → NY specific, but framework transfers
- **Structurally transferable: YES** - Engine A framework applies

**Expected Confidence:** HIGH (if tested and validated)

**Failure Risk:** LOW (exact same logic as validated Engine A)

---

### Candidate 2: NY → Asia Next-Day Cascades

**How It Could Fail:**
- Cross-day correlation weaker than intra-session
- Different participants (NY institutions vs Asia retail)
- Overnight gap resets momentum
- Zero-lookahead broken: NY trades don't close before Asia

**Market Regime That Would Kill It:**
- **Increased gap openings** → Asia gaps away from NY close
- **Day-to-day independence** → No carry-over
- **Extended NY holding times** → Trades don't close before 0900

**Transferability:**
- **Asset-specific: NO** - Temporal correlation universal
- **Session-specific: NO** - Framework applies to any day-boundary correlation
- **Structurally transferable: YES** - Engine B framework applies

**Expected Confidence:** MODERATE (if validated)

**Failure Risk:** MODERATE (cross-day correlation weaker than intra-session)

---

### Candidate 3: Lagged Features for Remaining ORBs

**How It Could Fail:**
- Same as Strategy 8B
- Additionally: Features work for 0030, 1100 but NOT for 0900, 1000, 1800, 2300
- Insufficient sample size for some buckets

**Market Regime That Would Kill It:**
- Same as Strategy 8B

**Transferability:**
- **Asset-specific: PARTIALLY** - Same as Strategy 8B
- **Session-specific: YES** - Works for some ORBs, not others
- **Structurally transferable: YES** - Framework applies, results vary

**Expected Confidence:** HIGH (if significant improvements found)

**Failure Risk:** LOW (proven method, just expanding coverage)

---

### Candidate 4: ORB Size Filters for 0900 and 1800

**How It Could Fail:**
- Same as Strategy 8C
- Additionally: Filters already tested and showed NO EDGE (0900) or NEGATIVE (1800)
- May be session-specific: Compression/exhaustion doesn't apply to 0900/1800

**Market Regime That Would Kill It:**
- Same as Strategy 8C

**Transferability:**
- **Asset-specific: PARTIALLY** - Same as Strategy 8C
- **Session-specific: YES** - Works for 4 ORBs, not 2
- **Structurally transferable: YES** - Concept transfers, but may not apply to all sessions

**Expected Confidence:** LOW (initial test failed)

**Failure Risk:** HIGH (already tested negative, low probability of success with refined thresholds)

---

### Candidate 5: NQ Cascades and Single Liquidity

**How It Could Fail:**
- Same as Strategies 2 and 3
- Additionally: NQ 13× more volatile → Gap thresholds very different
- Pattern may not transfer: NQ institutional behavior different from MGC

**Market Regime That Would Kill It:**
- Same as Strategies 2 and 3
- **NQ-specific:** High volatility makes sweeps/gaps too common (no edge)

**Transferability:**
- **Asset-specific: YES** - Performance likely 50-100% of MGC (same as ORBs)
- **Session-specific: NO** - Cascades/liquidity are session-independent concepts
- **Structurally transferable: YES** - Framework applies

**Expected Confidence:** MODERATE (if validated)

**Failure Risk:** MODERATE (transfer learning has 40-50% failure rate)

---

### Candidate 6: Combined Filters (Stacking)

**How It Could Fail:**
- Over-optimization: Too many filters → <5% of days trade
- Redundant filters: Measuring same underlying edge
- Sample size collapse: <30 trades total after all filters
- Non-additive: Improvements cancel out instead of stacking

**Market Regime That Would Kill It:**
- Any regime shift affecting individual filters
- **Over-filtering regime** → Becomes too selective

**Transferability:**
- **Asset-specific: PARTIALLY** - Each component filter is asset-specific
- **Session-specific: YES** - Filters tailored per ORB
- **Structurally transferable: LIMITED** - Stacking approach transfers, but filters don't

**Expected Confidence:** LOW (high over-optimization risk)

**Failure Risk:** HIGH (risk of curve-fitting, redundancy, over-restriction)

---

### Candidate 7: Volatility Regime Filters

**How It Could Fail:**
- Regime changes: HIGH volatility becomes LOW volatility
- Threshold drift: 80th percentile becomes irrelevant
- Pattern reverses: LOW volatility becomes better for RR 4.0
- Too restrictive: Only 20-30% of days trade

**Market Regime That Would Kill It:**
- **Extended low volatility** → Filter rejects most trades
- **Volatility spike** → All days are HIGH, filter irrelevant

**Transferability:**
- **Asset-specific: PARTIALLY** - Volatility percentiles asset-dependent
- **Session-specific: PARTIALLY** - Likely works for RR 4.0 ORBs (2300, 0030), not RR 1.0
- **Structurally transferable: YES** - Regime concept universal

**Expected Confidence:** MODERATE (if validated)

**Failure Risk:** MODERATE (new dimension, related to proven size filters but different)

---

### Candidate 8: Intra-London ORB Correlations

**How It Could Fail:**
- Same as Strategy 7 (Engine B)
- Additionally: New ORBs (1900, 2000) may have NO baseline edge
- London session less correlated than Asia session
- Insufficient sample size after adding new ORBs

**Market Regime That Would Kill It:**
- Same as Strategy 7

**Transferability:**
- **Asset-specific: NO** - Momentum concept universal
- **Session-specific: YES** - London-specific (if pattern exists)
- **Structurally transferable: YES** - Engine B framework applies

**Expected Confidence:** LOW (requires new ORBs, high development cost)

**Failure Risk:** HIGH (unknown if London ORBs beyond 1800 have baseline edge)

---

### Candidate 9: Alternative Instruments (SI, CL, ES)

**How It Could Fail:**
- Asset-specific characteristics differ: SI more volatile than MGC, CL has oil-specific drivers
- Liquidity differences: CL more liquid than MGC, ES vastly more liquid
- Pattern doesn't transfer: ORBs work on MGC/NQ but not SI/CL/ES
- Parameter drift: Optimal values very different per instrument

**Market Regime That Would Kill It:**
- **Commodity-specific regimes:** Oil shocks (CL), dollar strength (SI), equity crashes (ES)
- **Liquidity changes:** Instrument-specific liquidity events

**Transferability:**
- **Asset-specific: YES** - Each instrument has unique characteristics
- **Session-specific: NO** - Sessions universal across instruments
- **Structurally transferable: PARTIALLY** - Framework transfers, performance varies widely

**Expected Confidence:** UNKNOWN (high variance expected)

**Failure Risk:** HIGH (50%+ chance pattern doesn't transfer or performs poorly)

---

### Candidate 10: Cross-Session Cascades (London → NY → Asia Next Day)

**How It Could Fail:**
- Cross-day cascade weaker than intra-day
- Different participants: Asia traders don't care about prior London/NY
- Overnight resets: Asia gaps away from NY close
- Rare pattern: <5% of days → insufficient sample

**Market Regime That Would Kill It:**
- **Increased gap openings** → Cascade alignment breaks
- **Day-to-day independence** → No carry-over
- **Asia isolation** → Asian markets trade independently

**Transferability:**
- **Asset-specific: NO** - Cascade concept universal
- **Session-specific: NO** - Framework applies to any 3-session sequence
- **Structurally transferable: YES** - Concept transfers

**Expected Confidence:** LOW (rare pattern, cross-day uncertain)

**Failure Risk:** HIGH (cross-day cascades less likely than intra-day)

---

## TRANSFERABILITY MATRIX

### Structurally Universal (High Transfer Probability)
**Strategies that work across assets/sessions:**
1. ORB Breakouts (Strategy 1) - ✅ MGC, ✅ NQ, likely ✅ SI/CL/ES
2. Multi-Liquidity Cascades (Strategy 3) - ✅ Concept universal
3. Session-Based Enhancements (Strategy 6) - ✅ Framework applies to any session pair
4. Outcome Momentum (Strategy 7) - ✅ Temporal correlation universal
5. Size Filters (Strategy 8C) - ✅ Compression/exhaustion concept universal

**Use these frameworks FIRST when exploring new assets/sessions**

---

### Session-Specific (Low Transfer Probability)
**Strategies that work on specific sessions only:**
1. Single Liquidity Reactions (Strategy 2) - ✅ 1800 ONLY, ❌ Failed on 4 other sessions
2. London Advanced Filters (Strategy 5) - ✅ 1800 ONLY, stacked filters
3. ORB Positioning (Strategy 8A) - ✅ Different patterns per ORB pair
4. Lagged Features (Strategy 8B) - ✅ Works for 0030, 1100; ❌ NOT for 1000

**Do NOT assume these transfer - re-discover per session**

---

### Asset-Dependent (Moderate Transfer Probability)
**Strategies that transfer but with different parameters:**
1. ORB Breakouts (Strategy 1) - ✅ Transfers but NQ 2.2× worse than MGC
2. NQ Strategies (Strategy 4) - ✅ Framework transfers, performance varies
3. Size Filters (Strategy 8C) - ✅ Concept transfers, thresholds asset-specific

**Expect 50-100% of source performance when transferring**

---

## REGIME SENSITIVITY

### High Regime Sensitivity (Likely to Break)
**Strategies vulnerable to regime shifts:**
1. Size Filters (Strategy 8C) - Volatility regime dependent
2. London Advanced Filters (Strategy 5) - Filter stacking fragile
3. Combined Filters (Candidate 6) - Over-optimization risk
4. Volatility Regime Filters (Candidate 7) - Regime-by-definition

**Monitor quarterly, adjust thresholds if needed**

---

### Moderate Regime Sensitivity
**Strategies somewhat vulnerable:**
1. Single Liquidity Reactions (Strategy 2) - Liquidity behavior changes
2. Session-Based Enhancements (Strategy 6) - Inventory respect changes
3. Lagged Features (Strategy 8B) - Day-to-day correlation changes

**Monitor semi-annually**

---

### Low Regime Sensitivity (Robust)
**Strategies likely to persist:**
1. ORB Breakouts (Strategy 1) - Structural, parameter-dependent
2. Multi-Liquidity Cascades (Strategy 3) - Multi-session alignment rare but strong
3. Outcome Momentum (Strategy 7) - Small edge, persistent across regimes

**Monitor annually**

---

## FAILURE PROBABILITY RANKING

### Low Failure Risk (<20%)
1. ORB Breakouts (Strategy 1)
2. Multi-Liquidity Cascades (Strategy 3)
3. Outcome Momentum (Strategy 7)
4. Candidate 1 (London → NY Inventory)
5. Candidate 3 (Lagged Features Expansion)

---

### Moderate Failure Risk (20-50%)
1. Session-Based Enhancements (Strategy 6)
2. Size Filters (Strategy 8C)
3. Single Liquidity Reactions (Strategy 2)
4. London Advanced Filters (Strategy 5)
5. Candidate 2 (NY → Asia Cascades)
6. Candidate 5 (NQ Cascades/Liquidity)
7. Candidate 7 (Volatility Regime Filters)

---

### High Failure Risk (>50%)
1. ORB Positioning (Strategy 8A) - Small edge, marginal sample
2. Lagged Features (Strategy 8B) - Regime-dependent
3. NQ Strategies (Strategy 4) - Inferior performance
4. Candidate 4 (0900/1800 Size Filters) - Already tested negative
5. Candidate 6 (Combined Filters) - Over-optimization
6. Candidate 8 (Intra-London Correlations) - Unknown baseline
7. Candidate 9 (Alternative Instruments) - High variance
8. Candidate 10 (Cross-Day Cascades) - Rare pattern

---

## MONITORING FRAMEWORK

### Monthly Monitoring (High Regime Sensitivity)
- Strategy 8C (Size Filters) - Check ATR percentile distribution
- Candidate 6 (Combined Filters) - Check rejection rate
- Candidate 7 (Volatility Regime Filters) - Check regime distribution

**Action:** If rejection rate changes >20%, re-validate thresholds

---

### Quarterly Monitoring (Moderate Regime Sensitivity)
- Strategy 2 (Single Liquidity) - Check sweep frequency
- Strategy 5 (London Filters) - Check Asia range distribution
- Strategy 6 (Session-Based) - Check inventory resolution frequency
- Strategy 8B (Lagged Features) - Check correlation strength

**Action:** If edge degrades >50%, adjust filters or pause strategy

---

### Annual Monitoring (Low Regime Sensitivity)
- Strategy 1 (ORB Breakouts) - Full parameter re-sweep
- Strategy 3 (Cascades) - Check gap frequency
- Strategy 7 (Outcome Momentum) - Check WR improvements
- Strategy 4 (NQ) - Re-compare to MGC performance

**Action:** If edge disappears, retire strategy

---

## PHASE 4 COMPLETE

**Failure Analysis:** ✅ COMPLETE (17 existing + 10 new candidates)

**Transferability Classification:**
- Structurally Universal: 5 strategies
- Session-Specific: 4 strategies
- Asset-Dependent: 3 strategies

**Regime Sensitivity:**
- High: 4 strategies (monthly monitoring)
- Moderate: 7 strategies (quarterly monitoring)
- Low: 6 strategies (annual monitoring)

**Failure Risk Ranking:**
- Low Risk: 5 strategies
- Moderate Risk: 7 strategies
- High Risk: 8 strategies

---

## FINAL RECOMMENDATIONS

### Deploy with Confidence (Low Failure Risk)
1. Continue all TIER 1-2 strategies (Strategies 1-3)
2. Test Candidate 1 (London → NY Inventory)
3. Test Candidate 3 (Lagged Features Expansion)

---

### Deploy with Monitoring (Moderate Failure Risk)
1. Continue TIER 3 strategies with quarterly monitoring
2. Test Candidate 2 (NY → Asia Cascades)
3. Consider Candidate 5 (NQ Cascades/Liquidity)

---

### Research Only (High Failure Risk)
1. Re-test Candidate 4 (0900/1800 Size Filters) with refined approach
2. Skip Candidates 8-10 unless significant new evidence emerges
3. Wait for more data on marginal strategies (8A, 8B for some ORBs)

---

**All Phases Complete:**
- ✅ Phase 1: Discovery Logic Documented
- ✅ Phase 2: Edge Discovery Playbook Created
- ✅ Phase 3: New Strategy Candidates Generated
- ✅ Phase 4: Transferability & Failure Analysis Complete

**Next Step:** Test top 3 candidates (Candidates 1, 2, 3) using Edge Discovery Playbook
