# STRATEGY DISCOVERY LOGIC - Phase 1

**Date:** 2026-01-14
**Purpose:** Reverse-engineer HOW existing strategies were discovered (not WHAT the rules are)
**Per:** clearfolder.txt "update 2" - Strategy Discovery Transfer meta-prompt

---

## CRITICAL DISTINCTION

This document explains **THE DISCOVERY PROCESS**, not the strategy rules.

**Question answered:** "HOW was this edge found?"
**NOT:** "What are the entry/exit rules?"

---

## DISCOVERY FRAMEWORK ELEMENTS

For each strategy, we reconstruct:

1. **Initial Observation** - What market condition was noticed first?
2. **Constraint Applied** - What rule turned randomness into edge?
3. **Held Constant** - What variables were frozen during search?
4. **Allowed to Vary** - What dimension was explored?
5. **Measured Before Trade** - What was quantified upfront?
6. **Not Measured (Assumed)** - What was implicitly believed?
7. **Validation Method** - How were false positives rejected?
8. **Survivorship Filter** - What killed most candidates?

---

## STRATEGY 1: MGC ORB BREAKOUTS (6 ORBs)

### How This Edge Was Discovered

**Initial Observation:**
- Opening ranges create structural breakout patterns (known trading concept)
- Question: "Do all 6 sessions work the same way?"

**Discovery Method:**
- **Exhaustive parameter sweep** - 252 configurations tested
- Variables: 7 RR ratios (1.0-4.0) × 2 SL modes (HALF/FULL) × 3 filter sets × 6 ORBs
- Held constant: 5-minute ORB window duration, entry confirmation method
- Allowed to vary: RR ratio, stop placement mode, per-session

**Constraint That Created Edge:**
- Different sessions require different RR/SL combinations
- Discovery: Night sessions (2300, 0030) work at RR 4.0 HALF SL
- Discovery: Day sessions (0900, 1000, 1100) work at RR 1.0-3.0 FULL SL
- Discovery: Session transition (1800) works at RR 1.0 HALF SL

**What Was Measured:**
- Win rate, Avg R, Total R for each configuration
- Date-matched baseline for each session
- Data integrity (bar completeness, timezone alignment)

**What Was NOT Measured (Assumed):**
- Entry slippage (assumed 1-2 ticks)
- Real-world execution delays (assumed perfect fills)
- Psychological factors (ignored)

**Validation Method:**
- Compare all 252 configs, select optimal per ORB
- Data integrity audit (6 tests, all passed)
- Baseline comparison (conditional vs unconditional)

**Survivorship Filter:**
- Configurations with negative Total R rejected
- Configurations with <30 trades rejected
- Sessions with inconsistent results across time periods rejected

**Key Insight:**
- **The edge is NOT "ORBs work"** - the edge is "ORBs work DIFFERENTLY per session"
- Parameter-dependency discovered through systematic sweep, not theory

---

## STRATEGY 2: SINGLE LIQUIDITY REACTIONS (1800 ORB)

### How This Edge Was Discovered

**Initial Observation:**
- London session high/low levels get swept at NY open (1800 ORB)
- Price often reverses immediately after sweep

**Discovery Method:**
- **Custom pattern definition** - NOT a parameter sweep
- Observation → hypothesis → test → refine
- Initially tested "unified framework" (3 generic patterns) → FAILED on most sessions
- Switched to session-specific custom patterns → SUCCESS at 1800

**Constraint That Created Edge:**
- Liquidity sweep + immediate reversal within N minutes
- Invalidation rule: If acceptance occurs (3 bars beyond level), pattern fails
- Entry confirmation: Wait for reversal bar close

**What Was Measured:**
- Sweep occurrence frequency
- Reversal success rate after sweep
- Time to reversal (N minutes)
- Acceptance failure rate

**What Was NOT Measured (Assumed):**
- Why liquidity sweeps occur (order flow assumptions)
- Market maker behavior (implicitly assumed liquidity provision)
- Volume at sweep (not available in 5m bar data)

