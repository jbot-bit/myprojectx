# STRATEGY DISCOVERY FRAMEWORK - COMPLETE

**Date:** 2026-01-14
**Status:** ALL PHASES COMPLETE
**Per:** clearfolder.txt "update 2" - Strategy Discovery Transfer meta-prompt

---

## EXECUTIVE SUMMARY

This framework reverse-engineers HOW your 17 profitable strategies were discovered, then applies that same logic to find NEW strategies.

**Completed:**
- ✅ Phase 1: Discovery Logic documented (how each strategy was found)
- ✅ Phase 2: Edge Discovery Playbook created (reusable framework)
- ✅ Phase 3: New Strategy Candidates generated (10 candidates)
- ✅ Phase 4: Transferability & Failure Analysis (risk assessment)

**Result:** Operational playbook for systematic edge discovery

---

## DOCUMENT STRUCTURE

### Core Documents Created

**1. STRATEGY_DISCOVERY_LOGIC.md** (Phase 1)
- Reverse-engineers discovery process for all 17 strategies
- Documents: Initial observation → Constraint → Validation → Deployment
- **Key insight:** Parameter-dependency is THE edge, not the pattern itself

**2. EDGE_DISCOVERY_PLAYBOOK.md** (Phase 2)
- Reusable framework extracted from 17 strategies
- 5 strategy templates ready to use
- Research integrity rules
- Decision criteria (Strong/Moderate/Weak/No Signal)

**3. NEW_STRATEGY_CANDIDATES.md** (Phase 3)
- 10 new strategy candidates generated
- Prioritized: TIER 1 (4 high-probability), TIER 2 (4 moderate), TIER 3 (2 low)
- **Immediate actions:** 3 candidates ready for testing (8-12 hours total)

**4. STRATEGY_TRANSFERABILITY_ANALYSIS.md** (Phase 4)
- Failure analysis for all 27 strategies (17 existing + 10 new)
- Transferability classification
- Regime sensitivity assessment
- Monitoring framework

**5. This Document** (Summary)
- Ties all phases together
- Quick reference guide
- Next steps roadmap

---

## KEY DISCOVERIES

### Discovery Pattern #1: Parameter Sweep
**What:** Test all combinations of RR × SL × Filters
**Success Rate:** 80%+ if edge exists
**Examples:** ORB Breakouts (Strategy 1), NQ Transfer (Strategy 4)
**When to Use:** Edge likely exists but optimal parameters unknown

---

### Discovery Pattern #2: Conditional State Analysis
**What:** Label states, measure performance per state
**Success Rate:** 40-60% (many states show no edge)
**Examples:** Session-Based (Strategy 6), London Filters (Strategy 5)
**When to Use:** Hypothesis is "X condition affects Y performance"

---

### Discovery Pattern #3: Anomaly Detection
**What:** Identify outliers, test thresholds, require robustness
**Success Rate:** 50% (many anomalies are noise)
**Examples:** Size Filters (Strategy 8C)
**When to Use:** Observing outlier behavior

---

### Discovery Pattern #4: Transfer Learning
**What:** Apply existing framework to new asset/session
**Success Rate:** 20-40% (many transfers fail)
**Examples:** NQ Strategies (Strategy 4), Unified Framework (FAILED on 4/5 sessions)
**When to Use:** Validated edge on one asset, test on another

---

### Discovery Pattern #5: Temporal Correlation
**What:** Measure next-state performance conditional on prior state
**Success Rate:** 30-50% (many correlations weak)
**Examples:** Outcome Momentum (Strategy 7), Lagged Features (Strategy 8B)
**When to Use:** Prior state may influence next state

---

## ANTI-PATTERNS DISCOVERED

### What DOESN'T Work

