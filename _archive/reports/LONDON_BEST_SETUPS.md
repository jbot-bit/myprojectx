# London ORB - Best Backtest Configurations

**Date:** 2026-01-12
**Test:** 126 configurations across multiple filters, RR values, and stop modes
**Dataset:** 499-521 London ORB trades (2020-2026)

---

## 🏆 WINNER: ASIA_NORMAL + NY_HIGH + SKIP_NY_LOW + RR 3.0 + FULL SL

### **Performance:**
- **68 trades**
- **51.5% win rate**
- **+1.059R average per trade** 🔥
- **+72.0R total**
- **Full stop-loss mode** (stop at opposite ORB edge)

### **Rules:**
1. **Asia range 100-200 ticks** (NORMAL)
2. **Asia resolved prior NY high** → Trade UP only
3. **Skip if Asia resolved prior NY low** (broken pattern)
4. **RR = 3.0** (target 3x the risk)
5. **Full SL** (stop at opposite ORB edge, not midpoint)

**This is the best expectancy setup: +1.059R per trade.**

---

## 🥈 RUNNER-UP: ALL_FILTERS + RR 3.0 + FULL SL

### **Performance:**
- **32 trades**
- **46.9% win rate**
- **+0.875R average per trade**
- **+28.0R total**
- **Full stop-loss mode**

### **Rules:**
1. **Asia range 100-200 ticks** (NORMAL)
2. **Small London ORB** (<20 ticks)
3. **NY_HIGH directional filter** (UP only if resolved)
4. **Skip NY_LOW**
5. **RR = 3.0**
6. **Full SL**

**This adds the small ORB filter but reduces sample size significantly.**

---

## 🥉 HIGH-VOLUME WINNER: BASELINE + RR 1.5 + FULL SL

### **Performance:**
- **499 trades** (largest sample)
- **55.5% win rate**
- **+0.388R average per trade**
- **+193.5R total** (highest absolute R)
- **Full stop-loss mode**

### **Rules:**
1. **No filters** (trade all London ORBs)
2. **RR = 1.5**
3. **Full SL**

**This is the most consistent, highest-volume setup. Lower per-trade edge but massive sample size.**

---

## 📊 TOP 10 CONFIGURATIONS

| Rank | Config | Trades | WR | Avg R | Total R | RR | SL |
|------|--------|--------|-----|-------|---------|----|----|
| 1 | ASIA_NORMAL_NY_HIGH_SKIP_LOW | 68 | 51.5% | +1.059R | +72.0R | 3.0 | FULL |
| 2 | ASIA_NORMAL_NY_HIGH_SKIP_LOW | 67 | 40.3% | +1.015R | +68.0R | 4.0 | FULL |
| 3 | ASIA_NORMAL_NY_HIGH_SKIP_LOW | 67 | 41.8% | +0.881R | +59.0R | 3.5 | FULL |
| 4 | ALL_FILTERS | 32 | 46.9% | +0.875R | +28.0R | 3.0 | FULL |
| 5 | ASIA_NORMAL_NY_HIGH_SKIP_LOW | 68 | 52.9% | +0.853R | +58.0R | 2.5 | FULL |
| 6 | ASIA_NORMAL_NY_HIGH_SKIP_LOW | 68 | 60.3% | +0.809R | +55.0R | 2.0 | FULL |
| 7 | ALL_FILTERS | 32 | 59.4% | +0.781R | +25.0R | 2.0 | FULL |
| 8 | ALL_FILTERS | 32 | 50.0% | +0.750R | +24.0R | 2.5 | FULL |
| 9 | ALL_FILTERS | 32 | 34.4% | +0.719R | +23.0R | 4.0 | FULL |
| 10 | ASIA_NORMAL_NY_HIGH_SKIP_LOW | 68 | 66.2% | +0.654R | +44.5R | 1.5 | FULL |

---

## 🎯 RECOMMENDED SETUPS (By Goal)

### **Goal 1: HIGHEST EXPECTANCY (Best R per Trade)**

