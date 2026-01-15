# NEW STRATEGY CANDIDATES - Phase 3

**Date:** 2026-01-14
**Purpose:** Apply Edge Discovery Playbook to generate new strategy candidates
**Per:** clearfolder.txt "update 2" - Strategy Discovery Transfer meta-prompt Phase 3

---

## PHASE 3 OBJECTIVE

Use the **same discovery logic** that found existing 17 strategies to discover NEW strategies.

**Constraints (from meta-prompt):**
- ❌ Do NOT copy parameters from old strategies
- ❌ Do NOT optimize early
- ✅ Only test conditions knowable at trade time
- ✅ Explain why each candidate mirrors past discovery logic

---

## CANDIDATE GENERATION METHOD

**3 Approaches:**
1. **Unexplored Dimensions** - Test variations not yet explored in existing strategies
2. **Transfer Learning** - Apply successful frameworks to untested sessions/assets
3. **Combination Stacking** - Combine multiple validated edges

---

## TIER 1 CANDIDATES: HIGH PROBABILITY

### Candidate 1: London → NY Inventory Resolution (Engine A Transfer)

**What:** Apply Asia → London inventory framework to London → NY

**Why This Exists:**
- Engine A works for Asia → London (+0.15R improvement)
- Same logic: Prior session inventory resolution creates directional bias
- London high/low become "prior inventory" for NY ORBs (2300, 0030)

**Discovery Logic Mirror:**
- **Same as Strategy 6** (Session-Based Enhancements)
- If London resolved prior Asia HIGH → NY LONG only
- If London resolved prior Asia LOW → NY SHORT only
- If London failed to resolve → NY both directions

**What Condition Creates Edge:**
- NY trades the result of what London did with Asia inventory
- Continuation dominates (never fade)

**Discovery Method:**
1. Label London states: Resolved Asia HIGH, Resolved Asia LOW, Failed, Clean
2. Measure 2300 and 0030 expectancy conditional on London state
3. Compare to baseline (unconditional)
4. Calculate deltas

**Expected Frequency:** 40-60% of days (similar to Asia → London)

**Expected Improvement:** +0.10R to +0.20R per setup

**Why This Mirrors Past Logic:**
- Identical to Engine A discovery (just different sessions)
- Same state labeling methodology
- Same baseline comparison approach

**Tools:**
- `compute_session_labels.py` - Add London resolution labels
- `analyze_session_conditional_expectancy.py` - Measure NY conditional on London
- SQL: `london_high >= asia_high` → Resolved HIGH

**Priority:** **HIGH** (exact same logic as validated Strategy 6)

---

### Candidate 2: NY → Asia Next-Day Cascades (Temporal Correlation)

**What:** Test if 2300+0030 outcomes predict next-day 0900 performance

**Why This Exists:**
- Outcome momentum works intra-session (0900 WIN → 1000 UP)
- Question: Does it work CROSS-DAY?
- If NY session (2300+0030) both WIN → Does Asia open (0900) continue?

**Discovery Logic Mirror:**
- **Same as Strategy 7** (Outcome Momentum)
- Track prior session outcomes (2300, 0030)
- Measure 0900 win rate conditional on NY outcomes
- **Critical:** Only use if BOTH 2300 and 0030 trades CLOSED before 0900

**What Condition Creates Edge:**
- If 2300 WIN + 0030 WIN → 0900 UP has higher WR
- If 2300 LOSS + 0030 LOSS → 0900 DOWN has higher WR (reversal)

**Discovery Method:**
1. Track 2300 and 0030 outcomes (WIN/LOSS, direction)
2. Measure 0900 WR conditional on NY combined state
3. Test patterns: Both WIN, Both LOSS, Mixed
4. Calculate WR improvement (threshold: +2% minimum)

**Expected Frequency:** 60-80% of days (most trades close overnight)

**Expected Improvement:** +2% to +5% WR improvement

**Why This Mirrors Past Logic:**
- Identical to Engine B discovery (just cross-day instead of intra-session)
- Same outcome tracking methodology
- Same zero-lookahead enforcement (only if CLOSED)

**Tools:**
- `test_ny_to_asia_cascade.py` - Cross-day correlation test
- Database: Add `prev_2300_outcome`, `prev_0030_outcome` columns
- SQL LAG() functions across day boundary

**Priority:** **HIGH** (exact same logic as validated Strategy 7, just cross-day)