**Validation Method:**
- Test on 1800 ORB → +0.687R on 49 trades (VALIDATED)
- Test unified framework on other sessions (0900, 1000, 1100, 0030) → NO EDGE
- Temporal stability: 3/3 time chunks positive
- Date-matched baseline comparison

**Survivorship Filter:**
- Generic patterns killed by applying to all sessions (failed 4 out of 5)
- Only session-specific custom pattern survived
- Rare pattern (triggers <10% of days) but strong edge when present

**Key Insight:**
- **Liquidity patterns are SESSION-SPECIFIC**, not universal
- Generic rules fail; custom observation per session succeeds
- "If it works everywhere, it works nowhere" - session-specificity IS the edge

---

## STRATEGY 3: MULTI-LIQUIDITY CASCADES

### How This Edge Was Discovered

**Initial Observation:**
- Large gaps between session highs/lows (Asia → London → NY)
- When Asia high << London high << NY high, price trending strongly

**Discovery Method:**
- **Gap analysis** - Measure session-to-session displacement
- Held constant: Cascade concept (3 sessions aligned)
- Allowed to vary: Gap threshold (tested 7pts, 9.5pts, 12pts)
- Measured: Win rate when gap > threshold

**Constraint That Created Edge:**
- Minimum gap: 9.5 points between Asia and London (or London and NY)
- Acceptance rule: Price must fail to accept back above gap within 3 bars
- Direction: Trade in direction of gap (gap up → LONG)

**What Was Measured:**
- Gap frequency (9.3% of days)
- Win rate when gap present (69.6%)
- Avg R per cascade trade (+1.95R)

**What Was NOT Measured (Assumed):**
- Why cascades form (assumed institutional accumulation/distribution)
- Optimal entry timing (assumed ORB breakout is best)
- Session participant differences (assumed different timezone traders matter)

**Validation Method:**
- Frequency test: <10% selectivity required (9.3% PASS)
- Edge test: +1.95R avg >> baseline +0.425R
- Sample size: 69 trades over 2 years (adequate)

**Survivorship Filter:**
- Smaller gaps (< 9.5pts) → too frequent, no edge
- Larger gaps (> 12pts) → too rare, insufficient sample
- 9.5pts threshold balances frequency and edge

**Key Insight:**
- **Multi-session alignment creates momentum**, not single-session patterns
- Gap threshold found by testing multiple values, not theory
- Rare pattern (9.3%) but massive edge (+1.95R) justifies low frequency

---

## STRATEGY 4: NQ ORB BREAKOUTS (Alternative Instrument)

### How This Edge Was Discovered

**Initial Observation:**
- Question: "Does MGC framework transfer to NQ?"
- Hypothesis: Same structural patterns, different optimal parameters

**Discovery Method:**
- **Transfer learning** from MGC
- Applied MGC discovery methodology to NQ data
- Re-ran parameter sweep (RR, SL mode, filters) on NQ
- Held constant: Discovery framework (same as MGC)
- Allowed to vary: All parameters (no assumption of transfer)

**Constraint That Created Edge:**
- Same patterns exist (ORB breakouts work)
- Different optimal parameters (NQ 13× more volatile)
- Example: 0900 ORB works at RR 1.0 FULL with 0.050×ATR filter on NQ
- Example: 2300 ORB FAILS on NQ (negative even with filters) → SKIP

**What Was Measured:**
- All 6 ORBs tested on NQ data
- Performance vs MGC (NQ +0.194R vs MGC +0.430R per trade)
- Volatility ratio (NQ 13× MGC in absolute terms)

**What Was NOT Measured (Assumed):**
- Correlation between MGC and NQ (assumed independent)
- Tick value differences handled correctly (assumed $2/tick for MNQ)

**Validation Method:**
- Date-matched comparison to MGC
- Robustness: If MGC pattern transfers, expect similar WR and R profile
- Result: Patterns transfer but with 2.2× worse performance