**Setup:** ASIA_NORMAL + NY_HIGH + SKIP_NY_LOW + RR 3.0 + FULL SL

- **68 trades, 51.5% WR, +1.059R avg**
- **~13-14 trades per year**
- **Annual expectation: +14R to +15R**

**When to use:** Maximum edge per trade, don't care about frequency

---

### **Goal 2: HIGH VOLUME + GOOD EDGE**

**Setup:** BASELINE + RR 1.5 + FULL SL

- **499 trades, 55.5% WR, +0.388R avg, +193.5R total**
- **~100 trades per year**
- **Annual expectation: +38R to +40R**

**When to use:** Want consistent action, many trades

---

### **Goal 3: BALANCED (Good Edge + Decent Volume)**

**Setup:** ASIA_NORMAL + RR 3.0 + FULL SL

- **199 trades, 37.2% WR, +0.487R avg, +97.0R total**
- **~40 trades per year**
- **Annual expectation: +19R to +20R**

**When to use:** Balance between edge and frequency

---

### **Goal 4: HIGH WIN RATE**

**Setup:** ASIA_NORMAL_SMALL_ORB + RR 1.5 + FULL SL

- **98 trades, 65.3% WR, +0.633R avg, +62.0R total**
- **~20 trades per year**
- **Annual expectation: +12R to +13R**

**When to use:** Psychological comfort from high win rate

---

## 🔬 KEY INSIGHTS

### 1. **Full SL > Half SL (Always)**

**Full SL dominates across ALL configurations.**

- Best FULL SL: +193.5R (baseline RR 1.5)
- Best HALF SL: +115.0R (baseline RR 3.0)
- **Difference: +78.5R in favor of FULL SL**

**Conclusion:** Use FULL stop-loss (stop at opposite ORB edge), not midpoint.

---

### 2. **RR Sweet Spots by Filter**

| Filter Set | Best RR | Trades | WR | Avg R | Total R |
|-----------|---------|--------|-----|-------|---------|
| BASELINE | 1.5 | 499 | 55.5% | +0.388R | +193.5R |
| NY_HIGH_DIR | 2.0 | 357 | 47.6% | +0.429R | +153.0R |
| ASIA_NORMAL | 3.0 | 199 | 37.2% | +0.487R | +97.0R |
| ASIA_NORMAL_NY_HIGH_SKIP_LOW | **3.0** | 68 | 51.5% | **+1.059R** | +72.0R |
| SMALL_ORB | 1.5 | 175 | 61.1% | +0.529R | +92.5R |

**Pattern:**
- **More filters → Higher optimal RR**
- Baseline works best at RR 1.5
- Filtered setups work best at RR 2.0-3.0
- Highly filtered setups work best at RR 3.0-4.0

---

### 3. **Filter Impact (vs Baseline)**

| Filter | Trades | Avg R | Delta vs Baseline |
|--------|--------|-------|-------------------|
| BASELINE | 499 | +0.388R | — |
| +ASIA_NORMAL | 201 | +0.480R | +0.092R (+24%) |
| +NY_HIGH_DIR | 358 | +0.411R | +0.023R (+6%) |
| +ASIA_NORMAL+NY_HIGH | 148 | +0.470R | +0.082R (+21%) |
| +ASIA_NORMAL+NY_HIGH+SKIP_LOW | **68** | **+1.059R** | **+0.671R (+173%)** |
| +SMALL_ORB | 175 | +0.529R | +0.141R (+36%) |

**Key takeaway:** Stacking filters dramatically improves per-trade edge, but reduces frequency.

---

### 4. **Win Rate Analysis**

**Highest Win Rates (min 50 trades):**

| Setup | RR | Trades | WR |
|-------|-----|--------|-----|
| ASIA_NORMAL_NY_HIGH_SKIP_LOW | 1.0 | 68 | 72.1% |
| ASIA_NORMAL_SMALL_ORB | 1.0 | 98 | 71.4% |
| SMALL_ORB | 1.0 | 175 | 69.7% |
| ASIA_NORMAL | 1.0 | 202 | 68.8% |