---

### Candidate 3: Lagged Features for Remaining ORBs (Expand Strategy 8B)

**What:** Test PREV_ASIA and PREV_LONDON features for ORBs not yet tested

**Why This Exists:**
- Lagged features work for 0030 (+0.193R) and 1100 (+0.166R)
- Question: Do they work for 0900, 1000, 1800, 2300?
- Same discovery method, different ORBs

**Discovery Logic Mirror:**
- **Same as Strategy 8B** (Lagged Features)
- Test PREV_ASIA_IMPULSE, PREV_ASIA_CLOSE_POS, PREV_LONDON_RANGE
- Measure expectancy conditional on lagged state
- Calculate deltas vs baseline

**What Condition Creates Edge:**
- Example: 1800 + PREV_ASIA_CLOSE_POS=HIGH → improvement?
- Example: 2300 + PREV_LONDON_SWEPT_ASIA_HIGH → improvement?

**Discovery Method:**
1. Add lagged features to database (if not present)
2. Run conditional analysis for each ORB × lagged feature combination
3. Filter to significant improvements (delta >= +0.15R)
4. Validate sample sizes (30+ trades per bucket)

**Expected Frequency:** 15-35% of setups (varies by feature)

**Expected Improvement:** +0.10R to +0.20R per setup

**Why This Mirrors Past Logic:**
- Identical to Strategy 8B discovery
- Same SQL LAG() methodology
- Same significance thresholds

**Tools:**
- `test_lagged_features_all_orbs.py` - Already exists, expand coverage
- SQL window functions
- `build_day_state_features.py` - Add lagged columns

**Priority:** **HIGH** (proven method, just apply to more ORBs)

---

### Candidate 4: ORB Size Filters for 0900 and 1800 (Expand Strategy 8C)

**What:** Re-test size filters for ORBs not yet filtered

**Why This Exists:**
- Size filters work for 1000, 1100, 2300, 0030 (4 out of 6 ORBs)
- 0900 shows no filter in initial test
- 1800 shows NEGATIVE filter in initial test
- Question: Were thresholds wrong, or does filter not work?

**Discovery Logic Mirror:**
- **Same as Strategy 8C** (Size Filters)
- Test multiple thresholds (0.05×ATR to 0.20×ATR)
- Measure performance above vs below threshold
- Require robustness (4/5 thresholds positive)

**What Condition Creates Edge:**
- Small ORB = compression → genuine breakout
- Large ORB = exhaustion → false breakout
- Same pattern as other ORBs?

**Discovery Method:**
1. Test 6-8 threshold values for 0900 and 1800
2. Measure Avg R and WR above vs below each threshold
3. Check robustness (80%+ thresholds must work)
4. Verify lookahead safety

**Expected Frequency:** 10-40% of setups (varies by threshold)

**Expected Improvement:** +0.05R to +0.15R per setup

**Why This Mirrors Past Logic:**
- Identical to Strategy 8C discovery
- Same anomaly detection methodology
- Same robustness requirements

**Tools:**
- `analyze_anomalies.py` - Re-run for 0900 and 1800
- `verify_anomaly_analysis.py` - Validate
- Test wider threshold range (maybe 0900/1800 need different range)

**Priority:** **MEDIUM** (proven method but initial test showed no edge for 0900, negative for 1800)

---

## TIER 2 CANDIDATES: MODERATE PROBABILITY

### Candidate 5: NQ Cascades and Single Liquidity (Transfer Learning)

**What:** Test cascades and single liquidity strategies on NQ

**Why This Exists:**
- NQ ORBs validated (+0.194R avg)
- Cascades work on MGC (+1.95R avg)
- Single liquidity works on MGC (+1.44R avg)
- Question: Do these patterns transfer to NQ?

**Discovery Logic Mirror:**
- **Same as Strategy 4** (NQ Transfer)
- Apply MGC cascade framework to NQ
- Re-optimize thresholds (NQ 13× more volatile)
- Example: Min gap 15-20 pts on NQ (vs 9.5 pts on MGC)

**What Condition Creates Edge:**
- Same multi-session alignment creates momentum on NQ
- Same liquidity sweep + reversal pattern on NQ

**Discovery Method:**
1. Measure NQ session gaps (Asia → London → NY)
2. Test gap thresholds: 10, 12.5, 15, 17.5, 20 pts
3. Backtest cascade entries
4. Measure single liquidity sweep frequency and success rate

