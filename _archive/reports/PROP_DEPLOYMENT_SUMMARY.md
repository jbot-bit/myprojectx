# Prop Deployment Summary

**Date**: 2026-01-12
**Status**: ✅ Prop-safe configurations validated
**Data**: 2024-2026 (740 days)

---

## ✅ CONFIRMED: Asia ORBs CAN Be Prop-Safe

**With the right constraints.**

---

## 🚨 THE PROBLEM (Full Frequency)

**Original backtest** (all 3 Asia ORBs per day):
- 09:00 ORB: +125R (487 trades, RR 1.0)
- 10:00 ORB: +154R (455 trades, RR 2.5)
- 11:00 ORB: +139R (465 trades, RR 1.0)
- **Combined**: +418R (1,407 trades)

**Looks great, BUT**:
- Max intraday loss: **-3R** (all 3 lose same day)
- Happens ~10-15 times per year
- **VIOLATES** most prop firm daily limits (-2R to -3R)
- **NOT PROP-SAFE**

---

## ✅ THE SOLUTION (Max 1 Trade/Day)

**Prop-safe backtest** (max 1 Asia trade per day):
- MAX 1 TRADE PER DAY (no clustered losses)
- WORST-CASE same-bar resolution (conservative)
- Full risk metrics (losing streaks, max DD)

### Results:

| Mode | Trades | WR% | Avg R | Total R/yr | Max Streak | Max DD |
|------|--------|-----|-------|------------|------------|--------|
| **11:00 ONLY** (RR 1.0) | 465 | **64.9%** | +0.299 | +70R | **5** | **-6.0R** |
| **10:00 ONLY** (RR 2.5) | 455 | 38.2% | **+0.338** | +77R | 8 | -11.5R |
| **FIRST_BREAK** (09→10→11) | 520 | 62.7% | +0.288 | +75R | 6 | -6.0R |

**All modes**: Max daily loss = -1R (guaranteed)

---

## 🏆 RECOMMENDED FOR PROP

### **TIER 1: SAFEST**

**11:00 ORB ONLY (RR 1.0, FULL SL)**

```
WHY:
- Highest win rate: 64.9%
- Lowest losing streak: 5 trades
- Lowest drawdown: -6.0R
- Most psychologically manageable
- Safe for ANY prop firm

PERFORMANCE:
- +0.299R avg per trade
- ~233 trades/year
- ~+70R per year
- Max daily loss: -1R

PROP COMPATIBILITY:
- -2R daily limit: ✅ Safe (6R buffer after max streak)
- -3R daily limit: ✅ Safe (7R buffer after max streak)
- -4R+ daily limit: ✅ Very safe

RISK:
- Max losing streak: 5 trades = -5R
- Max drawdown: -6.0R
- Occurs over multiple days, not clustered
```

**This is the NO-BRAINER choice for prop accounts.**

---

### **TIER 2: HIGHEST EDGE**

**10:00 ORB ONLY (RR 2.5, FULL SL)**

```
WHY:
- Highest avg R: +0.338 per trade
- Mid-session timing catches momentum
- Higher RR compensates for lower WR

PERFORMANCE:
- +0.338R avg per trade
- ~228 trades/year
- ~+77R per year
- Max daily loss: -1R

CAUTION:
- Max losing streak: 8 trades = -8R
- Max drawdown: -11.5R
- Lower win rate: 38.2%
- Requires stronger psychology

PROP COMPATIBILITY:
- -2R daily limit: ⚠️ Risky (only 3R buffer after max streak)
- -3R daily limit: ✅ Safe (4R buffer after max streak)
- -4R+ daily limit: ✅ Safe

RISK:
- Worst 5 losing streaks: -8R, -8R, -8R, -7R, -7R
- Need mental resilience for long streaks
```

**For experienced traders who can handle volatility.**

---

### **TIER 3: BALANCED**

**FIRST_BREAK (09:00 → 10:00 → 11:00)**

```
WHY:
- Captures whichever ORB has edge that day
- More trading opportunities (520/year)
- Good balance of WR and edge

PERFORMANCE:
- +0.288R avg per trade
- ~260 trades/year
- ~+75R per year
- Max daily loss: -1R

RISK:
- Max losing streak: 6 trades = -6R
- Max drawdown: -6.0R
- Win rate: 62.7%

PROP COMPATIBILITY:
- -2R daily limit: ✅ Safe (5R buffer after max streak)
- -3R daily limit: ✅ Safe (6R buffer after max streak)
- -4R+ daily limit: ✅ Very safe
```

**Good middle ground between safety and edge.**

---

## 📊 EXPECTED PROP PERFORMANCE

### $50K Prop Account (1% risk per R):

**11:00 ONLY mode**:
- Position sizing: $500 per R
- Trades: ~233 per year
- Expected R: +70R/year
- Expected $: +$35,000/year
- Conservative (50-80%): +$17,500 to +$28,000/year
- Prop payout (80%): +$14,000 to +$22,400/year