**Survivorship Filter:**
- 2300 ORB killed (negative on NQ, positive on MGC)
- Filters tighter on NQ (0.050×ATR vs 0.155×ATR for MGC)
- 5 ORBs survive, 1 rejected

**Key Insight:**
- **Discovery methodology transfers, not parameters**
- Same framework applied to different asset finds similar structures
- Edge magnitude is asset-specific (MGC > NQ for ORB strategies)

---

## STRATEGY 5: LONDON ADVANCED FILTERS (3 Tiers)

### How This Edge Was Discovered

**Initial Observation:**
- Baseline 1800 ORB: +0.425R avg (decent but improvable)
- Question: "Can we filter for higher-quality setups?"

**Discovery Method:**
- **Stacked filter testing** - 126 configurations
- Variables: Asia range filters × Directional filters × RR values × SL modes
- Held constant: London ORB 1800 timing
- Allowed to vary: Pre-conditions (Asia state, prior session inventory)

**Constraint That Created Edge:**
- **TIER 1 (Best):** Asia NORMAL (100-200 ticks) + Prior NY HIGH resolved + SKIP if NY LOW
- Result: +1.059R avg on 68 trades (2.5× baseline)
- **TIER 2 (Balanced):** Asia NORMAL + RR 3.0
- Result: +0.487R avg on 199 trades
- **TIER 3 (Volume):** Baseline + RR 1.5
- Result: +0.388R avg on 499 trades

**What Was Measured:**
- Expectancy per filter combination
- Trade frequency (selectivity percentage)
- Win rate changes with filters applied

**What Was NOT Measured (Assumed):**
- Why NY_LOW resolution is toxic (assumed prior inventory clearing)
- Optimal Asia range buckets (tested 3 buckets: SMALL, NORMAL, WIDE)

**Validation Method:**
- Baseline comparison for each tier
- Filter impact: Measure delta vs baseline (+0.671R for TIER 1)
- Robustness: Multiple filter combinations tested, not just one

**Survivorship Filter:**
- Most combinations < +0.20R improvement → rejected
- High selectivity (<5% of days) → rejected (too rare)
- NY_LOW resolution pattern → SKIP (toxic -0.37R delta)

**Key Insight:**
- **More filters = higher edge per trade, but lower frequency**
- Trade-off between expectancy and volume explicit
- Stacking filters improves edge IF filters are structural (not curve-fit)

---

## STRATEGY 6: SESSION-BASED ENHANCEMENTS (Engine A - Liquidity/Inventory)

### How This Edge Was Discovered

**Initial Observation:**
- Question: "Does Asia session behavior predict London performance?"
- Hypothesis: Prior session inventory resolution creates directional bias

**Discovery Method:**
- **State-based conditional analysis**
- Labeled Asia states: Resolved prior HIGH, Resolved prior LOW, Failed to resolve, Clean trend
- Measured London expectancy conditional on each Asia state
- Held constant: Prior session definition (NY and London highs/lows from previous day)
- Allowed to vary: Asia resolution state

**Constraint That Created Edge:**
- If Asia resolved prior HIGH → London LONG only (+0.15R improvement)
- If Asia resolved prior LOW → London SHORT only (+0.15R improvement)
- If Asia failed to resolve → London both directions (~+0.10R improvement)
- **TOXIC PATTERN:** Asia resolved prior HIGH → London SHORT (-0.37R WORST)

**What Was Measured:**
- London expectancy per Asia state (200+ trades each)
- Prior session levels (NY high/low, London high/low)
- Resolution depth (swept vs deeply penetrated)

**What Was NOT Measured (Assumed):**
- Why continuation works (assumed institutional flow alignment)
- Optimal prior session lookback (assumed 1 day, not 2-3 days)
- Resolution timing (early vs late Asia) - tested separately

**Validation Method:**
- Baseline comparison (conditional vs unconditional)
- Toxic pattern identification (negative delta = avoid)
- Sample size: 200+ trades per pattern (adequate)

