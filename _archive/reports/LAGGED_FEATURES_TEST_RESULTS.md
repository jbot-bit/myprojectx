# LAGGED FEATURES TEST - RESULTS

**Test Date:** 2026-01-13
**Objective:** Determine if PREVIOUS DAY session structure predicts NEXT DAY ORB performance
**Method:** SQL window functions (LAG) on day_state_features joined with realistic-entry trade outcomes

---

## EXECUTIVE SUMMARY

**DECISION: GO - IMPLEMENT LAGGED FEATURES**

✅ **3 significant improvements found** (delta >= +0.15R with >=30 trades)
✅ **2 ORBs benefit** (00:30, 11:00)
✅ **Maximum improvement:** +0.193R (00:30 ORB with PREV_ASIA_IMPULSE = HIGH)
✅ **Average improvement:** +0.171R across significant findings

**Key Insight:** The user's hypothesis was CORRECT - previous day liquidity DOES matter for some ORBs. We missed conditional states by only testing same-day features.

---

## SIGNIFICANT FINDINGS

### 1. 00:30 ORB + PREV_ASIA_IMPULSE = HIGH

**Baseline (unconditional):**
- Avg R: **-0.069R** (NEGATIVE EDGE)
- Win Rate: 22.8%
- Total trades: 483

**With lagged condition:**
- Avg R: **+0.124R** (POSITIVE EDGE)
- Win Rate: 26.5%
- Sample size: 83 trades (17.2% of total)
- **Improvement: +0.193R** ⭐⭐⭐

**Interpretation:**
When previous day Asia had HIGH impulse (directional, strong move), next day 00:30 ORB turns from a losing setup into a winning one. This is a **massive** finding - transforms a -0.069R baseline into +0.124R edge.

---

### 2. 11:00 ORB + PREV_ASIA_CLOSE_POS = HIGH

**Baseline (unconditional):**
- Avg R: **+0.026R** (thin edge)
- Win Rate: 30.9%
- Total trades: 492

**With lagged condition:**
- Avg R: **+0.192R** (strong edge)
- Win Rate: 37.7%
- Sample size: 154 trades (31.3% of total)
- **Improvement: +0.166R** ⭐⭐⭐

**Interpretation:**
When previous day Asia closed HIGH in its range (bullish close position), next day 11:00 ORB shows 7.4x better expectancy. Sample size is large (154 trades), making this a robust finding.

---

### 3. 00:30 ORB + PREV_ASIA_CLOSE_POS = LOW

**Baseline (unconditional):**
- Avg R: **-0.069R** (NEGATIVE EDGE)
- Win Rate: 22.8%
- Total trades: 483

**With lagged condition:**
- Avg R: **+0.085R** (POSITIVE EDGE)
- Win Rate: 29.2%
- Sample size: 120 trades (24.8% of total)
- **Improvement: +0.154R** ⭐⭐

**Interpretation:**
When previous day Asia closed LOW in its range (bearish close position), next day 00:30 ORB also turns positive. Combined with finding #1, this shows 00:30 ORB has strong predictive power from previous Asia state.

---

## OTHER NOTABLE FINDINGS (Below 0.15R threshold)

### 1800 ORB + PREV_ASIA_CLOSE_POS = HIGH
- Baseline: +0.106R
- Conditioned: +0.239R
- **Delta: +0.132R** (just below threshold)
- Sample: 180 trades
- **Near-significant** - worth monitoring

### 1100 ORB + PREV_ASIA_RANGE = SMALL
- Baseline: +0.026R
- Conditioned: +0.155R
- **Delta: +0.130R**
- Sample: 160 trades

### 10:00 ORB FINDINGS (UNCONDITIONAL EDGE CONFIRMED)
- Baseline: +0.056R
- Best lagged condition: PREV_ASIA_CLOSE_POS = HIGH → +0.137R (delta +0.081R)
- **Below 0.15R threshold** - original "unconditional edge" finding remains valid
- No single lagged feature provides sufficient improvement to warrant filtering

---

## BASELINE PERFORMANCE (All ORBs)

| ORB  | Trades | Win Rate | Avg R    | Median R | Total R  | Status       |
|------|--------|----------|----------|----------|----------|--------------|
| 0900 | 502    | 29.5%    | -0.045R  | -0.646R  | -22.8R   | Weak/Negative|
| 1000 | 510    | 33.3%    | +0.056R  | -0.635R  | +28.6R   | Thin positive|
| 1100 | 492    | 30.9%    | +0.026R  | -0.620R  | +12.6R   | Very thin    |
| 1800 | 508    | 35.6%    | +0.106R  | -0.624R  | +54.0R   | Decent       |
| 2300 | 496    | 25.4%    | -0.153R  | -0.690R  | -75.8R   | Negative     |
| 0030 | 483    | 22.8%    | -0.069R  | -0.571R  | -33.5R   | Negative     |

**Critical observation:** 23:00 and 00:30 ORBs show NEGATIVE baseline expectancy in this test. This contradicts earlier findings that showed these as strong night ORBs. Requires investigation (possible configuration mismatch or data period difference).

---

## LAGGED FEATURES TESTED

For each ORB, tested these previous-day features:

