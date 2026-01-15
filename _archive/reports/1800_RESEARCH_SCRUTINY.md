# 1800 ORB RESEARCH - CRITICAL SCRUTINY REPORT

**Date**: 2026-01-13
**Status**: ⚠️ MAJOR METHODOLOGICAL FLAWS IDENTIFIED

---

## 🔴 EXECUTIVE SUMMARY

**The 1800 ORB research has SERIOUS methodological flaws that invalidate the specific results:**

1. ❌ **Not a real backtest** - Uses pre-computed outcomes as proxy
2. ❌ **RR testing is fake** - RR 1.0, 2.0, 3.0 all show identical results
3. ❌ **Size filter testing is flawed** - Not simulating actual bar-by-bar execution
4. ❌ **Wrong SL mode** - Database uses HALF SL, deployed config uses FULL SL
5. ⚠️ **No IS/OOS split** - All data is 2024-2026 (need pre-2024)

**However**: The DIRECTIONAL finding (1800 ORB is profitable) is likely valid, but the exact numbers (71.3% WR, +0.425R) are questionable.

---

## 🔍 DETAILED FLAW ANALYSIS

### FLAW 1: Not a Real Backtest ⚠️⚠️⚠️

**What the code does**:
```python
def simulate_trade(signal, df_features):
    # Get actual outcome from database
    outcome = row['orb_1800_outcome']
    r_multiple = row['orb_1800_r_multiple']

    # Just return the pre-computed result
    return {'outcome': outcome, 'r_multiple': r_multiple, ...}
```

**The problem**:
- It's NOT simulating trades bar-by-bar
- It's just retrieving pre-computed ORB outcomes from `daily_features_v2_half`
- Those outcomes were computed during feature building with different parameters

**Impact**:
- We're not testing the strategy, we're just summarizing existing database results
- Can't test different RR multiples this way
- Can't test different SL modes this way

**Severity**: 🔴 CRITICAL

---

### FLAW 2: RR Testing is Fake ⚠️⚠️⚠️

**Evidence**:
```
ORB_Breakout_RR1: 522 trades, 71.3% WR, +0.425R
ORB_Breakout_RR2: 522 trades, 71.3% WR, +0.425R  (IDENTICAL!)
ORB_Breakout_RR3: 522 trades, 71.3% WR, +0.425R  (IDENTICAL!)
```

**Why this happened**:
- All three templates retrieve the SAME `orb_1800_r_multiple` from database
- The RR parameter in the template is IGNORED
- Database r_multiple is always +1.0 (WIN) or -1.0 (LOSS)

**Impact**:
- We have NO IDEA what the actual RR impact is
- Can't distinguish between RR 1.0, 2.0, or 3.0
- The deployed RR=1.0 is a GUESS, not validated

**Severity**: 🔴 CRITICAL

---

### FLAW 3: Size Filter Testing is Flawed ⚠️⚠️

**What the code does**:
```python
# Filter: Skip if ORB too large
if orb_size_norm > threshold:
    continue  # Skip this trade

# Then retrieve SAME database outcome for remaining trades
outcome = row['orb_1800_outcome']
```

**The problem**:
- It's just filtering which trades to INCLUDE
- Not simulating whether large ORBs ACTUALLY perform worse
- Using the same pre-computed outcomes for all

**Why "size filters worsen performance"**:
- Baseline: Uses ALL 522 trades with their database outcomes
- Filtered: Uses SUBSET with their database outcomes
- If the subset happens to include more losing trades, it looks worse

**But this doesn't prove**:
- That large ORBs are actually better
- That the database outcomes are representative
- That size filtering wouldn't help with proper bar-by-bar execution

**Impact**:
- Can't trust the finding that "size filters worsen performance"
- This could be sampling bias, not structural insight

**Severity**: 🔴 CRITICAL

---

### FLAW 4: Wrong SL Mode Deployed ⚠️⚠️

**Database outcomes**:
```python
# build_daily_features_v2.py uses:
orb_1800 = calculate_orb_1m_exec(..., sl_mode=self.sl_mode)

# For daily_features_v2_HALF table:
sl_mode = "HALF"  # Midpoint stop
```

**Deployed configuration**:
```python
# trading_app/config.py:
"1800": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"}  # FULL stop!
```

**The problem**:
- Research tested HALF SL (tighter stop at ORB midpoint)
- Deployed config uses FULL SL (wider stop at opposite ORB edge)
- These have VERY different risk profiles

