# EDGE DISCOVERY PLAYBOOK - Phase 2

**Date:** 2026-01-14
**Purpose:** Abstract discovery patterns from existing strategies into reusable framework
**Per:** clearfolder.txt "update 2" - Strategy Discovery Transfer meta-prompt Phase 2

---

## PURPOSE

This is the **OPERATIONAL FRAMEWORK** for discovering new trading edges.

Extracted from 17 validated strategies (8 automated, 9 validated manual/advanced).

**Use this playbook when:**
- Investigating new market observations
- Testing hypotheses about edge conditions
- Applying existing methodology to new assets/sessions

---

## DISCOVERY FRAMEWORK OVERVIEW

```
OBSERVATION → HYPOTHESIS → DIMENSIONAL SEARCH → VALIDATION → DEPLOYMENT
```

**5 Phases:**
1. **Entry Point** - What observation starts the search?
2. **Dimensional Reduction** - What is frozen vs explored?
3. **Validation Method** - How are false positives rejected?
4. **Survivorship Filters** - What kills most candidates?
5. **Deployment Decision** - Accept, reject, or continue research?

---

## PHASE 1: ENTRY POINT

### Question: What Observation Starts the Search?

**4 Valid Entry Types:**

### Type A: Market Observation
**Definition:** Notice a recurring price behavior
**Examples:**
- "Large gaps between session highs create momentum" → Cascades
- "Price sweeps London levels then reverses" → Single liquidity
- "Large ORBs seem to fail more often" → Size filters

**Entry Protocol:**
1. Document the observation clearly
2. State it as testable hypothesis
3. Define "success" and "failure" outcomes
4. Estimate frequency (rough guess)

**Output:** Hypothesis statement
- Example: "IF gap > X points, THEN breakout has higher WR"

---

### Type B: User Question
**Definition:** Explicit question about market behavior
**Examples:**
- "Do winning ORBs predict next ORB direction?" → Outcome momentum
- "Does previous day matter?" → Lagged features
- "Does Asia behavior predict London?" → Session-based enhancements

**Entry Protocol:**
1. Reframe question as hypothesis
2. Identify what needs to be measured
3. Define conditional states
4. Determine baseline comparison

**Output:** Hypothesis + measurement plan
- Example: "Measure London expectancy conditional on Asia resolution state"

---

### Type C: Parameter Uncertainty
**Definition:** Edge likely exists but optimal parameters unknown
**Examples:**
- "ORBs work but which RR/SL combo?" → Parameter sweep
- "Liquidity reactions exist but what threshold?" → Robustness testing

**Entry Protocol:**
1. Identify parameter space (RR: 1.0-4.0, SL: HALF/FULL)
2. Define search grid
3. Plan exhaustive or sampled sweep
4. Set acceptance criteria

**Output:** Parameter grid + sweep plan
- Example: "Test 7 RR × 2 SL × 6 ORBs = 84 configurations"

---

### Type D: Transfer Hypothesis
**Definition:** Existing edge on one asset/session, test on another
**Examples:**
- "MGC ORBs work, does NQ work?" → NQ strategy
- "1800 liquidity works, does 0900 work?" → Unified framework (failed)

**Entry Protocol:**
1. Document source edge (MGC, 1800, etc.)
2. State transfer hypothesis (similar structure expected?)
3. Re-optimize all parameters (do NOT copy blindly)
4. Measure performance gap (target / source)

**Output:** Transfer hypothesis + re-optimization plan
- Example: "Test NQ with MGC framework, expect 50-100% of MGC performance"

---

## PHASE 2: DIMENSIONAL REDUCTION

### Question: What is Frozen vs Explored?

**Goal:** Isolate ONE dimension to test, hold everything else constant

**Framework:**

### Step 1: Identify All Dimensions
List every variable in the system:
- Timing (ORB window, entry delay)
- Parameters (RR, SL mode, filters)
- Conditions (prior session state, volatility regime)
- Assets (MGC vs NQ)
- Sessions (0900 vs 1800 vs 2300)

### Step 2: Freeze Most Dimensions
**Rule:** Change only ONE dimension per test

**Examples:**

**Test RR values (freeze everything else):**
```
Frozen: SL mode = FULL, filters = NONE, session = 0900
Vary: RR = 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0
Measure: Avg R, WR per RR value
```

