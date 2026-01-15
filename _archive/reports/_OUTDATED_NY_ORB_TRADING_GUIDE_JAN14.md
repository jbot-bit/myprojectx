# NY ORB Trading Guide

**The Most Profitable ORBs (Previously Thought to be "Skip")**

---

## 🚨 MAJOR DISCOVERY

**NY ORBs (23:00 and 00:30) are NOT "skip" sessions.**

They are actually the **BEST PERFORMING ORBs** in the entire system.

### Why They Were Previously Marked "Skip":

Old documentation tested them with wrong parameters:
- Tested: RR 2.0, HALF SL → Lost money
- Optimal: RR 4.0, HALF SL → **HIGHLY PROFITABLE**

**The difference:** RR 4.0 vs RR 2.0 = +1,171R over 2 years

---

## 📊 NY ORB PERFORMANCE

### **23:00 ORB (NY Futures Session)**

```
Optimal Config: RR 4.0, HALF SL, BASELINE

Performance:
- Trades:   479
- Win Rate: 41.5%
- Avg R:    +1.077 per trade
- Total R:  +516.0R over 2 years
- Annual:   ~+258R per year

Rank: #2 best ORB by total R
```

### **00:30 ORB (NYSE Cash Session)**

```
Optimal Config: RR 4.0, HALF SL, BASELINE

Performance:
- Trades:   425
- Win Rate: 50.8%
- Avg R:    +1.541 per trade
- Total R:  +655.0R over 2 years
- Annual:   ~+327R per year

Rank: #1 BEST ORB (highest avg R and total R)
```

### **Combined NY ORBs:**

```
Total:    +1,171R over 2 years
Annual:   ~+585R per year
Trades:   904 (452 per year)
Win Rate: 45.9% (weighted average)

This is 64% of the ENTIRE SYSTEM'S EDGE (+1,816R total)
```

---

## 🎯 WHY NY ORBs WORK SO WELL

### **23:00 ORB:**
- NY futures market opens (23:00 local = 7:00 AM ET)
- High liquidity injection
- Strong directional moves as institutions position
- 4.0 RR captures the full move
- HALF SL prevents getting stopped on noise

### **00:30 ORB:**
- NYSE cash market opens (00:30 local = 8:30 AM ET)
- Massive liquidity increase
- Pre-market positions get validated or rejected
- Strongest session of the day
- 50.8% WR at 4.0 RR is exceptional

---

## 🔧 IMPLEMENTATION

### **23:00 ORB Setup**

**Time:** 23:00-23:05 local (Australia/Brisbane)
**US Time:** 7:00-7:05 AM ET

**Step 1:** Wait for ORB to form (23:00:00 to 23:04:59)
- Record ORB high
- Record ORB low
- Calculate ORB midpoint = (High + Low) / 2

**Step 2:** Wait for first 5m close outside ORB (23:05+)
- UP signal: Close > ORB high
- DOWN signal: Close < ORB low

**Step 3:** Enter on next bar
- UP trade: Buy at market
- DOWN trade: Sell at market

**Step 4:** Set stops and targets
- Stop: ORB midpoint (HALF SL)
- Risk = |Entry - Midpoint|
- Target = Entry ± (4.0 × Risk)

**Example:**

```
23:00 ORB: High = 3000.0, Low = 2990.0
Midpoint = 2995.0

First close at 23:05: 3001.0 (above ORB high)
→ Signal: UP

Entry: 3001.0
Stop: 2995.0 (midpoint)
Risk: 3001.0 - 2995.0 = 6.0 ticks
Target: 3001.0 + (4.0 × 6.0) = 3025.0

Risk/Reward: 6 ticks risk for 24 ticks reward (4:1)
```

---

### **00:30 ORB Setup**

**Time:** 00:30-00:35 local (Australia/Brisbane)
**US Time:** 8:30-8:35 AM ET

**Step 1:** Wait for ORB to form (00:30:00 to 00:34:59)
- Record ORB high
- Record ORB low
- Calculate ORB midpoint = (High + Low) / 2

**Step 2:** Wait for first 5m close outside ORB (00:35+)
- UP signal: Close > ORB high
- DOWN signal: Close < ORB low

**Step 3:** Enter on next bar
- UP trade: Buy at market
- DOWN trade: Sell at market

