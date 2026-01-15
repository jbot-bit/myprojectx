# High-Confidence Trading Ruleset (CURRENT DATA)

**Created:** 2026-01-12
**Based on:** Current database (2024-01-02 to 2026-01-10)
**Dataset:** 2 years, 740 days
**Approach:** Conservative - only filter what clearly doesn't work

**⚠️ NOTE:** This uses 2024-2026 data only. After overnight backfill of 2020-2023, this will be updated with 5+ years of data.

---

## 🚨 PROP ACCOUNT WARNING

**Asia ORBs at full frequency (3 trades/day) are NOT PROP-SAFE.**

**Issue**: Trading all 3 Asia ORBs on the same day = potential **-3R daily loss** (clustered losses)

**For prop accounts, see**: `ASIA_PROP_SAFETY_REPORT.md`

**Prop-safe modes** (max 1 trade/day):
- ✅ **11:00 ORB ONLY** (RR 1.0): Safest, 64.9% WR, max 5-trade losing streak
- ✅ **10:00 ORB ONLY** (RR 2.5): Highest edge +0.338R avg, max 8-trade losing streak
- ✅ **FIRST_BREAK** (09→10→11): Balanced, 62.7% WR, max 6-trade losing streak

**Personal account**: Can trade all 3 ORBs if you can handle -3R daily swings

---

## 📊 CURRENT DATA STATUS

**Available:**
- Date range: 2024-01-02 to 2026-01-10
- Total days: 740
- Asia ORBs (09:00, 10:00, 11:00): ~500 trades each
- London ORB (18:00): ~508 trades
- Sample size: Adequate for initial trading (>500 per ORB)

**After backfill (tonight):**
- Date range: 2020-12-20 to 2026-01-10
- Total days: ~1,800
- More robust statistics
- Out-of-sample validation possible

---

## 🏆 BEST ASIA ORB CONFIGURATIONS (Current Data)

### **09:00 ORB**

**Best Setup:** RR 1.0, FULL SL, No Filters
- **487-507 trades**
- **62.8-63.3% win rate**
- **+0.257 to +0.266R average**
- **+125.0 to +135.0R total**

**With Filters (MAX_STOP=100, ASIA_TP_CAP=150):**
- 487 trades, 62.8% WR, +0.257R avg, +125.0R total

**Verdict:** ✅ **TRADE 09:00** (contrary to old docs)

---

### **10:00 ORB**

**Best Setup:** RR 2.5-3.0, FULL SL, No Filters or MAX_STOP=100
- **489-503 trades**
- **33.3-38.0% win rate**
- **+0.323 to +0.342R average**
- **+159.0 to +167.0R total**

**With Filters (MAX_STOP=100, ASIA_TP_CAP=150):**
- 455 trades, 38.2% WR, +0.338R avg, +154.0R total

**Verdict:** ✅ **BEST ASIA ORB** (highest total R)

---

### **11:00 ORB**

**Best Setup:** RR 1.0, FULL SL, No Filters
- **502 trades**
- **64.9% win rate**
- **+0.299R average**
- **+150.0R total**

**With Filters (MAX_STOP=100, ASIA_TP_CAP=150):**
- 465 trades, 64.9% WR, +0.299R avg, +139.0R total

**Verdict:** ✅ **HIGHEST WIN RATE**

---

## 🏆 BEST LONDON ORB CONFIGURATIONS (Current Data)

### **18:00 ORB**

**Best Setup (Highest Edge):** ASIA_NORMAL + NY_HIGH + SKIP_NY_LOW + RR 3.0 + FULL SL
- **68 trades**
- **51.5% win rate**
- **+1.059R average** 🔥
- **+72.0R total**

**Best Setup (Highest Volume):** BASELINE + RR 1.5 + FULL SL
- **499 trades**
- **55.5% win rate**
- **+0.388R average**
- **+193.5R total**

**Verdict:** ✅ **TRADE LONDON** (multiple viable setups)

---

## 📋 RECOMMENDED TRADING RULES

### **TIER 1: ASIA ORBS (Start Here)**

**Trade all 3 Asia ORBs with filters:**