**Test session dependency (freeze everything else):**
```
Frozen: RR = 2.0, SL mode = HALF, filters = NONE
Vary: Session = 0900, 1000, 1100, 1800, 2300, 0030
Measure: Avg R per session
```

**Test conditional states (freeze everything else):**
```
Frozen: RR = 1.0, SL mode = HALF, session = 1800
Vary: Asia state = Resolved HIGH, Resolved LOW, Failed, Clean
Measure: London expectancy per Asia state
```

### Step 3: Multi-Dimensional Search (Advanced)
**Only after single-dimension tests complete**

**Grid Search:**
```
Dimension 1: RR (7 values)
Dimension 2: SL mode (2 values)
Dimension 3: Session (6 values)
Total configs: 7 × 2 × 6 = 84
```

**Warning:** Combinatorial explosion
- 3 dimensions: 10 × 10 × 10 = 1,000 configs
- Requires automation (execution_engine.py)
- Manual testing: Max 2-3 dimensions

---

## PHASE 3: VALIDATION METHOD

### Question: How Are False Positives Rejected?

**5 Validation Tests (Apply All):**

### Test 1: Baseline Comparison
**Rule:** Conditional must beat unconditional by significance threshold

**Method:**
1. Measure unconditional (baseline) performance
2. Measure conditional (filtered) performance
3. Calculate delta: conditional - baseline
4. **Significance threshold:** Delta >= +0.15R (strong) or +0.10R (moderate)

**Example:**
```
Baseline (all London ORBs): +0.425R
Filtered (Asia NORMAL + NY_HIGH): +1.059R
Delta: +0.634R ✅ SIGNIFICANT
```

**Rejection:**
- If delta < +0.10R → NOT SIGNIFICANT (reject or continue research)
- If delta NEGATIVE → TOXIC PATTERN (document, never trade)

---

### Test 2: Sample Size Adequacy
**Rule:** Minimum 30 trades per bucket, prefer 50+

**Thresholds:**
- **< 20 trades:** INSUFFICIENT (reject)
- **20-30 trades:** MARGINAL (continue research, needs more data)
- **30-50 trades:** ADEQUATE (accept if other tests pass)
- **50+ trades:** STRONG (high confidence)
- **100+ trades:** VERY STRONG (highest confidence)

**Example:**
```
Pattern: 1100 ORB + ORB size < 0.095×ATR
Trades: 59
Sample: ADEQUATE (>30) ✅
```

**Rejection:**
- Volatility exhaustion pattern: 7 trades → INSUFFICIENT ❌

---

### Test 3: Robustness Across Variations
**Rule:** Test parameter variations, require 80%+ positive

**Method:**
1. Identify "optimal" parameter from initial test
2. Test 4-6 variations around optimal
3. Count how many variations are positive
4. **Threshold:** 80%+ must be positive (4 out of 5, or 5 out of 6)

**Example:**
```
Optimal: 0030 ORB size filter = 0.112×ATR → +0.142R
Variations tested:
  0.090×ATR → +0.120R ✅
  0.100×ATR → +0.135R ✅
  0.112×ATR → +0.142R ✅ (optimal)
  0.120×ATR → +0.130R ✅
  0.130×ATR → +0.105R ✅
Result: 5/5 positive (100%) ✅ ROBUST
```

**Rejection:**
- If only 1 threshold works → CURVE-FIT ❌
- If <80% work → NOT ROBUST ❌

---

### Test 4: Temporal Stability
**Rule:** Split data into time chunks, require consistent results

**Method:**
1. Split data into 3 equal time periods (early, mid, late)
2. Measure performance in each chunk
3. **Threshold:** 2/3 or 3/3 chunks must be positive

**Example:**
```
Strategy: Single liquidity reactions (1800 ORB)
Chunk 1 (2024 Q1-Q2): +0.650R ✅
Chunk 2 (2024 Q3-Q4): +0.720R ✅
Chunk 3 (2025 Q1-Q2): +0.690R ✅
Result: 3/3 positive ✅ STABLE
```

**Rejection:**
- If only 1/3 chunks positive → REGIME-SPECIFIC ❌
- If performance declining over time → DEGRADING EDGE ⚠️

---

### Test 5: Lookahead Safety
**Rule:** All features must be knowable at entry time