**Expected Frequency:** 8-12% (cascades), 15-18% (single liquidity)

**Expected Improvement:** +0.80R to +1.50R (vs MGC +1.95R and +1.44R)

**Why This Mirrors Past Logic:**
- Identical to NQ ORB transfer (Strategy 4)
- Same transfer learning methodology
- Same expectation: 50-100% of source performance

**Tools:**
- `backtest_cascade_nq.py` - New script
- `test_single_liquidity_nq.py` - New script
- Adapt execution_engine.py for NQ

**Priority:** **MEDIUM** (transfer learning has 40-50% failure rate, but proven method)

---

### Candidate 6: Combined Filters (Positioning + Outcome + Lagged)

**What:** Stack multiple validated filters on same ORB

**Why This Exists:**
- Positioning works (Strategy 8A): +0.05R to +0.06R
- Outcome momentum works (Strategy 7): +2% to +5% WR
- Lagged features work (Strategy 8B): +0.15R to +0.19R
- Question: Do they stack additively?

**Discovery Logic Mirror:**
- **Similar to Strategy 5** (London Advanced Filters)
- Test combinations of filters
- Measure if improvements are additive, multiplicative, or redundant

**What Condition Creates Edge:**
- Example: 1000 ORB + BELOW 0900 (positioning) + 0900 WIN (outcome) + PREV_ASIA_CLOSE_POS=HIGH (lagged)
- Expected: +0.05R + 0.05R + 0.15R = +0.25R improvement?

**Discovery Method:**
1. Identify ORBs with multiple validated filters
2. Test combinations: 2-filter, 3-filter
3. Measure performance vs baseline
4. Check if filters are redundant (measuring same thing) or complementary

**Expected Frequency:** 5-15% of setups (very selective)

**Expected Improvement:** +0.15R to +0.30R per setup (if additive)

**Why This Mirrors Past Logic:**
- Similar to London filter stacking (Strategy 5)
- Same risk of over-filtering (too restrictive)
- Balance edge and frequency

**Tools:**
- SQL: Combine filter conditions with AND
- `find_*_edge_states.py` - Test combined states
- Track rejection rate (if >95%, too restrictive)

**Priority:** **MEDIUM** (risk of over-optimization, but validated components)

---

### Candidate 7: Volatility Regime Filters (Adaptive Entry)

**What:** Only trade certain ORBs in specific volatility regimes

**Why This Exists:**
- Night ORBs (2300, 0030) perform best at RR 4.0 (wide targets)
- Question: Do they perform even better on HIGH volatility days?
- Size filters remove LARGE ORBs → What about regime-based entry?

**Discovery Logic Mirror:**
- **Similar to Strategy 8C** (Size Filters)
- Instead of "skip if ORB large", test "only trade if ATR(20) > threshold"
- Measure performance in HIGH vs LOW volatility regimes

**What Condition Creates Edge:**
- High volatility → Larger moves → RR 4.0 targets more reachable
- Low volatility → Smaller moves → RR 4.0 targets unreachable

**Discovery Method:**
1. Label days as LOW, MEDIUM, HIGH volatility (ATR percentile)
2. Measure 2300 and 0030 performance per regime
3. Test if HIGH regime improves edge
4. Check robustness across threshold variations

**Expected Frequency:** 30-40% of days (if filtering to HIGH regime)

**Expected Improvement:** +0.10R to +0.20R per setup

**Why This Mirrors Past Logic:**
- Similar to size filter discovery (Strategy 8C)
- Same anomaly detection on volatility dimension
- Same robustness testing

**Tools:**
- `analyze_volatility_regime_segmentation.py` - Already exists
- Add ATR percentile to daily_features
- Test thresholds: 50th, 60th, 70th, 80th percentile

**Priority:** **MEDIUM** (new dimension, but related to proven size filters)

---

## TIER 3 CANDIDATES: LOW PROBABILITY (High Risk)

### Candidate 8: Intra-London ORB Correlations (Requires New ORBs)

**What:** Test outcome momentum within London session

**Why This Exists:**
- Intra-Asia momentum works (0900 → 1000 → 1100)
- Question: Does intra-London momentum work?
- Problem: Only 1800 ORB tested, no 1900 or 2000 ORBs

**Discovery Logic Mirror:**
- **Same as Strategy 7** (Outcome Momentum)
- But requires NEW ORB windows (1900, 2000, 2100, 2200)