| ORB | RR | SL Mode | Filters | Expected |
|-----|-----|---------|---------|----------|
| **09:00** | 1.0 | FULL | MAX_STOP=100, TP_CAP=150 | +125.0R (487 trades, 62.8% WR) |
| **10:00** | 2.5 | FULL | MAX_STOP=100, TP_CAP=150 | +154.0R (455 trades, 38.2% WR) |
| **11:00** | 1.0 | FULL | MAX_STOP=100, TP_CAP=150 | +139.0R (465 trades, 64.9% WR) |

**Combined Performance (with filters):**
- **Total:** +418.0R (1,407 trades)
- **Average:** +0.297R per trade
- **Annual (2 years):** ~+209R per year

**Why these settings:**
- 09:00 + 11:00: RR 1.0 for high win rate consistency
- 10:00: RR 2.5 for higher R per trade (despite lower WR)
- Full SL: Outperforms half-SL across all ORBs
- Filters prevent outliers (stops >100 ticks, targets >150 ticks)

---

### **TIER 2: LONDON ORB (Add After Asia Success)**

**Setup:** ASIA_NORMAL + RR 3.0 + FULL SL

**Rules:**
1. Asia range 100-200 ticks
2. RR = 3.0
3. Stop at opposite ORB edge (full SL)
4. Optional: Add NY_HIGH directional filter

**Expected:**
- 199 trades (baseline), 37.2% WR, +0.487R avg, +97.0R total
- **Annual:** ~+50R per year

**With NY_HIGH + SKIP_NY_LOW:**
- 68 trades, 51.5% WR, +1.059R avg, +72.0R total
- **Annual:** ~+36R per year (but fewer trades)

---

## 📊 COMPARISON: SKIP 09:00 vs TRADE ALL

**Old recommendation (outdated docs):** Skip 09:00, trade only 10:00 + 11:00

**Current data shows:**
- Trade all 3 ORBs: +418.0R
- Skip 09:00, trade 10:00 + 11:00: +293.0R
- **Difference:** +125.0R in favor of trading 09:00

**Conclusion:** ✅ **Trade 09:00** with current data (RR 1.0, 62.8% WR)

---

## 🎯 COMPLETE RECOMMENDED STRATEGY

### **Asia Session (09:00-11:00):**

**09:00 ORB:**
- RR: 1.0
- SL: Full (opposite ORB edge)
- Filters: MAX_STOP=100, TP_CAP=150
- Expected: 62.8% WR, +0.257R avg

**10:00 ORB:**
- RR: 2.5
- SL: Full (opposite ORB edge)
- Filters: MAX_STOP=100, TP_CAP=150
- Expected: 38.2% WR, +0.338R avg

**11:00 ORB:**
- RR: 1.0
- SL: Full (opposite ORB edge)
- Filters: MAX_STOP=100, TP_CAP=150
- Expected: 64.9% WR, +0.299R avg

---

### **London Session (18:00):**

**Option A (Simpler):**
- Asia range 100-200 ticks only
- RR: 3.0
- SL: Full
- Expected: 37.2% WR, +0.487R avg (~40 trades/year)

**Option B (Higher Edge):**
- Asia range 100-200 ticks
- NY_HIGH → London UP only
- Skip if NY_LOW resolved
- RR: 3.0
- SL: Full
- Expected: 51.5% WR, +1.059R avg (~14 trades/year)

---

## 📈 EXPECTED ANNUAL PERFORMANCE

**Based on 2 years of data:**

| Component | Annual R | Trades/Year |
|-----------|----------|-------------|
| Asia ORBs (all 3) | +209R | ~700 |
| London (Option A) | +50R | ~100 |
| London (Option B) | +36R | ~34 |
| **Total (Asia + London A)** | **+259R** | **~800** |

**Conservative Estimate (50-80% of backtest):**
- Real-world: +130R to +207R per year
- Accounts for slippage, commissions, psychology

---

## ⚙️ IMPLEMENTATION DETAILS

### **Universal Settings:**

- **Timeframe:** 5-minute bars
- **ORB Period:** First 5 minutes of session
- **Entry Confirmation:** 1 consecutive 5m close outside ORB
- **Stop Placement:** Opposite ORB edge (full SL mode)
- **Buffer:** 0 ticks
- **Filters:**
  - MAX_STOP = 100 ticks
  - ASIA_TP_CAP = 150 ticks (Asia ORBs only)

### **Risk Calculation:**