**Checklist:**
- [ ] ORB size computed at ORB close (e.g., 23:05)
- [ ] Entry occurs after ORB close (e.g., 23:06+)
- [ ] ATR uses only historical data (20 bars BEFORE current bar)
- [ ] Prior session data available (from previous day)
- [ ] Prior ORB outcome used only if trade CLOSED

**Timeline Example (23:00 ORB with size filter):**
```
23:00:00 - ORB window opens
23:04:59 - ORB window closes
23:05:00 - ORB size computed: orb_high - orb_low
23:05:00 - ATR(20) fetched (uses bars BEFORE 23:00)
23:05:00 - Filter check: orb_size / ATR(20) < 0.155?
23:05:01 - IF PASS → Generate entry signals
23:06:00 - First 5m bar closes outside ORB
23:06:01 - ENTRY ✅ (all data available before entry)
```

**Rejection:**
- If any feature uses future bars → LOOKAHEAD BIAS ❌
- If prior outcome used while trade still OPEN → LOOKAHEAD ❌

---

## PHASE 4: SURVIVORSHIP FILTERS

### Question: What Kills Most Candidates?

**7 Common Failure Modes:**

### Failure 1: Insufficient Sample Size
**Kills:** 30-40% of candidates
**Example:** Volatility exhaustion pattern (7 trades) ❌

**How to avoid:**
- Estimate frequency before testing
- If pattern triggers <5% of days, likely insufficient sample
- Adjust threshold to balance frequency and edge

---

### Failure 2: Not Significant vs Baseline
**Kills:** 20-30% of candidates
**Example:** Unified framework on 0900 ORB (+0.003R delta) ❌

**How to avoid:**
- Set significance threshold upfront (+0.10R minimum)
- Don't overstate marginal improvements
- Accept "no edge found" as valid result

---

### Failure 3: Curve-Fit (Not Robust)
**Kills:** 15-20% of candidates
**Example:** Only 1 threshold works, others negative ❌

**How to avoid:**
- Always test parameter variations
- Require 80%+ to be positive
- If only one value works, likely curve-fit

---

### Failure 4: Regime-Specific (No Temporal Stability)
**Kills:** 10-15% of candidates
**Example:** Works 2024, fails 2025 ❌

**How to avoid:**
- Split data into time chunks
- Test across different market regimes
- Prefer structural edges (work in all regimes)

---

### Failure 5: Lookahead Bias
**Kills:** 5-10% of candidates (usually caught in validation)
**Example:** Using ORB outcome while trade still OPEN ❌

**How to avoid:**
- Document timeline of feature availability
- Verify entry occurs AFTER all features computed
- Manual walkthrough of one example trade

---

### Failure 6: Over-Optimization (Too Many Filters)
**Kills:** 5-10% of candidates
**Example:** 5 stacked filters → 3 trades over 2 years ❌

**How to avoid:**
- Balance edge and frequency
- If selectivity <5%, likely too restrictive
- Prefer fewer, stronger filters over many weak filters

---

### Failure 7: Does Not Transfer (Session/Asset-Specific)
**Kills:** 40-50% of transfer attempts
**Example:** 1800 liquidity framework on 0900 ORB ❌