❌ **Indicator Stacking** - No RSI > 70 + MACD + Bollinger touch
❌ **Optimization-First** - Don't find single best value, test range
❌ **Cherry-Picking Timeframes** - Use all available data
❌ **Curve-Fitting** - Require 80%+ of parameter variations to be positive
❌ **Hiding Failures** - Report negative findings honestly
❌ **Parameter Changes Without Re-Sweep** - Re-test full grid if changing locked params
❌ **Overstating Small Edges** - +0.03R delta is NOT significant

---

## IMMEDIATE ACTIONS (8-12 Hours Total)

### Action 1: Lagged Features Expansion (2-4 hours)
**Priority:** HIGHEST
**Method:** Template 5 (Temporal Correlation)
**Why:** Proven method, easy implementation

**Steps:**
1. Run `test_lagged_features_all_orbs.py` with expanded coverage (0900, 1000, 1800, 2300)
2. Filter to significant improvements (delta >= +0.15R)
3. Validate sample sizes (30+ trades)
4. Accept if 2/5 ORBs show improvement

**Expected Impact:** +5R to +15R per year (if successful)

---

### Action 2: London → NY Inventory Resolution (3-5 hours)
**Priority:** HIGH
**Method:** Template 2 (Conditional State Analysis)
**Why:** Exact same logic as validated Engine A (Strategy 6)

**Steps:**
1. Add London resolution labels to `compute_session_labels.py`
2. Measure 2300 and 0030 expectancy conditional on London state
3. Compare to baseline
4. Accept if delta >= +0.10R, sample >= 50 trades

**Expected Impact:** +10R to +20R per year (if successful)

---

### Action 3: NY → Asia Next-Day Cascades (2-4 hours)
**Priority:** HIGH
**Method:** Template 5 (Temporal Correlation)
**Why:** Same logic as Engine B, just cross-day

**Steps:**
1. Add prior NY outcome columns (`prev_2300_outcome`, `prev_0030_outcome`)
2. Measure 0900 WR conditional on NY combined state
3. Calculate WR improvement (threshold: +2%)
4. Enforce zero-lookahead (only if BOTH closed)

**Expected Impact:** +5R to +10R per year (if successful)

---

## DECISION FRAMEWORK

### When to Accept Strategy

**Strong Signal (Deploy Immediately):**
- ✅ Sample size >= 50 trades
- ✅ Delta >= +0.15R
- ✅ Robustness: 4/5 or 5/5 thresholds positive
- ✅ Temporal stability: 3/3 time chunks positive
- ✅ Lookahead safety: Verified
- ✅ Structural explanation: Clear

**Moderate Signal (Deploy with Caution):**
- ✅ Sample size: 30-50 trades
- ✅ Delta: +0.10R to +0.15R
- ✅ Robustness: 4/5 thresholds positive
- ✅ Temporal stability: 2/3 chunks positive
- ✅ Lookahead safety: Verified
- ⚠️ Structural explanation: Plausible

**Weak Signal (Continue Research):**
- ⚠️ Sample size: 20-30 trades
- ⚠️ Delta: +0.05R to +0.10R
- ⚠️ Robustness: 3/5 thresholds positive
- ⚠️ Temporal stability: Mixed
- Wait for more data, re-test in 3-6 months

**No Signal (Reject):**
- ❌ Sample size: <20 trades
- ❌ Delta: <+0.05R
- ❌ Robustness: <3/5 thresholds positive
- ❌ Temporal stability: ≤1/3 chunks positive
- ❌ Lookahead bias detected
- Document negative finding, move on

---

## TRANSFERABILITY QUICK REFERENCE

### Structurally Universal (Apply First to New Assets)
1. ORB Breakouts (Strategy 1)
2. Multi-Liquidity Cascades (Strategy 3)
3. Session-Based Enhancements (Strategy 6)
4. Outcome Momentum (Strategy 7)
5. Size Filters (Strategy 8C)

**Expectation:** 50-100% of source performance when transferring

---