**Survivorship Filter:**
- Patterns with <30 trades → rejected
- Patterns with delta < +0.10R → not significant
- Fade patterns (opposite to resolution) → killed by toxic results

**Key Insight:**
- **Prior session inventory creates directional bias FOR NEXT SESSION**
- Continuation dominates (never fade)
- State-based thinking: "When Asia resolves X, London does Y"

---

## STRATEGY 7: OUTCOME MOMENTUM (Engine B - Intra-Session Correlations)

### How This Edge Was Discovered

**Initial Observation:**
- Question: "Do winning ORBs predict next ORB direction?"
- User intuition: "When 09:00 wins, 10:00 seems to continue"

**Discovery Method:**
- **Outcome correlation analysis**
- Tracked prior ORB state: WIN/LOSS, direction UP/DOWN
- Measured next ORB win rate conditional on prior outcome
- Held constant: Intra-session timing (09:00 → 10:00 → 11:00)
- Allowed to vary: Prior outcome combinations

**Constraint That Created Edge:**
- 09:00 WIN → 10:00 UP: 57.9% WR (vs 55.5% baseline = +2.4% improvement)
- 09:00 LOSS + 10:00 WIN → 11:00 DOWN: 57.7% WR (+5.4% improvement - BEST)
- Combined momentum (2 prior wins) stronger than single win

**What Was Measured:**
- Win rate improvement conditional on prior ORB state
- Sample sizes per pattern (200+ each)
- Zero-lookahead enforcement (only use if prior ORB CLOSED)

**What Was NOT Measured (Assumed):**
- Why momentum exists (assumed psychological/order flow continuation)
- Optimal lookback (tested only 1 prior ORB, not 2-3 ORBs back)
- Cross-session momentum (Asia → London) - separate framework

**Validation Method:**
- Baseline comparison (conditional WR vs unconditional WR)
- Delta threshold: +2% WR minimum for significance
- Zero-lookahead check: Verify prior trade CLOSED before using outcome

**Survivorship Filter:**
- Patterns with <50 trades → rejected
- Patterns with WR delta < +2% → not significant
- Cross-session patterns → killed (Asia → London shows no outcome momentum)

**Key Insight:**
- **Intra-session momentum is real but SMALL** (2-5% WR improvement)
- Only use if prior trade is CLOSED (zero-lookahead critical)
- Combined momentum (2 wins → 3rd trade) stronger than single win momentum

---

## STRATEGY 8A: ORB POSITIONING ANALYSIS

### How This Edge Was Discovered

**Initial Observation:**
- User noticed: "0900 drops, lifts back to bottom, forms 10, same pattern repeats"
- Question: "Does ORB positioning relative to prior ORB matter?"

**Discovery Method:**
- **Spatial clustering analysis**
- Categorized 10:00 ORB position relative to 09:00 ORB
- Categories: BELOW, OVERLAP, NEAR_TOP, NEAR_BOTTOM, ABOVE
- Measured performance per positioning state
- Held constant: ORB timing (09:00, 10:00, 11:00)
- Allowed to vary: Spatial position

**Constraint That Created Edge:**
- 10:00 ORB BELOW 09:00: +0.400R avg (vs +0.342R baseline = +0.058R improvement, 70% WR)
- 10:00 ORB OVERLAP 09:00: +0.393R avg (+0.050R improvement, 69.6% WR)
- 10:00 ORB ABOVE 09:00: +0.276R avg (-0.066R degradation, 63.8% WR)

**What Was Measured:**
- Win rate by positioning category
- Avg R by positioning category
- Sample sizes (110-135 trades per category)

**What Was NOT Measured (Assumed):**
- Why BELOW performs better (assumed continuation > reversal)
- Optimal position threshold (categories somewhat arbitrary)
- Intraday bar-by-bar price action (would need 1m bars to see "lift back" pattern)

**Validation Method:**
- Baseline comparison per category
- Sample size check (all categories >75 trades)
- Opposite pattern check: 11:00 vs 10:00 shows REVERSE pattern (NEAR_TOP best)