**Max drawdown**: -6.0R = -$3,000 (manageable)

---

## 🚫 WHAT NOT TO DO

### ❌ NEVER: Trade all 3 Asia ORBs in prop account

**Why**: -3R daily loss violates prop limits

**Example bad day**:
- 09:00 breaks UP → Lose -1R
- 10:00 breaks DOWN → Lose -1R
- 11:00 breaks UP → Lose -1R
- **Daily loss**: -3R → **ACCOUNT VIOLATION**

Happens ~10-15 times per year in volatile conditions.

---

### ❌ NEVER: Use half-SL mode

**Full SL outperforms half-SL by +78.5R** in baseline tests.

Reason: Tighter stops get hit more often, lower WR doesn't compensate.

---

### ❌ NEVER: Skip filters

**MAX_STOP=100**: Prevents trading outlier volatile days
**TP_CAP=150**: Prevents unrealistic targets on huge ORBs

Without filters, results degrade and risk increases.

---

## 📋 IMPLEMENTATION CHECKLIST

**For Prop Accounts**:

### Pre-Trading:
- [ ] Choose ONE mode (recommend: 11:00 ONLY)
- [ ] Set hard rule: MAX 1 TRADE PER DAY
- [ ] Use FULL SL (opposite ORB edge)
- [ ] Apply filters: MAX_STOP=100, TP_CAP=150
- [ ] Risk 1% per R (conservative prop sizing)
- [ ] Verify prop firm daily limit (-2R, -3R, etc.)

### During Trading:
- [ ] Track daily P&L in R (not $)
- [ ] Stop trading after -1R loss (done for day)
- [ ] Log every trade (date, ORB, outcome, R)
- [ ] Monitor cumulative drawdown
- [ ] Track losing streak count

### Psychology:
- [ ] Expect 5-6 trade losing streaks (normal)
- [ ] 64.9% WR ≠ no losing streaks
- [ ] One trade per day = easier to walk away
- [ ] Focus on process, not daily results
- [ ] Trust the edge over 200+ trades

---

## 🎯 SIMPLE START GUIDE

**Day 1 Setup**:
1. Read `ASIA_PROP_SAFETY_REPORT.md` (full details)
2. Choose 11:00 ONLY mode (safest)
3. Set alert for 11:00 ORB (Australia/Brisbane time)
4. Risk 1% per R ($500 per R on $50K account)

**Daily Routine**:
1. Wait for 11:00-11:05 ORB to form
2. Check filters: ORB range 0-100 ticks? (skip if >100)
3. Wait for first 5m close outside ORB
4. Enter in break direction
5. Stop at opposite ORB edge
6. Target at 1.0 × risk
7. **Done for the day** (no more Asia trades)

**Weekly Review**:
- Log all trades in spreadsheet
- Calculate weekly R (should average +0.3R per trade)
- Review losing streaks (max 5 expected)
- Adjust if rules not followed

---

## 📚 DOCUMENTATION

**Essential reading**:
- `ASIA_PROP_SAFETY_REPORT.md` - Full prop analysis
- `TRADING_RULESET_CURRENT.md` - Current trading rules
- `backtest_asia_prop_safe.py` - Backtest code

**Framework docs**:
- `TERMINOLOGY_EXPLAINED.md` - Beginner concepts
- `ASIA_LONDON_FRAMEWORK.md` - Engine A (liquidity logic)
- `ORB_OUTCOME_MOMENTUM.md` - Engine B (outcome momentum)

**Analysis**:
- `asia_prop_safe_results.csv` - Full backtest results
- `DATABASE_AUDIT_REPORT.md` - Data integrity check

---

## ⚠️ DATA DISCLAIMER

**Current data**: 2024-01-02 to 2026-01-10 (2 years, 740 days)

**After overnight backfill** (2020-2023 data):
- Sample size will increase ~2.5x to 1,800 days
- Win rates may adjust ±2-5%
- Max losing streaks may extend by 1-2 trades
- **All reports will be updated with 5-year validation**

**Current results are valid** for paper trading and prop evals now, but will be more robust with full 5-year dataset.

---

## ✅ FINAL VERDICT

**Asia ORBs ARE prop-safe** with these constraints:

1. ✅ Max 1 trade per day (11:00 ONLY recommended)
2. ✅ Full SL mode (opposite ORB edge)
3. ✅ Apply filters (MAX_STOP=100, TP_CAP=150)
4. ✅ Conservative sizing (1% risk per R)
5. ✅ Strong process discipline

**Expected results**:
- +70R per year (11:00 mode)
- 64.9% win rate
- Max 5-trade losing streak
- Max -6.0R drawdown
- **Compatible with all major prop firms**

**Ready to deploy**: Paper trade for 50+ trades, then go live with prop eval.

---

**Last Updated**: 2026-01-12
**Status**: ✅ Prop-safe validated with worst-case testing
**Next**: Run overnight backfill, revalidate with 5-year data