**09:00 + 11:00 (RR 1.0):**
- Risk = |ORB_high - ORB_low|
- Target = Entry ± (1.0 × Risk)
- Stop = Opposite ORB edge

**10:00 (RR 2.5):**
- Risk = |ORB_high - ORB_low|
- Target = Entry ± (2.5 × Risk)
- Stop = Opposite ORB edge

**London (RR 3.0):**
- Risk = |ORB_high - ORB_low|
- Target = Entry ± (3.0 × Risk)
- Stop = Opposite ORB edge

---

## ⚠️ KEY DIFFERENCES FROM OLD DOCS

| Aspect | Old Docs (2020-2026?) | Current Data (2024-2026) |
|--------|----------------------|--------------------------|
| **09:00 verdict** | Skip (-22.8R) | ✅ Trade (+125.0R with RR 1.0) |
| **09:00 best RR** | 2.0 (if trading) | 1.0 (62.8% WR) |
| **10:00 best RR** | 2.0 | 2.5-3.0 |
| **11:00 best RR** | 2.0 (?) | 1.0 (64.9% WR) |
| **London best RR** | 2.0 (?) | 3.0 (51.5% WR with filters) |
| **Sample size** | "2,845 trades" | 1,407 Asia + 508 London = 1,915 |

**Key insight:** 09:00 works well at RR 1.0 with current data, contrary to old recommendations.

---

## 📝 FILTERS EXPLAINED

### **MAX_STOP = 100 ticks:**
- Skip trades where ORB range > 100 ticks
- Prevents trading outlier volatile days
- Improves consistency

### **ASIA_TP_CAP = 150 ticks:**
- For Asia ORBs only
- Prevents unrealistic targets on huge ORB days
- Example: If ORB = 80 ticks and RR = 2.5, target would be 200 ticks → capped at 150
- London doesn't need this (already has Asia range filter)

---

## 🚨 CRITICAL RULES

### ❌ NEVER:
- Use half-SL mode (full SL always better)
- Trade 23:00 or 00:30 ORBs (lose consistently)
- Trade London if Asia range < 100 or > 200 ticks
- Trade London DOWN if Asia resolved NY_HIGH (toxic: -0.030R avg)
- Trade London at all if Asia resolved NY_LOW (broken pattern)

### ✅ ALWAYS:
- Use full SL (stop at opposite ORB edge)
- Apply MAX_STOP=100 filter for Asia ORBs
- Apply ASIA_TP_CAP=150 filter for Asia ORBs
- Use RR 1.0 for 09:00 and 11:00 (high WR)
- Use RR 2.5 for 10:00 (best total R)
- Use RR 3.0 for London (best with filters)

---

## 🔬 AFTER BACKFILL (Update Expected)

Once 2020-2023 data is backfilled:
- Sample size will increase ~2.5x
- Win rates may adjust slightly
- Total R will scale up proportionally
- May discover new patterns
- **Will rerun all backtests and update this document**

**Current results are valid** but will be more robust with full dataset.

---

## ✅ CONFIDENCE LEVEL

**HIGH (for current 2024-2026 data):**
- All ORBs have >450 trades
- 2 years is adequate sample
- Results are stable across configurations
- Ready for paper trading

**WILL INCREASE (after backfill):**
- 5+ years of data = more robust
- Can split in-sample / out-of-sample
- Better validation of patterns
- More confidence in long-term edges

---

## 📚 FILES REFERENCE

### Current Analysis:
- `backtest_asia_orbs_current.py` - Asia ORB backtest (2024-2026)
- `backtest_london_optimized.py` - London ORB backtest (2024-2026)
- `asia_orb_backtest_current.csv` - Full Asia results
- `london_backtest_results.csv` - Full London results

### Framework Docs:
- `ASIA_LONDON_FRAMEWORK.md` - Engine A (liquidity logic)
- `ORB_OUTCOME_MOMENTUM.md` - Engine B (outcome correlations)
- `LONDON_BEST_SETUPS.md` - Detailed London analysis
- `HOW_TO_TRADE_LONDON.md` - London implementation guide

### Database:
- `gold.db` - Current database (2024-2026)
- `DATABASE_AUDIT_REPORT.md` - Data integrity check

---

**Last Updated:** 2026-01-12 (Current 2024-2026 data)
**Status:** Ready for paper trading (will update after backfill)
**Confidence Level:** HIGH (adequate sample size)