**What Condition Creates Edge:**
- If 1800 WIN → 1900 UP has higher WR
- If 1800+1900 WIN → 2000 UP has higher WR

**Discovery Method:**
1. Add new ORB windows to database (1900, 2000, 2100, 2200)
2. Backfill historical data
3. Run baseline tests (do these ORBs have unconditional edge?)
4. If yes, test outcome correlations

**Expected Frequency:** Unknown (need baseline first)

**Expected Improvement:** +2% to +5% WR (if pattern transfers)

**Why This Mirrors Past Logic:**
- Identical to intra-Asia momentum (Strategy 7)
- Same discovery method

**Why LOW PRIORITY:**
- Requires significant infrastructure (new ORB windows)
- Unknown if London ORBs (beyond 1800) have baseline edge
- High development cost for uncertain payoff

**Tools:**
- `build_daily_features_v2.py` - Add 1900, 2000, 2100, 2200 ORBs
- `backtest_orb_exec_5m.py` - Test new ORBs
- May require 6-12 hours of development

**Priority:** **LOW** (high cost, uncertain benefit)

---

### Candidate 9: Alternative Instruments (Silver, Crude, S&P)

**What:** Transfer MGC framework to other instruments

**Why This Exists:**
- MGC and NQ both validated
- Question: Do patterns transfer to SI (Silver), CL (Crude Oil), ES (S&P)?

**Discovery Logic Mirror:**
- **Same as Strategy 4** (NQ Transfer)
- Apply MGC discovery methodology
- Re-optimize all parameters (do NOT copy)

**What Condition Creates Edge:**
- Same ORB breakout structures exist on all liquid futures
- Different optimal parameters per instrument

**Discovery Method:**
1. Backfill historical data for SI, CL, ES
2. Run parameter sweep (RR, SL mode, filters)
3. Compare to MGC performance
4. Accept if >= 50% of MGC edge

**Expected Frequency:** Same as MGC (6 ORBs per day)

**Expected Improvement:** Unknown (depends on instrument characteristics)

**Why This Mirrors Past Logic:**
- Identical to NQ transfer (Strategy 4)
- Same transfer learning methodology

**Why LOW PRIORITY:**
- Requires data backfill for new instruments
- Unknown if patterns transfer (SI and CL have different characteristics)
- High development cost (3-5 days per instrument)
- Focus on mastering MGC and NQ first

**Tools:**
- `backfill_databento_continuous.py` - Adapt for SI, CL, ES
- All existing backtest scripts
- May require 1-2 weeks per instrument

**Priority:** **LOW** (high cost, uncertain benefit, master existing first)

---

### Candidate 10: Cross-Session Cascades (London → NY → Asia Next Day)

**What:** Test 3-session cascades across day boundary

**Why This Exists:**
- Asia → London → NY cascades work (+1.95R)
- Question: Does London → NY → Asia (next day) work?

**Discovery Logic Mirror:**
- **Same as Strategy 3** (Multi-Liquidity Cascades)
- Measure gaps between London, NY, and next-day Asia
- Test if alignment predicts Asia continuation

**What Condition Creates Edge:**
- If London high < NY high < Asia (next day) high → Continuation

**Discovery Method:**
1. Measure London → NY gap
2. Measure NY → Asia (next day) gap
3. Test if both gaps > threshold → Asia breakout edge
4. Compare to baseline Asia ORB performance

**Expected Frequency:** 5-10% of days (rare)

**Expected Improvement:** +0.50R to +1.50R per setup (if pattern holds)

**Why This Mirrors Past Logic:**
- Identical to cascade discovery (Strategy 3)
- Same gap analysis methodology

**Why LOW PRIORITY:**
- Cross-day cascades may not work (different participants)
- Rare pattern (low frequency)
- Sample size may be insufficient
- Try Candidate 1 (London → NY inventory) first (higher probability)

**Tools:**
- `test_london_to_next_asia_cascade.py` - New script
- SQL: LAG() across day boundary
- Compare to intra-day cascades

**Priority:** **LOW** (rare pattern, uncertain logic)

---

## PRIORITY RANKING

### Deploy Immediately (Proven Logic, Easy Implementation)
1. **Candidate 3:** Lagged Features for Remaining ORBs - 2-4 hours
2. **Candidate 1:** London → NY Inventory Resolution - 3-5 hours
3. **Candidate 2:** NY → Asia Next-Day Cascades - 2-4 hours