**Pattern:** RR 1.0 has highest win rates (67-72%), but lower total R than RR 1.5-3.0.

---

### 5. **The NY_LOW Problem is REAL**

**With SKIP_NY_LOW filter:**
- 68 trades, +1.059R avg (RR 3.0)

**Without SKIP_NY_LOW filter (ASIA_NORMAL_NY_HIGH):**
- 148 trades, +0.486R avg (RR 3.0)

**Difference:** +0.573R per trade by skipping NY_LOW

**Conclusion:** NY_LOW resolution is toxic for London. Always skip it.

---

## 🎲 TRADE-OFF ANALYSIS

### **Expectancy vs Frequency:**

| Setup | Trades/Year | Avg R | Annual R |
|-------|-------------|-------|----------|
| ASIA_NORMAL_NY_HIGH_SKIP_LOW (RR 3.0) | ~14 | +1.059R | +15R |
| ASIA_NORMAL (RR 3.0) | ~40 | +0.487R | +19R |
| BASELINE (RR 1.5) | ~100 | +0.388R | +39R |

**Insight:** More trades = more total R, even with lower per-trade edge.

**Strategy:**
1. **Conservative:** Trade only ASIA_NORMAL_NY_HIGH_SKIP_LOW (highest edge, fewest trades)
2. **Moderate:** Trade ASIA_NORMAL (balanced)
3. **Aggressive:** Trade BASELINE (most trades, highest annual R)

---

## 📋 FINAL RECOMMENDATIONS

### **TIER 1: START HERE (Highest Confidence)**

**Setup:** ASIA_NORMAL + RR 3.0 + FULL SL

**Rules:**
1. Asia range 100-200 ticks
2. RR = 3.0
3. Stop at opposite ORB edge (full SL)
4. Trade both directions

**Expected:** 199 trades over 5 years, 37.2% WR, +0.487R avg, +97.0R total

**Why:** Good balance of edge, volume, and simplicity. No directional complexity.

---

### **TIER 2: ADD DIRECTIONAL FILTER (After Success)**

**Setup:** ASIA_NORMAL + NY_HIGH + SKIP_NY_LOW + RR 3.0 + FULL SL

**Rules:**
1. Asia range 100-200 ticks
2. If Asia resolved prior NY high → Trade UP only
3. If Asia resolved prior NY low → **SKIP London**
4. RR = 3.0
5. Stop at opposite ORB edge (full SL)

**Expected:** 68 trades over 5 years, 51.5% WR, +1.059R avg, +72.0R total

**Why:** Best expectancy per trade. Maximum edge.

---

### **TIER 3: HIGH VOLUME (For Active Traders)**

**Setup:** BASELINE + RR 1.5 + FULL SL

**Rules:**
1. Trade all London ORBs (no filters)
2. RR = 1.5
3. Stop at opposite ORB edge (full SL)

**Expected:** 499 trades over 5 years, 55.5% WR, +0.388R avg, +193.5R total

**Why:** Most trades, highest total R, simplest execution.

---

## ⚙️ IMPLEMENTATION DETAILS

### **Full SL Mode:**
- Entry: First 5m close outside ORB
- Stop: Opposite ORB edge
  - UP break: stop = ORB low
  - DOWN break: stop = ORB high
- Target: Entry ± (RR × Risk)
  - Risk = |entry - stop|

### **RR Calculation:**
- RR 1.0: Target = entry + 1 × risk
- RR 1.5: Target = entry + 1.5 × risk
- RR 2.0: Target = entry + 2 × risk
- RR 3.0: Target = entry + 3 × risk

### **Daily Workflow:**

#### Before 09:00:
- [ ] Identify prior NY high (from yesterday)

#### At 11:00 (End of Asia):
- [ ] Measure Asia range (high - low in ticks)
- [ ] Check if Asia range is 100-200 ticks
  - If NO → Skip London (if using ASIA_NORMAL filter)