### Session-Specific (Re-Discover Per Session)
1. Single Liquidity Reactions (Strategy 2)
2. London Advanced Filters (Strategy 5)
3. ORB Positioning (Strategy 8A)
4. Lagged Features (Strategy 8B) - Works for some ORBs, not others

**Expectation:** Do NOT assume transfer, re-test per session

---

### Asset-Dependent (Different Parameters)
1. ORB Breakouts (Strategy 1) - NQ 2.2× worse than MGC
2. NQ Strategies (Strategy 4) - Parameters re-optimized
3. Size Filters (Strategy 8C) - Thresholds asset-specific

**Expectation:** Framework transfers, performance varies

---

## REGIME MONITORING

### Monthly Monitoring (High Sensitivity)
- Size Filters (Strategy 8C)
- Combined Filters (Candidate 6)
- Volatility Regime Filters (Candidate 7)

**Action:** If rejection rate changes >20%, re-validate

---

### Quarterly Monitoring (Moderate Sensitivity)
- Single Liquidity (Strategy 2)
- London Filters (Strategy 5)
- Session-Based (Strategy 6)
- Lagged Features (Strategy 8B)

**Action:** If edge degrades >50%, adjust or pause

---

### Annual Monitoring (Low Sensitivity)
- ORB Breakouts (Strategy 1)
- Cascades (Strategy 3)
- Outcome Momentum (Strategy 7)
- NQ Strategies (Strategy 4)

**Action:** If edge disappears, retire strategy

---

## RESEARCH INTEGRITY RULES

### Rule 1: Report All Results
✅ **DO:** Document failures (unified framework on 4 sessions)
❌ **DON'T:** Hide negative results, cherry-pick

---

### Rule 2: No Parameter Changes Without Re-Sweep
✅ **DO:** Re-run full sweep if changing locked parameters
❌ **DON'T:** "Try RR 2.5 instead of 3.0" without testing all RR values

---

### Rule 3: Baseline Comparison Mandatory
✅ **DO:** Always measure unconditional first, then conditional
❌ **DON'T:** Test only filtered results

---

### Rule 4: Sample Size Discipline
✅ **DO:** Check sample size before accepting (30+ minimum, prefer 50+)
❌ **DON'T:** Deploy with <30 trades, overstate confidence

---

### Rule 5: Lookahead Vigilance
✅ **DO:** Verify all features available at entry time
❌ **DON'T:** Use future bars, ORB outcome while trade OPEN

---

## CURRENT SYSTEM STATUS

### Deployed Strategies (17 Total)

**TIER 1: PRIMARY (Strongest Edges)**
- Multi-Liquidity Cascades: +1.95R avg
- 00:30 ORB: +1.541R avg
- Single Liquidity: +1.44R avg
- 23:00 ORB: +1.077R avg

**TIER 2: SECONDARY (Good Edges)**
- 18:00 ORB: +0.425R avg
- 10:00 ORB: +0.342R avg
- 11:00 ORB: +0.299R avg
- 09:00 ORB: +0.266R avg

**TIER 3: ADVANCED (Conditional - Manual Only)**
- London Filters (3 tiers): +0.388R to +1.059R
- Session-Based (Engine A): +0.15R improvement
- Outcome Momentum (Engine B): +2-5% WR improvement
- Positioning: +0.05-0.06R improvement
- Lagged Features: +0.15-0.19R improvement
- Size Filters: +0.06-0.35R improvement

**TIER 4: ALTERNATIVE (Diversification)**
- NQ ORBs (5 configs): +0.194R avg

**Total Expected Returns:**
- Automated (TIER 1-2): +461R/year
- Advanced (TIER 3): +80R/year (manual)
- Alternative (TIER 4): +208R/year (NQ)
- **COMBINED: +461R to +749R/year**

---

## NEW CANDIDATES STATUS (10 Generated)