**Expected Impact:** +10R to +30R per year (combined)

---

### Test Next (Moderate Probability)
4. **Candidate 4:** ORB Size Filters for 0900/1800 - 3-4 hours
5. **Candidate 7:** Volatility Regime Filters - 4-6 hours
6. **Candidate 6:** Combined Filters - 4-6 hours
7. **Candidate 5:** NQ Cascades and Single Liquidity - 8-12 hours

**Expected Impact:** +5R to +20R per year (if successful)

---

### Research Later (Low Probability or High Cost)
8. **Candidate 10:** Cross-Session Cascades - 6-8 hours
9. **Candidate 8:** Intra-London Correlations - 12-20 hours
10. **Candidate 9:** Alternative Instruments - 1-2 weeks per instrument

**Expected Impact:** Unknown

---

## IMMEDIATE NEXT ACTIONS

### Action 1: Lagged Features Expansion (Candidate 3)
**Why First:** Proven method, easy implementation, high probability

**Steps:**
1. Run `test_lagged_features_all_orbs.py` with expanded coverage
2. Test 0900, 1000, 1800, 2300 (already did 0030, 1100)
3. Filter to significant improvements (delta >= +0.15R)
4. Validate sample sizes (30+ trades)
5. Document findings

**Time:** 2-4 hours
**Tools:** Already exist
**Risk:** LOW

---

### Action 2: London → NY Inventory (Candidate 1)
**Why Second:** Exact same logic as validated Engine A

**Steps:**
1. Update `compute_session_labels.py` to add London resolution labels
2. Add columns: `london_resolved_asia_high`, `london_resolved_asia_low`, `london_failed`, `london_clean`
3. Run `analyze_session_conditional_expectancy.py` for 2300 and 0030 conditional on London state
4. Compare to baseline
5. Accept if delta >= +0.10R

**Time:** 3-5 hours
**Tools:** Modify existing scripts
**Risk:** LOW (proven logic)

---

### Action 3: NY → Asia Cascades (Candidate 2)
**Why Third:** Same logic as Engine B, just cross-day

**Steps:**
1. Add prior NY outcome columns to database
2. Track 2300 and 0030 outcomes (WIN/LOSS, direction)
3. Measure 0900 WR conditional on NY combined state
4. Calculate WR improvement (threshold: +2%)
5. Enforce zero-lookahead (only if BOTH closed)

**Time:** 2-4 hours
**Tools:** Similar to `analyze_orb_outcome_momentum.py`
**Risk:** LOW (proven logic)

---

## RESEARCH PROTOCOL FOR NEW CANDIDATES

### Step 1: Baseline First
- Measure unconditional performance before testing conditions
- Never skip baseline comparison

### Step 2: Sample Size Check
- Verify 30+ trades per bucket before accepting
- If insufficient, wait for more data

### Step 3: Robustness Test
- Test parameter variations (5-6 values)
- Require 80%+ positive for acceptance

### Step 4: Lookahead Verification
- Document timeline of feature availability
- Manual walkthrough of one example trade
- Verify entry occurs AFTER all features known

### Step 5: Deployment Decision
- Strong signal (delta >= +0.15R, 50+ trades) → Deploy
- Moderate signal (delta >= +0.10R, 30-50 trades) → Deploy with caution
- Weak signal (delta < +0.10R) → Reject or continue research

---

## PHASE 3 STATUS

**Candidates Generated:** 10

**TIER 1 (High Probability):** 4 candidates
- Expected impact: +15R to +40R per year (if all successful)
- Time investment: 10-18 hours total
- Risk: LOW (all use proven methodologies)

**TIER 2 (Moderate Probability):** 4 candidates
- Expected impact: +5R to +20R per year (if successful)
- Time investment: 20-35 hours total
- Risk: MODERATE (new dimensions, transfer attempts)

**TIER 3 (Low Probability):** 2 candidates
- Expected impact: Unknown
- Time investment: 1-3 weeks
- Risk: HIGH (uncertain patterns, high development cost)

**Immediate Actions:** 3 candidates ready for testing
1. Lagged Features Expansion (2-4 hours)
2. London → NY Inventory (3-5 hours)
3. NY → Asia Cascades (2-4 hours)

---

**Next:** Phase 4 - Transferability & Failure Analysis