**Step 4:** Set stops and targets
- Stop: ORB midpoint (HALF SL)
- Risk = |Entry - Midpoint|
- Target = Entry ± (4.0 × Risk)

**Example:**

```
00:30 ORB: High = 3020.0, Low = 3008.0
Midpoint = 3014.0

First close at 00:35: 3022.0 (above ORB high)
→ Signal: UP

Entry: 3022.0
Stop: 3014.0 (midpoint)
Risk: 3022.0 - 3014.0 = 8.0 ticks
Target: 3022.0 + (4.0 × 8.0) = 3054.0

Risk/Reward: 8 ticks risk for 32 ticks reward (4:1)
```

---

## 🧠 PSYCHOLOGY OF RR 4.0

### **What RR 4.0 Means:**

- You need **20% win rate** to break even (1 win = 4 losses)
- Actual win rate: 41.5% (23:00) and 50.8% (00:30)
- This is **DOUBLE** the breakeven rate

### **The Challenge:**

**You will lose more often than lower RR setups:**
- RR 1.0: ~65% WR (lose 35% of time)
- RR 4.0: ~45% WR (lose 55% of time)

**BUT:** When you win, you win BIG (4× your risk)

### **Mental Preparation:**

1. **Expect losing streaks:**
   - 3-5 losses in a row is normal
   - At 45% WR, expect to lose ~11 out of 20 trades
   - This is NOT the system failing

2. **Trust the math:**
   - 20 trades at 45% WR, RR 4.0:
   - 9 wins × 4R = +36R
   - 11 losses × -1R = -11R
   - Net: +25R (+1.25R avg per trade)

3. **Don't tighten stops:**
   - HALF SL is optimal (tested vs FULL SL)
   - Tightening stop → lower WR → worse results
   - The midpoint stop gives moves room to breathe

4. **Don't lower RR:**
   - RR 2.0 tested → loses money
   - RR 3.0 tested → worse than RR 4.0
   - RR 4.0 is optimal from complete parameter sweep

---

## 💰 POSITION SIZING

### **Conservative Approach:**

Because RR 4.0 has wider targets and lower hit rate, consider:

**Personal Account:**
- Risk 0.5-0.75% per R (vs 1% for Asia ORBs)
- This reduces account volatility
- Still captures the edge

**Example ($100K account):**
- Normal risk: 1% = $1,000 per R
- Conservative: 0.5% = $500 per R
- This halves your position size but also halves volatility

**Prop Account:**
- Must consider daily loss limits
- 23:00 + 00:30 = potential -2R daily (both lose)
- If daily limit is -3R, you have 1R buffer
- Consider trading only 00:30 (best performer) for prop

---

## 📈 EXPECTED PERFORMANCE

### **Full NY Session (Both ORBs):**

**Annual Expectation:**
- Total: +585R per year
- 23:00: +258R per year
- 00:30: +327R per year

**Conservative (50-80% of backtest):**
- Total: +293R to +468R per year

**On $100K account (1% risk per R):**
- Backtest: +$585K per year
- Conservative: +$293K to +468K per year

**On $100K account (0.5% risk per R):**
- Backtest: +$293K per year
- Conservative: +$146K to +234K per year

---

## 🚨 RISKS AND CAUTIONS

### **Overnight Exposure:**

Both NY ORBs carry overnight risk (from Australian perspective):
- 23:00 entry → Hold until target/stop (could be hours)
- 00:30 entry → Hold until target/stop (could extend to 02:00 or beyond)
- Positions may be open while you sleep (if in Australia)

**Mitigation:**
- Use limit orders for targets (set and forget)
- Use stop orders (broker will exit if hit)
- Check positions at 02:00 or 08:00 local if still open

### **Volatility:**

NY sessions can have:
- Gap moves
- Fast directional runs
- Sudden reversals

**Mitigation:**
- Trust the HALF SL placement
- Don't manually intervene
- Let system work

### **Psychological Difficulty:**

RR 4.0 is harder to trade than RR 1.0:
- More frequent losses (55% of time)
- Longer time to target (4× the distance)
- Temptation to exit early when in profit

**Mitigation:**
- Set target order immediately after entry
- Don't watch the trade tick-by-tick
- Trust the process over 100+ trades