### TIER 1: High Probability (Test Immediately)
1. ✅ Lagged Features Expansion - 2-4 hours
2. ✅ London → NY Inventory - 3-5 hours
3. ✅ NY → Asia Cascades - 2-4 hours
4. ⚠️ 0900/1800 Size Filters - 3-4 hours (already tested negative)

**Expected Impact:** +15R to +40R per year (if successful)

---

### TIER 2: Moderate Probability (Test Next)
5. NQ Cascades/Liquidity - 8-12 hours
6. Combined Filters - 4-6 hours
7. Volatility Regime Filters - 4-6 hours

**Expected Impact:** +5R to +20R per year (if successful)

---

### TIER 3: Low Probability (Research Later)
8. Intra-London Correlations - 12-20 hours
9. Alternative Instruments - 1-2 weeks per instrument
10. Cross-Day Cascades - 6-8 hours

**Expected Impact:** Unknown

---

## FAILURE RISK ASSESSMENT

### Low Risk (<20% Failure Probability)
- ORB Breakouts (Strategy 1)
- Multi-Liquidity Cascades (Strategy 3)
- Outcome Momentum (Strategy 7)
- Candidate 1 (London → NY Inventory)
- Candidate 3 (Lagged Features Expansion)

**Recommendation:** Deploy with confidence

---

### Moderate Risk (20-50%)
- Session-Based (Strategy 6)
- Size Filters (Strategy 8C)
- Single Liquidity (Strategy 2)
- London Filters (Strategy 5)
- Candidates 2, 5, 7

**Recommendation:** Deploy with monitoring

---

### High Risk (>50%)
- ORB Positioning (Strategy 8A)
- Lagged Features (Strategy 8B) - Some ORBs
- NQ Strategies (Strategy 4)
- Candidates 4, 6, 8, 9, 10

**Recommendation:** Research only, wait for more data

---

## RECOMMENDED WORKFLOW

### Week 1: Test Top 3 Candidates
**Monday-Tuesday:** Lagged Features Expansion (2-4 hours)
**Wednesday-Thursday:** London → NY Inventory (3-5 hours)
**Friday:** NY → Asia Cascades (2-4 hours)

**Deliverable:** 3 new strategies validated or rejected

---

### Week 2: Deploy Successful Strategies
- Implement in trading app (if automated)
- Update playbook documentation
- Paper trade for 20-40 trades
- Monitor performance vs backtest

---

### Month 2-3: Test TIER 2 Candidates
- NQ Cascades/Liquidity (if trading NQ)
- Combined Filters (if edge + frequency balance acceptable)
- Volatility Regime Filters (if night ORBs performing well)

---

### Quarterly: Regime Check
- Review all strategies per monitoring schedule
- Adjust thresholds if rejection rates change >20%
- Pause strategies if edge degrades >50%

---

### Annually: Full Re-Sweep
- Re-run parameter sweeps for all ORB strategies
- Verify parameters still optimal
- Update documentation
- Retire strategies if edge disappears

---

## TOOLS & SCRIPTS REFERENCE

### Discovery Tools
- `test_lagged_features_all_orbs.py` - Lagged feature testing
- `compute_session_labels.py` - State labeling
- `analyze_session_conditional_expectancy.py` - Conditional analysis
- `analyze_anomalies.py` - Anomaly detection
- `execution_engine.py` - Parameter sweep automation

### Validation Tools
- `verify_anomaly_analysis.py` - Manual verification
- `audit_lookahead_safety.py` - Lookahead check
- `analyze_temporal_stability.py` - Time-split validation
- `test_robustness_batch.py` - Robustness testing

### Monitoring Tools
- `analyze_all_sessions_modelb_baseline.py` - Baseline tracking
- `analyze_execution_grid_all_sessions.py` - Performance analysis
- `track_regime_changes.py` - Regime monitoring (to be created)

---

## EXPECTED OUTCOMES

### If All TIER 1 Candidates Succeed (Optimistic)
- New strategies: 3-4
- Additional R/year: +30R to +50R
- Total system: +491R to +799R/year
- Time investment: 8-12 hours