**Impact**:
- Deployed config may perform differently than research
- HALF SL: Tighter stop, different win rate
- FULL SL: Wider stop, different win rate

**Expected difference**:
- HALF SL might have: Higher WR, lower avg R
- FULL SL might have: Lower WR, higher avg R (or worse overall)

**Severity**: 🔴 CRITICAL - Wrong config deployed

---

### FLAW 5: No In-Sample / Out-of-Sample Split ⚠️

**Data used**:
```
Date range: 2024-01-02 to 2026-01-09 (522 days)
Pre-2024 data: NONE
```

**The problem**:
- Can't do proper IS/OOS validation
- No pre-2024 data available in database
- All results are effectively "in-sample" (or all OOS, depending on perspective)

**Impact**:
- Can't prove results aren't specific to 2024-2026 period
- Can't prove robustness across different market regimes

**Severity**: ⚠️ MODERATE (can be fixed with data backfill)

---

### FLAW 6: No Bar-by-Bar Simulation ⚠️⚠️

**What's missing**:
- No loading of 1m or 5m bars
- No simulation of entry timing (first close outside ORB)
- No simulation of TP/SL hit detection
- No slippage modeling

**Why this matters**:
- Entry timing affects results (immediate breakout vs delayed)
- TP/SL order matters (which hit first?)
- Slippage affects expectancy

**Impact**:
- Results are approximations, not precise
- Can't test execution variations

**Severity**: ⚠️ MODERATE (acceptable for initial research)

---

## 📊 WHAT IS ACTUALLY VALID?

### ✅ Valid Findings

**1. 1800 ORB Baseline is Profitable**
- 522 trades over 2 years
- Using HALF SL mode (from database)
- Avg R of +0.425R is directionally correct
- This IS a real pattern, not noise

**2. High Win Rate (71.3%)**
- Consistent with other good ORBs (0900: 71.7%)
- Makes sense for major session transition
- Likely robust

**3. 1800 is Better Than Some ORBs**
- Outperforms 1000, 2300, 0030
- Comparable to 0900, 1100
- Ranking (2nd best) is probably valid

---

### ❌ Invalid Findings

**1. RR = 1.0 is Optimal**
- NOT TESTED - all RR values showed identical results
- Need proper bar-by-bar backtest to determine optimal RR

**2. Size Filters Worsen Performance**
- NOT VALIDATED - just subset filtering, not causal
- Could be sampling bias
- Need proper bar-by-bar test

**3. Exact Expectancy (+0.425R)**
- This is for HALF SL, not FULL SL
- Deployed config uses FULL SL (different)
- True expectancy unknown

**4. 71.3% Win Rate with FULL SL**
- Database shows 71.3% with HALF SL
- FULL SL will have different win rate
- Likely lower WR, possibly higher R per win

---

## 🔧 HOW TO FIX

### IMMEDIATE (Critical Fixes)

**1. Fix Deployed Config** ⚠️ URGENT
```python
# Change from:
"1800": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"}

# To:
"1800": {"rr": 1.0, "sl_mode": "HALF", "tier": "DAY"}  # Match database
```

**Reason**: Research used HALF SL, deployed FULL SL. They're different strategies.

**2. Add Warning to Documentation**
```markdown
⚠️ WARNING: 1800 ORB results are PRELIMINARY
- Based on proxy (database outcomes), not bar-by-bar simulation
- RR impact not tested (all RR showed identical results)
- Size filter conclusion questionable
- Performance metrics may change with proper backtest
```

---

### SHORT-TERM (Proper Validation)

**1. Build Bar-by-Bar 1800 Simulator**
- Load actual 1m/5m bars for 18:00-23:00 window
- Simulate entry: First close outside ORB
- Simulate TP/SL detection with proper timing
- Test RR 1.0, 2.0, 3.0 properly

**2. Test Both SL Modes**
- HALF SL (ORB midpoint)
- FULL SL (opposite ORB edge)
- Compare win rate, avg R, expectancy

**3. Test Size Filters Properly**
- Simulate bar-by-bar with size filtering
- Don't just filter which trades to include
- Measure CAUSAL impact of filter on execution

**4. Backfill Pre-2024 Data**
- Get 2020-2023 data
- Proper IS/OOS split
- Validate robustness

---

### MEDIUM-TERM (Full Robustness)

**1. Parameter Sweep**
- RR: 1.0, 1.5, 2.0, 2.5, 3.0
- SL: HALF, FULL
- Entry timing variations
- Exit conditions