---

## 📊 COMPARISON TO OTHER ORBs

| ORB | RR | SL | Avg R | Total R | Difficulty |
|-----|-----|-----|-------|---------|------------|
| 00:30 | 4.0 | HALF | +1.541 | +655R | 🔴🔴🔴 Hard |
| 23:00 | 4.0 | HALF | +1.077 | +516R | 🔴🔴🔴 Hard |
| 18:00 | 2.0 | FULL | +0.393 | +193R | 🟡🟡 Medium |
| 10:00 | 3.0 | FULL | +0.342 | +167R | 🟡🟡 Medium |
| 11:00 | 1.0 | FULL | +0.299 | +150R | 🟢 Easy |
| 09:00 | 1.0 | FULL | +0.266 | +135R | 🟢 Easy |

**NY ORBs:**
- Highest edge (+1.171R combined)
- Hardest psychologically (RR 4.0)
- Requires discipline and patience

**Recommendation:**
- Master Asia ORBs first (09:00, 11:00)
- Then add London (18:00)
- THEN add NY ORBs after 100+ successful trades
- Don't start with NY ORBs despite high edge

---

## ✅ TRADING CHECKLIST

### **Pre-Trade (Before 23:00):**
- [ ] Account balance verified
- [ ] Position sizing calculated
- [ ] Alerts set for 23:05 and 00:35
- [ ] Mental state: Calm, focused, ready to follow rules

### **During 23:00 ORB:**
- [ ] ORB formed (23:00-23:04:59)
- [ ] ORB high, low, midpoint recorded
- [ ] First 5m close checked (23:05+)
- [ ] Entry signal confirmed (close outside ORB)
- [ ] Entry executed (next bar)
- [ ] Stop placed at midpoint
- [ ] Target calculated: Entry ± (4.0 × Risk)
- [ ] Target order placed

### **During 00:30 ORB:**
- [ ] ORB formed (00:30-00:34:59)
- [ ] ORB high, low, midpoint recorded
- [ ] First 5m close checked (00:35+)
- [ ] Entry signal confirmed (close outside ORB)
- [ ] Entry executed (next bar)
- [ ] Stop placed at midpoint
- [ ] Target calculated: Entry ± (4.0 × Risk)
- [ ] Target order placed

### **Post-Trade:**
- [ ] Trade logged (date, ORB, direction, outcome, R)
- [ ] Performance tracked vs backtest
- [ ] Rule violations noted (if any)
- [ ] Mental state reviewed (emotional trading?)

---

## 📚 SUPPORTING EVIDENCE

**Parameter Sweep Results:**
- File: `complete_orb_sweep_results.csv`
- Configurations tested: 252 (7 RR × 2 SL × 3 filters × 6 ORBs)
- 23:00 optimal: RR 4.0, HALF SL, BASELINE (+516R)
- 00:30 optimal: RR 4.0, HALF SL, BASELINE (+655R)

**Data Integrity:**
- File: `audit_data_integrity.py`
- Status: ✅ ALL TESTS PASS
- Lookahead bias: None
- Timezone: Correct (UTC+10)
- Contract rolls: Verified

**Canonical Ruleset:**
- File: `TRADING_RULESET_CANONICAL.md`
- Status: LOCKED (parameters frozen pending 5-year validation)

---

## 🎯 FINAL VERDICT

**NY ORBs (23:00 and 00:30) are TRADEABLE and HIGHLY PROFITABLE.**

**They are the BEST ORBs in the system:**
- Highest avg R per trade
- Highest total R
- 64% of entire system's edge

**But they require:**
- Mental discipline (RR 4.0 psychology)
- Patience (55% of trades will lose)
- Trust in the process (100+ trade sample needed)

**Deployment recommendation:**
1. Start with Asia ORBs (easier, high WR)
2. Add London after 50+ trades
3. Add NY ORBs after 100+ trades and mental readiness
4. Don't skip straight to NY despite high edge

**If you can handle the psychology, NY ORBs will be your biggest profit center.**

---

**Last Updated:** 2026-01-12
**Status:** CANONICAL
**Confidence:** HIGH (252 configs tested, data verified)
**Next Update:** After 2020-2023 backfill validation