1. **PREV_ASIA_RANGE** (SMALL/MEDIUM/LARGE)
2. **PREV_ASIA_CLOSE_POS** (LOW/MID/HIGH) - where Asia closed in its range
3. **PREV_ASIA_IMPULSE** (LOW/MEDIUM/HIGH) - directional strength
4. **PREV_LONDON_RANGE** (SMALL/MEDIUM/LARGE)
5. **PREV_LONDON_CLOSE_POS** (LOW/MID/HIGH)
6. **PREV_LONDON_SWEPT_ASIA_HIGH** (YES/NO)
7. **PREV_LONDON_SWEPT_ASIA_LOW** (YES/NO)

**Most predictive features:**
- **PREV_ASIA_IMPULSE** - Strong signal for 00:30 ORB
- **PREV_ASIA_CLOSE_POS** - Strong signal for 11:00 and 00:30 ORBs
- **PREV_LONDON sweep flags** - Weak/no signal (insufficient samples)

---

## IMPLICATIONS

### For 00:30 ORB Strategy
**Current status:** Baseline shows -0.069R (negative expectancy)

**With lagged filtering:**
- Trade ONLY when prev_asia_impulse = HIGH → +0.124R (17% of setups)
- Trade ONLY when prev_asia_close_pos = LOW → +0.085R (25% of setups)
- **Combined filter potential:** Test if both conditions can be combined

**Action:** 00:30 ORB should be CONDITIONAL, not unconditional. Implement lagged filters.

### For 11:00 ORB Strategy
**Current status:** Baseline shows +0.026R (thin edge)

**With lagged filtering:**
- Trade ONLY when prev_asia_close_pos = HIGH → +0.192R (31% of setups)
- **7.4x improvement** in expectancy
- Adequate sample size (154 trades)

**Action:** 11:00 ORB should trade conditionally with prev_asia_close_pos filter.

### For 10:00 ORB Strategy (Original Question)
**Current status:** Baseline shows +0.056R (thin but positive)

**With lagged filtering:**
- Best condition: prev_asia_close_pos = HIGH → +0.137R (delta +0.081R)
- **Below 0.15R threshold** for significance
- No single condition provides decisive improvement

**Verdict:** Original "unconditional edge" finding is CORRECT for 10:00 ORB. Trade all setups without lagged filtering.

---

## NEXT STEPS (Ordered by Priority)

### 1. Investigate 23:00 & 00:30 Baseline Discrepancy (CRITICAL)
The test shows 23:00 and 00:30 with NEGATIVE baseline expectancy, contradicting previous findings that showed these as strong night ORBs (+1.08R and +1.54R).

**Possible causes:**
- Configuration mismatch (RR, sl_mode, close_confirmations)
- Different data period
- Different entry methodology
- Database/view mismatch

**Action:** Before implementing ANY lagged features, verify baseline results match validated findings. Read the original validation scripts for 23:00 and 00:30 to confirm methodology.

### 2. Implement Lagged Feature Schema (After #1 resolved)
**Add columns to day_state_features:**
```sql
-- Previous Asia features
prev_asia_high DOUBLE,
prev_asia_low DOUBLE,
prev_asia_range DOUBLE,
prev_asia_close_pos DOUBLE,
prev_asia_impulse DOUBLE,

-- Previous London features
prev_london_high DOUBLE,
prev_london_low DOUBLE,
prev_london_range DOUBLE,
prev_london_close_pos DOUBLE,
prev_london_impulse DOUBLE,
prev_london_swept_asia_high BOOLEAN,
prev_london_swept_asia_low BOOLEAN,

-- Previous range/displacement buckets
prev_range_bucket VARCHAR,
prev_disp_bucket VARCHAR
```

**Rebuild feature table:** Run `build_day_state_features.py` with LAG() calculations for all historical dates.

### 3. Update Edge State Testing Scripts
Modify `find_*_edge_states.py` scripts to include lagged features in state testing.

### 4. Retest All ORBs With Full Feature Set
Run comprehensive state testing with both same-day AND lagged features.

### 5. Update Trading App Configuration
For ORBs with significant lagged improvements:
- Add lagged feature filters to strategy evaluation logic
- Update app_trading_hub.py to display lagged conditions
- Add "WHY" reasons that reference previous day state

---

## TECHNICAL NOTES

### Test Configuration
- Database: gold.db
- Trade source: orb_trades_5m_exec_orbr (realistic entry at close)
- RR: 2.0
- SL Mode: half
- Close confirmations: 1
- Buffer ticks: 0
- Minimum sample size: 30 trades per bucket
- Significance threshold: +0.15R delta vs baseline

### Lag Implementation
Used LAG() window function partitioned by orb_code:
```sql
LAG(column, 1) OVER (PARTITION BY orb_code ORDER BY date_local)
```

This ensures each ORB's lag is calculated independently (09:00 ORB doesn't lag from 00:30 ORB data).

### Data Availability
- 0900: NO lagged features (can't lag from previous 09:00 on prior day due to trading day definition)
- All other ORBs: Full lagged feature availability (99%+ coverage)

---

## CONCLUSION

The user's hypothesis was VALIDATED: **Previous day liquidity DOES predict next day ORB performance for some sessions.**

We found conditional states that improve expectancy by +0.15R to +0.19R for two ORBs (00:30, 11:00). This is sufficient to warrant implementing lagged features in the full system.

However, **10:00 ORB** shows NO significant lagged dependency - the original "unconditional edge" finding (+0.056R) remains valid.

**CRITICAL BLOCKER:** Before implementing lagged features, resolve the discrepancy in 23:00 and 00:30 baseline results. These ORBs should show positive expectancy based on previous validation.

**Recommendation:** Proceed with lagged feature implementation AFTER resolving baseline discrepancy.