**Survivorship Filter:**
- Categories with <30 trades → rejected
- Categories with delta < +0.05R → marginal
- User-described "lift back" pattern unclear from 5m data (needs 1m validation)

**Key Insight:**
- **Positioning matters but DIRECTION IS COUNTERINTUITIVE**
- User expected "lift back" to be best, but data shows "continued move" performs better
- Pattern reverses for different ORB pairs (10:00/09:00 vs 11:00/10:00)

---

## STRATEGY 8B: LAGGED FEATURES (Previous Day Predictors)

### How This Edge Was Discovered

**Initial Observation:**
- Question: "Does previous day session structure predict next day ORB performance?"
- Hypothesis: Prior day liquidity creates "memory" effect

**Discovery Method:**
- **SQL window functions (LAG)** - Time-series analysis
- Created lagged features: PREV_ASIA_IMPULSE, PREV_ASIA_CLOSE_POS, PREV_ASIA_RANGE
- Measured next-day ORB expectancy conditional on lagged features
- Held constant: Current ORB parameters
- Allowed to vary: Previous day state

**Constraint That Created Edge:**
- 00:30 ORB + PREV_ASIA_IMPULSE=HIGH: +0.124R (vs -0.069R baseline = **+0.193R improvement**)
  - **Transforms LOSING setup into WINNING setup**
- 11:00 ORB + PREV_ASIA_CLOSE_POS=HIGH: +0.192R (vs +0.026R baseline = +0.166R improvement)
  - **7.4× better expectancy**
- 00:30 ORB + PREV_ASIA_CLOSE_POS=LOW: +0.085R (vs -0.069R baseline = +0.154R improvement)

**What Was Measured:**
- Expectancy conditional on lagged features
- Sample sizes per bucket (83-154 trades)
- Coverage (99%+ of trades have lagged data available)

**What Was NOT Measured (Assumed):**
- Why previous day matters (assumed order flow memory, positioning)
- Optimal lookback period (tested 1 day, not 2-3 days)
- Cross-feature interactions (tested features independently, not combined)

**Validation Method:**
- Baseline comparison (conditional vs unconditional)
- Delta threshold: +0.15R minimum for significance
- Sample size: 30+ trades per bucket minimum
- Transformation test: Negative baseline → positive conditioned (strongest validation)

**Survivorship Filter:**
- Features with delta < +0.15R → not significant
- Features with <30 trades → insufficient sample
- 10:00 ORB shows NO lagged dependency (unconditional edge validated)

**Key Insight:**
- **Previous day DOES matter for SOME ORBs** (00:30, 11:00)
- Lagged features can TRANSFORM losing setups into winners
- Not all ORBs have day-to-day memory (10:00 shows none)

---

## STRATEGY 8C: ORB SIZE FILTERS (Adaptive ATR)

### How This Edge Was Discovered

**Initial Observation:**
- Question: "Do large ORBs perform worse than small ORBs?"
- Hypothesis: Large ORB = exhaustion (expansion already occurred)

**Discovery Method:**
- **Anomaly analysis** - Size distribution testing
- Normalized ORB size by ATR(20): orb_size / ATR(20)
- Tested thresholds: 0.05×ATR to 0.20×ATR
- Measured performance above vs below threshold
- Held constant: ORB parameters (RR, SL mode)
- Allowed to vary: Size threshold

**Constraint That Created Edge:**
- 11:00 ORB: Skip if orb_size > 0.095×ATR → +0.347R improvement (+77%, 78% WR)
- 00:30 ORB: Skip if orb_size > 0.112×ATR → +0.142R improvement (+61%, 65.7% WR)
- 23:00 ORB: Skip if orb_size > 0.155×ATR → +0.060R improvement (+15%, 69.1% WR)
- 10:00 ORB: Skip if orb_size > 0.088×ATR → +0.079R improvement (+23%, 71.9% WR)

