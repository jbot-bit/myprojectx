# Quick Start Guide - Trading the Canonical System

**Last Updated:** 2026-01-12

---

## 🎯 YOU ARE HERE

You have:
- ✅ Complete parameter sweep (252 configs tested)
- ✅ Data integrity verified (all tests passed)
- ✅ Canonical parameters locked
- ✅ All 6 ORBs proven tradeable
- ✅ NY ORBs discovered as best performers

**Now what?**

---

## 🚀 START TRADING IN 3 STEPS

### **STEP 1: Read the Ruleset (15 minutes)**

📖 **Read:** `TRADING_RULESET_CANONICAL.md`

This is your primary reference. It contains:
- All 6 ORBs with locked optimal parameters
- Complete implementation details
- Entry/stop/target calculations
- Daily routine
- Risk management

**Key takeaway:** Parameters are LOCKED. Do not deviate.

---

### **STEP 2: Choose Your Tier (5 minutes)**

Pick one:

#### **TIER 1: Conservative** 🟢 (RECOMMENDED)
- **Trade:** 09:00, 11:00, 18:00 ORBs
- **Expected:** +238R per year
- **Difficulty:** Easy (high win rates)
- **Psychology:** Manageable
- **Best for:** Beginners, prop accounts, building confidence

#### **TIER 2: Balanced** 🟡
- **Trade:** 09:00, 10:00, 11:00, 18:00, 00:30 ORBs
- **Expected:** +565R per year
- **Difficulty:** Medium
- **Psychology:** Mix of styles (high WR + high RR)
- **Best for:** After 50+ successful Tier 1 trades

#### **TIER 3: Full System** 🔴
- **Trade:** All 6 ORBs
- **Expected:** +585R per year (database-verified)
- **Difficulty:** Hard
- **Psychology:** Requires discipline (managing 6 positions)
- **Best for:** After 200+ trades, mental readiness for volatility

**Recommendation:** Start with Tier 1, graduate to higher tiers as confidence builds.

---

### **STEP 3: Paper Trade (50+ trades minimum)**

Before risking real money:

1. **Set up paper trading account** (broker's demo or manual tracking)
2. **Trade Tier 1 for 50+ trades** (will take ~1-2 months)
3. **Log every trade:**
   - Date
   - ORB (09:00, 11:00, 18:00)
   - Direction (UP/DOWN)
   - Entry price
   - Stop price
   - Target price
   - Outcome (WIN/LOSS)
   - R multiple (+1.0, -1.0, etc.)

4. **Calculate stats after 50 trades:**
   - Total R
   - Win rate
   - Avg R per trade
   - Compare to expected (from canonical ruleset)

5. **Proceed to live only if:**
   - Total R is positive
   - Win rate is within ±5% of expected
   - You followed rules on every trade
   - You feel confident with the process

---

## 📋 DAILY CHECKLIST

### **Morning Prep (Before 09:00):**
- [ ] Check account balance
- [ ] Calculate position sizes for today's ORB ranges
- [ ] Set alerts for ORB close times (09:05, 11:05, 18:05)
- [ ] Mental check: Calm, focused, ready to follow rules

### **During Trading Hours:**

**09:00-09:05:** Watch 09:00 ORB form
- Record high, low
- Wait for 09:05 close

**09:05+:** Check for breakout
- If close > high → Enter UP
- If close < low → Enter DOWN
- Set stop at opposite edge
- Set target at entry + 1.0R
- Log trade

**11:00-11:05:** Watch 11:00 ORB form
- Record high, low
- Wait for 11:05 close

**11:05+:** Check for breakout
- If close > high → Enter UP
- If close < low → Enter DOWN
- Set stop at opposite edge
- Set target at entry + 1.0R
- Log trade

**18:00-18:05:** Watch 18:00 ORB form
- Record high, low
- Wait for 18:05 close

**18:05+:** Check for breakout
- If close > high → Enter UP
- If close < low → Enter DOWN
- Set stop at opposite edge
- Set target at entry + 2.0R
- Log trade

### **End of Day:**
- [ ] Review all trades
- [ ] Update trade log
- [ ] Calculate daily P&L in R
- [ ] Note any rule violations
- [ ] Plan for tomorrow

---

## 🧮 POSITION SIZING

**Formula:**
```
Position Size = (Account × Risk% per R) / (ORB Range in $ × Contract Multiplier)
```

**Example (MGC):**
- Account: $50,000
- Risk per R: 1% = $500
- ORB range: 50 ticks = 5.0 points
- MGC contract multiplier: 10
- ORB range in $: 5.0 × 10 = $50

**Position Size = $500 / $50 = 10 contracts**

**Simplification:**
Since MGC tick = $1 (0.10 × 10):
```
Position Size = (Risk in $) / (ORB range in ticks)
Position Size = $500 / 50 ticks = 10 contracts
```

**Rule:** Recalculate EVERY trade (ORB range varies daily)

---

## 📊 TRACKING PERFORMANCE

### **Required Metrics:**

**Per Trade:**
- Date
- ORB
- Direction
- Entry/Stop/Target
- Outcome (WIN/LOSS)
- R multiple

**Weekly Summary:**
- Total trades
- Wins/Losses
- Win rate
- Total R
- Avg R
- Compare to expected

**Monthly Review:**
- Compare to backtest expectations
- Identify patterns (time of day, market conditions)
- Check for rule violations
- Adjust if needed (but don't change parameters!)

---

## 🚨 COMMON MISTAKES TO AVOID

### **1. Changing Parameters**
❌ "I'll use RR 2.0 instead of 1.0 for 09:00"
✅ Stick to canonical parameters (1.0 for 09:00)

### **2. Entering Early**
❌ Entering on wick outside ORB
✅ Wait for CLOSE outside ORB

### **3. Moving Stops**
❌ "It's close to my stop, I'll move it tighter"
✅ Set and forget, let system work

### **4. Taking Profit Early**
❌ "I'm up 0.5R, I'll take it"
✅ Let it run to target (or stop)

### **5. Adding Discretionary Filters**
❌ "Market feels weak, I'll skip this signal"
✅ Trade the signal or don't trade

### **6. Trading Without ORB Confirmation**
❌ Entering before ORB closes
✅ Wait full 5 minutes for ORB to form

### **7. Not Logging Trades**
❌ Trading without tracking
✅ Log EVERY trade immediately

---

## 📈 WHEN TO UPGRADE TIERS

### **From Tier 1 → Tier 2:**

Upgrade when:
- ✅ 50+ Tier 1 trades completed
- ✅ Total R is positive
- ✅ Win rate within ±5% of expected
- ✅ Comfortable with RR 1.0 and 2.0 psychology
- ✅ Ready to learn RR 3.0 (10:00 ORB)

**Action:** Review performance in `CORRECTED_PERFORMANCE_SUMMARY.md` before adding more ORBs

---

### **From Tier 2 → Tier 3:**

Upgrade when:
- ✅ 100+ total trades completed
- ✅ Consistently profitable for 3+ months
- ✅ Comfortable managing multiple positions
- ✅ Ready to add night session ORBs (23:00, 00:30)
- ✅ Can handle 6 simultaneous positions

**Caution:** Tier 3 is psychologically demanding (managing all 6 ORBs requires discipline)

---

## 🎓 ADVANCED RESOURCES

### **For Night Session ORBs (23:00, 00:30):**
📖 **Read:** `TRADING_PLAYBOOK_COMPLETE.md` (Night Session section)

Learn:
- Why HALF SL mode works for night sessions
- Position sizing considerations
- Managing lower win rates (61-69% vs 71%+ for day sessions)
- Realistic performance expectations (+0.231R to +0.387R avg)

### **For London ORB Enhancements:**
📖 **Read:** `LONDON_BEST_SETUPS.md`

Learn:
- Asia range filters (100-200 ticks)
- NY_HIGH directional filters
- Advanced London configurations

### **For Prop Accounts:**
📖 **Read:** `ASIA_PROP_SAFETY_REPORT.md`

Learn:
- Max 1 trade/day strategies
- Daily loss limit management
- Safest ORBs for prop firms

---

## ✅ SUCCESS CRITERIA

### **After 50 Trades:**
- [ ] Total R: Positive
- [ ] Win rate: Within ±5% of expected per ORB
- [ ] Rule violations: <5% of trades
- [ ] Confidence: High
- [ ] Ready to continue or upgrade tier

### **After 200 Trades:**
- [ ] Consistent profitability (3+ months)
- [ ] Comfortable with all tier ORBs
- [ ] Emotional control maintained
- [ ] System is second nature
- [ ] Ready for live trading

---

## 🎯 YOUR PATH FORWARD

### **Week 1-2:**
- Read `TRADING_RULESET_CANONICAL.md` thoroughly
- Choose Tier 1 (recommended)
- Set up paper trading
- Start tracking ORBs (don't trade yet, just observe)

### **Week 3-4:**
- Begin paper trading Tier 1
- Log every trade meticulously
- Review daily

### **Month 2:**
- Continue paper trading
- Aim for 50+ trades
- Calculate stats
- Compare to expected

### **Month 3:**
- If stats look good → Go live with small size
- If not → Continue paper trading, identify issues
- Read advanced guides if adding tiers

### **Month 4+:**
- Scale up position size gradually
- Consider adding Tier 2 ORBs
- Continue logging and reviewing

---

## 📞 HELP & SUPPORT

### **If Results Don't Match Expected:**

1. **Check rule violations:**
   - Entering early?
   - Moving stops?
   - Taking profit early?

2. **Verify calculations:**
   - ORB range correct?
   - Stop placement correct?
   - Target calculation correct?

3. **Check sample size:**
   - <20 trades: Too early to judge
   - 20-50 trades: Variance still high
   - 50+ trades: Stats should converge

4. **Review data:**
   - Are you tracking the right ORB times?
   - Timezone correct (Australia/Brisbane)?
   - Bar data clean?

### **If Emotional Issues:**

1. Read psychology sections in:
   - `TRADING_RULESET_CANONICAL.md`
   - `NY_ORB_TRADING_GUIDE.md`

2. Reduce position size (risk 0.5% instead of 1%)

3. Trade fewer ORBs (stick to Tier 1 longer)

4. Take breaks after losing streaks

---

## 🎉 FINAL WORDS

**You have everything you need:**
- Proven system (252 configs tested)
- Verified data (all audits passed)
- Clear parameters (locked and optimal)
- Implementation guides (step-by-step)
- Support docs (for every scenario)

**What you do with it is up to you.**

**Start conservative. Be patient. Follow the rules. Log everything. Trust the process.**

**The edge is there. The system works. Now execute.**

---

**Files You Need:**
1. `TRADING_RULESET_CANONICAL.md` - Your bible
2. `NY_ORB_TRADING_GUIDE.md` - For adding NY ORBs
3. `CANONICAL_UPDATE_SUMMARY.md` - What changed and why

**Optional Reading:**
- `LONDON_BEST_SETUPS.md` - Advanced London
- `ASIA_PROP_SAFETY_REPORT.md` - Prop accounts
- `TERMINOLOGY_EXPLAINED.md` - Concepts explained

---

**Good luck. Trade well. Stay disciplined.**

**The system is canonical. The data is verified. The parameters are locked.**

**You're ready.**