**2. Slippage Sensitivity**
- Test 0, 1, 2 tick slippage
- Verify edge survives realistic costs

**3. Outlier Dependence**
- Remove top 1% best days
- Verify edge isn't dependent on outliers

**4. Market Regime Analysis**
- Segment by volatility (ATR quintiles)
- Test in trending vs ranging markets
- Verify robustness across regimes

---

## 🎯 RECOMMENDED ACTIONS

### Option A: Conservative Approach (RECOMMENDED)

**1. CORRECT the deployed config immediately**
```python
"1800": {"rr": 1.0, "sl_mode": "HALF", "tier": "DAY"}  # Match research
```

**2. Paper trade for 2 weeks** with HALF SL

**3. Build proper bar-by-bar simulator** in parallel

**4. Re-validate with proper backtest** before live trading

**5. Update documentation** with caveats

---

### Option B: Aggressive Approach (NOT RECOMMENDED)

**1. Keep FULL SL deployment**

**2. Monitor actual performance**

**3. Adjust if results diverge from expectations**

**Risk**: FULL SL may perform worse than HALF SL. Unknown until tested.

---

## 📈 EXPECTED REAL PERFORMANCE

### Best Case (if research is accurate)
- Win Rate: 71.3%
- Avg R: +0.425R (with HALF SL)
- Frequency: ~5 trades/week

### Likely Case (with FULL SL deployed)
- Win Rate: 60-65% (lower than HALF SL)
- Avg R: +0.30 to +0.40R (uncertain)
- Frequency: ~5 trades/week

### Worst Case (if flaws are significant)
- Win Rate: 50-55%
- Avg R: +0.10 to +0.20R (or negative)
- Frequency: ~5 trades/week

---

## 🔬 STATISTICAL CONCERNS

### Sample Size
- **522 trades** is reasonable for initial validation
- **260 trades/year** is good frequency
- **Not enough for robust RR optimization** (need ~1000+)

### Time Period
- **2024-2026 only** - need longer history
- **Recent period** - may not represent all regimes
- **No major crisis events** in period

### Multiple Comparisons
- **7 templates tested** - some false positives expected
- **All passed Stage 1** - suspicious (lucky period?)
- **Need Bonferroni correction** for confidence

---

## ✅ WHAT TO TRUST

**High Confidence**:
1. 1800 ORB baseline is profitable (HALF SL mode)
2. Win rate is high (65-75% range)
3. 1800 is better than 0030, 2300, 1000 ORBs
4. Frequency is good (~5/week)

**Medium Confidence**:
1. 1800 is 2nd best ORB (vs 1100, 0900)
2. Expectancy is +0.3 to +0.5R (with HALF SL)
3. Works across 2024-2026 period

**Low Confidence**:
1. RR=1.0 is optimal (NOT TESTED)
2. Size filters worsen performance (QUESTIONABLE)
3. FULL SL performance (UNKNOWN)
4. Exact expectancy of +0.425R (APPROXIMATE)

---

## 🚨 CRITICAL RECOMMENDATION

**URGENT: Fix the SL mode mismatch**

**Current state**:
- Research: HALF SL (database)
- Deployed: FULL SL (config)
- **These are different strategies!**

**Action required**:
```python
# trading_app/config.py line 78
# Change from:
"1800": {"rr": 1.0, "sl_mode": "FULL", "tier": "DAY"}

# To:
"1800": {"rr": 1.0, "sl_mode": "HALF", "tier": "DAY"}
```

**Then**: Paper trade for 2 weeks to validate before live.

---

## 📝 CONCLUSION

**The 1800 ORB research has major methodological flaws:**
1. Not a real backtest (uses proxy data)
2. RR testing is fake (all RR identical)
3. SL mode mismatch (researched HALF, deployed FULL)
4. Size filter conclusion questionable

**However, the core finding is likely valid:**
- 1800 ORB IS profitable
- High win rate (~70%)
- Good frequency (~5/week)
- Comparable to best ORBs

**Recommendation**:
1. **Fix SL mode to HALF** (match research)
2. **Paper trade for 2 weeks**
3. **Build proper bar-by-bar simulator**
4. **Re-validate before live trading**

**Do NOT trust**:
- Exact expectancy numbers
- RR optimization
- Size filter conclusions
- FULL SL performance (not tested)

---

**VERDICT**: 🟡 PROMISING BUT FLAWED - Fix critical issues before deployment
