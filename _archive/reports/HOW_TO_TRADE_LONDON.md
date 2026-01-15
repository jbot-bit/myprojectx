# How to Trade London ORB - Comprehensive Analysis

**Date:** 2026-01-12
**Dataset:** 502-503 London ORB trades (2020-2026)
**Baseline:** 36.1% WR, +0.109R avg, +54.9R total

---

## 🎯 THE BEST LONDON SETUP (Simple, High Confidence)

### **FILTER: Asia Range 100-200 Ticks**

**Performance:**
- **208 trades, 42.3% WR, +0.316R avg, +65.7R total**
- **+0.207R vs baseline** (improvement)
- **+120% better** than baseline
- **41% of all London trades** (good sample size)

**Rule:**
1. At 11:00 (end of Asia), measure Asia range: `asia_high - asia_low`
2. If range is **100-200 ticks** → Trade London ORB (both directions)
3. If range is < 100 or > 200 ticks → **SKIP London**

**Why it works:**
- Tight Asia (<100 ticks) = no energy → London flat (-0.070R)
- Normal Asia (100-200 ticks) = proper volatility → London expands (+0.316R) ✅
- Wide Asia (200-300 ticks) = exhausted → London weak (+0.054R)
- Expanded Asia (>300 ticks) = chaos → London loses (-0.089R)

**This is the simplest, strongest London filter.**

---

## 🔥 SECONDARY FILTER: Small London ORB (<20 Ticks)

### **Performance:**
- **184 trades (tiny + small), 40.8% WR, +0.200R avg, +36.8R total**
- **Small (10-20 ticks):** 159 trades, 39.6% WR, +0.198R avg, +31.5R total
- **Tiny (<10 ticks):** 25 trades, 48.0% WR, +0.213R avg, +5.3R total

**Large/Normal London ORBs (20-30 ticks):** 153 trades, 32.0% WR, -0.017R avg **[FLAT]**

**Rule:**
- At 18:05 (London ORB close), measure ORB size
- If ORB < 20 ticks → Trade the break
- If ORB >= 20 ticks → **SKIP** (or use NY_HIGH filter)

**Why it works:**
- Small ORBs = tight range, explosive breakouts
- Large ORBs = already extended, less follow-through

**Can combine with Asia range filter for even better results.**

---

## 🎲 ENGINE A: Prior Inventory (Directional Edge)

### **NY_HIGH Resolution → London LONG**

**Overall Performance (all timing):**
- 147 trades, 38.1% WR, +0.160R avg, +23.6R total
- London UP (continuation): 90 trades, 43.3% WR, +0.281R avg
- London DOWN (fade): 57 trades, 29.8% WR, -0.030R avg **[TOXIC]**

**Broken Down by Timing:**

#### **EARLY (Resolved by 09:00):**
- London UP: **121 trades, 43.0% WR, +0.289R avg, +35.0R total** ✅
- London DOWN: 92 trades, 30.4% WR, -0.031R avg, -2.8R total ❌
- **Delta:** +0.320R (continuation > fade)

#### **MID (Resolved by 10:00):**
- London UP: 10 trades, 50.0% WR, +0.567R avg, +5.7R total
- London DOWN: 8 trades, 50.0% WR, +0.661R avg, +5.3R total
- **Small sample, inconclusive**

#### **LATE (Resolved by 11:00):**
- London UP: **10 trades, 60.0% WR, +0.729R avg, +7.3R total** 🔥
- London DOWN: 6 trades, 33.3% WR, +0.136R avg, +0.8R total
- **Delta:** +0.594R (continuation > fade)
- **Tiny sample, but strong signal**

**Rule:**
1. Before 09:00, identify prior NY high (max of 2300 and 0030 from previous day)
2. At 11:00, check if Asia high >= prior NY high
3. If YES → **ONLY trade London UP** breaks, skip DOWN
4. Expected: 43% WR, +0.289R avg (121 trades for early resolution)

**Note:** Late resolution (by 11:00) has amazing stats (+0.729R avg, 60% WR) but only 10 trades. Needs more data.

---

## ❌ NY_LOW IS BROKEN - DO NOT USE

### **NY_LOW Resolution → FAILS**

**Overall:**
- 98 trades, 32.7% WR, +0.040R avg (barely positive)
- Continuation (London DOWN): **28.8% WR, -0.058R avg** ❌ LOSES
- Fade (London UP): 37.0% WR, +0.150R avg (reversal works??)

**By Timing:**
- **EARLY_0900:** Cont -0.167R, Fade +0.126R (fade better)
- **MID_1000:** Cont -0.116R, Fade +0.186R (fade better)
- **LATE_1100:** Cont +0.069R, Fade -0.819R (finally cont works but fade TOXIC)

**Conclusion:** NY_LOW pattern is unreliable. Skip it entirely.

---

## 🧩 COMBINATION PATTERNS

### **Pattern 1: NY_HIGH + Small London ORB**

**Condition:** Asia resolved NY high + London ORB < 20 ticks
**Performance:** 53 trades, 43.4% WR, +0.281R avg, +14.9R total
**Verdict:** Strong combo, stacks well