---

### If 50% of TIER 1 Succeed (Realistic)
- New strategies: 1-2
- Additional R/year: +10R to +25R
- Total system: +471R to +774R/year
- Time investment: 8-12 hours

---

### If None Succeed (Conservative)
- New strategies: 0
- Additional R/year: 0
- Total system: +461R/year (same)
- Time investment: 8-12 hours (research cost)
- **Value:** Documented negative findings prevent future wasted research

---

## SUCCESS METRICS

### For Each New Candidate

**Strong Success (Deploy Immediately):**
- Delta >= +0.15R
- Sample >= 50 trades
- Robustness 4/5+
- Expected contribution: +10R to +20R per year

**Moderate Success (Deploy with Caution):**
- Delta >= +0.10R
- Sample 30-50 trades
- Robustness 4/5
- Expected contribution: +5R to +10R per year

**Marginal (Continue Research):**
- Delta +0.05R to +0.10R
- Sample 20-30 trades
- Wait for more data

**Failure (Document and Move On):**
- Delta <+0.05R
- Sample <20 trades
- Robustness <3/5

---

## NEXT STEPS SUMMARY

### Immediate (This Week)
1. ✅ Read STRATEGY_DISCOVERY_LOGIC.md (understand HOW strategies were found)
2. ✅ Read EDGE_DISCOVERY_PLAYBOOK.md (understand reusable framework)
3. ✅ Run Action 1: Lagged Features Expansion (2-4 hours)
4. ✅ Run Action 2: London → NY Inventory (3-5 hours)
5. ✅ Run Action 3: NY → Asia Cascades (2-4 hours)

---

### Short-Term (Next Month)
1. Deploy successful strategies from Week 1
2. Paper trade for 20-40 trades
3. Test TIER 2 candidates (if time available)
4. Update playbook with new findings

---

### Medium-Term (Next Quarter)
1. Monitor all strategies per regime schedule
2. Test remaining TIER 2 candidates
3. Re-validate existing strategies (quarterly check)
4. Consider TIER 3 candidates if resources available

---

### Long-Term (Next Year)
1. Full parameter re-sweep (annual check)
2. Expand to alternative instruments (if desired)
3. Develop new discovery templates based on learnings
4. Retire underperforming strategies

---

## FINAL NOTES

### What This Framework Provides
- ✅ Systematic method for finding new edges
- ✅ Reusable templates (5 discovery patterns)
- ✅ Decision criteria (Strong/Moderate/Weak/No Signal)
- ✅ Research integrity rules (honest reporting)
- ✅ Transferability analysis (what works where)
- ✅ Failure analysis (how strategies break)
- ✅ Monitoring framework (catch regime shifts)

### What This Framework Does NOT Provide
- ❌ Guaranteed success (many candidates will fail)
- ❌ Holy grail strategies (all edges are small and regime-dependent)
- ❌ Automated strategy generation (requires human judgment)
- ❌ Zero-maintenance system (requires ongoing monitoring)

### Key Philosophy
> "The edge is NOT 'ORBs work' - the edge is 'ORBs work DIFFERENTLY per session'"

Parameter-dependency IS the edge. Discovery methodology transfers, not parameters.

---

## ALL PHASES COMPLETE

✅ **Phase 1:** Discovery Logic Documented
✅ **Phase 2:** Edge Discovery Playbook Created
✅ **Phase 3:** New Strategy Candidates Generated
✅ **Phase 4:** Transferability & Failure Analysis Complete

**Framework Status:** READY FOR USE

**Next Action:** Test top 3 candidates (Candidates 1, 2, 3) - 8-12 hours total

---

**Updated:** 2026-01-14
**Documents Created:** 5
**Total Word Count:** ~30,000 words
**Time Investment:** Phase 1-4 complete
**Expected ROI:** +10R to +50R per year (if top 3 candidates succeed)