**How to avoid:**
- Expect transfer to fail often
- Re-optimize ALL parameters (don't copy)
- Accept if new asset shows 50-100% of source edge

---

## PHASE 5: DEPLOYMENT DECISION

### Question: Accept, Reject, or Continue Research?

**Decision Tree:**

### Decision: ACCEPT (Deploy Strategy)
**Criteria:** ALL must be true
- ✅ Sample size >= 50 trades (or 30-50 if very strong edge)
- ✅ Delta vs baseline >= +0.15R (strong) or +0.10R (moderate with other strengths)
- ✅ Robustness: 80%+ variations positive
- ✅ Temporal stability: 2/3 or 3/3 chunks positive
- ✅ Lookahead safety: Verified
- ✅ Structural explanation exists (why does this work?)

**Action:**
1. Document strategy in playbook
2. Implement in trading app (if automated)
3. Paper trade for 20-40 trades
4. Deploy live after validation

**Examples:** All 17 current strategies (Strategies 1-8)

---

### Decision: REJECT (Document and Move On)
**Criteria:** ANY is true
- ❌ Sample size < 20 trades (insufficient)
- ❌ Delta vs baseline < +0.05R (not significant)
- ❌ Robustness: <50% variations positive (curve-fit)
- ❌ Temporal stability: <2/3 chunks positive (regime-specific)
- ❌ Lookahead bias detected
- ❌ No structural explanation (random?)

**Action:**
1. Document negative finding honestly
2. Add to "TESTED_AND_REJECTED" log
3. Move to next hypothesis

**Examples:**
- Unified framework on 0900, 1000, 1100, 0030 ❌
- 18:00 pre-asia filter ❌
- Direction persistence (insufficient sample) ❌

---

### Decision: CONTINUE RESEARCH (More Data Needed)
**Criteria:** SOME positives, SOME concerns
- ⚠️ Sample size 20-30 trades (marginal)
- ⚠️ Delta +0.05R to +0.10R (marginal)
- ⚠️ Robustness 60-80% (borderline)
- ⚠️ Temporal stability 1/3 or 2/3 (mixed)
- ⚠️ Structural explanation unclear

**Action:**
1. Collect more data (wait for more trades)
2. Refine hypothesis (adjust filters/parameters)
3. Re-test after data accumulates
4. Set decision deadline (3-6 months)

**Examples:**
- 1800 ORB research (proxy data, needs bar-by-bar validation) ⚠️
- 2300 liquidity reactions (16 trades, inconclusive) ⚠️

---

## STRATEGY TEMPLATES

### Template 1: Parameter Sweep
**Use when:** Edge exists but optimal parameters unknown

**Steps:**
1. Define parameter space (RR, SL mode, filters)
2. Generate all combinations (grid search)
3. Run backtest on all configs
4. Rank by Avg R and Total R
5. Select optimal per session/asset
6. Validate with robustness tests

**Tools:**
- `execution_engine.py` - Automated backtesting
- `backtest_orb_exec_5m.py` - ORB-specific sweep
- `analyze_execution_grid_all_sessions.py` - Results analysis

**Time:** 1-2 days (mostly compute time)

**Success Rate:** HIGH (80%+ if edge exists)

---

### Template 2: Conditional State Analysis
**Use when:** Hypothesis is "X condition affects Y performance"

**Steps:**
1. Define states (e.g., Asia resolved HIGH, LOW, NONE, CLEAN)
2. Label all historical days with state
3. Measure target performance per state
4. Compare to baseline (unconditional)
5. Calculate deltas
6. Filter to significant states (delta >= +0.10R)

**Tools:**
- `compute_session_labels.py` - State labeling
- `find_*_edge_states.py` - State discovery
- `analyze_session_conditional_expectancy.py` - Analysis

**Time:** 2-4 hours (mostly SQL)

**Success Rate:** MODERATE (40-60%, many states show no edge)

---

### Template 3: Anomaly Detection
**Use when:** Observing outlier behavior (large ORBs, extreme ranges)

**Steps:**
1. Identify anomaly dimension (ORB size, range, volatility)
2. Normalize by ATR or similar
3. Test thresholds (skip if > threshold)
4. Measure performance above vs below threshold
5. Test robustness (5-6 threshold variations)
6. Verify structural explanation

**Tools:**
- `analyze_anomalies.py` - Distribution analysis
- `verify_anomaly_analysis.py` - Manual verification
- `test_filter_implementation.py` - Validation

**Time:** 3-5 hours

**Success Rate:** MODERATE (50%, many anomalies are noise)

---

### Template 4: Transfer Learning
**Use when:** Existing edge on one asset/session, test on another

**Steps:**
1. Document source edge (performance, parameters)
2. Identify target asset/session
3. Verify similar structure exists (ORBs form, levels exist, etc.)
4. Re-run parameter sweep (do NOT copy parameters)
5. Measure performance gap (target / source)
6. **Accept if target >= 50% of source**

**Tools:**
- Same tools as source edge
- Adapt data loader for new asset
- Compare results to source

**Time:** 1-3 days (depends on complexity)

**Success Rate:** LOW (20-40%, many transfers fail)

---

### Template 5: Temporal Correlation
**Use when:** Prior state may influence next state

**Steps:**
1. Define prior state (ORB outcome, session resolution, etc.)
2. Add LAG() features to database
3. Measure next-state performance conditional on prior state
4. **Critical:** Enforce zero-lookahead (only use if prior CLOSED)
5. Calculate win rate or R improvement
6. Accept if delta >= +0.10R or WR improvement >= +2%

**Tools:**
- `test_lagged_features_all_orbs.py` - Lagged features
- `analyze_orb_outcome_momentum.py` - Outcome correlations
- SQL window functions (LAG, LEAD)

**Time:** 2-4 hours

**Success Rate:** MODERATE (30-50%, many correlations are weak)

---

## DECISION CRITERIA SUMMARY

### Strong Signal (Deploy Immediately)
- Sample size: 50+ trades
- Delta: +0.15R or greater
- Robustness: 5/5 or 4/5 thresholds positive
- Temporal stability: 3/3 chunks positive
- Lookahead: Verified safe
- Structural explanation: Clear

**Example:** Size filters (Strategy 8C)

---

### Moderate Signal (Deploy with Caution)
- Sample size: 30-50 trades
- Delta: +0.10R to +0.15R
- Robustness: 4/5 thresholds positive
- Temporal stability: 2/3 chunks positive
- Lookahead: Verified safe
- Structural explanation: Plausible

**Example:** Lagged features (Strategy 8B)

---

### Weak Signal (Continue Research)
- Sample size: 20-30 trades
- Delta: +0.05R to +0.10R
- Robustness: 3/5 thresholds positive
- Temporal stability: Mixed
- Lookahead: Uncertain
- Structural explanation: Unclear

**Action:** Collect more data, re-test in 3-6 months

---

### No Signal (Reject)
- Sample size: <20 trades
- Delta: <+0.05R
- Robustness: <3/5 thresholds positive
- Temporal stability: 1/3 or 0/3 chunks positive
- Lookahead: Bias detected
- Structural explanation: None

**Action:** Document negative finding, move on

---

## RESEARCH INTEGRITY RULES

### Rule 1: Report All Results
**Positive AND negative findings**

**Do:**
- ✅ Document failed tests (unified framework on 4 sessions)
- ✅ Report marginal results honestly (+0.031R not overstated)
- ✅ Disclose sample size limitations

**Don't:**
- ❌ Hide negative results
- ❌ Cherry-pick best-performing subset
- ❌ Overstate marginal improvements

---

### Rule 2: No Parameter Changes Without Re-Sweep
**Locked parameters are LOCKED**

**Do:**
- ✅ Re-run full sweep if changing parameters
- ✅ Document why change is needed
- ✅ Compare new results to old

**Don't:**
- ❌ "Try RR 2.5 instead of 3.0" without testing all RR values
- ❌ Change SL mode without re-testing both modes
- ❌ Assume parameters transfer across assets

---

### Rule 3: Baseline Comparison Mandatory
**Always measure unconditional first**

**Do:**
- ✅ Run baseline (no filters)
- ✅ Run filtered
- ✅ Calculate delta
- ✅ Accept only if delta significant

**Don't:**
- ❌ Test only filtered results
- ❌ Compare to different baseline
- ❌ Accept marginal improvements without robustness

---

### Rule 4: Sample Size Discipline
**30+ trades minimum, prefer 50+**

**Do:**
- ✅ Check sample size before accepting
- ✅ Wait for more data if insufficient
- ✅ Disclose sample size in documentation

**Don't:**
- ❌ Deploy strategy with <30 trades
- ❌ Overstate confidence with small samples
- ❌ Ignore sample size warnings

---

### Rule 5: Lookahead Vigilance
**Verify all features available at entry time**

**Do:**
- ✅ Document timeline of feature computation
- ✅ Manual walkthrough of one example
- ✅ Verify entry occurs AFTER features known

**Don't:**
- ❌ Use future bar data
- ❌ Use ORB outcome while trade OPEN
- ❌ Assume "close enough" on timing

---

## PHASE 2 STATUS

**Framework Complete:** ✅

**5 Templates Ready:**
1. ✅ Parameter Sweep
2. ✅ Conditional State Analysis
3. ✅ Anomaly Detection
4. ✅ Transfer Learning
5. ✅ Temporal Correlation

**Decision Criteria:** ✅ Defined (Strong / Moderate / Weak / No Signal)

**Research Integrity Rules:** ✅ Documented

---

**Next:** Phase 3 - Apply This Playbook to Discover New Strategies