### **Pattern 2: NY_HIGH + Wide Asia**

**Condition:** Asia resolved NY high + Asia range > 200 ticks
**Performance:** 84 trades, 40.5% WR, +0.214R avg, +18.0R total
**Verdict:** Decent, but wide Asia alone is weak (contradiction)

### **Pattern 3: NY_HIGH Resolved by 10:00**

**Condition:** Asia resolved NY high by 10:00 ORB
**Performance:** 122 trades, 41.8% WR, +0.257R avg, +31.4R total
**Verdict:** Solid, captures early + mid resolution

---

## 📊 COMPLETE PERFORMANCE BREAKDOWN

### **Asia Range (Most Important Filter)**

| Asia Range | Trades | WR | Avg R | Total R | Verdict |
|-----------|--------|-----|-------|---------|---------|
| Tight (<100 ticks) | 72 | 30.6% | -0.070R | -5.0R | ❌ SKIP |
| **Normal (100-200 ticks)** | **208** | **42.3%** | **+0.316R** | **+65.7R** | ✅ **BEST** |
| Wide (200-300 ticks) | 92 | 33.7% | +0.054R | +5.0R | ~ Weak |
| Expanded (>300 ticks) | 131 | 30.5% | -0.089R | -11.6R | ❌ SKIP |

### **London ORB Size**

| ORB Size | Trades | WR | Avg R | Total R | Verdict |
|----------|--------|-----|-------|---------|---------|
| Tiny (<10 ticks) | 25 | 48.0% | +0.213R | +5.3R | ✅ Trade |
| **Small (10-20 ticks)** | **159** | **39.6%** | **+0.198R** | **+31.5R** | ✅ **TRADE** |
| Normal (20-30 ticks) | 153 | 32.0% | -0.017R | -2.6R | ❌ SKIP |
| Large (30-50 ticks) | 118 | 33.9% | +0.096R | +11.3R | ~ Weak |
| Huge (>50 ticks) | 48 | 35.4% | +0.179R | +8.6R | ~ OK |

### **Prior Inventory + Timing**

| Pattern | Trades | WR | Avg R | Total R | Verdict |
|---------|--------|-----|-------|---------|---------|
| **NY_HIGH (Early) → London UP** | **121** | **43.0%** | **+0.289R** | **+35.0R** | ✅ **TRADE** |
| NY_HIGH (Late) → London UP | 10 | 60.0% | +0.729R | +7.3R | 🔥 Amazing (tiny sample) |
| NY_HIGH → London DOWN | 92-106 | 29.8-30.4% | -0.030R | -2.8R | ❌ TOXIC |
| NY_LOW → London DOWN | 76-97 | 26.3-28.8% | -0.167R to -0.058R | -12.7R to -3.0R | ❌ BROKEN |

---

## 🎯 RECOMMENDED TRADING RULES

### **TIER 1: High-Confidence (START HERE)**

**Rule:** Asia Range 100-200 Ticks Filter
- **Setup:** At 11:00, measure Asia range (asia_high - asia_low)
- **Trade:** If 100-200 ticks → Trade London ORB (both directions)
- **Skip:** If < 100 or > 200 ticks → Skip London
- **Expected:** 42.3% WR, +0.316R avg
- **Sample:** 208 trades
- **Confidence:** **HIGH** ✅

---

### **TIER 2: Directional Edge (Add This)**

**Rule:** NY_HIGH → London LONG Only
- **Setup:** Before 09:00, identify prior NY high
- **Check:** At 11:00, did Asia sweep prior NY high?
- **Trade:** If YES → ONLY trade London UP breaks, skip DOWN
- **Skip:** If NO → Use Tier 1 filter only
- **Expected:** 43.0% WR, +0.289R avg (early resolution)
- **Sample:** 121 trades
- **Confidence:** **HIGH** ✅

---

### **TIER 3: London ORB Size Filter (Optional Stack)**

**Rule:** Small London ORB Filter
- **Setup:** At 18:05, measure London ORB size
- **Trade:** If ORB < 20 ticks → Trade the break
- **Skip:** If ORB >= 20 ticks → Skip (unless Tier 2 applies)
- **Expected:** 39.6% WR, +0.198R avg
- **Sample:** 159 trades
- **Confidence:** **MEDIUM-HIGH** ✅

**Note:** This is a late filter (after ORB forms), so less useful for planning. Best used as confirmation.

---

## 🧮 STACKING FILTERS (Advanced)

### **Stack 1: Asia Range + NY_HIGH**

**Condition:** Asia range 100-200 ticks + Asia resolved NY high
- **Trade:** London UP only
- **Expected:** Better than either filter alone (estimated 45%+ WR)
- **Sample:** ~60-80 trades (need to verify)

### **Stack 2: Asia Range + Small ORB**

**Condition:** Asia range 100-200 ticks + London ORB < 20 ticks
- **Trade:** Both directions
- **Expected:** Better than either filter alone (estimated 44%+ WR)
- **Sample:** ~70-90 trades (need to verify)

### **Stack 3: All Three**