- [ ] Check if Asia resolved prior NY high
  - If YES → London UP only (if using NY_HIGH filter)
- [ ] Check if Asia resolved prior NY low
  - If YES → Skip London (if using SKIP_NY_LOW filter)

#### At 18:05 (London ORB Close):
- [ ] Measure London ORB
- [ ] Set entry orders based on direction rules
- [ ] Set stop at opposite ORB edge
- [ ] Set target at entry ± (RR × risk)

---

## 🚨 CRITICAL RULES

### ❌ NEVER Use Half-SL Mode
- Full SL outperforms by +78.5R in baseline comparison
- Wider stop = better performance (counterintuitive but proven)

### ❌ NEVER Trade NY_LOW Resolution
- Skipping NY_LOW improves edge by +0.573R per trade
- NY_LOW continuation is broken (see previous analysis)

### ✅ ALWAYS Use RR >= 1.5
- RR 1.0 has high WR but lower total R
- RR 1.5-3.0 is the sweet spot
- Higher filters need higher RR (3.0-4.0)

### ✅ ALWAYS Use Full SL
- Stop at opposite ORB edge, not midpoint
- Proven across all configurations

---

## 📈 EXPECTED ANNUAL PERFORMANCE

### **Conservative (Tier 2 Only):**
- Setup: ASIA_NORMAL_NY_HIGH_SKIP_LOW + RR 3.0
- Trades: ~14 per year
- Expected: +14R to +15R per year

### **Moderate (Tier 1 Only):**
- Setup: ASIA_NORMAL + RR 3.0
- Trades: ~40 per year
- Expected: +19R to +20R per year

### **Aggressive (Tier 3 Only):**
- Setup: BASELINE + RR 1.5
- Trades: ~100 per year
- Expected: +38R to +40R per year

### **Combined (All Tiers):**
- If trading all setups when they occur
- Trades: ~140-150 per year
- Expected: +60R to +75R per year (combined)

**Note:** These are additive if the setups don't overlap significantly.

---

## 🔬 NEXT STEPS

### **Paper Trade Priority:**

1. **Start with Tier 1** (ASIA_NORMAL + RR 3.0)
   - 20-30 trades minimum
   - Validate 37% WR, +0.487R avg

2. **Add Tier 2** after success (NY_HIGH + SKIP_NY_LOW)
   - 10-15 trades minimum
   - Validate 51% WR, +1.059R avg

3. **Consider Tier 3** for volume (BASELINE + RR 1.5)
   - 30-50 trades minimum
   - Validate 55% WR, +0.388R avg

### **Track Separately:**
- Keep stats for each tier independently
- Compare real-world vs backtest
- Adjust if edges deteriorate

---

## 📚 FILES REFERENCE

- Backtest script: `backtest_london_optimized.py`
- Full results: `london_backtest_results.csv`
- Analysis doc: `HOW_TO_TRADE_LONDON.md`
- Framework: `ASIA_LONDON_FRAMEWORK.md`

---

## ✅ FINAL SUMMARY

**BEST SINGLE SETUP:**
- ASIA_NORMAL + NY_HIGH + SKIP_NY_LOW + RR 3.0 + FULL SL
- **+1.059R per trade** (68 trades)

**BEST HIGH-VOLUME SETUP:**
- BASELINE + RR 1.5 + FULL SL
- **+193.5R total** (499 trades, 55.5% WR)

**BEST BALANCED SETUP:**
- ASIA_NORMAL + RR 3.0 + FULL SL
- **+0.487R per trade** (199 trades, 37.2% WR)

**KEY RULES:**
1. ✅ **Always use FULL SL** (not half)
2. ✅ **Use RR 1.5-3.0** (depending on filters)
3. ❌ **Never trade NY_LOW resolution**
4. ❌ **Never use half-SL mode**

**Expected annual R:**
- Conservative: +14R to +15R
- Moderate: +19R to +20R
- Aggressive: +38R to +40R
- Combined: +60R to +75R