**What Was Measured:**
- Avg R above vs below threshold
- Win rate change with filter
- Trade frequency reduction (11-42% of trades kept)
- Robustness: Tested 5 thresholds around optimal (4-5/5 positive)

**What Was NOT Measured (Assumed):**
- Why size matters (assumed compression → expansion cycle)
- Optimal ATR period (tested ATR(20), not ATR(10) or ATR(30))
- Session-specific reasons (night vs day ORBs)

**Validation Method:**
- Manual calculation (verified no lookahead)
- Robustness testing (5 thresholds per ORB, 80%+ must be positive)
- Structural explanation: Small ORB = compression, Large ORB = exhaustion
- Same pattern across 4 ORBs (not curve-fit to one)

**Survivorship Filter:**
- ORBs with no improvement → no filter (09:00)
- ORBs where filter worsens performance → rejected (18:00 pre-asia filter)
- Thresholds with <10% trade frequency → too restrictive

**Key Insight:**
- **ORB size relative to volatility predicts breakout quality**
- Small ORB (compression) → genuine breakout
- Large ORB (exhaustion) → false breakout, chasing
- Pattern is STRUCTURAL (works across 4 sessions), not curve-fit

---

## CROSS-CUTTING DISCOVERY PATTERNS

### Common Methodology Across All Strategies

**1. Observation-Driven (Not Theory-Driven)**
- Start with market observation or question
- Test hypothesis with data
- Accept results (even if negative)

**2. Dimensional Reduction**
- Hold most variables constant
- Vary only one dimension at a time
- Example: Test RR values with fixed SL mode, then test SL modes with fixed RR

**3. Baseline Comparison**
- Always measure unconditional performance first
- Compare conditional (filtered) to unconditional (baseline)
- Delta must exceed significance threshold (+0.10R to +0.15R minimum)

**4. Sample Size Discipline**
- Minimum 30 trades per bucket
- Prefer 50+ trades for confidence
- Reject patterns with insufficient sample

**5. Robustness Testing**
- Test variations around "optimal" parameter
- If optimal is threshold=0.10, test 0.08, 0.09, 0.10, 0.11, 0.12
- Require 80%+ of variations to be positive

**6. Lookahead Vigilance**
- Explicitly verify all features available at entry time
- ORB size known at ORB close (e.g., 23:05)
- Entry occurs after (e.g., 23:06+)
- No future bar data used

**7. Honest Rejection**
- Report negative findings explicitly
- Example: Unified liquidity framework FAILED on 4 out of 5 sessions
- Example: 18:00 pre-asia filter NEGATIVE (-0.003R)
- Do not hide failures

**8. State-Based Thinking**
- "When X condition, then Y performs differently"
- Conditional expectancy framework
- Measure performance per state, not aggregate

---

## ANTI-PATTERNS (What Was NOT Done)

### Practices Deliberately Avoided

**1. Indicator Stacking**
- ❌ NO RSI > 70 + MACD cross + Bollinger touch
- ✅ Structural patterns only (ORB, gaps, liquidity levels)

**2. Optimization-First**
- ❌ NO "find best parameter across all data"
- ✅ Test parameter range, require robustness, accept best if robust

**3. Cherry-Picking Timeframes**
- ❌ NO "test on 2024 data because it performed well"
- ✅ Use all available data (2024-2026, expanding to 2020-2026)

**4. Curve-Fitting to Single Value**
- ❌ NO "optimal threshold is 0.1234567"
- ✅ Test multiple thresholds, accept if 80%+ work

**5. Ignoring Negative Results**
- ❌ NO hiding failed sessions
- ✅ Report: "Unified framework failed on 0900, 1000, 1100, 0030"

**6. Parameter Changes Without Re-Sweep**
- ❌ NO "let's try RR 2.5 instead of 3.0"
- ✅ Re-run full parameter sweep if changing locked parameters

**7. Overstating Edges**
- ❌ NO "this is a holy grail system"
- ✅ "2-5% WR improvement, expect variance over 20 trades"