**Condition:** Asia 100-200 ticks + NY_HIGH + London ORB < 20 ticks
- **Trade:** London UP only
- **Expected:** Best possible (estimated 47%+ WR, +0.35R avg)
- **Sample:** ~25-35 trades (small but high quality)

**Note:** More filters = fewer trades but higher quality. Start with Tier 1 only, add Tier 2 after paper trading success.

---

## 🚨 DO NOT TRADE THESE

### ❌ Skip Patterns:

1. **Asia range < 100 ticks** (-0.070R avg, 30.6% WR)
2. **Asia range > 300 ticks** (-0.089R avg, 30.5% WR)
3. **London ORB 20-30 ticks** (-0.017R avg, 32.0% WR - flat)
4. **NY_LOW resolution** (broken, unreliable)
5. **NY_HIGH → London DOWN** (-0.030R avg, 29.8% WR - toxic)

---

## 📝 IMPLEMENTATION CHECKLIST

### Daily Workflow:

#### **Before 09:00:**
- [ ] Get prior NY high (max of yesterday's 2300 and 0030 ORB highs)

#### **At 11:00 (End of Asia):**
- [ ] Calculate Asia range: `asia_high - asia_low` in ticks
- [ ] Check: Is Asia range 100-200 ticks?
  - If NO → **Skip London**
  - If YES → Proceed to next check
- [ ] Check: Did Asia sweep prior NY high?
  - If YES → **Trade London UP ONLY**
  - If NO → **Trade both directions**

#### **At 18:05 (London ORB Close):**
- [ ] Measure London ORB size
- [ ] Optional: If ORB >= 20 ticks and no NY_HIGH filter → Consider skip
- [ ] Wait for break confirmation
- [ ] Execute trade based on direction rules

#### **Risk Management:**
- Standard: 1R = ORB range, stop at midpoint, target 2.0R
- Position size: Same as other ORBs (1 contract baseline)
- Optional: Increase to 1.5x size if all filters align (Tier 1 + Tier 2 + small ORB)

---

## 🎓 KEY INSIGHTS

### What Makes London Work:

1. **Asia volatility matters most** - 100-200 tick range is the sweet spot
2. **Small London ORBs break cleanly** - compressed range, explosive move
3. **Prior inventory creates directional bias** - NY_HIGH → London UP continuation
4. **Timing doesn't matter much** - Early or late NY_HIGH resolution both work
5. **London is NOT like Asia** - Different personality, needs different filters

### What Doesn't Work:

1. **Extreme Asia ranges** - Too tight or too wide both fail
2. **Large London ORBs** - Already extended, poor follow-through
3. **NY_LOW continuation** - Broken pattern, avoid entirely
4. **Fading NY_HIGH** - Toxic (-0.030R avg)

---

## 📈 EXPECTED PERFORMANCE

### **Tier 1 Only (Asia Range 100-200)**

- Trades per year: ~40-50 (208 trades over 5 years)
- Win rate: 42.3%
- Avg R: +0.316R
- Annual expectation: +12.6R to +15.8R

### **Tier 1 + Tier 2 (Asia Range + NY_HIGH)**

- Trades per year: ~15-25 (estimated 60-80 trades over 5 years)
- Win rate: ~45% (estimated)
- Avg R: ~+0.35R (estimated)
- Annual expectation: +5.2R to +8.8R

**Combined (if trading both setups):** ~+18R to +25R per year from London alone

---

## 🔬 NEXT STEPS (Optional Refinement)

### Tests to Run:

1. **Verify stacking performance** - Test Asia range + NY_HIGH combined
2. **Test NY_HIGH late resolution** - Only 10 trades, needs more data
3. **Investigate NY_LOW reversal** - Why does fade work better than continuation?
4. **Test Asia net direction** - Does Asia trend direction matter?
5. **Test pre-London range** - Does 11:00-18:00 activity matter? (currently all <30 ticks)

### Implementation:

1. **Paper trade Tier 1 for 20-30 trades** - Validate Asia range filter
2. **Add Tier 2 after success** - Implement NY_HIGH direction filter
3. **Track results separately** - London performance vs Asia ORBs
4. **Adjust if needed** - If real-world results differ significantly

---

## ✅ FINAL RECOMMENDATION

**START WITH THIS:**

1. **Trade London ONLY when Asia range is 100-200 ticks**
   - 208 trades, 42.3% WR, +0.316R avg
   - Simple, high confidence, large sample

2. **Add direction filter after paper trading success:**
   - If Asia swept prior NY high → ONLY trade UP
   - Otherwise → trade both directions

3. **Skip London if:**
   - Asia range < 100 or > 200 ticks
   - No other exceptions

**This is the clearest, most tradeable London setup.**

---

## 📚 REFERENCES

- Analysis script: `analyze_london_comprehensive.py`
- Previous test: `test_london_prior_inventory.py`
- Framework: `ASIA_LONDON_FRAMEWORK.md`
- Data: `daily_features_v2`, `orb_trades_5m_exec_orbr`
- Sample: 502-503 London ORB trades, 2020-2026