---

## VALIDATION HIERARCHY

### Confidence Levels by Validation Strength

**TIER 1: HIGHEST CONFIDENCE**
- Exhaustive parameter sweep (252 configs)
- Data integrity audit passed
- Robustness across threshold variations
- Sample size >200 trades
- **Example:** MGC ORB breakouts (Strategy 1)

**TIER 2: HIGH CONFIDENCE**
- Custom pattern with strong edge (+0.50R+)
- Temporal stability (3/3 time chunks positive)
- Sample size >50 trades
- Baseline comparison significant
- **Example:** Single liquidity reactions (Strategy 2)

**TIER 3: MODERATE CONFIDENCE**
- Conditional improvement +0.15R+
- Sample size >50 trades
- Robustness tested
- Structural explanation exists
- **Example:** London advanced filters (Strategy 5)

**TIER 4: PRELIMINARY**
- Sample size 30-50 trades
- Delta +0.10R to +0.15R
- Needs more data for confirmation
- **Example:** Some lagged feature conditions

---

## DISCOVERY EFFICIENCY ANALYSIS

### Time Investment vs Edge Magnitude

**High ROI Discoveries:**
1. **ORB parameter sweep** - 252 configs tested → Found 6 positive edges
   - Time: ~2 days of compute + analysis
   - Result: +908R/year system

2. **Size filters** - Anomaly analysis → Found 4 valid filters
   - Time: ~4 hours analysis + validation
   - Result: +0.158R per trade improvement (+44.9%)

3. **Lagged features** - SQL window functions → Found 3 significant improvements
   - Time: ~2 hours SQL + analysis
   - Result: Transformed 2 losing setups to winners

**Low ROI Discoveries:**
1. **Unified liquidity framework** - Generic patterns → 1 success, 4 failures
   - Time: ~8 hours development + testing
   - Result: Only 1800 ORB validated, others failed

2. **Direction persistence** - All 3 ORBs same direction → Insufficient sample
   - Time: ~1 hour analysis
   - Result: NULL values, pattern too rare

**Lesson:** Parameter sweeps and statistical analysis (high automation) > Manual pattern observation

---

## KEY INSIGHTS FOR PHASE 2

### Patterns to Abstract into Framework

**1. Parameter Sweep Template**
- Works when: Edge exists but optimal parameters unknown
- Method: Grid search across RR × SL mode × filters
- Requires: 200+ base trades for sufficient splits

**2. Conditional State Analysis**
- Works when: Hypothesis is "X condition affects Y performance"
- Method: Label states, measure performance per state, compare to baseline
- Requires: 50+ trades per state for confidence

**3. Anomaly Detection**
- Works when: Observing outlier behavior (large ORBs, extreme ranges)
- Method: Distribution analysis, threshold testing, robustness check
- Requires: Clear structural explanation for why outliers differ

**4. Transfer Learning**
- Works when: Existing framework validated on one asset/session
- Method: Apply same methodology to new asset, re-optimize parameters
- Requires: Similar market structure (ORBs exist on both MGC and NQ)

**5. Temporal Correlation**
- Works when: Prior state may influence next state (outcome momentum, lagged features)
- Method: Time-series analysis, LAG functions, conditional expectancy
- Requires: Zero-lookahead enforcement (only use if prior state CLOSED)

---

## CONCLUSION

All strategies were discovered using **data-driven hypothesis testing**, not theoretical prediction.

**Common thread:**
- Observation → Hypothesis → Test → Validate → Accept or Reject

**Key differentiator:**
- Honest rejection of failures (unified framework, 18:00 pre-asia filter)
- Parameter-dependency explicit (different sessions need different RR/SL)
- Sample size discipline (30+ trades minimum, prefer 50+)

**Next Phase:** Abstract these discovery patterns into reusable framework (Phase 2)

---

**Phase 1 Status:** COMPLETE
**Next:** Phase 2 - Abstract Discovery Pattern into Reusable Framework
